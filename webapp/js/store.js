/* Local-first store: everything lives in this browser (localStorage).
 * Mirrors the miniprogram's "纯本地 wx.storage" design — the user owns the data,
 * and the Export button makes that verifiable.
 */
(function () {
  const KEY = "hed-state-v1";

  function todayKey(offset = 0) {
    const d = new Date();
    d.setDate(d.getDate() + offset);
    return d.toISOString().slice(0, 10);
  }

  function load() {
    try {
      return JSON.parse(localStorage.getItem(KEY) || "null");
    } catch {
      return null;
    }
  }

  let state = load() || {
    lang: null, // null = follow browser language
    checkins: {}, // { "2026-10-09": minutes }
    sessions: [], // [{ id, date, exerciseId, name, mode, reps, standard, minutes, issues }]
  };

  function save() {
    localStorage.setItem(KEY, JSON.stringify(state));
  }

  function streak() {
    let n = 0;
    let offset = state.checkins[todayKey()] ? 0 : -1; // today not yet → count from yesterday
    while (state.checkins[todayKey(offset - n)]) n++;
    return n;
  }

  function bestStreak() {
    const days = Object.keys(state.checkins).sort();
    let best = 0, run = 0, prev = null;
    for (const d of days) {
      if (prev) {
        const gap = (new Date(d) - new Date(prev)) / 86400000;
        run = gap === 1 ? run + 1 : 1;
      } else {
        run = 1;
      }
      best = Math.max(best, run);
      prev = d;
    }
    return Math.max(best, streak());
  }

  function checkin(minutes = 0) {
    const k = todayKey();
    state.checkins[k] = (state.checkins[k] || 0) + minutes;
    save();
  }

  function isCheckedIn() {
    return !!state.checkins[todayKey()];
  }

  function addSession(s) {
    state.sessions.unshift({ id: Date.now(), date: todayKey(), ...s });
    state.sessions = state.sessions.slice(0, 200);
    save();
    checkin(s.minutes || 0);
  }

  function sessions() { return state.sessions; }

  function last14() {
    const out = [];
    for (let i = 13; i >= 0; i--) {
      const k = todayKey(-i);
      out.push({ day: k, minutes: state.checkins[k] || 0 });
    }
    return out;
  }

  function totals() {
    return {
      sessions: state.sessions.length,
      minutes: Math.round(state.sessions.reduce((a, s) => a + (s.minutes || 0), 0)),
    };
  }

  function setLang(lang) { state.lang = lang; save(); }
  function lang() { return state.lang; }

  function exportJSON() {
    const blob = new Blob([JSON.stringify({ exported_at: new Date().toISOString(), ...state }, null, 2)], {
      type: "application/json",
    });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "ai-healthier-every-day-data.json";
    a.click();
    URL.revokeObjectURL(a.href);
  }

  window.Store = {
    todayKey, streak, bestStreak, checkin, isCheckedIn, addSession,
    sessions, last14, totals, setLang, lang, exportJSON,
  };
})();
