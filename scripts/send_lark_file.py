"""
Gửi 1 FILE (vd báo cáo .html) vào group Lark bằng APP BOT (CẦN INTERNET).

Khác send_lark.py (chỉ gửi card qua webhook), script này upload file thật rồi
gửi message msg_type=file vào group → người trong group bấm tải về.

Yêu cầu:
  - App có scope: im:message:send_as_bot (hoặc im:message) + im:resource
  - App đã release version mới sau khi thêm scope
  - Bot đã được add vào group cần gửi
  - config.json có: LARK_APP_ID, LARK_APP_SECRET, LARK_CHAT_ID, (tùy chọn) LARK_DOMAIN

Dùng:
  python send_lark_file.py <đường_dẫn_file>
  python send_lark_file.py report.html --chat oc_xxx        # ghi đè chat_id
  python send_lark_file.py report.html --name "Bao cao.html" # đổi tên hiển thị
"""
import argparse
import json
import os
import sys

import requests

sys.stdout.reconfigure(encoding="utf-8")

DEFAULT_DOMAIN = "https://open.larksuite.com"


def load_config():
    """Đọc cấu hình: ưu tiên BIẾN MÔI TRƯỜNG (an toàn cho public repo), rồi tới config.json."""
    cfg = {}
    path = os.path.join(os.path.dirname(__file__), "..", "config.json")
    try:
        with open(path, encoding="utf-8") as f:
            cfg = json.load(f)
    except Exception:
        cfg = {}
    # Env vars ghi đè giá trị trong file (nếu được set và không rỗng)
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


def upload_file(domain, token, path, display_name):
    url = f"{domain}/open-apis/im/v1/files"
    # file_type: dùng 'stream' cho file chung (html, zip, ...)
    with open(path, "rb") as f:
        files = {
            "file_type": (None, "stream"),
            "file_name": (None, display_name),
            "file": (display_name, f, "application/octet-stream"),
        }
        r = requests.post(url, headers={"Authorization": f"Bearer {token}"}, files=files, timeout=60)
    data = r.json()
    if data.get("code") != 0:
        raise RuntimeError(f"Upload file lỗi: {data}")
    return data["data"]["file_key"]


def send_file_message(domain, token, chat_id, file_key):
    url = f"{domain}/open-apis/im/v1/messages"
    payload = {
        "receive_id": chat_id,
        "msg_type": "file",
        "content": json.dumps({"file_key": file_key}),
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
        raise RuntimeError(f"Gửi message lỗi: {data}")
    return data


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path", help="Đường dẫn file cần gửi (vd report.html)")
    ap.add_argument("--chat", help="chat_id ghi đè (oc_xxx)")
    ap.add_argument("--name", help="Tên file hiển thị trong Lark")
    args = ap.parse_args()

    if not os.path.isfile(args.path):
        print(f"Không thấy file: {args.path}"); sys.exit(1)

    cfg = load_config()
    domain = cfg.get("LARK_DOMAIN", DEFAULT_DOMAIN).rstrip("/")
    app_id = cfg.get("LARK_APP_ID", "").strip()
    app_secret = cfg.get("LARK_APP_SECRET", "").strip()
    chat_id = (args.chat or cfg.get("LARK_CHAT_ID", "")).strip()
    display_name = args.name or os.path.basename(args.path)

    if not (app_id and app_secret):
        print("Thiếu LARK_APP_ID / LARK_APP_SECRET trong config.json"); sys.exit(1)
    if not chat_id:
        print("Thiếu chat_id (truyền --chat hoặc điền LARK_CHAT_ID)"); sys.exit(1)

    print("→ Lấy tenant_access_token...")
    token = get_tenant_token(domain, app_id, app_secret)
    print("→ Upload file...")
    file_key = upload_file(domain, token, args.path, display_name)
    print(f"  file_key = {file_key}")
    print("→ Gửi vào group...")
    send_file_message(domain, token, chat_id, file_key)
    print(f"✓ Đã gửi '{display_name}' vào {chat_id}")


if __name__ == "__main__":
    main()
