/* App orchestration: tabs, Today/Train/Coach/Progress, i18n re-render.
 * Same-origin API: /api/exercises, /api/selfcare/plan, /api/coach/agent, /api/status.
 */
(function () {
  const $ = (id) => document.getElementById(id);
  const t = (k) => window.I18N.t(k);
  const locale = () => window.I18N.locale();

  let catalog = [];
  let plan = null;
  let currentCategory = "all";
  let selected = null;
  let chatHistory = [];
  const sessionId = "web-" + Math.random().toString(36).slice(2, 8);

  const AREA_KEYS = {
    shallow_depth: "pa_shallow", back_rounding: "pa_back", hip_shift: "pa_hipshift",
    hip_sag: "pa_hipsag", hip_pike: "pa_hipike", torso_lean: "pa_lean",
    incomplete_lockout: "pa_lockout",
  };
  const TOOL_KEYS = {
    lookup_exercise: "tool_lookup", list_exercises: "tool_lookup",
    build_week_plan: "tool_plan", today: "tool_today", screen_safety: "tool_safety",
  };

  /* ---------------- boot ---------------- */

  // Catalog items carry a localized `name`; plan items carry name_en/name_zh.
  const itemName = (it) =>
    locale() === "zh" ? (it.name_zh != null ? it.name_zh : it.name) : (it.name_en != null ? it.name_en : it.name);

  async function boot() {
    const stored = window.Store.lang();
    window.I18N.setLocale(stored || ((navigator.language || "en").startsWith("zh") ? "zh" : "en"));
    window.I18N.applyStatic();
    bindChrome();
    renderToday();
    renderProgress();
    initCoach();
    refreshStatus();
    const lang = locale();
    try {
      const [cat, planRes] = await Promise.all([
        fetch(`/api/exercises?lang=${lang}`).then((r) => r.json()),
        fetch(`/api/selfcare/plan?level=gentle&minutes_per_day=10`).then((r) => r.json()),
      ]);
      catalog = cat.items || [];
      plan = planRes;
    } catch {
      catalog = [];
    }
    renderToday();
    renderCatalog();
  }

  function refreshStatus() {
    const el = $("ai-status");
    el.className = "ai-status";
    $("ai-status-text").textContent = t("status_checking");
    fetch("/api/status")
      .then((r) => r.json())
      .then((s) => {
        el.className = "ai-status " + (s.agent || s.llm ? "live" : "fallback");
        $("ai-status-text").textContent = s.agent || s.llm ? t("status_live") : t("status_fallback");
      })
      .catch(() => {
        el.className = "ai-status fallback";
        $("ai-status-text").textContent = t("status_fallback");
      });
  }

  function bindChrome() {
    document.querySelectorAll(".tab").forEach((btn) => {
      btn.addEventListener("click", () => {
        document.querySelectorAll(".tab").forEach((b) => b.classList.toggle("active", b === btn));
        document.querySelectorAll(".tab-panel").forEach((p) =>
          p.classList.toggle("active", p.id === `tab-${btn.dataset.tab}`)
        );
        if (btn.dataset.tab === "progress") renderProgress();
      });
    });
    $("lang-toggle").addEventListener("click", () => {
      const next = locale() === "en" ? "zh" : "en";
      window.Store.setLang(next);
      window.I18N.setLocale(next);
      renderToday();
      renderCatalog();
      renderSelectedBrief();
      renderProgress();
      refreshStatus();
      if (catalog.length) loadCatalogLang(next);
    });
    $("checkin-btn").addEventListener("click", () => {
      window.Store.checkin(0);
      renderToday();
    });
    $("export-btn").addEventListener("click", () => {
      window.Store.exportJSON();
      $("export-btn").textContent = t("export_done");
      setTimeout(() => ($("export-btn").textContent = t("export_data")), 1600);
    });
  }

  async function loadCatalogLang(lang) {
    try {
      const cat = await fetch(`/api/exercises?lang=${lang}`).then((r) => r.json());
      catalog = cat.items || [];
      renderCatalog();
      renderSelectedBrief();
      renderToday();
    } catch { /* keep old catalog */ }
  }

  /* ---------------- Today ---------------- */

  function renderToday() {
    const h = new Date().getHours();
    $("greeting").textContent =
      h < 12 ? t("greeting_morning") : h < 18 ? t("greeting_afternoon") : t("greeting_evening");
    $("date-line").textContent = new Date().toLocaleDateString(
      locale() === "zh" ? "zh-CN" : "en-SG",
      { weekday: "long", month: "long", day: "numeric" }
    );

    const s = window.Store.streak();
    $("streak-num").textContent = s;
    const C = 2 * Math.PI * 52;
    $("streak-ring").style.strokeDashoffset = C * (1 - Math.min(s / 7, 1));

    const checked = window.Store.isCheckedIn();
    $("checkin-btn").disabled = checked;
    $("checkin-btn").textContent = checked ? t("checked_in") : t("checkin_today");
    $("checkin-note").textContent = checked ? "" : t("checkin_hint");

    const wrap = $("today-items");
    if (plan) {
      const idx = (new Date().getDay() + 6) % 7; // plan starts Monday
      const day = plan.days[idx];
      $("plan-total").textContent = `${day.total_minutes} ${t("min")}`;
      wrap.innerHTML = "";
      day.items.forEach((it) => {
        const row = document.createElement("div");
        row.className = "item-row";
        const meta = document.createElement("div");
        meta.innerHTML = `<div class="name">${itemName(it)}</div><div class="meta">${it.minutes} ${t("min")}${it.trackable ? " · " + t("trackable") : ""}</div>`;
        const btn = document.createElement("button");
        btn.className = "secondary-btn";
        btn.textContent = "▶";
        btn.addEventListener("click", () => selectExercise(it.id));
        row.append(meta, btn);
        wrap.appendChild(row);
      });
    }

    if (catalog.length) {
      const seed = new Date().getDate() % catalog.length;
      const e = catalog[seed];
      $("daily-tip").textContent = `${e.name}: ${e.safety}`;
    }
  }

  /* ---------------- Train ---------------- */

  function renderCatalog() {
    const cats = ["all", ...new Set(catalog.map((e) => e.category))];
    const chips = $("category-chips");
    chips.innerHTML = "";
    cats.forEach((c) => {
      const b = document.createElement("button");
      b.className = "chip" + (currentCategory === c ? " active" : "");
      b.type = "button";
      b.textContent = c === "all" ? t("cat_all") : t("cat_" + c);
      b.addEventListener("click", () => { currentCategory = c; renderCatalog(); });
      chips.appendChild(b);
    });

    const grid = $("exercise-grid");
    grid.innerHTML = "";
    catalog
      .filter((e) => currentCategory === "all" || e.category === currentCategory)
      .forEach((e) => {
        const card = document.createElement("button");
        card.type = "button";
        card.className = "ex-card";
        card.innerHTML = `
          <div class="ex-name">${e.name}</div>
          <div class="ex-meta">
            <span class="badge">${t("cat_" + e.category)}</span>
            <span class="badge">${t("level_" + e.level)}</span>
            <span class="badge ${e.trackable ? "" : "warn"}">${e.trackable ? t("trackable") : t("timer_only")}</span>
          </div>
          <div class="ex-purpose">${e.purpose}</div>`;
        card.addEventListener("click", () => selectExercise(e.id));
        grid.appendChild(card);
      });
  }

  function selectExercise(id) {
    selected = catalog.find((e) => e.id === id) || null;
    if (!selected) return;
    $("train-catalog").classList.add("hidden");
    $("train-session").classList.remove("hidden");
    $("session-summary").classList.add("hidden");
    $("pose-stage").classList.add("hidden");
    $("timer-stage").classList.add("hidden");
    $("start-row").classList.remove("hidden");
    $("start-camera").classList.toggle("hidden", !selected.trackable);
    $("rep-count").textContent = "0";
    $("pose-cue").textContent = t("phase_ready");
    renderSelectedBrief();
    document.querySelector(".tab[data-tab='train']").click();
    window.scrollTo({ top: 0 });
  }

  function renderSelectedBrief() {
    if (!selected) return;
    $("session-title").textContent = selected.name;
    $("session-brief").innerHTML = `
      <p><b>${t("purpose")}:</b> ${selected.purpose}</p>
      <p><b>${t("cues")}:</b></p>
      <ul style="margin:4px 0 0 18px">${selected.cues.map((c) => `<li>${c}</li>`).join("")}</ul>`;
    $("session-safety").textContent = selected.safety ? `⚠ ${t("safety")}: ${selected.safety}` : "";
  }

  let poseSession = null; // {stop}
  let timerId = null;
  let sessionStats = null;

  $("start-camera") &&
  ($("start-camera").onclick = async () => {
    if (!selected || !selected.trackable) return;
    $("pose-cue").textContent = t("thinking");
    const res = await window.PoseCam.start({
      video: $("cam"),
      canvas: $("skeleton"),
      exerciseKey: selected.trackable,
      counters: {
        onCue: (info) => {
          if (info.lowConf) $("pose-cue").textContent = t("keep_in_frame");
          else $("pose-cue").textContent = info.phase === "down" ? t("phase_down") : t("phase_up");
        },
        onRep: (analysis) => tallyRep(analysis, true),
        onPartial: (analysis) => tallyRep(analysis, false),
      },
    });
    if (!res.ok) {
      startTimer(); // graceful fallback: camera/model unavailable → timer
      return;
    }
    poseSession = res;
    $("pose-stage").classList.remove("hidden");
    $("start-row").classList.add("hidden");
    beginStats();
  });

  $("start-timer") && ($("start-timer").onclick = () => startTimer());

  function startTimer() {
    if (!selected) return;
    const total = Math.round((selected.minutes || 3) * 60);
    let left = total;
    $("timer-stage").classList.remove("hidden");
    $("start-row").classList.add("hidden");
    const cues = selected.cues.length ? selected.cues : ["…"];
    let cueIdx = 0;
    $("timer-cue").textContent = cues[0];
    const C = 2 * Math.PI * 52;
    beginStats();
    timerId = setInterval(() => {
      left -= 1;
      const m = Math.floor(left / 60), s = left % 60;
      $("timer-text").textContent = `${m}:${String(s).padStart(2, "0")}`;
      $("timer-arc").style.strokeDashoffset = C * (1 - left / total);
      if (left % 8 === 0) {
        cueIdx = (cueIdx + 1) % cues.length;
        $("timer-cue").textContent = cues[cueIdx];
      }
      if (left <= 0) finishSession();
    }, 1000);
    $("timer-text").textContent = `${Math.floor(total / 60)}:${String(total % 60).padStart(2, "0")}`;
  }

  function tallyRep(analysis, complete) {
    if (!sessionStats) beginStats();
    sessionStats.reps += 1;
    if (analysis) {
      if (complete && analysis.isStandard) sessionStats.standard += 1;
      (analysis.problemAreas || []).forEach((p) => {
        sessionStats.issues[p.area] = (sessionStats.issues[p.area] || 0) + 1;
      });
    }
    $("rep-count").textContent = sessionStats.reps;
  }

  function beginStats() {
    sessionStats = { startedAt: Date.now(), reps: 0, standard: 0, issues: {} };
  }

  async function finishSession() {
    if (poseSession) {
      await poseSession.stop();
      poseSession = null;
    }
    if (timerId) { clearInterval(timerId); timerId = null; }
    $("pose-stage").classList.add("hidden");
    $("timer-stage").classList.add("hidden");
    $("start-row").classList.remove("hidden");

    const minutes = Math.max(1, Math.round((Date.now() - sessionStats.startedAt) / 60000));
    window.Store.addSession({
      exerciseId: selected.id,
      name: selected.name,
      mode: selected.trackable && sessionStats.reps > 0 ? "camera" : "timer",
      reps: sessionStats.reps,
      standard: sessionStats.standard,
      minutes,
      issues: sessionStats.issues,
    });

    const issueList = Object.entries(sessionStats.issues)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 3)
      .map(([area, n]) => `<li>${t(AREA_KEYS[area] || area)} × ${n}</li>`)
      .join("");
    $("session-summary").innerHTML = `
      <h2>${selected.name} — ✓</h2>
      <div class="summary-grid">
        <div class="s"><b>${sessionStats.reps}</b><span>${t("sum_reps")}</span></div>
        <div class="s"><b>${sessionStats.standard}</b><span>${t("sum_standard")}</span></div>
        <div class="s"><b>${minutes}</b><span>${t("sum_minutes")}</span></div>
      </div>
      ${sessionStats.reps === 0 ? `<p class="muted">${t("sum_none")}</p>` : ""}
      ${issueList ? `<p><b>${t("sum_issues")}:</b></p><ul style="margin:4px 0 0 18px">${issueList}</ul>` : ""}
      <p class="muted small">${t("sum_done")}</p>`;
    $("session-summary").classList.remove("hidden");
    renderToday();
    sessionStats = null;
  }

  $("pose-finish") && ($("pose-finish").onclick = finishSession);
  $("timer-finish") && ($("timer-finish").onclick = finishSession);
  $("session-back") &&
  ($("session-back").onclick = async () => {
    if (poseSession) { await poseSession.stop(); poseSession = null; }
    if (timerId) { clearInterval(timerId); timerId = null; }
    $("train-session").classList.add("hidden");
    $("train-catalog").classList.remove("hidden");
    selected = null;
  });

  /* ---------------- Coach ---------------- */

  function initCoach() {
    const quick = $("quick-chips");
    [1, 2, 3, 4].forEach((i) => {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "chip";
      b.textContent = t("quick_" + i);
      b.addEventListener("click", () => sendChat(t("quick_" + i)));
      quick.appendChild(b);
    });
    $("chat-form").addEventListener("submit", (ev) => {
      ev.preventDefault();
      const input = $("chat-input");
      const text = input.value.trim();
      if (text) { input.value = ""; sendChat(text); }
    });
    addBotBubble(
      locale() === "zh"
        ? "你好！我是你的自我照护伙伴。可以让我排计划、推荐今天的练习，或者聊聊怎么坚持下去。"
        : "Hi! I'm your self-care companion. Ask me to plan your week, pick today's session, or help you keep the streak going."
    );
  }

  function addBubble(role, html, metaHtml = "") {
    const div = document.createElement("div");
    div.className = "msg " + (role === "user" ? "user" : "bot");
    div.innerHTML = html + metaHtml;
    $("chat-log").appendChild(div);
    $("chat-log").scrollTop = $("chat-log").scrollHeight;
    return div;
  }

  function addUserBubble(text) {
    chatHistory.push({ role: "user", content: text });
    addBubble("user", escapeHtml(text));
  }

  function addBotBubble(text, extraHtml = "") {
    chatHistory.push({ role: "assistant", content: text });
    addBubble("bot", escapeHtml(text) + extraHtml);
  }

  function escapeHtml(s) {
    return s.replace(/[&<>"']/g, (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
    );
  }

  function coachContext() {
    const ctx = { streak_days: window.Store.streak() };
    if (plan) {
      const idx = (new Date().getDay() + 6) % 7;
      const day = plan.days[idx];
      ctx.today_plan = day.items.map((it) => `${itemName(it)} ${it.minutes}min`).join(", ");
    }
    return ctx;
  }

  async function sendChat(text) {
    addUserBubble(text);
    const thinking = addBubble("bot", `<span class="muted">${t("thinking")}</span>`);
    try {
      const resp = await fetch("/api/coach/agent", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: text,
          messages: chatHistory.slice(-9, -1),
          context: coachContext(),
          session_id: sessionId,
          lang: locale(),
        }),
      });
      if (!resp.ok) throw new Error(String(resp.status));
      const data = await resp.json();
      thinking.remove();

      const meta = `
        <div class="msg-meta">
          <span class="badge ${data.source === "template" ? "template" : "agent"}">${t("src_" + (data.source === "llm" ? "llm" : data.source))}</span>
          ${(data.tools_used || []).map((x) => `<span class="badge tool">${t(TOOL_KEYS[x] || x)}</span>`).join("")}
        </div>`;
      const safety = data.safety_flags && data.safety_flags.length
        ? `<div class="safety-banner">⚠ ${escapeHtml(data.safety_advice || "")}</div>`
        : "";
      let html = escapeHtml(data.reply || "");
      if (data.suggestions && data.suggestions.length) {
        html += `<div class="chips" style="margin-top:8px">${data.suggestions
          .map((s) => `<button type="button" class="chip sug">${escapeHtml(s)}</button>`)
          .join("")}</div>`;
      }
      const bubble = addBubble("bot", html, meta + safety);
      bubble.querySelectorAll(".sug").forEach((b) =>
        b.addEventListener("click", () => sendChat(b.textContent))
      );
      chatHistory[chatHistory.length - 1] = { role: "assistant", content: data.reply };
    } catch (err) {
      thinking.remove();
      addBotBubble(t("chat_error"));
    }
  }

  /* ---------------- Progress ---------------- */

  function renderProgress() {
    const s = window.Store.streak();
    const best = window.Store.bestStreak();
    const totals = window.Store.totals();
    $("stat-streak").textContent = s;
    $("stat-best").textContent = best;
    $("stat-sessions").textContent = totals.sessions;
    $("stat-minutes").textContent = totals.minutes;

    const canvas = $("chart");
    const dpr = window.devicePixelRatio || 1;
    const W = canvas.clientWidth || canvas.parentElement.clientWidth - 32;
    canvas.width = W * dpr;
    canvas.height = 160 * dpr;
    const ctx = canvas.getContext("2d");
    ctx.scale(dpr, dpr);
    const data = window.Store.last14();
    const max = Math.max(10, ...data.map((d) => d.minutes));
    const bw = W / 14;
    ctx.clearRect(0, 0, W, 160);
    data.forEach((d, i) => {
      const h = (d.minutes / max) * 120;
      ctx.fillStyle = d.minutes > 0 ? "#0d9488" : "#e5e7eb";
      ctx.fillRect(i * bw + bw * 0.2, 140 - h, bw * 0.6, Math.max(h, 2));
      ctx.fillStyle = "#9ca3af";
      ctx.font = "10px sans-serif";
      ctx.textAlign = "center";
      if (i % 2 === 0) ctx.fillText(d.day.slice(8), i * bw + bw / 2, 154);
    });

    const list = $("history-list");
    const sessions = window.Store.sessions();
    list.innerHTML = "";
    if (!sessions.length) {
      list.innerHTML = `<p class="muted">${t("empty_history")}</p>`;
      return;
    }
    sessions.slice(0, 12).forEach((sess) => {
      const row = document.createElement("div");
      row.className = "item-row";
      row.innerHTML = `<div><div class="name">${escapeHtml(sess.name)}</div>
        <div class="when">${sess.date} · ${sess.mode === "camera" ? t("trackable") : t("timer_only")}</div></div>
        <div class="meta">${sess.reps ? sess.reps + " " + t("reps") + " · " : ""}${sess.minutes} ${t("session_min")}</div>`;
      list.appendChild(row);
    });
  }

  boot();
})();
