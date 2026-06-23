"""
Gửi 1 CARD có BẢNG (dựng bằng column_set) vào group Lark bằng APP BOT.

Lark card markdown KHÔNG render bảng GitHub-style. Script này dựng "bảng" bằng
column_set: mỗi cột bảng = 1 column markdown (header in đậm + các dòng), xếp cạnh nhau.
Phù hợp bảng nhỏ, mỗi ô 1 dòng ngắn.

Đọc cấu hình: ưu tiên BIẾN MÔI TRƯỜNG rồi tới config.json.
Cần: LARK_APP_ID, LARK_APP_SECRET, LARK_CHAT_ID, (tùy chọn) LARK_DOMAIN.

Dữ liệu bảng truyền qua JSON (file hoặc stdin):
  {
    "headers": ["Game", "Diem TB", "Reviews", "Xu huong"],
    "rows": [
      ["Tile Pyramid", "4.38", "188", "tich cuc"],
      ["Snake Go", "3.1", "8", "kha tich cuc"]
    ],
    "note": "**Tuan 23/06/2026** — tong hop nhanh"   # tùy chọn, markdown trên bảng
  }

Dùng:
  python send_lark_table.py "<tiêu đề>" data.json
  cat data.json | python send_lark_table.py "<tiêu đề>"
  python send_lark_table.py "<tiêu đề>" data.json --color green --chat oc_xxx
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


def build_table_columns(headers, rows):
    """Mỗi cột bảng -> 1 column chứa markdown: '**Header**\\nval1\\nval2...'. Xếp cạnh nhau = bảng."""
    columns = []
    for ci, head in enumerate(headers):
        lines = [f"**{head}**"]
        for row in rows:
            cell = str(row[ci]) if ci < len(row) else ""
            lines.append(cell)
        columns.append({
            "tag": "column",
            "width": "auto",
            "vertical_align": "top",
            "elements": [{"tag": "markdown", "content": "\n".join(lines)}],
        })
    return {"tag": "column_set", "flex_mode": "stretch", "horizontal_spacing": "default", "columns": columns}


def send_table_card(domain, token, chat_id, title, headers, rows, note, color):
    elements = []
    if note:
        elements.append({"tag": "markdown", "content": note})
        elements.append({"tag": "hr"})
    elements.append(build_table_columns(headers, rows))
    card = {
        "config": {"wide_screen_mode": True},
        "header": {"template": color, "title": {"tag": "plain_text", "content": title}},
        "elements": elements,
    }
    url = f"{domain}/open-apis/im/v1/messages"
    payload = {"receive_id": chat_id, "msg_type": "interactive", "content": json.dumps(card)}
    r = requests.post(
        url,
        params={"receive_id_type": "chat_id"},
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json=payload,
        timeout=30,
    )
    data = r.json()
    if data.get("code") != 0:
        raise RuntimeError(f"Gửi card bảng lỗi: {data}")
    return data


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("title", help="Tiêu đề card")
    ap.add_argument("data", nargs="?", help="File JSON {headers, rows, note} (bỏ trống = đọc stdin)")
    ap.add_argument("--color", default="blue")
    ap.add_argument("--chat")
    args = ap.parse_args()

    raw = open(args.data, encoding="utf-8").read() if args.data else sys.stdin.read()
    spec = json.loads(raw)
    headers = spec.get("headers") or []
    rows = spec.get("rows") or []
    note = spec.get("note", "")
    if not headers or not rows:
        print("Thiếu 'headers' hoặc 'rows' trong JSON"); sys.exit(1)

    cfg = load_config()
    domain = cfg.get("LARK_DOMAIN", DEFAULT_DOMAIN).rstrip("/")
    app_id = cfg.get("LARK_APP_ID", "").strip()
    app_secret = cfg.get("LARK_APP_SECRET", "").strip()
    chat_id = (args.chat or cfg.get("LARK_CHAT_ID", "")).strip()
    if not (app_id and app_secret):
        print("Thiếu LARK_APP_ID / LARK_APP_SECRET"); sys.exit(1)
    if not chat_id:
        print("Thiếu chat_id"); sys.exit(1)

    token = get_tenant_token(domain, app_id, app_secret)
    send_table_card(domain, token, chat_id, args.title, headers, rows, note, args.color)
    print(f"✓ Đã gửi card bảng '{args.title}' vào {chat_id}")


if __name__ == "__main__":
    main()
