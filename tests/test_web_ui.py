"""Kiểm tra trang chat dành cho người dùng cuối."""

from fastapi.testclient import TestClient

from app.main import app


def test_web_ui_co_the_mo_khong_can_api_key():
    response = TestClient(app).get("/")
    assert response.status_code == 200
    assert "Hỏi AI Agent" in response.text
    assert "id=\"api-key\"" in response.text


def test_web_ui_khong_nhung_secret_vao_html():
    response = TestClient(app).get("/")
    assert "AGENT_API_KEY=" not in response.text
    assert "localStorage" in response.text  # trang nói rõ là không lưu khóa
