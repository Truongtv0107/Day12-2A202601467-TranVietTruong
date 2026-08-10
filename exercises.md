# Phiếu Phản Ánh — K3 Ngày 12

> **Bài làm cá nhân.** Trả lời bằng lời của chính bạn, dựa trên những gì bạn
> quan sát được khi chạy code — không sao chép đáp án của người khác.
>
> Cách trả lời: thay phần trả lời mẫu của mỗi câu bằng nội dung của bạn.
> `grade.py` đếm số câu đã trả lời (15 điểm cho 10 câu).
>
> Họ và tên: **Trần Việt Trường**  Mã học viên: **2A202601467**

---

### Câu 1 — Fail fast (CP1)

Trong `Settings`, `agent_api_key` không có giá trị mặc định nên app chết ngay
khi khởi động nếu thiếu biến môi trường. Hãy mô tả một tình huống cụ thể mà
việc "chết sớm" này cứu bạn, so với việc để mặc định `"changeme"`.

> Nếu quên khai báo `AGENT_API_KEY` trên Railway, service dừng ngay và health check báo lỗi. Nhờ vậy tôi phát hiện thiếu secret trước khi service public nhận request. Nếu dùng khóa mặc định, người lạ có thể gọi `/ask` bằng khóa đó và làm phát sinh chi phí trước khi tôi biết lỗi cấu hình.

---

### Câu 2 — Log cho máy đọc (CP1)

Chạy service và gọi `/ask` vài lần. Dán một dòng log JSON bạn thu được, rồi
nêu **hai** việc bạn làm được với dòng log đó mà `print("đã trả lời xong")`
không làm được.

> Ví dụ log: `{"event":"ask_completed","level":"info","timestamp":"2026-08-10T02:00:00+00:00","user_id":"sv-test","cost_usd":0.0001}`. Tôi có thể lọc toàn bộ request của một user và tính tổng chi phí theo `cost_usd`; ngoài ra có thể tạo cảnh báo khi số lỗi hoặc chi phí vượt ngưỡng. Một dòng `print` tự do không có cấu trúc ổn định để công cụ log làm hai việc này.

---

### Câu 3 — Kích thước image (CP2)

Build cả hai phiên bản và ghi lại số đo thật:

```bash
docker build -f <Dockerfile-1-stage> -t agent:single .
docker build -t agent:multi .
docker images | grep agent
```

| Bản | Dung lượng |
|-----|-----------|
| 1 stage (bản đầu) | Chưa đo vì Docker Desktop trên máy chưa chạy |
| Multi-stage | Chưa đo vì Docker Desktop trên máy chưa chạy |

Giải thích: phần dung lượng chênh lệch đó là những gì?

> Bản multi-stage chỉ copy các package Python đã cài sang runtime image; compiler, cache pip và file build ở stage `builder` không đi theo. Vì vậy image runtime nhỏ hơn và bề mặt tấn công cũng ít hơn. Tôi sẽ chạy lại hai lệnh build và cập nhật số MB thật khi Docker Desktop hoạt động.

---

### Câu 4 — Thứ tự lệnh trong Dockerfile (CP2)

Sửa một ký tự trong `app/main.py` rồi build lại. Với Dockerfile của bạn, những
layer nào được dùng lại từ cache, layer nào phải chạy lại? Nếu bạn đặt
`COPY . .` lên trước `RUN pip install` thì kết quả khác thế nào?

> Khi chỉ sửa `app/main.py`, các layer `COPY requirements.txt` và `RUN pip install` được lấy lại từ cache; chỉ layer `COPY app` và các layer phía sau phải chạy lại. Nếu `COPY . .` đứng trước `RUN pip install`, thay đổi ở bất cứ file source nào cũng làm Docker mất cache dependency và cài lại toàn bộ thư viện.

---

### Câu 5 — Vì sao không chạy bằng root (CP2)

Container mặc định chạy bằng root. Mô tả chuỗi sự kiện dẫn từ "một lỗ hổng
trong code Python của bạn" tới "kẻ tấn công có quyền cao trên máy host", và
lệnh `USER` cắt đứt chuỗi đó ở chỗ nào.

> Một lỗ hổng cho phép thực thi lệnh trong app sẽ chạy với quyền của process container. Nếu process là root, kẻ tấn công có thể sửa file hệ thống trong container, lấy credential mount nhầm hoặc khai thác lỗi escape container với quyền cao hơn. `USER appuser` giảm quyền của process, nên kể cả khi app bị chiếm, hành động bị giới hạn vào quyền user thường.

---

### Câu 6 — Cửa sổ trượt (CP3)

Rate limit của bạn dùng sliding window 60 giây. Nếu thay bằng cách đếm theo
phút đồng hồ (reset lúc giây 00), một người dùng có thể gửi tối đa bao nhiêu
request trong 2 giây liên tiếp khi hạn mức là 10/phút? Giải thích cách đạt được
con số đó.

> Người dùng có thể gửi 10 request ở 10:00:59 rồi thêm 10 request ở 10:01:01, tổng cộng 20 request trong 2 giây. Bộ đếm theo phút đồng hồ reset ở giây 00 nên không thấy đây là một burst lớn. Sliding window luôn đếm 60 giây gần nhất nên request thứ 11 sẽ bị chặn.

---

### Câu 7 — Rate limit và cost guard (CP3)

Hai cơ chế này khác nhau ở điểm nào? Cho một tình huống mà rate limit cho qua
nhưng cost guard phải chặn, và một tình huống ngược lại.

> Rate limit giới hạn tần suất, còn cost guard giới hạn tổng tiền theo tháng của từng user. Một user có thể gửi ít request nhưng mỗi request rất dài: rate limit cho qua nhưng cost guard chặn khi vượt ngân sách. Ngược lại, user có nhiều request rất ngắn trong một phút có thể bị rate limit chặn dù tổng chi phí tháng vẫn còn thấp.

---

### Câu 8 — /health khác /ready (CP4)

Nếu gộp hai endpoint làm một và cho nó kiểm tra Redis, chuyện gì xảy ra với cụm
3 container khi Redis mất kết nối 30 giây? Trả lời theo đúng thứ tự sự kiện.

> Nếu `/health` kiểm tra Redis, Redis mất kết nối 30 giây sẽ làm cả ba container trả probe lỗi. Orchestrator lần lượt restart chúng, trong khi process app thực tế vẫn sống; khi Redis trở lại, cụm vừa mất thời gian khởi động và làm gián đoạn traffic. Tách `/health` chỉ kiểm tra process, còn `/ready` kiểm tra Redis để load balancer tạm rút instance khỏi traffic mà không restart vô ích.

---

### Câu 9 — Stateless (CP4)

Chạy `docker compose up --scale agent=3` rồi gọi `/ask` nhiều lần với cùng một
`X-User-Id`. Quan sát `history_length` trong response. Nếu lịch sử được lưu
trong một dict Python thay vì Redis, bạn sẽ thấy con số đó thay đổi thế nào?

> Với Redis, cả ba container đọc cùng key `history:<user_id>`, nên sau request đầu tiên `history_length` ở request sau là 2 dù request tới instance nào. Nếu dùng dict Python, mỗi instance có bộ nhớ riêng: khi request đổi instance thì lịch sử có thể quay về 0 hoặc thiếu message. Redis cũng giữ dữ liệu qua restart theo TTL đã đặt.

---

### Câu 10 — Deploy thật (CP5)

Ghi lại **một** lỗi bạn gặp khi deploy lên cloud (build fail, health check
timeout, sai REDIS_URL, app không đọc `$PORT`...): thông báo lỗi là gì, bạn
tìm ra nguyên nhân bằng cách nào, và sửa ra sao?

> Khi deploy lần đầu, Railway lặp lại lỗi `Invalid value for '--port': '$PORT' is not a valid integer`, sau đó healthcheck thất bại. Tôi đọc Deploy Logs và nhận ra start command đang truyền chuỗi literal `$PORT` cho Uvicorn thay vì để shell mở rộng biến. Tôi bỏ start command sai trong `railway.toml`, dùng `CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]` và sửa Docker healthcheck đọc đúng `PORT`. Sau khi redeploy, `/health` và `/ready` đều trả 200, còn `/ask` không có API key trả 401 đúng yêu cầu.
