"""Mock LLM chạy offline, không cần API key nhà cung cấp.

Trả lời tất định (cùng câu hỏi → cùng câu trả lời) nên không cần API key,
không tốn tiền, và test luôn cho kết quả ổn định.

Dùng:
    from utils.mock_llm import ask_llm
    result = ask_llm("Docker là gì?", history=[...])
    result["answer"], result["tokens_in"], result["tokens_out"], result["cost_usd"]
"""

from __future__ import annotations

import hashlib
import re
import unicodedata

# Giá giả lập, tính theo 1.000 token (giống thang giá gpt-4o-mini)
PRICE_INPUT_PER_1K = 0.00015
PRICE_OUTPUT_PER_1K = 0.00060

_TEMPLATES = [
    "Mình chưa hiểu rõ ý bạn. Bạn có thể hỏi cụ thể hơn về Docker, Redis, cloud hoặc cách deploy không?",
    "Bạn nói rõ thêm một chút nhé. Mình hỗ trợ tốt nhất các câu hỏi về hạ tầng và triển khai ứng dụng.",
    "Mình cần thêm ngữ cảnh để trả lời chính xác. Bạn thử đặt một câu hỏi đầy đủ hơn nhé.",
]


def _normalize(text: str) -> str:
    """Chuẩn hóa tiếng Việt để nhận diện một số câu ngắn phổ biến."""
    decomposed = unicodedata.normalize("NFD", text.lower().strip())
    without_marks = "".join(char for char in decomposed if not unicodedata.combining(char))
    without_marks = without_marks.replace("đ", "d")
    return re.sub(r"[^a-z0-9]+", " ", without_marks).strip()


def _answer_for(question: str) -> str:
    """Trả lời theo ý định đơn giản mà không chép lại nguyên câu hỏi."""
    normalized = _normalize(question)
    words = set(normalized.split())

    if normalized in {"hi", "hello", "hey", "alo", "chao", "xin chao"}:
        return "Chào bạn 👋 Mình có thể giúp gì về Docker, Redis, cloud hoặc triển khai ứng dụng?"

    handsome_phrases = ("dz ko", "dep zai khong", "dep trai khong", "co dep trai khong")
    if any(phrase in normalized for phrase in handsome_phrases):
        return "Có chứ 😄 Nhưng điểm mạnh của mình vẫn là hỗ trợ bạn về Docker, Redis và cloud!"

    if "khoe khong" in normalized or normalized == "khoe ko":
        return "Mình khỏe và đang sẵn sàng hỗ trợ bạn 😄 Bạn muốn hỏi gì nào?"

    if words & {"cam", "thanks", "thank"} and ("cam on" in normalized or "thank" in normalized):
        return "Không có gì! Nếu còn câu hỏi về triển khai ứng dụng, cứ hỏi mình nhé."

    if "docker" in words or "container" in words:
        return (
            "Docker đóng gói ứng dụng cùng thư viện và môi trường chạy vào container. "
            "Nhờ vậy cùng một image có thể chạy nhất quán trên máy cá nhân và cloud."
        )

    if "redis" in words:
        return (
            "Redis là kho dữ liệu key-value chạy trên bộ nhớ, có tốc độ cao. Trong hệ thống này, "
            "Redis lưu lịch sử hội thoại, rate limit và chi phí để nhiều instance dùng chung state."
        )

    if words & {"cloud", "deploy", "railway"}:
        return (
            "Deploy lên cloud là đóng gói ứng dụng, truyền cấu hình bằng biến môi trường, "
            "mở endpoint công khai và dùng health check để nền tảng theo dõi trạng thái."
        )

    if "api key" in normalized or "apikey" in normalized:
        return (
            "API key là khóa xác thực cho client được phép gọi hệ thống. Khóa phải nằm trong "
            "biến môi trường, không ghi vào source code hay đăng công khai."
        )

    if "rate limit" in normalized or "gioi han" in normalized:
        return (
            "Rate limit giới hạn số request trong một khoảng thời gian. Bài này dùng cửa sổ trượt "
            "60 giây trên Redis để chặn burst request chính xác hơn bộ đếm theo phút cố định."
        )

    if words & {"health", "ready", "readiness", "liveness"}:
        return (
            "Liveness cho biết process còn sống, còn readiness cho biết service đã sẵn sàng nhận "
            "traffic và các dependency như Redis đang hoạt động."
        )

    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return _TEMPLATES[int(digest[:8], 16) % len(_TEMPLATES)]


def _estimate_tokens(text: str) -> int:
    """Ước lượng thô: ~4 ký tự / token, tối thiểu 1."""
    return max(1, len(text) // 4)


def ask_llm(question: str, history: list[dict] | None = None) -> dict:
    """Giả lập một lượt gọi LLM.

    Args:
        question: câu hỏi của người dùng.
        history: lịch sử hội thoại, list các dict {"role": ..., "content": ...}.

    Returns:
        dict gồm answer, tokens_in, tokens_out, cost_usd.
    """
    history = history or []
    answer = _answer_for(question)

    if history:
        answer += f" (Mình đang nhớ {len(history)} tin nhắn trước đó.)"

    prompt_text = question + "".join(turn.get("content", "") for turn in history)
    tokens_in = _estimate_tokens(prompt_text)
    tokens_out = _estimate_tokens(answer)
    cost = (
        tokens_in / 1000 * PRICE_INPUT_PER_1K
        + tokens_out / 1000 * PRICE_OUTPUT_PER_1K
    )

    return {
        "answer": answer,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "cost_usd": round(cost, 8),
    }
