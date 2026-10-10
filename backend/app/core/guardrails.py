"""Deterministic safety guardrail (healthcare red lines).

Screens free text for red-flag symptoms and produces care-escalation advice.
This runs in code — NOT in the LLM — so the guardrail works even when every
model is down. It is part of the project red line: numbers and safety calls
come from deterministic rules; the LLM only narrates around them.

Scope note baked into all outputs: this is a self-care companion, not a
diagnostic device. Escalation advice always points to professional care.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SafetyFinding:
    """One matched red-flag category."""

    category: str  # e.g. "chest_pain"
    matched: str  # the exact keyword that triggered it


@dataclass
class SafetyScreenResult:
    """Screen output consumed by the agent, the API layer and the UI."""

    flags: list[SafetyFinding] = field(default_factory=list)
    escalate: bool = False
    advice_en: str = ""
    advice_zh: str = ""

    @property
    def categories(self) -> list[str]:
        return sorted({f.category for f in self.flags})


# Keyword screen: deliberately wide (over-trigger is fine — the advice is
# always "involve a professional", which is safe). English + Chinese.
_PATTERNS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "chest_pain",
        ("chest pain", "chest tightness", "chest pressure", "pressure in my chest",
         "pain in my chest", "angina",
         "胸口痛", "胸痛", "胸闷", "心口痛", "胸口疼"),
    ),
    (
        "breathing",
        ("shortness of breath", "can't breathe", "cannot breathe", "can't catch my breath",
         "hard to breathe", "breathless", "wheezing", "out of breath",
         "喘不上气", "呼吸困难", "气短", "透不过气", "喘不过气"),
    ),
    (
        "dizziness",
        ("dizzy", "dizziness", "lightheaded", "light-headed", "faint", "fainted",
         "passed out", "blackout",
         "头晕", "眩晕", "头昏", "差点晕倒", "晕厥"),
    ),
    (
        "palpitations",
        ("palpitations", "heart racing", "heart pounding", "irregular heartbeat",
         "heart palpitations",
         "心悸", "心慌", "心跳很快", "心律不齐"),
    ),
    (
        "numbness",
        ("numb", "numbness", "tingling", "pins and needles", "one side weak",
         "facial droop", "slurred speech", "weakness on one side",
         "麻木", "发麻", "手脚发麻", "一侧无力", "口齿不清", "口角歪斜"),
    ),
    (
        "acute_pain",
        ("sharp pain", "sudden pain", "severe pain", "pulled a muscle", "tore",
         "sprained", "hurt my back", "severe low back pain", "injured",
         "剧痛", "突然疼", "扭伤", "拉伤", "摔伤", "摔倒了", "闪到腰", "疼得厉害"),
    ),
    (
        "recent_events",
        ("surgery", "post-op", "just had surgery", "hospital stay",
         "recently hospitalized", "hospitalization",
         "手术", "术后", "刚出院", "住院"),
    ),
    (
        "pregnancy",
        ("pregnant", "pregnancy", "trimester",
         "怀孕", "孕期", "孕早期", "孕中期", "孕晚期"),
    ),
)

_ADVICE_EN = (
    "Stop exercising and check in with a healthcare professional before "
    "continuing. If symptoms are severe or sudden — especially chest pain, "
    "trouble breathing, one-sided weakness or fainting — seek emergency care "
    "immediately."
)
_ADVICE_ZH = (
    "请先停止运动，并在继续前咨询专业医护人员。"
    "如果症状严重或突发——尤其是胸痛、呼吸困难、单侧无力或晕倒——请立即就医。"
)


def screen_text(text: str) -> SafetyScreenResult:
    """Screen free text for red-flag symptoms (case-insensitive substring)."""
    lowered = (text or "").lower()
    findings: list[SafetyFinding] = []
    for category, keywords in _PATTERNS:
        for kw in keywords:
            if kw in lowered:
                findings.append(SafetyFinding(category=category, matched=kw))
                break  # one hit per category is enough
    result = SafetyScreenResult(flags=findings, escalate=bool(findings))
    result.advice_en = _ADVICE_EN if result.escalate else ""
    result.advice_zh = _ADVICE_ZH if result.escalate else ""
    return result


def format_flags(result: SafetyScreenResult) -> str:
    """Compact machine-readable summary for prompts/logs."""
    if not result.escalate:
        return "none"
    return ",".join(result.categories)
