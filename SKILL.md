---
name: skylink-review-report
description: >-
  Phân tích & tổng hợp review game mobile của Skylink Studio (App Store / Google Play)
  thành báo cáo tổng quan: điểm trung bình, phân bố sao, người chơi khen điểm gì, phàn nàn
  vấn đề gì, có bug nào, và đề xuất cải thiện. Dùng khi người dùng cung cấp file review
  (JSON/CSV) hoặc tên/ID game và muốn "tổng hợp review", "phân tích đánh giá",
  "viết report review", "xem game được đánh giá thế nào". Tùy chọn gửi báo cáo lên Lark.
---

# Skylink Review Report

Mục tiêu: biến review thô của một game thành **báo cáo tổng quan dễ đọc bằng tiếng Việt**.

## Quy trình

### Bước 1 — Lấy dữ liệu review (chọn 1 trong 2)

**(A) Người dùng đã cung cấp dữ liệu** (upload file JSON/CSV, hoặc dán review):
→ Dùng luôn, KHÔNG cần mạng. Đây là đường mặc định, **luôn chạy được kể cả trên sandbox web bị chặn internet**.
Mỗi review nên có tối thiểu: `rating` (1–5) và `content` (nội dung; rỗng = chỉ đánh sao).

**(B) Người dùng chỉ đưa tên/ID game và muốn tự cào** (cần internet + cài thư viện):
→ Chạy `python scripts/fetch_reviews.py` (xem `--help`). Chỉ dùng khi môi trường có internet
(Claude Code local hoặc cloud routine). Nếu trên web báo lỗi network/`403`/timeout → báo người dùng
rằng sandbox web chặn mạng, đề nghị họ upload file review để phân tích thay thế.

### Bước 2 — Thống kê nhanh (bằng code, không suy đoán)
Dùng `python scripts/classify_rule.py <file.json>` để có số liệu khách quan:
điểm trung bình, phân bố sao, số review theo nhóm (bug / phàn nàn / khen / khen+chê / chỉ-đánh-sao).
Số liệu này để **đối chiếu**, không phải kết luận cuối — vì rule có thể gán nhầm vài ca.

### Bước 3 — ĐỌC và phân tích (phần quan trọng nhất)
TỰ ĐỌC nội dung review (ưu tiên đọc kỹ nhóm chê/bug/mixed, đọc lướt nhóm khen) rồi rút ra:
- **Tổng quan:** điểm, phân bố sao, tâm lý chung tích cực hay tiêu cực.
- **Khen — CỤ THỂ điểm nào** (gameplay, đồ họa, thư giãn, nhạc, chủ đề…), kèm dẫn chứng.
- **Phàn nàn — CỤ THỂ vấn đề gì** (quảng cáo, độ khó, pay-to-win, UI…), xếp theo mức độ nhức nhối + tần suất.
- **Bug:** lỗi kỹ thuật được nhắc (crash, ad không trả thưởng, màn hình đen, level kẹt…).
- **Đề xuất cải thiện** ngắn gọn, ưu tiên theo tác động.

Viết tiếng Việt, có cấu trúc rõ (heading + bullet), nêu được "khen gì / chê gì" cụ thể chứ không chung chung.

### Bước 4 — (Tùy chọn) Gửi lên Lark
Khi người dùng muốn gửi báo cáo lên Lark, chạy:
`python scripts/send_lark.py "<tiêu đề>" "<nội dung markdown>"`
Webhook đã được cấu hình sẵn trong `config.json` (script tự đọc) nên không cần truyền tay.
Muốn gửi sang group khác thì truyền webhook làm tham số thứ 3.
Lưu ý: trên sandbox web, lệnh này có thể bị **chặn mạng** → nếu lỗi network/timeout, báo người dùng
rằng web không gửi được, và phần gửi Lark nên chạy ở Claude Code/cloud routine.

## Lưu ý môi trường
- **Web (Claude.ai):** sandbox thường **chặn internet** → Bước 1B và Bước 4 có thể không chạy.
  Hãy hướng người dùng theo đường (A): upload file review để phân tích. Phân tích (Bước 2–3) luôn chạy được.
- **Claude Code / cloud routine:** chạy đầy đủ cả cào lẫn gửi Lark.

## File kèm theo
- `config.json` — webhook Lark cấu hình sẵn (LARK_WEBHOOK_URL).
- `scripts/fetch_reviews.py` — cào review iOS (RSS) + Android (google-play-scraper).
- `scripts/classify_rule.py` — thống kê + phân loại nhanh bằng luật (không cần mạng/API).
- `scripts/send_lark.py` — gửi 1 card lên Lark (tự đọc webhook từ config.json).
- `examples/sample_reviews.json` — dữ liệu mẫu để thử ngay trên web.
