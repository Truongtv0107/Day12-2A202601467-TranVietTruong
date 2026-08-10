# BÁO CÁO CÁ NHÂN — DAY 12: CLOUD INFRASTRUCTURE & DEPLOYMENT

## 1. Thông tin học viên

| Mục | Nội dung |
|---|---|
| Họ và tên | Trần Việt Trường |
| Mã học viên | 2A202601467 |
| Repository | [DAY12-2A202601467-TranVietTruong](https://github.com/Truongtv0107/DAY12-2A202601467-TranVietTruong) |
| Nền tảng triển khai | Railway |
| API công khai | [day12-2a202601467-tranviettruong-production-ae8c.up.railway.app](https://day12-2a202601467-tranviettruong-production-ae8c.up.railway.app) |
| Swagger UI | [/docs](https://day12-2a202601467-tranviettruong-production-ae8c.up.railway.app/docs) |

## 2. Mục tiêu đề tài

Đề tài đưa một AI agent từ môi trường local lên Internet dưới dạng REST API. Hệ
thống phải có cấu hình tách khỏi mã nguồn, xác thực API key, giới hạn tần suất,
giới hạn chi phí, lưu lịch sử hội thoại trên Redis, health/readiness probe,
graceful shutdown, Docker image an toàn và quy trình CI/CD.

Lab sử dụng mock LLM chạy offline nên không cần khóa OpenAI. `AGENT_API_KEY` là
khóa riêng để bảo vệ endpoint `/ask`, không phải khóa của nhà cung cấp LLM.

## 3. Kiến trúc hệ thống

```text
Client / Swagger UI
        |
        | HTTPS + X-API-Key + X-User-Id
        v
Railway public domain
        |
        v
FastAPI agent
  |-- verify_api_key  -> xác thực constant-time
  |-- RateLimiter     -> sliding window 60 giây trên Redis ZSET
  |-- CostGuard       -> ngân sách theo user/tháng trên Redis
  |-- mock LLM        -> sinh câu trả lời và thống kê token/chi phí
  |-- ConversationStore -> lưu lịch sử dùng chung trên Redis List
  `-- JSON logging    -> log có cấu trúc cho nền tảng cloud
        |
        v
Railway Redis
```

Ứng dụng không giữ lịch sử trong bộ nhớ của process. Vì vậy nhiều instance có
thể đọc chung lịch sử từ Redis và service không mất trạng thái hội thoại khi
container được thay thế.

## 4. Kết quả theo checkpoint

| Checkpoint | Nội dung đã hoàn thành | Kết quả |
|---|---|---|
| CP1 | `Settings` theo 12-Factor, fail-fast khi thiếu secret, JSON log, `/health` | 13/13 test pass |
| CP2 | Docker multi-stage, image slim, non-root user, healthcheck, `.dockerignore`, Compose + Redis | 14/14 test cấu trúc pass; 2 test build được bỏ qua khi Docker Desktop không chạy |
| CP3 | API key, `compare_digest`, sliding-window rate limit, cost guard theo tháng | 22/22 test pass |
| CP4 | Redis conversation store, TTL/cắt lịch sử, `/ready`, graceful shutdown | 19/19 test pass |
| CP5 | Deploy thật trên Railway, HTTPS, Redis cloud, public health/readiness và API có xác thực | Đã kiểm tra trực tiếp trên bản production |
| Exercises | Hoàn thành 10 câu phản ánh bằng thông tin cá nhân | 10/10 câu |
| Bonus | GitHub Actions chạy test, build Docker và deploy sau khi test xanh | 12/13 test local; test badge cần Internet |

Kết quả `python grade.py` chạy trong `.venv` ngày 10/08/2026: **100.0/100** sau
khi tính bonus. Các kiểm tra cần Internet không chạy được trong sandbox local,
nhưng service production đã được kiểm tra trực tiếp như phần 5.

## 5. Bằng chứng triển khai thật

| Kiểm tra | Kết quả |
|---|---|
| `GET /health` | HTTP 200, `status=ok`, service `day12-agent`, version `1.0.0` |
| `GET /ready` | HTTP 200, `status=ready`, `redis=true` |
| `POST /ask` không có API key | HTTP 401 |
| `POST /ask` có API key | HTTP 200 |
| User demo | `2A202601467` |
| Redis conversation history | Hoạt động; response demo ghi nhận `history_length=8` |
| Theo dõi chi phí | Response có `cost_usd` và số token input/output |

Ví dụ cấu trúc response đã nhận từ production:

```json
{
  "answer": "Câu trả lời của agent",
  "user_id": "2A202601467",
  "history_length": 8,
  "cost_usd": 0.0000582,
  "tokens": {
    "in": 200,
    "out": 47
  }
}
```

Giá trị API key không được ghi vào báo cáo hoặc repository.

## 6. Bảo mật và kiểm soát chi phí

- Secret chỉ được truyền qua biến môi trường; `.env` nằm trong `.gitignore` và
  `.dockerignore`.
- `AGENT_API_KEY` không có giá trị mặc định, giúp service fail fast nếu cấu hình
  cloud thiếu secret.
- So sánh khóa bằng `secrets.compare_digest` để hạn chế timing attack.
- Mỗi user có cửa sổ trượt 60 giây; mặc định tối đa 10 request/phút.
- Mỗi user có ngân sách tháng riêng; request bị chặn trước khi gọi LLM nếu vượt
  ngân sách.
- Container runtime chạy bằng user thường thay vì root.
- Lịch sử chỉ giữ 20 message gần nhất và tự hết hạn sau 7 ngày.

## 7. Độ tin cậy và vận hành

- `/health` chỉ kiểm tra process, không phụ thuộc Redis.
- `/ready` kiểm tra Redis để load balancer chỉ chuyển traffic đến instance sẵn
  sàng.
- Handler SIGTERM/SIGINT đánh dấu trạng thái shutdown và gọi lại handler của
  Uvicorn, tránh cắt ngang request khi deploy phiên bản mới.
- Log JSON một dòng có timestamp, user, token và chi phí, phù hợp để tìm kiếm,
  thống kê và cảnh báo trên cloud.
- GitHub Actions chỉ deploy nhánh `main` sau khi test và Docker build thành công.

## 8. Sự cố đã gặp và cách xử lý

1. Railway báo `Invalid value for '--port': '$PORT' is not a valid integer`.
   Nguyên nhân là start command truyền chuỗi literal `$PORT` thay vì để shell
   mở rộng biến. Cách sửa là bỏ start command sai trong `railway.toml` và để
   Docker chạy `sh -c "uvicorn ... --port ${PORT:-8000}"`.
2. Healthcheck thất bại vì ứng dụng không lắng nghe đúng cổng cloud. Docker
   healthcheck được sửa để đọc chính biến `PORT`.
3. Railway báo không tìm thấy repository sau khi repo được đổi tên. Quyền GitHub
   của Railway được cấp lại, nguồn repo được kết nối lại rồi redeploy.
4. Sau khi sửa, `/health`, `/ready`, `/docs` và `/ask` đều hoạt động trên domain
   HTTPS công khai.

## 9. Kịch bản demo trên lớp

1. Mở [Swagger UI](https://day12-2a202601467-tranviettruong-production-ae8c.up.railway.app/docs).
2. Mở `GET /health`, bấm **Try it out** rồi **Execute** để chứng minh process sống.
3. Mở `GET /ready` và Execute để chứng minh Redis đã kết nối.
4. Mở `POST /ask`, bấm **Try it out**.
5. Nhập API key đang lưu trong Railway vào `x-api-key`; nhập
   `2A202601467` vào `x-user-id`.
6. Nhập body `{"question":"Docker là gì?"}` rồi Execute.
7. Giải thích response: `answer` là câu trả lời, `history_length` chứng minh Redis
   nhớ hội thoại, `cost_usd` và `tokens` phục vụ kiểm soát chi phí.
8. Không chiếu hoặc gửi API key trong ảnh/video. Nếu khóa từng bị lộ, tạo khóa
   mới và thay biến `AGENT_API_KEY` trên Railway trước khi demo.

## 10. Kết luận

Bài làm đã hoàn thành luồng triển khai một agent production cơ bản: đóng gói
Docker, cấu hình an toàn, API có xác thực, kiểm soát tải và chi phí, Redis làm
state dùng chung, health/readiness probe, shutdown an toàn, deploy HTTPS và
CI/CD. Service hiện có thể được mentor gọi trực tiếp qua Internet và kiểm tra
bằng Swagger UI.
