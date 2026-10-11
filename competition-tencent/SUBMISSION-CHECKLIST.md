# Tencent Cloud AI CAN DO IT Hackathon Singapore 2026 — Submission Checklist

Track: Healthcare (NTU LKCMedicine) · Challenge 2: **AI Healthier Every Day — Intelligent Support for Long-Term Self-Care**
Deadline per event page: submission window closes **2026-10-23 23:59** (event intro also mentions 10-16 — treat 10-16 as the safe target).

| # | Form field | Status | Asset / Notes |
|---|-----------|--------|---------------|
| 1 | Project Title | ✅ ready | `AI Healthier Every Day` |
| 2 | Short Blurb (<10 words) | ✅ ready | "An AI companion that makes daily self-care stick."（8 词；中文备选：每天 3 分钟，AI 陪你把自我照护坚持下来） |
| 3 | Project Description | ✅ draft done | see `description.md` (EN+ZH) — paste per-field |
| 4 | Cover Image (16:9, ≤1MB) | ✅ generated | `cover.png` (760×432, regenerable via `generate_cover.py`) |
| 5 | **Project Web Link (browser-accessible)** | ⬜ needs user | Deploy per `../DEPLOY.md` (Docker / Tencent Cloud Run / Lighthouse), then paste URL. Local preview: `uvicorn app.main:app --port 8000` → `http://127.0.0.1:8000/` |
| 6 | Demo Video (5–8 min) | ⬜ needs user | Script ready: `demo-script.md`. Record the deployed web app + optional miniprogram segment |
| 7 | WorkBuddy/CodeBuddy/Miora chat history (+≥3 screenshots, ≤10MB) | ⬜ needs user | Use CodeBuddy/WorkBuddy during remaining development; export chat + screenshots. Tip: this repo's git history plus the screenshots together evidence the build process |
| 8 | Architecture Diagram PPT (≤100MB) | ⬜ needs user | Content outline in `description.md` §Architecture; slides can be built from the three-layer diagram in README |
| 9 | Source Code (GitHub URL) | ✅ pushed | https://github.com/G1en-114/ai-healthier-everyday (main @ 5e803a4, Apache-2.0 per repository license) |

## Dev-tool usage evidence (judging criteria)

- Develop the remaining changes with **CodeBuddy** (code) and **WorkBuddy** (docs/planning); consider a **Miora** flow for the coach persona tuning. Capture ≥3 chat screenshots.
- Keep commits small and messages descriptive — reviewers can read the history.

## Timeline (recommended)

- 10-10 ~ 10-13: user deploys backend (DEPLOY.md), records video per script, collects CodeBuddy/WorkBuddy screenshots
- 10-14: architecture PPT; fill the form
- **10-16: submit** (buffer before the 10-23 hard close)
