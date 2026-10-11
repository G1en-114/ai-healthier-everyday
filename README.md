# AI Healthier Every Day

> Small daily self-care, guided by AI · 每天一点自我照护，AI 陪你坚持

**Tencent Cloud AI CAN DO IT Hackathon Singapore 2026** — Healthcare Track (NTU LKCMedicine), Challenge 2: **"AI Healthier Every Day: Intelligent Support for Long-Term Self-Care"**.

An agentic self-care companion for long-term habit building: gentle mobility, balance & fall prevention, breathing relaxation, and everyday strength — with in-browser pose AI that counts your reps, a deterministic safety guardrail that always escalates red-flag symptoms, and a tool-calling agent that plans your week. Evolved from the model layer of our open-source base [Health-525/lian_le_ma](https://github.com/Health-525/lian_le_ma) (own work, MIT).

## 三层 AI 架构 / Three-layer AI architecture

| Layer | Capability | Where |
|-------|-----------|-------|
| L1 Browser pose AI | MediaPipe Pose Landmarker runs fully in-browser; rep counting & form cues come from the project's deterministic angle-rule state machine (shared, test-covered code with the WeChat miniprogram) | `webapp/js/pose.js` + `webapp/js/poseRules.js` (synced by `tools/sync-web-core.mjs`) |
| L2 Agentic coach | A tool-calling agent (OpenAI-compatible; built for Tencent Cloud Hunyuan) over a deterministic tool belt: self-care catalog lookup, 7-day plan builder, calendar, red-flag safety screen. Falls back to single-shot LLM → template coach. **The service never 5xxs.** | `backend/app/providers/coach_llm/agent.py` |
| L2 vision (optional) | Self-trained ST-GCN action recognition + VLM snapshot commentary | `backend/app/providers/vision/` + `src/`, `model/` |

**Safety red lines / 安全红线**:
- Reps, scores, plans and safety calls come from deterministic code only; the LLM only narrates around them.
- The guardrail (`backend/app/core/guardrails.py`) screens every message for red-flag symptoms (chest pain, dizziness, breathlessness, numbness, recent surgery, pregnancy — EN+ZH) and prepends care-escalation advice **independent of the LLM output**.
- Not a medical device, no diagnosis, visible disclaimers in the product.

## 仓库导览 / Repository map

| Path | What |
|------|------|
| `webapp/` | Browser self-care app (no build step): Today / Train / AI Coach / Progress, EN+ZH toggle, in-browser pose counting, local-first storage with data export |
| `backend/` | FastAPI model service: `/api/coach/agent` (agentic), `/api/coach/chat`, `/api/exercises`, `/api/selfcare/plan`, `/api/vision/analyze`, `/api/usage`, `/api/status` |
| `miniprogram/` | WeChat mini-program client (Chinese market channel), shares the same deterministic core |
| `cloudfunctions/llmcoach/` | WeChat cloud function for on-channel AI text polish (Hunyuan) |
| `src/`, `model/`, `data/` | Base model layer: RTMPose + ST-GCN training/inference (kept from base repo) |
| `test/`, `backend/tests/` | Node tests (miniprogram core, 50) + pytest (backend, 80) |
| `competition-tencent/` | Hackathon submission materials: checklist, description drafts, demo script, cover |

## 快速开始 / Quick start

### 1. Web app + backend（评委入口 / judge entry — one command）

```bash
cd backend
cp .env.example .env       # 填 LLM_API_KEY；推荐腾讯云混元 OpenAI 兼容端点
pip install -e ".[test]"
uvicorn app.main:app --port 8000
# open http://127.0.0.1:8000/
```

Without any API key everything still runs: the agent degrades to the template coach, clearly labeled "Offline tips mode" in the UI. Camera pose counting runs in the browser via MediaPipe (CDN); if the CDN or camera is unavailable, sessions gracefully fall back to the guided-timer mode.

### 2. WeChat miniprogram（可选渠道）

DevTools → import `miniprogram/` → test AppID → run. Point `miniprogram/config.js` → `MODEL_SERVICE_BASE_URL` at the backend to enable the cloud AI toggle.

### 3. Tests

```bash
node --test "test/*.test.js"           # 50 pass — deterministic core
cd backend && python -m pytest tests/  # 80 pass — API / guardrails / catalog / agent fallback / metering / auth
```

## 部署 / Deployment

See `DEPLOY.md` (Docker + Tencent Cloud options) — the web link requirement needs one publicly reachable URL serving both the SPA and the API.

## 能力开放与商业化边界 / Commercial boundary

No paywall, no pricing — all capabilities open. The model service ships API-key auth + SQLite usage metering (calls & tokens) as a data plane; billing is left to platform/vendor ecosystems.

## 与基座的关系 / Relation to the base repo

Cloned from our own `Health-525/lian_le_ma` (WeChat mini-program competition entry) and `G1en-114/lianlema` (Tmall hackathon edition). The miniprogram baseline is retained; the web app, agent, guardrails and self-care catalog are new for this hackathon.

## License

Apache License 2.0 — see [LICENSE](LICENSE). (The base repo `Health-525/lian_le_ma` was MIT; this derivative is relicensed Apache-2.0 by the original author for this competition repo.)
