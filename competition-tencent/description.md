# Project Description (form field 3 — paste per section)

> Bilingual draft: English is the primary paste; Chinese follows each block for reference.

## Short Blurb (field 2, <10 words)

**An AI companion that makes daily self-care stick.**

中文：每天 3 分钟，AI 陪你把自我照护坚持下来。

## 1. Project Overview — scenarios, users, value

AI Healthier Every Day is an agentic self-care companion for long-term habit building. It turns the smallest safe daily actions — 2–4 minutes of gentle mobility, balance & fall-prevention, breathing relaxation, and everyday strength — into a durable routine through: a deterministic weekly plan, one-tap check-ins with streaks, in-browser pose AI that counts reps and corrects form in real time, and a tool-calling AI agent that plans the week, adapts to the user's energy, and enforces safety. Target users: (a) older adults at risk of deconditioning and falls, (b) sedentary desk workers, (c) people managing chronic conditions who need safe daily movement. Value proposition: hospital-grade caution (deterministic safety guardrails, no diagnosis, video never leaves the device) combined with consumer-grade ease (zero equipment, zero install, one URL).

中文：AI Healthier Every Day 是一个面向长期自我照护的智能体伴侣。它把最微小的安全日常动作（2–4 分钟的温和活动、平衡防跌倒、呼吸放松、生活肌力）变成可持续的习惯：确定性周计划 + 一键打卡连续记录 + 浏览器内姿态 AI 实时计次纠错 + 会做计划、懂适配、守红线的工具调用 Agent。目标用户：有跌倒/失能风险的老年人、久坐办公人群、需要安全日常运动的慢病人群。价值主张：医院级谨慎（确定性安全红线、不做诊断、视频不出设备）+ 消费级易用（零器械、零安装、一个网址）。

## 2. Real-World Scenario Insights — pain points, audience, core problem

Insight source: long-term-condition self-management practice (NTU LKCMedicine healthcare context). Home-programme adherence is the classic failure point — patients receive a leaflet or a single physiotherapy demonstration, then practice alone; typical home-exercise adherence falls below 50% within weeks, and unsupervised older adults fear injury more than they fear inactivity. Meanwhile, mainstream fitness apps assume already-motivated users with 30+ minutes and bodies without limitations. The core problem we solve is closing the daily loop — *did you do it, did you do it right, and was it safe* — with near-zero friction.

中文：洞察来自慢病长期自我管理的现实（NTU LKCMedicine 医疗语境）：居家锻炼方案的最大失败点是坚持率——患者拿到一张纸或看过一次演示后就独自练习，数周内坚持率通常跌破 50%；老年人对无人指导下受伤的恐惧甚至超过对不活动的担忧。而主流健身 App 默认用户已有动力、有 30 分钟以上时间、身体无限制。我们要解决的核心问题是：以近乎零摩擦闭环「今天做了吗→做得对不对→安不安全」。

## 3. Comprehensive Solution Design — business & technical architecture, and how prompts drive the AI generation

**Business architecture.** Free, fully open product; no paywall. A built-in metering plane (API-key auth + SQLite usage ledger of calls and tokens) is the monetization hook: platform/vendor ecosystems can attach billing without any product change. Two distribution channels share one deterministic core: the browser web app (global/Singapore) and a WeChat mini-program (China).

**Technical architecture (three layers, graceful degradation everywhere).**
- L1 — Browser pose AI: MediaPipe Pose Landmarker runs entirely in-browser; rep counting and form cues come from our deterministic angle-rule state machine (the exact code covered by unit tests, shared with the mini-program via a sync script). Privacy by design: video frames never leave the device.
- L2 — Optional cloud vision: our self-trained ST-GCN action recognizer plus a VLM snapshot commentator (OpenAI-compatible; Hunyuan-ready).
- L3 — Agentic coach: an LLM reasoner with a deterministic tool belt — self-care catalog lookup, 7-day plan builder, calendar, and a red-flag safety screen — under a hard step budget. Degradation chain: agent → single-shot LLM → template coach; the service never returns 5xx.

**How prompts drive the AI generation.** The system prompt encodes persona plus hard rules: cite only tool results or user-provided structured facts; never invent numbers; never diagnose; output strict JSON. Prompts drive *orchestration and narration*, not data: "for any weekly plan call build_week_plan; before recommending any exercise call lookup_exercise" — so plans, counts and safety calls stay deterministic while the LLM chooses tools, sequences multi-step reasoning, and words the coaching. The red-flag guardrail runs *outside* the LLM and overrides its output. Paired EN/ZH prompt variants keep the coach in the user's language.

中文：商业架构：产品完全免费开放、无付费墙；内置计量数据面（API-key 鉴权 + 调用/token 用量账本）留给平台/厂商生态计费接入，作品侧零改动；浏览器 Web App（新加坡/全球）与微信小程序（中国）双渠道共享同一确定性内核。技术架构三层：L1 浏览器姿态 AI（MediaPipe 全程在端内，计次纠错走确定性角度规则状态机——与小程序共享同一份被测试覆盖的代码，视频帧不出设备）；L2 可选云端视觉（自研 ST-GCN + VLM 快照评述，OpenAI 兼容、可接混元）；L3 智能体教练（LLM 推理 + 确定性工具带：动作目录/周计划/日历/红旗安全筛查，硬步数预算；降级链 Agent→单轮 LLM→模板，服务永不 5xx）。提示词如何驱动生成：系统提示词写入人设与铁律（只引用工具结果或用户结构化事实、不编造数值、不做诊断、严格 JSON 输出）；提示词驱动的是「编排与表达」而非数据——周计划必须调 build_week_plan、推荐动作前必须调 lookup_exercise，数值与安全判定留在确定性代码里；红旗安全筛查独立于 LLM 运行并可覆盖其输出；中英双语提示词保证回复跟随用户语言。

## 4. Business Value — quantifiable metrics / defined impact

North-star metric: **sustained adherence**. Instrumented in-product: check-in streak distribution, weekly active minutes per user, session completion rate, form-correction acceptance. Targets: ≥3 check-ins/week still sustained at week 8; ≥70% guided-session completion; 100% interception of red-flag messages (deterministic, test-covered — verified in CI). For partners (insurers, employers, community care): engagement is the leading indicator of claims-reducing behaviour change; the usage-metering data plane supports per-key partner reporting. Impact definition: closing the daily self-care loop for people whom conventional fitness products exclude.

中文：北极星指标是「持续坚持率」。产品内建度量：打卡连续分布、周活跃分钟、引导练习完成率、纠错采纳率。目标：第 8 周仍保持每周 ≥3 次打卡；引导练习完成率 ≥70%；红旗消息拦截率 100%（确定性实现、测试覆盖、CI 验证）。对合作方（保险、雇主、社区照护）：参与度是行为改变从而降低医疗支出的先行指标；计量数据面支持按合作方维度的报表。影响定义：把传统健身产品排除在外的人群的每日自我照护闭环补上。
