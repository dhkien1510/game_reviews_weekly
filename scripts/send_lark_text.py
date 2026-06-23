"""
Gửi 1 tin nhắn TEXT vào group Lark bằng APP BOT (CẦN INTERNET).

Đọc cấu hình: ưu tiên BIẾN MÔI TRƯỜNG (an toàn cho public repo) rồi tới config.json.
Cần: LARK_APP_ID, LARK_APP_SECRET, LARK_CHAT_ID, (tùy chọn) LARK_DOMAIN.
Scope app: im:message:send_as_bot (hoặc im:message). Bot phải ở trong group.

Dùng:
  python send_lark_text.py "<nội dung>"            # text từ argv
  echo "..." | python send_lark_text.py             # text từ stdin (multiline)
  python send_lark_text.py "<nội dung>" --chat oc_xxx
"""
import argparse
import json
import os
import sys

import requests

sys.stdout.reconfigure(encoding="utf-8")
sys.stdin.reconfigure(encoding="utf-8")

DEFAULT_DOMAIN = "https://open.larksuite.com"


def load_config():
    cfg = {}
    path = os.path.join(os.path.dirname(__file__), "..", "config.json")
    try:
        with open(path, encoding="utf-8") as f:
            cfg = json.load(f)
    except Exception:
        cfg = {}
    for k in ("LARK_DOMAIN", "LARK_APP_ID", "LARK_APP_SECRET", "LARK_CHAT_ID"):
        v = os.environ.get(k, "").strip()
        if v:
            cfg[k] = v
    return cfg


def get_tenant_token(domain, app_id, app_secret):
    url = f"{domain}/open-apis/auth/v3/tenant_access_token/internal"
    r = requests.post(url, json={"app_id": app_id, "app_secret": app_secret}, timeout=30)
    data = r.json()
    if data.get("code") != 0:
        raise RuntimeError(f"Lấy token lỗi: {data}")
    return data["tenant_access_token"]


def send_text(domain, token, chat_id, text):
    url = f"{domain}/open-apis/im/v1/messages"
    payload = {
        "receive_id": chat_id,
        "msg_type": "text",
        "content": json.dumps({"text": text}),
    }
    r = requests.post(
        url,
        params={"receive_id_type": "chat_id"},
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json=payload,
        timeout=30,
    )
    data = r.json()
    if data.get("code") != 0:
        raise RuntimeError(f"Gửi text lỗi: {data}")
    return data


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("text", nargs="?", help="Nội dung text (bỏ trống = đọc stdin)")
    ap.add_argument("--chat", help="chat_id ghi đè (oc_xxx)")
    args = ap.parse_args()

    text = args.text if args.text is not None else sys.stdin.read()
    if not text.strip():
        print("Không có nội dung để gửi"); sys.exit(1)

    cfg = load_config()
    domain = cfg.get("LARK_DOMAIN", DEFAULT_DOMAIN).rstrip("/")
    app_id = cfg.get("LARK_APP_ID", "").strip()
    app_secret = cfg.get("LARK_APP_SECRET", "").strip()
    chat_id = (args.chat or cfg.get("LARK_CHAT_ID", "")).strip()

    if not (app_id and app_secret):
        print("Thiếu LARK_APP_ID / LARK_APP_SECRET"); sys.exit(1)
    if not chat_id:
        print("Thiếu chat_id (truyền --chat hoặc set LARK_CHAT_ID)"); sys.exit(1)

    token = get_tenant_token(domain, app_id, app_secret)
    send_text(domain, token, chat_id, text)
    print(f"✓ Đã gửi text vào {chat_id}")


if __name__ == "__main__":
    main()
