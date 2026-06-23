# Skylink Review Skill — runner cho cloud routine

Scripts cào & tổng hợp review game Skylink (App Store / Google Play), dùng cho
Claude Code cloud routine chạy weekly.

## ⚠️ Bảo mật

Repo này có thể để **PUBLIC** — vì vậy **KHÔNG commit secret**:
- `config.json` chỉ chứa placeholder rỗng.
- Secret Lark (`LARK_APP_ID`, `LARK_APP_SECRET`, `LARK_CHAT_ID`) được truyền qua
  **biến môi trường** lúc chạy. Script đọc env trước, file sau.

## Cài đặt

```bash
pip install -r requirements.txt
```

## Quy trình chạy 1 game

```bash
# 1) Cào review (vd Tile Pyramid Android)
python scripts/fetch_reviews.py --google-pkg com.skl.pyramid.quest.match3.tile.puzzle.games --countries all --count 500 --out reviews.json
# hoặc iOS:
python scripts/fetch_reviews.py --apple-id 6755671033 --countries all --out reviews.json

# 2) Thống kê nhanh
python scripts/classify_rule.py reviews.json

# 3) (Claude tự đọc & phân tích, tạo report.json) rồi render HTML
python scripts/render_html.py reviews.json --title "Tile Pyramid (Android)" --report report.json --out report.html

# 4) Gửi lên Lark (cần env LARK_APP_ID/SECRET/CHAT_ID)
python scripts/send_lark_file.py report.html --name "Tile Pyramid - report.html"
```

## File

- `games.json` — bảng tra App ID / package theo tên game.
- `scripts/fetch_reviews.py` — cào iOS RSS + Android.
- `scripts/classify_rule.py` — thống kê + phân loại nhanh (stdlib).
- `scripts/render_html.py` — render báo cáo HTML (stdlib).
- `scripts/send_lark_file.py` — gửi FILE lên group Lark qua App Bot (env-var).
- `scripts/send_lark.py` — gửi card markdown qua webhook (legacy).
