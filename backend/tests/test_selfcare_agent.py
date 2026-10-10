"""自我照护赛道新增能力测试（guardrails / selfcare_catalog / agent / 新端点）。

红线：安全筛查与计划生成是确定性纯函数，不依赖网络；Agent 在 LLM
未配置或故障时必须落到模板兜底（source != agent），服务永不 5xx。
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.guardrails import screen_text
from app.deterministic.selfcare_catalog import (
    build_week_plan,
    get_exercise,
    list_exercises,
    summarize_plan,
)
from app.main import app
from app.services.metering import get_meter

client = TestClient(app)


@pytest.fixture()
def isolated_env(tmp_path, monkeypatch):
    monkeypatch.setenv("MODEL_SERVICE_DB", str(tmp_path / "usage.db"))
    monkeypatch.delenv("MODEL_SERVICE_API_KEYS", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("LLM_API_BASE", raising=False)
    get_settings.cache_clear()
    get_meter.cache_clear()
    yield
    get_settings.cache_clear()
    get_meter.cache_clear()


# ---- guardrails（确定性安全红线） ----


def test_safety_screen_flags_chest_pain() -> None:
    result = screen_text("I feel some chest pain when I squat.")
    assert result.escalate
    assert "chest_pain" in result.categories
    assert "emergency" in result.advice_en.lower()


def test_safety_screen_flags_chinese_symptoms() -> None:
    result = screen_text("今天蹲下的时候有点头晕，要不要继续？")
    assert result.escalate
    assert "dizziness" in result.categories
    assert "就医" in result.advice_zh


def test_safety_screen_quiet_on_normal_text() -> None:
    result = screen_text("今天的坐站练习做了 8 次，感觉不错！")
    assert not result.escalate
    assert result.categories == []


# ---- selfcare catalog（确定性目录与计划） ----


def test_catalog_has_five_categories_and_bilingual_fields() -> None:
    items = list_exercises()
    assert {e.category for e in items} == {
        "mobility", "balance", "breathing", "strength", "flexibility"
    }
    for e in items:
        assert e.name_en and e.name_zh
        assert e.safety_en and e.safety_zh


def test_catalog_trackable_exercises_map_to_pose_rules() -> None:
    sit_to_stand = get_exercise("sit_to_stand")
    assert sit_to_stand is not None
    assert sit_to_stand.trackable == "squat"
    assert get_exercise("wall_pushup").trackable == "push_up"
    assert get_exercise("box_breathing").trackable is None


def test_week_plan_deterministic_and_covers_categories() -> None:
    a = build_week_plan(level="gentle", minutes_per_day=10)
    b = build_week_plan(level="gentle", minutes_per_day=10)
    assert a == b  # 纯函数：同输入同输出
    assert len(a) == 7
    cats = {d["category"] for d in a}
    assert {"mobility", "balance", "strength", "breathing", "flexibility"} <= cats
    for day in a:
        assert day["items"], "每天都不能为空"
        assert day["total_minutes"] > 0
    # gentle 级别过滤掉 moderate 动作
    moderate_ids = {e.id for e in list_exercises() if e.level == "moderate"}
    assert all(it["id"] not in moderate_ids for d in a for it in d["items"])
    assert summarize_plan(a, lang="zh")


# ---- Agent 降级链 ----


def test_agent_falls_back_to_template_without_llm(isolated_env) -> None:
    resp = client.post(
        "/api/coach/agent",
        json={"message": "今天练什么？", "session_id": "t1", "lang": "en"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["source"] == "template"  # LLM 未配置 → 模板兜底
    assert body["reply"]
    assert isinstance(body["suggestions"], list)


def test_agent_safety_guardrail_overrides_reply(isolated_env) -> None:
    """红线独立于 LLM：模板兜底路径下红旗症状仍必须前置就医建议。"""
    resp = client.post(
        "/api/coach/agent",
        json={"message": "I have chest pain, should I train?", "lang": "en"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "chest_pain" in body["safety_flags"]
    assert "emergency" in body["reply"].lower()


# ---- 新端点 ----


def test_exercises_endpoint_bilingual_and_filter(isolated_env) -> None:
    en = client.get("/api/exercises?lang=en").json()
    zh = client.get("/api/exercises?lang=zh").json()
    assert en["items"], "目录不能为空"
    assert en["items"][0]["id"] == zh["items"][0]["id"]
    assert en["items"][0]["name"] != zh["items"][0]["name"]  # 双语字段确实不同
    balance = client.get("/api/exercises?category=balance").json()
    assert balance["items"]
    assert all(it["category"] == "balance" for it in balance["items"])
    weird = client.get("/api/exercises?category=nonexistent").json()
    assert len(weird["items"]) == len(en["items"])


def test_selfcare_plan_endpoint(isolated_env) -> None:
    resp = client.get("/api/selfcare/plan?level=gentle&minutes_per_day=10")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["days"]) == 7
    assert body["days"][0]["items"]
