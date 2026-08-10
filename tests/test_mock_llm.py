"""Kiểm tra câu trả lời demo của Mock LLM."""

from utils.mock_llm import ask_llm


def test_cau_xa_giao_khong_bi_chep_lai():
    answer = ask_llm("đz ko")["answer"]
    assert not answer.lower().startswith("theo mình hiểu, đz ko")
    assert "😄" in answer


def test_docker_duoc_tra_loi_dung_chu_de():
    answer = ask_llm("Docker là gì?")["answer"]
    assert "container" in answer.lower()
    assert "image" in answer.lower()


def test_lich_su_hien_dung_don_vi_tin_nhan():
    result = ask_llm("hello", [{"role": "user", "content": "hi"}])
    assert "1 tin nhắn trước đó" in result["answer"]
