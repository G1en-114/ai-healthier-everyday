/* Bilingual UI dictionary (EN primary for Singapore judges, ZH toggle). */
(function () {
  const I18N = {
    en: {
      tagline: "Small daily self-care, guided by AI",
      nav_today: "Today", nav_train: "Train", nav_coach: "AI Coach", nav_progress: "Progress",
      checkin_today: "Check in today",
      checked_in: "Checked in — see you tomorrow!",
      checkin_hint: "A check-in counts: any session or this button.",
      streak_days: "day streak",
      today_plan: "Today's gentle plan",
      plan_note: "Built by a deterministic weekly planner — no AI invented it. Swap any session in Train.",
      daily_tip: "Self-care tip of the day",
      choose_exercise: "Choose a self-care exercise",
      back: "Back",
      reps: "reps",
      finish_session: "Finish",
      start_camera: "Start with camera AI counting",
      start_timer: "Start guided timer",
      coach_title: "Your self-care agent",
      coach_sub: "Plans, adapts, and checks on safety — never diagnoses.",
      ask_placeholder: "Ask about your routine, energy, or an exercise…",
      send: "Send",
      best_streak: "best streak",
      total_sessions: "sessions",
      total_minutes: "minutes",
      last14: "Last 14 days",
      history: "History",
      export_data: "Export my data",
      disclaimer:
        "AI Healthier Every Day supports healthy habits — it is not a medical device and does not diagnose. Stop if you feel pain, dizziness or breathlessness, and consult a healthcare professional. In an emergency, call your local emergency number.",
      status_live: "AI agent online",
      status_fallback: "Offline tips mode",
      status_checking: "checking…",
      greeting_morning: "Good morning", greeting_afternoon: "Good afternoon", greeting_evening: "Good evening",
      min: "min",
      level_gentle: "gentle", level_moderate: "moderate",
      trackable: "AI rep counting", timer_only: "guided timer",
      cat_mobility: "Mobility", cat_balance: "Balance", cat_breathing: "Breathing",
      cat_strength: "Strength", cat_flexibility: "Flexibility", cat_all: "All",
      purpose: "Why", cues: "Form cues", safety: "Stay safe",
      phase_ready: "Get into position — I'm watching your joints",
      phase_up: "Nice — now lower slowly",
      phase_down: "Good depth — drive back up",
      keep_in_frame: "Keep your whole body in the frame",
      pa_shallow: "Go a little deeper", pa_back: "Keep your back neutral", pa_hipshift: "Balance your weight evenly",
      pa_hipsag: "Don't let the hips sag", pa_hipike: "Don't pike the hips up", pa_lean: "Stay upright a little more",
      pa_lockout: "Straighten fully at the top",
      sum_reps: "reps", sum_standard: "standard reps", sum_minutes: "minutes",
      sum_issues: "form reminders", sum_done: "Session logged. Small steps, kept daily — that's the whole trick.",
      sum_none: "No reps counted — try standing further back so your whole body is visible.",
      tool_lookup: "catalog", tool_plan: "planner", tool_today: "clock", tool_safety: "safety screen",
      src_agent: "AI agent", src_template: "offline tips", src_llm: "AI coach",
      thinking: "Thinking…",
      quick_1: "Build me a gentle weekly plan",
      quick_2: "I feel low on energy today — what should I do?",
      quick_3: "How do I do sit-to-stands safely?",
      quick_4: "I've stuck to this for a week — what's next?",
      empty_history: "No sessions yet — your first one will show up here.",
      export_done: "Downloaded your data as JSON.",
      session_min: "min",
      chat_error: "The coach service is unreachable — your data is safe locally. Try again later.",
      all_categories: "Showing all categories",
    },
    zh: {
      tagline: "每天一点自我照护，AI 陪你坚持",
      nav_today: "今天", nav_train: "练习", nav_coach: "AI 伙伴", nav_progress: "进度",
      checkin_today: "今日打卡",
      checked_in: "已打卡，明天见！",
      checkin_hint: "完成一次练习或点这里都算打卡。",
      streak_days: "连续天数",
      today_plan: "今天的温和计划",
      plan_note: "计划由确定性周计划器生成——不是 AI 编的。可在「练习」里随时替换动作。",
      daily_tip: "今日自我照护小贴士",
      choose_exercise: "选择一个自我照护练习",
      back: "返回",
      reps: "次",
      finish_session: "结束",
      start_camera: "摄像头 AI 计数开始",
      start_timer: "引导计时开始",
      coach_title: "你的自我照护伙伴",
      coach_sub: "会做计划、会调整、会守安全线——绝不做诊断。",
      ask_placeholder: "聊聊你的计划、精力或某个动作…",
      send: "发送",
      best_streak: "最长连续",
      total_sessions: "练习次数",
      total_minutes: "总分钟数",
      last14: "最近 14 天",
      history: "历史记录",
      export_data: "导出我的数据",
      disclaimer:
        "AI Healthier Every Day 帮助你养成健康习惯——它不是医疗器械，不做诊断。如出现疼痛、头晕或气短请立即停止，并咨询专业医护人员。紧急情况请拨打当地急救电话。",
      status_live: "AI 伙伴在线",
      status_fallback: "离线建议模式",
      status_checking: "检测中…",
      greeting_morning: "早上好", greeting_afternoon: "下午好", greeting_evening: "晚上好",
      min: "分钟",
      level_gentle: "温和", level_moderate: "中等",
      trackable: "AI 计次", timer_only: "引导计时",
      cat_mobility: "活动度", cat_balance: "平衡", cat_breathing: "呼吸",
      cat_strength: "肌力", cat_flexibility: "柔韧", cat_all: "全部",
      purpose: "为什么做", cues: "动作要点", safety: "安全提示",
      phase_ready: "摆好姿势，我在看着你的关节",
      phase_up: "很好——现在缓慢下落",
      phase_down: "到位了——发力回到起始位",
      keep_in_frame: "请让全身保持在画面内",
      pa_shallow: "再往下一点", pa_back: "腰背保持中立", pa_hipshift: "重心放均匀",
      pa_hipsag: "髋不要塌", pa_hipike: "髋不要撅起", pa_lean: "上身再立直一点",
      pa_lockout: "顶端要完全伸直",
      sum_reps: "次", sum_standard: "标准次数", sum_minutes: "分钟",
      sum_issues: "动作提醒", sum_done: "已记录。小步子，天天见——秘诀就这一条。",
      sum_none: "没有计到次数——试着站远一点，让全身都在画面里。",
      tool_lookup: "动作库", tool_plan: "计划器", tool_today: "日历", tool_safety: "安全筛查",
      src_agent: "AI 伙伴", src_template: "离线建议", src_llm: "AI 教练",
      thinking: "思考中…",
      quick_1: "帮我排一个温和的一周计划",
      quick_2: "今天没什么精力，该做点什么？",
      quick_3: "坐站练习怎样做才安全？",
      quick_4: "我已经坚持一周了，接下来呢？",
      empty_history: "还没有记录——完成第一次练习就会出现在这里。",
      export_done: "已下载你的数据（JSON）。",
      session_min: "分钟",
      chat_error: "暂时连不上教练服务——你的数据都安全地在本地。稍后再试。",
      all_categories: "显示全部分类",
    },
  };

  let current = "en";

  function t(key) {
    const d = I18N[current] || I18N.en;
    return d[key] != null ? d[key] : (I18N.en[key] != null ? I18N.en[key] : key);
  }

  function locale() { return current; }

  function setLocale(lang) {
    current = lang === "zh" ? "zh" : "en";
    document.documentElement.lang = current === "zh" ? "zh-CN" : "en";
    applyStatic();
  }

  function applyStatic() {
    document.querySelectorAll("[data-i18n]").forEach((el) => { el.textContent = t(el.dataset.i18n); });
    document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => { el.placeholder = t(el.dataset.i18nPlaceholder); });
    const toggle = document.getElementById("lang-toggle");
    if (toggle) toggle.textContent = current === "en" ? "中文" : "English";
  }

  window.I18N = { t, locale, setLocale, applyStatic };
})();
