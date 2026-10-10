"""Tool-calling self-care agent (Agentic AI layer).

The hackathon brief asks for Agentic AI solutions. This module is the agent:
an LLM reasoner that may call a small belt of DETERMINISTIC tools over
several steps before answering. Two red lines hold:

1. Every tool is pure local code (catalog lookup, plan builder, safety
   screen, clock). Numbers and safety calls never come from the LLM.
2. Any failure — no API key, provider without tool support, network error,
   unparseable output — raises and the caller falls back to the single-shot
   CoachChain and then to the template coach. The service never 5xxs.

An independent deterministic guardrail (``app.core.guardrails``) always runs
on the latest user message in the route layer, with or without the LLM.
"""

from __future__ import annotations

import datetime as _dt
import json

import httpx
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.core.guardrails import SafetyScreenResult, format_flags, screen_text
from app.deterministic.selfcare_catalog import (
    build_week_plan,
    get_exercise,
    list_exercises,
)

from .base import CoachContext, CoachReply

MAX_STEPS = 4
MEMORY_LIMIT = 24


class AgentReply(CoachReply):
    """CoachReply plus agent-trace fields (all optional, UI-safe)."""

    source: str = "agent"  # "agent" | "llm" | "template"
    tools_used: list[str] = Field(default_factory=list)
    steps: int = 0
    safety_flags: list[str] = Field(default_factory=list)
    safety_advice: str = ""


# ---- Tool belt (deterministic; serialised for the provider) ----

TOOL_SCHEMAS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "lookup_exercise",
            "description": (
                "Look up one self-care exercise by id: purpose, form cues, "
                "safety notes, duration. Use before recommending or "
                "explaining any specific exercise."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "exercise_id": {"type": "string"},
                },
                "required": ["exercise_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_exercises",
            "description": (
                "List the self-care catalog, optionally filtered by category: "
                "mobility | balance | breathing | strength | flexibility."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {"type": "string"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "build_week_plan",
            "description": (
                "Deterministic 7-day self-care plan. goal: general | energy | "
                "mobility | balance | stress; level: gentle | moderate; "
                "minutes_per_day: int."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "goal": {"type": "string"},
                    "level": {"type": "string"},
                    "minutes_per_day": {"type": "integer"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "today",
            "description": "Current local date and weekday. Use for any 'today' reference.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]


def _today() -> str:
    now = _dt.datetime.now()
    return now.strftime("%Y-%m-%d %A")


def _dispatch_tool(name: str, args: dict) -> str:
    """Execute one tool call and return its JSON result string."""
    if name == "lookup_exercise":
        e = get_exercise(str(args.get("exercise_id", "")))
        if e is None:
            return json.dumps({"error": "unknown_exercise_id"})
        return e.model_dump_json()
    if name == "list_exercises":
        cat = args.get("category") or None
        items = list_exercises(cat if isinstance(cat, str) else None)
        return json.dumps(
            [
                {
                    "id": e.id,
                    "name_en": e.name_en,
                    "name_zh": e.name_zh,
                    "category": e.category,
                    "level": e.level,
                    "minutes": e.minutes,
                }
                for e in items
            ],
            ensure_ascii=False,
        )
    if name == "build_week_plan":
        plan = build_week_plan(
            goal=str(args.get("goal") or "general"),
            level=str(args.get("level") or "gentle"),
            minutes_per_day=int(args.get("minutes_per_day") or 10),
        )
        return json.dumps(plan, ensure_ascii=False)
    if name == "today":
        return json.dumps({"today": _today()})
    return json.dumps({"error": "unknown_tool"})


class SessionFactMemory:
    """Tiny in-process memory of per-session structured facts.

    The web client reports its local facts (plan summary, streak) with each
    message; the memory merges and remembers them, so the agent can reference
    earlier facts without the client resending everything. Purely in-process
    and evictable — no PII beyond what the client volunteers.
    """

    def __init__(self) -> None:
        self._facts: dict[str, dict] = {}
        self._seen: dict[str, _dt.datetime] = {}

    def remember(self, session_id: str, context: CoachContext) -> CoachContext:
        """Merge ``context`` into the session store and return the merged view."""
        sid = session_id or "default"
        now = _dt.datetime.now()
        stored = self._facts.get(sid, {})
        merged = stored | context.model_dump(exclude_none=True)
        self._facts[sid] = merged
        self._seen[sid] = now
        self._evict(now)
        return CoachContext(**merged)

    def _evict(self, now: _dt.datetime, ttl_seconds: int = 3600) -> None:
        stale = [k for k, t in self._seen.items() if (now - t).total_seconds() > ttl_seconds]
        for k in stale:
            self._facts.pop(k, None)
            self._seen.pop(k, None)


class CoachAgent:
    """LLM reasoner + deterministic tools, with hard step budget."""

    name = "agent"

    def __init__(self, timeout: float = 30.0) -> None:
        self._timeout = timeout
        self.memory = SessionFactMemory()

    def available(self) -> bool:
        s = get_settings()
        return bool(s.LLM_API_KEY and s.LLM_API_BASE)

    # -- prompt -----------------------------------------------------------

    def _system_prompt(self, lang: str, context: CoachContext, safety: SafetyScreenResult) -> str:
        locale_rule = (
            "Reply in the user's language; default to English (Singapore)."
            if lang == "en"
            else "全程使用中文。"
        )
        guard = (
            f"DETERMINISTIC SAFETY SCREEN on the latest user message: "
            f"flags={format_flags(safety)}. "
            if safety.escalate
            else ""
        )
        return f"""You are the AI self-care companion of "AI Healthier Every Day" — an
everyday companion that helps people build and keep long-term self-care
habits: gentle mobility, balance, breathing, everyday strength and rest.

Audience includes older adults and people managing long-term conditions.
Tone: warm, encouraging, concrete; short sentences; no jargon.

HARD RULES:
1. Never diagnose, never interpret symptoms, never replace professional care.
   If the user mentions pain or symptoms, acknowledge, advise lowering
   intensity, and involve a healthcare professional.
2. Only cite facts returned by tools or given in STRUCTURED FACTS below.
   Never invent numbers, streaks, plans or exercise names outside the catalog.
3. For exercise recommendations, call lookup_exercise / list_exercises first;
   for weekly plans call build_week_plan; for any "today" call today().
4. You are one part of a system that already screens for red flags. {guard}
5. Output exactly one JSON object and nothing else:
   {{"reply": "...", "suggestions": ["...", "..."]}}
   reply: at most 90 words. suggestions: 0-3 short actionable next steps.

CONTEXT — STRUCTURED FACTS (only these; may be empty):
{_format_facts(context)}

{locale_rule}"""

    # -- loop -------------------------------------------------------------

    def run(
        self,
        messages: list[dict],
        context: CoachContext,
        lang: str = "en",
        session_id: str = "",
        max_steps: int = MAX_STEPS,
    ) -> AgentReply:
        s = get_settings()
        # Deterministic guardrail runs regardless of what the LLM does.
        last_user = next(
            (m["content"] for m in reversed(messages) if m.get("role") == "user"), ""
        )
        safety = screen_text(str(last_user))
        context = self.memory.remember(session_id, context)

        payload_messages: list[dict] = [
            {"role": "system", "content": self._system_prompt(lang, context, safety)}
        ]
        payload_messages.extend(messages[-MEMORY_LIMIT:])

        tools_used: list[str] = []
        headers = {"Authorization": f"Bearer {s.LLM_API_KEY}"}
        total_tokens = 0

        with httpx.Client(timeout=self._timeout) as client:
            for step in range(max_steps):
                payload = {
                    "model": s.LLM_MODEL,
                    "messages": payload_messages,
                    "tools": TOOL_SCHEMAS,
                    "tool_choice": "auto",
                }
                resp = client.post(
                    f"{s.LLM_API_BASE}/chat/completions", json=payload, headers=headers
                )
                resp.raise_for_status()
                body = resp.json()
                total_tokens += int(body.get("usage", {}).get("total_tokens") or 0)
                msg = body["choices"][0]["message"]
                calls = msg.get("tool_calls") or []

                if not calls:
                    parsed = self._parse_reply(str(msg.get("content") or ""))
                    return self._finalize(parsed, lang, safety, tools_used, step + 1, total_tokens)

                payload_messages.append(
                    {
                        "role": "assistant",
                        "content": msg.get("content") or "",
                        "tool_calls": calls,
                    }
                )
                for call in calls[:4]:
                    fn = call.get("function", {})
                    name = str(fn.get("name") or "")
                    try:
                        args = json.loads(fn.get("arguments") or "{}")
                    except json.JSONDecodeError:
                        args = {}
                    result = _dispatch_tool(name, args if isinstance(args, dict) else {})
                    tools_used.append(name)
                    payload_messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": call.get("id") or name,
                            "content": result,
                        }
                    )
            # Step budget exhausted without a final answer: raise and let the
            # caller fall back instead of fabricating one.
            raise RuntimeError("agent step budget exhausted")

    @staticmethod
    def _parse_reply(text: str) -> dict:
        from .openai_compat import _extract_json

        parsed = _extract_json(text)
        if not isinstance(parsed.get("reply"), str) or not parsed["reply"].strip():
            raise ValueError("empty reply in agent output")
        return parsed

    def _finalize(
        self,
        parsed: dict,
        lang: str,
        safety: SafetyScreenResult,
        tools_used: list[str],
        steps: int,
        tokens: int,
    ) -> AgentReply:
        reply_text = str(parsed["reply"]).strip()
        if safety.escalate:
            # Guardrail text is prepended verbatim — it must survive even if
            # the LLM softens the rest of the reply.
            advice = safety.advice_zh if lang == "zh" else safety.advice_en
            reply_text = f"{advice}\n\n{reply_text}"
        suggestions = [str(x) for x in (parsed.get("suggestions") or [])][:3]
        return AgentReply(
            reply=reply_text,
            suggestions=suggestions,
            source="agent",
            tokens=tokens,
            tools_used=tools_used,
            steps=steps,
            safety_flags=safety.categories,
            safety_advice=(safety.advice_zh if lang == "zh" else safety.advice_en)
            if safety.escalate
            else "",
        )


def _format_facts(context: CoachContext) -> str:
    lines: list[str] = []
    if context.today_plan:
        lines.append(f"- today_plan: {context.today_plan}")
    if context.latest_report:
        lines.append(f"- latest_report: {context.latest_report}")
    if context.exercise:
        lines.append(f"- exercise: {context.exercise}")
    if context.streak_days is not None:
        lines.append(f"- streak_days: {context.streak_days}")
    return "\n".join(lines) if lines else "(none yet)"
