"""模型服务路由（Tencent Cloud AI CAN DO IT Hackathon Singapore 2026，
Healthcare Track — "AI Healthier Every Day"）。

对外接口：
- ``POST /api/vision/analyze``   云端动作分析（ST-GCN 关键点识别 + 可选 VLM 快照评述）
- ``POST /api/coach/chat``       教练对话（LLM 单轮，模板兜底；小程序用）
- ``POST /api/coach/agent``      自我照护 Agent（工具调用多步循环 + 确定性安全红线；Web 用）
- ``POST /api/plan/explain``     计划个性化解释（同教练链）
- ``GET  /api/exercises``        自我照护动作目录（双语，Web 用）
- ``GET  /api/usage``            用量查询（按 API-key 汇总，为后续计费售卖预留数据面）
- ``GET  /api/status``           服务能力状态

商业化定位：本作品只提供模型能力与计量数据面，不做定价与收费——
计费售卖由平台/厂商在生态侧接入（API-key + usage 即接入点）。

设计红线：任何模型故障都降级为桩/模板而非 5xx；
数值与安全判定只出自确定性规则（guardrails / catalog / pose rules），
LLM/VLM 文字不参与计分、不越过安全红线。
"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.core.guardrails import screen_text
from app.deterministic.selfcare_catalog import (
    CATEGORY_LABELS,
    build_week_plan,
    list_exercises,
)
from app.providers.coach_llm import AgentReply, CoachAgent, CoachChain, CoachContext
from app.providers.vision import (
    StgcnFrameAnalyzer,
    StubVisionAnalyzer,
    VlmAdvisor,
    VisionAnalysisResult,
)
from app.services.metering import get_meter

router = APIRouter(prefix="/api", tags=["model-service"])

# 进程级单例：惰性加载，各 provider 自行判断可用性。
_stgcn = StgcnFrameAnalyzer()
_vlm = VlmAdvisor()
_coach = CoachChain()
_agent = CoachAgent()


# ---- 请求模型 ----


class VisionAnalyzeRequest(BaseModel):
    """云端动作分析请求。

    ``frames`` 为 COCO-17 关键点序列（[帧数][17][2]，与 ST-GCN 训练格式一致）；
    ``image_base64`` 为可选训练快照，配置了 VLM 密钥时产出文字评述。
    """

    exercise: str | None = None
    frames: list[list[list[float]]] = Field(default_factory=list)
    image_base64: str | None = None


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class CoachChatRequest(BaseModel):
    messages: list[ChatMessage]
    context: CoachContext = Field(default_factory=CoachContext)
    lang: Literal["zh", "en"] = "zh"


class AgentChatRequest(BaseModel):
    """自我照护 Agent 请求。

    ``message`` 为本轮用户输入；``messages`` 为可选历史（客户端维护）；
    ``context`` 携带客户端本地事实（计划/打卡等），Agent 端按 session 记忆合并。
    """

    message: str = Field(min_length=1, max_length=2000)
    messages: list[ChatMessage] = Field(default_factory=list)
    context: CoachContext = Field(default_factory=CoachContext)
    session_id: str = Field(default="web", max_length=64)
    lang: Literal["zh", "en"] = "en"


class PlanExplainRequest(BaseModel):
    plan_summary: str
    assessment: str | None = None


# ---- 鉴权 ----


def require_api_key(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> str:
    """模型服务 API-key 鉴权。

    未配置 ``MODEL_SERVICE_API_KEYS`` 时为开发模式：放行并归到 ``dev`` 账户
    （``/api/status`` 会标注 auth=disabled-dev，生产/演示前必须配置）。
    """
    configured = [
        key.strip()
        for key in (get_settings().MODEL_SERVICE_API_KEYS or "").split(",")
        if key.strip()
    ]
    if not configured:
        return "dev"
    if x_api_key in configured:
        return x_api_key
    raise HTTPException(status_code=401, detail="invalid or missing X-API-Key")


# ---- 接口 ----


@router.post("/vision/analyze", response_model=VisionAnalysisResult)
def vision_analyze(
    req: VisionAnalyzeRequest, api_key: str = Depends(require_api_key)
) -> VisionAnalysisResult:
    """云端动作分析：ST-GCN 关键点识别 + 确定性角度规则 + 可选 VLM 评述。"""
    update: dict = {}
    if _stgcn.available():
        try:
            result = _stgcn.analyze_frames(req.frames, req.exercise)
        except Exception as exc:  # noqa: BLE001 - 模型运行期故障降级到桩
            result = StubVisionAnalyzer(f"{type(exc).__name__}").analyze_frames(
                req.frames, req.exercise
            )
    else:
        result = StubVisionAnalyzer(_stgcn.disabled_reason()).analyze_frames(
            req.frames, req.exercise
        )

    if req.image_base64 and _vlm.available():
        try:
            advised = _vlm.advise_image(req.image_base64, req.exercise)
            if advised.get("assessment"):
                update["vlm_assessment"] = advised["assessment"]
        except Exception:  # noqa: BLE001 - VLM 故障只影响评述，不影响主结果
            update["vlm_assessment"] = None

    if update:
        result = result.model_copy(update=update)
    get_meter().record(api_key, "vision")
    return result


@router.post("/coach/chat")
def coach_chat(req: CoachChatRequest, api_key: str = Depends(require_api_key)):
    """LLM 教练对话；LLM 不可用时模板兜底（source 字段标明来源）。"""
    reply = _coach.chat([m.model_dump() for m in req.messages], req.context, lang=req.lang)
    get_meter().record(api_key, "coach", tokens=reply.tokens)
    return reply


@router.post("/coach/agent")
def coach_agent(req: AgentChatRequest, api_key: str = Depends(require_api_key)) -> AgentReply:
    """自我照护 Agent：LLM 推理 + 确定性工具循环 + 独立安全红线。

    降级链：Agent（工具循环）→ 单轮 LLM → 模板。任一环节失败自动落到
    下一层，source 字段标明实际来源，服务永不因大模型故障 5xx。
    安全红线（guardrails.screen_text）在 LLM 之外确定性执行：
    命中红旗症状时无论 LLM 输出如何都会前置就医建议并标记 flags。
    """
    history = [m.model_dump() for m in req.messages][-12:]
    messages = history + [{"role": "user", "content": req.message}]

    reply: AgentReply
    if _agent.available():
        try:
            reply = _agent.run(
                messages,
                req.context,
                lang=req.lang,
                session_id=req.session_id,
            )
        except Exception:  # noqa: BLE001 - Agent 故障降级到单轮/模板
            reply = AgentReply(**_coach.chat(messages, req.context, lang=req.lang).model_dump())
    else:
        reply = AgentReply(**_coach.chat(messages, req.context, lang=req.lang).model_dump())

    # 独立于 LLM 的确定性红线：命中红旗症状则强制前置就医建议。
    safety = screen_text(req.message)
    if safety.escalate and not reply.safety_flags:
        advice = safety.advice_zh if req.lang == "zh" else safety.advice_en
        reply = reply.model_copy(
            update={
                "safety_flags": safety.categories,
                "safety_advice": advice,
                "reply": f"{advice}\n\n{reply.reply}",
            }
        )

    get_meter().record(api_key, "agent", tokens=reply.tokens)
    return reply


@router.get("/exercises")
def exercises(
    category: str | None = Query(default=None),
    lang: Literal["zh", "en"] = Query(default="en"),
):
    """自我照护动作目录（双语）；category 非法时返回全量。"""
    items = list_exercises(category)
    label = CATEGORY_LABELS.get(category or "", {})
    return {
        "lang": lang,
        "category_label": (label.get(lang) if label else None),
        "items": [
            {
                "id": e.id,
                "name": e.name_zh if lang == "zh" else e.name_en,
                "name_alt": e.name_en if lang == "zh" else e.name_zh,
                "category": e.category,
                "level": e.level,
                "minutes": e.minutes,
                "purpose": e.purpose_zh if lang == "zh" else e.purpose_en,
                "cues": e.cues_zh if lang == "zh" else e.cues_en,
                "safety": e.safety_zh if lang == "zh" else e.safety_en,
                "trackable": e.trackable,
            }
            for e in items
        ],
    }


@router.get("/selfcare/plan")
def selfcare_plan(
    goal: str = Query(default="general"),
    level: Literal["gentle", "moderate"] = Query(default="gentle"),
    minutes_per_day: int = Query(default=10, ge=4, le=45),
):
    """确定性 7 天自我照护计划（不经过任何 LLM）。"""
    plan = build_week_plan(goal=goal, level=level, minutes_per_day=minutes_per_day)
    return {"goal": goal, "level": level, "minutes_per_day": minutes_per_day, "days": plan}


@router.post("/plan/explain")
def plan_explain(req: PlanExplainRequest, api_key: str = Depends(require_api_key)):
    """计划个性化解释：让用户明白「为什么今天的计划适合我」。"""
    context = CoachContext(today_plan=req.plan_summary, latest_report=req.assessment)
    messages = [
        {
            "role": "user",
            "content": "请用两三句话解释为什么今天的训练计划适合我，并给出一条今天执行时的建议。",
        }
    ]
    reply = _coach.chat(messages, context)
    get_meter().record(api_key, "plan", tokens=reply.tokens)
    return reply


@router.get("/usage")
def usage(api_key: str = Depends(require_api_key)):
    """按 API-key 的用量汇总（调用量 + token）：为后续计费售卖预留的数据面。"""
    return get_meter().summary(api_key)


@router.get("/status")
def status():
    """服务能力状态矩阵：客户端据此展示「云端 AI」可用性。"""
    configured = bool(
        [
            k.strip()
            for k in (get_settings().MODEL_SERVICE_API_KEYS or "").split(",")
            if k.strip()
        ]
    )
    return {
        "stgcn": _stgcn.available(),
        "vlm": _vlm.available(),
        "llm": bool(get_settings().LLM_API_KEY and get_settings().LLM_API_BASE),
        "agent": _agent.available(),
        "auth": "enabled" if configured else "disabled-dev",
    }
