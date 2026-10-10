"""OpenAI 兼容协议的 LLM 教练实现。

一个实现覆盖 Qwen（DashScope 兼容模式）/ DeepSeek / GLM / 本地 Ollama 等所有
OpenAI 风格 ``/chat/completions`` 端点：只换 ``LLM_API_BASE`` + ``LLM_MODEL`` + key。
结构化输出靠提示词约束 + JSON 容错解析，失败抛异常由责任链降级。
"""

from __future__ import annotations

import json

import httpx

from app.core.config import get_settings

from .base import CoachContext, CoachReply

SYSTEM_PROMPT_ZH = """你是「AI Healthier Every Day」的自我照护伙伴，陪伴用户长期坚持温和活动、
平衡、呼吸放松与生活肌力练习。用户可能包含中老年人与慢病人群。
铁律：
1. 不编造数据：只能引用 context 中给出的结构化事实（今日计划、最近报告、动作名、连续打卡天数）。
2. 不做医疗诊断或治疗建议；用户提到疼痛或症状时，先共情，建议降低强度，并提示咨询专业医疗人员。
3. 不评判用户身材或外貌，只谈动作与习惯安排。
4. 只输出一个 JSON 对象：{"reply": "...", "suggestions": ["...", "..."]}。
   reply 不超过 120 个汉字；suggestions 最多 3 条，每条不超过 30 个汉字。
5. 全程使用中文，语气鼓励、口语化、不啰嗦。"""

SYSTEM_PROMPT_EN = """You are the self-care companion of "AI Healthier Every Day": you help the user
keep a long-term self-care routine of gentle mobility, balance, breathing
relaxation and everyday strength. The audience may include older adults and
people managing chronic conditions.
HARD RULES:
1. Never invent data: only cite the structured facts given in context
   (today plan, latest report, exercise, streak days).
2. Never diagnose or give medical advice. If the user mentions pain or
   symptoms, acknowledge, suggest lowering intensity, and involve a
   healthcare professional.
3. Never comment on body shape or appearance; talk about habits and form only.
4. Output exactly one JSON object: {"reply": "...", "suggestions": ["...", "..."]}.
   reply: at most 80 words. suggestions: up to 3, each under 12 words.
5. Reply in English. Warm, encouraging, plain words, no jargon."""


def _extract_json(text: str) -> dict:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("no json object in llm response")
    return json.loads(cleaned[start : end + 1])


class OpenAICompatCoach:
    """OpenAI 兼容端点的教练实现。"""

    name = "llm"

    def __init__(self, timeout: float = 30.0) -> None:
        self._timeout = timeout

    def available(self) -> bool:
        s = get_settings()
        return bool(s.LLM_API_KEY and s.LLM_API_BASE)

    def chat(self, messages: list[dict], context: CoachContext, lang: str = "zh") -> CoachReply:
        s = get_settings()
        zh = lang != "en"
        context_lines = []
        if context.today_plan:
            context_lines.append(f"今日计划：{context.today_plan}" if zh else f"Today plan: {context.today_plan}")
        if context.latest_report:
            context_lines.append(
                f"最近训练报告：{context.latest_report}" if zh else f"Latest report: {context.latest_report}"
            )
        if context.exercise:
            context_lines.append(f"当前动作：{context.exercise}" if zh else f"Exercise: {context.exercise}")
        if context.streak_days is not None:
            context_lines.append(
                f"连续打卡：{context.streak_days} 天" if zh else f"Check-in streak: {context.streak_days} days"
            )
        if zh:
            context_block = "结构化事实（只能引用这些，不得编造其他数据）：\n" + "\n".join(
                context_lines
            ) if context_lines else "（暂无训练数据）"
        else:
            context_block = "STRUCTURED FACTS (cite only these, never invent other data):\n" + "\n".join(
                context_lines
            ) if context_lines else "(no data yet)"

        payload_messages = [
            {"role": "system", "content": SYSTEM_PROMPT_ZH if zh else SYSTEM_PROMPT_EN}
        ]
        payload_messages.append({"role": "system", "content": context_block})
        # 历史只保留最近 8 条，控制 token 成本。
        payload_messages.extend(messages[-8:])

        payload = {"model": s.LLM_MODEL, "messages": payload_messages}
        headers = {"Authorization": f"Bearer {s.LLM_API_KEY}"}
        with httpx.Client(timeout=self._timeout) as client:
            resp = client.post(f"{s.LLM_API_BASE}/chat/completions", json=payload, headers=headers)
            resp.raise_for_status()
            body = resp.json()

        text = body["choices"][0]["message"]["content"]
        parsed = _extract_json(text)
        suggestions = [str(x) for x in (parsed.get("suggestions") or [])][:3]
        tokens = int(body.get("usage", {}).get("total_tokens") or 0)
        return CoachReply(
            reply=str(parsed.get("reply") or text.strip()),
            suggestions=suggestions,
            source="llm",
            tokens=tokens,
        )
