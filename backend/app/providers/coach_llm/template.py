"""确定性模板教练：LLM 不可用时的兜底。

只消费 ``CoachContext`` 中的结构化事实，输出固定句式，
不依赖任何外部服务，保证演示与测试确定性。
"""

from __future__ import annotations

from .base import CoachContext, CoachReply

_DEFAULT_SUGGESTIONS = [
    "训练前热身 2 分钟",
    "动作宁慢勿快，保持呼吸",
    "训练后补充水分并拉伸",
]

_DEFAULT_SUGGESTIONS_EN = [
    "Warm up for 2 minutes first",
    "Slow and steady — keep breathing",
    "Drink water and stretch afterwards",
]


class TemplateCoach:
    """模板兜底实现（中英双语）。"""

    name = "template"

    def __init__(self) -> None:
        self.last_fallback_reason: str | None = None

    def available(self) -> bool:
        return True

    def chat(self, messages: list[dict], context: CoachContext, lang: str = "zh") -> CoachReply:
        zh = lang != "en"
        parts: list[str] = []
        if context.streak_days is not None and context.streak_days > 0:
            parts.append(
                f"你已经连续打卡 {context.streak_days} 天，保持这个节奏！"
                if zh
                else f"You're on a {context.streak_days}-day streak — keep it up!"
            )
        if context.today_plan:
            parts.append(
                f"今天的计划是：{context.today_plan}。" if zh else f"Today's plan: {context.today_plan}."
            )
        if context.latest_report:
            parts.append(
                f"上次训练：{context.latest_report}" if zh else f"Last session: {context.latest_report}"
            )
        if context.exercise:
            parts.append(
                f"做 {context.exercise} 时注意动作幅度，觉得吃力就降低难度。"
                if zh
                else f"For {context.exercise}, keep the range comfortable — ease off if it feels hard."
            )
        if not parts:
            parts.append(
                "今天还没安排练习，从 1 分钟微练习开始也不错。"
                if zh
                else "Nothing scheduled yet — even 1 minute of gentle movement counts."
            )

        return CoachReply(
            reply="".join(parts),
            suggestions=list(_DEFAULT_SUGGESTIONS if zh else _DEFAULT_SUGGESTIONS_EN),
            source="template",
            tokens=0,
        )
