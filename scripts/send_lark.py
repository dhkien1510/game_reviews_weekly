"""
Gửi 1 card lên Lark webhook (CẦN INTERNET — có thể bị chặn trên sandbox web).

Webhook được đọc theo thứ tự ưu tiên:
  1) tham số dòng lệnh (nếu có)
  2) file ../config.json (LARK_WEBHOOK_URL) — đã cấu hình sẵn trong skill

Dùng:
  python send_lark.py "<tiêu đề>" "<nội dung markdown>"                  # dùng webhook trong config.json
  python send_lark.py "<tiêu đề>" "<markdown>" "<WEBHOOK_URL>"           # tự truyền webhook
"""
import json
import os
import sys

import requests


def load_config_webhook():
    cfg = os.path.join(os.path.dirname(__file__), "..", "config.json")
    try:
        with open(cfg, encoding="utf-8") as f:
            return json.load(f).get("LARK_WEBHOOK_URL", "").strip()
    except Exception:
        return ""


def main():
    if len(sys.argv) < 3:
        print('Dùng: python send_lark.py "<tiêu đề>" "<markdown>" [<WEBHOOK_URL>]')
        sys.exit(1)
    title, md = sys.argv[1], sys.argv[2]
    webhook = sys.argv[3] if len(sys.argv) > 3 else load_config_webhook()
    if not webhook:
        print("Không có webhook (truyền tham số hoặc điền vào config.json)"); sys.exit(1)

    card = {
        "config": {"wide_screen_mode": True},
        "header": {"template": "blue", "title": {"tag": "plain_text", "content": title}},
        "elements": [{"tag": "markdown", "content": md}],
    }
    r = requests.post(webhook, json={"msg_type": "interactive", "card": card}, timeout=30)
    print("HTTP", r.status_code, "->", r.text)


if __name__ == "__main__":
    main()
