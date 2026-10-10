# 部署指引 / Deployment

提交表单的 **Project Web Link** 要求一个浏览器可访问的 URL，能在线体验项目。
本仓库的部署单元只有一个：FastAPI 服务 = 模型 API（`/api/*`）+ 自我照护 Web App（`/`）。

## 1. 本地 / 内网穿透（最快，适合 demo 前自测）

```bash
cd backend
cp .env.example .env        # 至少填 LLM_API_KEY / LLM_API_BASE（混元）
pip install -e ".[test]"
uvicorn app.main:app --port 8000
```

临时公网：`cloudflared tunnel --url http://127.0.0.1:8000` 或 ngrok 同理。
（演示仅数小时时可接受；正式提交建议下面的云部署。）

## 2. Docker（任何有 Docker 的主机）

仓库根目录：

```bash
docker build -f backend/Dockerfile -t ai-healthier .
docker run -d -p 80:8000 \
  -e LLM_API_BASE=https://api.hunyuan.cloud.tencent.com/v1 \
  -e LLM_MODEL=hunyuan-turbos-latest \
  -e LLM_API_KEY=<your-key> \
  -e MODEL_SERVICE_API_KEYS=<optional-client-key> \
  -v ai-healthier-data:/data \
  ai-healthier
```

- 不配 `LLM_API_KEY` 也能跑：Agent 降级为模板教练，UI 明确标注 "Offline tips mode"。
- `MODEL_SERVICE_API_KEYS` 对外演示务必配置（否则 `/api/status` 标注 disabled-dev 且不鉴权）。

## 3. 腾讯云（本赛事官方云）/ Tencent Cloud

任选其一（都能跑同一个镜像）：

- **Cloud Run（推荐，按量计费）**：控制台新建 Cloud Run 服务 → 镜像 `ai-healthier`（推到 TCR 个人版）→ 端口 8000 → 挂 COS/ CBS 持久卷或直接用默认盘存 SQLite → 得到公网域名。
- **Lighthouse 轻量服务器**：Docker 镜像 + `docker run -d -p 80:8000 ...` → 防火墙放行 80 → 域名解析。
- **TKE / CVM**：同 Docker 步骤。

环境变量在 `.env` 或容器 env 里配，全部可选、缺省自动降级（见 `backend/.env.example`）。

## 4. 提交前检查 / Pre-submission checklist

- [ ] `https://<your-domain>/` 能打开 Web App（英文默认）
- [ ] `/health` 返回 `{"status":"ok"}`
- [ ] `/api/status` 里 `agent: true`（配了混元 key）
- [ ] 无痕窗口试一遍：Today 打卡 → Train 计时模式 → Coach 提问（含一条红旗症状验证安全横幅）
- [ ] 手机宽度（375px）下布局正常
