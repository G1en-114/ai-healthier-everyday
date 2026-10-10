"""Self-care exercise catalog (bilingual, deterministic).

Purpose-built for the Tencent Cloud AI CAN DO IT Hackathon Singapore 2026,
Healthcare Track Challenge 2 — "AI Healthier Every Day: Intelligent Support
for Long-Term Self-Care" (NTU LKCMedicine).

Design rules (mirroring the project red lines):
- Pure data + pure functions. No I/O, no LLM, no randomness.
- Bilingual fields (``*_en`` / ``*_zh``): the web app picks a locale; the
  agent tool belt feeds these entries verbatim to the LLM for narration only.
- ``trackable`` entries map to deterministic pose rules (rep counting in the
  browser via MediaPipe landmarks + ``poseRules`` port). Non-trackable
  entries run in guided-timer mode.
- Every entry carries explicit ``safety`` notes — this is a self-care
  companion, not a medical device; the catalog itself must communicate
  contraindications, not just the LLM.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SelfCareExercise:
    """One self-care exercise, bilingual."""

    id: str
    name_en: str
    name_zh: str
    category: str  # mobility | balance | breathing | strength | flexibility
    level: str  # gentle | moderate
    minutes: float
    purpose_en: str
    purpose_zh: str
    cues_en: tuple[str, ...]
    cues_zh: tuple[str, ...]
    safety_en: str
    safety_zh: str
    # Pose-rule key from the deterministic rep-counting rules (web + miniprogram
    # share the same state machine). None => guided-timer mode.
    trackable: str | None = None
    loads: frozenset[str] = field(default_factory=frozenset)


CATEGORY_LABELS = {
    "mobility": {"en": "Gentle Mobility", "zh": "温和活动度"},
    "balance": {"en": "Balance & Fall Prevention", "zh": "平衡与防跌倒"},
    "breathing": {"en": "Breathing & Relaxation", "zh": "呼吸与放松"},
    "strength": {"en": "Everyday Strength", "zh": "生活肌力"},
    "flexibility": {"en": "Flexibility", "zh": "柔韧拉伸"},
}


def _ex(
    id: str,
    name_en: str,
    name_zh: str,
    category: str,
    level: str,
    minutes: float,
    purpose_en: str,
    purpose_zh: str,
    cues_en: tuple[str, ...],
    cues_zh: tuple[str, ...],
    safety_en: str,
    safety_zh: str,
    trackable: str | None = None,
    loads: tuple[str, ...] = (),
) -> SelfCareExercise:
    return SelfCareExercise(
        id=id,
        name_en=name_en,
        name_zh=name_zh,
        category=category,
        level=level,
        minutes=minutes,
        purpose_en=purpose_en,
        purpose_zh=purpose_zh,
        cues_en=cues_en,
        cues_zh=cues_zh,
        safety_en=safety_en,
        safety_zh=safety_zh,
        trackable=trackable,
        loads=frozenset(loads),
    )


# Ordered by category; keep ids stable — they appear in plans, sessions and logs.
CATALOG: tuple[SelfCareExercise, ...] = (
    # ---- Gentle mobility ----
    _ex(
        "shoulder_rolls", "Shoulder Rolls", "绕肩放松",
        "mobility", "gentle", 2.0,
        "Release neck-shoulder tension from long sitting; improves upper-back circulation.",
        "缓解久坐带来的肩颈紧张，改善上背血液循环。",
        ("Move slowly, arms relaxed", "Breathe steadily, no shrugging", "Small circles first, then larger"),
        ("动作放慢，手臂放松", "呼吸均匀，不要耸肩", "先画小圈再逐渐加大"),
        "Stop if you feel pinching in the neck or shoulders.",
        "颈肩出现刺痛感立即停止。",
    ),
    _ex(
        "standing_side_reach", "Standing Side Reach", "站姿体侧伸展",
        "mobility", "gentle", 2.0,
        "Open up the side of the body; eases stiffness after long sitting.",
        "舒展身体侧面，改善久坐后的躯干僵硬。",
        ("Reach up and over, don't twist forward", "Keep both feet grounded", "Exhale as you reach"),
        ("向上再向侧，不要向前扭转", "双脚站稳不离地", "侧屈时呼气"),
        "Keep the range pain-free; avoid if you feel unsteady standing.",
        "在无痛范围内进行；站立不稳者请扶稳再做。",
    ),
    _ex(
        "seated_torso_turn", "Seated Torso Turn", "坐姿转体",
        "mobility", "gentle", 2.0,
        "Gentle spinal rotation for desk workers and chair-based users.",
        "适合办公族与不便站立者的温和脊柱旋转。",
        ("Sit tall on a firm chair", "Turn from the waist, slowly", "Look over one shoulder at a time"),
        ("坐在稳固椅子上，腰背立直", "从腰部缓慢转动", "每次转头看一侧肩膀"),
        "Move within a comfortable range; never force the twist.",
        "转到舒适幅度即可，切勿硬掰。",
    ),
    # ---- Balance & fall prevention ----
    _ex(
        "sit_to_stand", "Sit-to-Stand (Chair Squat)", "坐站练习（椅子深蹲）",
        "balance", "moderate", 3.0,
        "The single most functional strength-balance move: keeps you independent for standing up, toilets, buses.",
        "最贴近生活的平衡肌力动作：站起来、上厕所、坐公交都靠它。",
        ("Feet hip-width, slightly back from chair", "Lean chest forward, push through heels", "Stand tall, sit down slowly"),
        ("双脚与髋同宽，稍微收在椅子后", "上身前倾，脚跟发力站起", "站直身体，缓慢坐下"),
        "Use a stable chair with armrests nearby; stop at any knee pain. Trackable: counts reps via knee-angle rules.",
        "用稳固椅子，附近最好有扶手；膝盖疼痛即停。可姿态追踪：按膝关节角度规则计次。",
        trackable="squat", loads=("knee",),
    ),
    _ex(
        "single_leg_stand", "Supported Single-Leg Stand", "扶止单腿站立",
        "balance", "gentle", 2.0,
        "Trains static balance — a strong predictor of fall risk in older adults.",
        "训练静态平衡能力——平衡时间是老年人跌倒风险的重要预测指标。",
        ("Stand near a wall or counter", "Shift weight to one leg, other foot slightly up", "Eyes forward, breathe calmly"),
        ("靠近墙壁或台面", "重心移到一条腿，另一脚微抬", "目视前方，平稳呼吸"),
        "Always keep support within reach; hold only as long as steady.",
        "支撑物必须在可触及范围；稳不住就放下，量力而行。",
    ),
    _ex(
        "heel_raises", "Calf / Heel Raises", "提踵练习",
        "balance", "gentle", 2.0,
        "Strengthens calves and ankle stability for safer walking and stairs.",
        "强化小腿与踝关节稳定性，走路与上下楼梯更稳。",
        ("Hold the back of a chair lightly", "Rise slowly onto the balls of your feet", "Lower with control"),
        ("轻扶椅背", "缓慢抬起脚跟立到前脚掌", "控制速度下落"),
        "Avoid bouncing; reduce range if calves cramp.",
        "不要弹动；小腿抽筋就减小幅度。",
    ),
    # ---- Breathing & relaxation ----
    _ex(
        "box_breathing", "Box Breathing 4-4-4-4", "方块呼吸 4-4-4-4",
        "breathing", "gentle", 3.0,
        "Down-regulates stress; useful before sleep or after a tense day.",
        "平复紧张情绪，适合睡前或高压一天之后。",
        ("Inhale 4s — hold 4s — exhale 4s — hold 4s", "Sit or lie comfortably", "Follow the on-screen timer"),
        ("吸气 4 秒—屏息 4 秒—呼气 4 秒—屏息 4 秒", "坐或躺均可，身体放松", "跟着屏幕计时即可"),
        "Breathe gently, never force the holds; skip breath-holds if you are pregnant or have uncontrolled hypertension.",
        "呼吸轻柔不憋气；孕期或高血压未控制者不做屏息。",
    ),
    _ex(
        "belly_breathing", "Diaphragmatic Breathing", "腹式呼吸",
        "breathing", "gentle", 3.0,
        "Strengthens the diaphragm habit; calms the nervous system.",
        "养成横膈膜呼吸习惯，安抚自主神经。",
        ("One hand on belly, one on chest", "Belly hand rises as you inhale", "Exhale slowly, longer than inhale"),
        ("一手放腹部，一手放胸口", "吸气时腹部手抬起", "呼气比吸气更慢更长"),
        "Keep it comfortable; light-headedness means you are pushing too hard.",
        "以舒适为准；出现头晕说明过度用力。",
    ),
    # ---- Everyday strength ----
    _ex(
        "wall_pushup", "Wall Push-Up", "推墙俯卧撑",
        "strength", "gentle", 3.0,
        "Upper-body pushing strength without floor work — shoulders, chest, triceps.",
        "不下地即可练上肢推力——肩、胸、肱三头肌。",
        ("Hands at shoulder height on a wall", "Body straight, heels down", "Bend elbows slowly, push back"),
        ("双手与肩同高扶墙", "身体成一条直线，脚跟着地", "缓慢屈肘再推回"),
        "Wrist or shoulder pain: reduce depth. Trackable: counts reps via elbow-angle rules.",
        "手腕或肩膀不适就减小幅度。可姿态追踪：按肘关节角度规则计次。",
        trackable="push_up", loads=("shoulder", "wrist"),
    ),
    _ex(
        "standing_march", "Standing March", "原地踏步",
        "strength", "gentle", 3.0,
        "Low-impact cardio and hip flexion — safe daily heart-health staple.",
        "低冲击心肺激活，安全的心血管日常保养。",
        ("Stand tall, march in place", "Lift knees to a comfortable height", "Swing arms naturally"),
        ("身体立直原地踏步", "膝盖抬到舒适高度", "手臂自然摆动"),
        "Hold a chair for support if needed; keep the pace conversational.",
        "需要时可扶椅；强度以能正常说话为准。",
    ),
    _ex(
        "glute_bridge", "Glute Bridge", "臀桥",
        "strength", "moderate", 3.0,
        "Wakes up glutes and protects the lower back for lifting and walking.",
        "激活臀部肌肉，为搬物和走路保护腰部。",
        ("Lie down, knees bent, feet flat", "Push through heels, lift hips", "Squeeze gently at the top, lower slowly"),
        ("仰卧屈膝，双脚踩实", "脚跟发力抬起髋部", "顶端轻收臀，缓慢下落"),
        "Stop if the lower back cramps; keep the lift small and controlled.",
        "腰部抽筋即停；抬起幅度小而受控。",
    ),
    # ---- Flexibility ----
    _ex(
        "hamstring_stretch", "Supported Hamstring Stretch", "扶物腘绳肌拉伸",
        "flexibility", "gentle", 3.0,
        "Eases tightness behind the thighs that pulls on the lower back.",
        "放松大腿后侧紧张，减轻对腰部的牵拉。",
        ("Foot on a low step, leg nearly straight", "Hinge from the hips, back flat", "Feel a gentle pull, not pain"),
        ("脚踩低台阶，腿接近伸直", "从髋部俯身，背部平直", "有轻微牵拉感即可，不是疼痛"),
        "Never bounce; keep the standing knee soft.",
        "不要弹震；支撑腿保持微屈。",
    ),
    _ex(
        "doorway_chest_stretch", "Doorway Chest Stretch", "门框胸部拉伸",
        "flexibility", "gentle", 2.0,
        "Opens the chest after hours at desks and phones; helps posture.",
        "打开长时间伏案与低头后的胸前侧，改善体态。",
        ("Forearms on the door frame", "Step through gently until chest opens", "Breathe and hold"),
        ("前臂扶在门框上", "身体缓缓前移直到胸部展开", "保持呼吸并停留"),
        "Shoulder impingement history: lower the arm position.",
        "有肩峰撞击史者降低手臂高度。",
    ),
)

_BY_ID = {e.id: e for e in CATALOG}


def get_exercise(exercise_id: str) -> SelfCareExercise | None:
    """Look up one exercise by id (agent tool target)."""
    return _BY_ID.get(exercise_id)


def list_exercises(category: str | None = None) -> list[SelfCareExercise]:
    """List catalog entries, optionally filtered by category."""
    if category and category in CATEGORY_LABELS:
        return [e for e in CATALOG if e.category == category]
    return list(CATALOG)


def build_week_plan(
    goal: str = "general",
    level: str = "gentle",
    minutes_per_day: int = 10,
) -> list[dict]:
    """Deterministic 7-day self-care plan (no LLM involved).

    Rotates categories so each week touches mobility, balance, strength,
    breathing and flexibility; ``level`` filters or shrinks durations.
    Returns bilingual day dicts that both the API and the agent narrate.
    """
    rotate = ["mobility", "balance", "strength", "breathing", "flexibility",
              "balance", "mobility"]
    days: list[dict] = []
    names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    for i, day_name in enumerate(names):
        cat = rotate[i % len(rotate)]
        picks: list[SelfCareExercise] = []
        budget = float(max(4, minutes_per_day))
        pool = [e for e in CATALOG if e.category == cat]
        alt = [e for e in CATALOG if e.category == "breathing"]
        for e in pool:
            if e.level == "moderate" and level == "gentle":
                continue
            if budget - e.minutes < -1:
                continue
            picks.append(e)
            budget -= e.minutes
            if budget <= 0:
                break
        if not picks:  # never leave a day empty
            picks = alt[:1]
        total = round(sum(e.minutes for e in picks), 1)
        days.append({
            "day": day_name,
            "category": cat,
            "category_en": CATEGORY_LABELS[cat]["en"],
            "category_zh": CATEGORY_LABELS[cat]["zh"],
            "items": [
                {
                    "id": e.id,
                    "name_en": e.name_en,
                    "name_zh": e.name_zh,
                    "minutes": e.minutes,
                    "trackable": e.trackable,
                }
                for e in picks
            ],
            "total_minutes": total,
        })
    return days


def summarize_plan(plan: list[dict], lang: str = "en") -> str:
    """One-line human-readable plan summary (deterministic)."""
    zh = lang == "zh"
    parts = []
    for d in plan:
        names = "/".join(
            (it["name_zh"] if zh else it["name_en"]) for it in d["items"]
        )
        parts.append(f"{d['day']} {names} ({d['total_minutes']}min)")
    return "; ".join(parts)
