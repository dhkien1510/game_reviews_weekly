"""
Cào review (CẦN INTERNET — không chạy được trên sandbox web bị chặn mạng).
Lưu kết quả ra file JSON để bước phân tích dùng.

Ví dụ:
  # iOS (App Store) qua RSS — chỉ cần requests
  python fetch_reviews.py --apple-id 6755671033 --countries us,vn --out reviews.json

  # Android (Google Play) — cần: pip install google-play-scraper
  python fetch_reviews.py --google-pkg com.skl.pyramid.quest.match3.tile.puzzle.games \
      --countries us --count 300 --out reviews.json

  # Cào nhiều quốc gia gọn: --countries all  (bung ra danh sách store lớn, đã dedup)
  python fetch_reviews.py --apple-id 6755671033 --countries all --out reviews.json
"""
import argparse
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

# 'all' bung ra danh sách 15 store lớn (đủ phủ, tránh quá tải + trùng lặp nặng).
# LƯU Ý: KHÔNG truyền chữ "all" thẳng vào API — cả iTunes RSS lẫn Google Play đều coi
# "all" là 1 mã quốc gia không hợp lệ -> trả trang rỗng. Phải bung thành list cụ thể.
ALL_COUNTRIES = [
    "us", "vn", "gb", "au", "ca", "sg", "ph", "th",
    "id", "de", "fr", "jp", "kr", "mx", "br",
]


def expand_countries(raw):
    """'all' -> ALL_COUNTRIES; ngược lại tách theo dấu phẩy."""
    if raw.strip().lower() == "all":
        return list(ALL_COUNTRIES)
    return [c.strip() for c in raw.split(",") if c.strip()]


def fetch_apple(app_id, countries, max_pages=10):
    import requests
    out = []
    for c in countries:
        for page in range(1, max_pages + 1):
            url = (f"https://itunes.apple.com/{c}/rss/customerreviews/"
                   f"page={page}/id={app_id}/sortby=mostrecent/json")
            try:
                entries = requests.get(url, timeout=30).json().get("feed", {}).get("entry", [])
            except Exception as e:
                print(f"[apple {c} p{page}] lỗi: {e}", file=sys.stderr)
                break
            # FIX: Apple RSS trả 'entry' là DICT (không phải list) khi quốc gia chỉ có đúng 1
            # review -> bản cũ vòng lặp gây TypeError. Normalize về list trước khi xử lý.
            if isinstance(entries, dict):
                entries = [entries]
            revs = [e for e in entries if isinstance(e, dict) and "im:rating" in e]
            if not revs:
                break
            for e in revs:
                try:
                    rating_val = e["im:rating"]
                    rating = int(rating_val["label"] if isinstance(rating_val, dict) else rating_val)
                    content_val = e.get("content", {})
                    content = (content_val.get("label", "") if isinstance(content_val, dict) else str(content_val) or "").strip()
                    version_val = e.get("im:version", {})
                    version = version_val.get("label", "") if isinstance(version_val, dict) else str(version_val or "")
                    id_val = e.get("id", {})
                    rid = id_val.get("label", "") if isinstance(id_val, dict) else str(id_val or "")
                    out.append({"platform": "iOS", "rating": rating, "content": content,
                                "version": version, "country": c, "_id": rid})
                except Exception as ex:
                    print(f"[apple] skip entry: {ex}", file=sys.stderr)
                    continue
            if len(revs) < 50:
                break
    return out


def fetch_google(pkg, countries, count):
    from google_play_scraper import reviews, Sort
    out = []
    for c in countries:
        try:
            res, _ = reviews(pkg, lang="en", country=c, sort=Sort.NEWEST, count=count)
        except Exception as e:
            print(f"[google {c}] lỗi: {e}", file=sys.stderr)
            continue
        for r in res:
            out.append({"platform": "Android", "rating": r.get("score"),
                        "content": (r.get("content") or "").strip(),
                        "version": r.get("reviewCreatedVersion") or "", "country": c,
                        "_id": r.get("reviewId") or ""})
    return out


def dedupe(reviews):
    """FIX: Google Play (và 1 phần iOS) trả CÙNG review cho nhiều quốc gia -> số liệu bị thổi phồng.
    Dedup theo reviewId nếu có; nếu không có id thì theo (platform, content, rating).
    KHÔNG gộp review rỗng-nội-dung không có id (tránh nuốt nhầm nhiều review chỉ-đánh-sao)."""
    seen = set()
    out = []
    for r in reviews:
        rid = (r.get("_id") or "").strip()
        if rid:
            key = ("id", rid)
        elif r.get("content"):
            key = ("cr", r.get("platform"), r.get("content"), r.get("rating"))
        else:
            key = None  # rỗng + không id -> luôn giữ
        if key is not None:
            if key in seen:
                continue
            seen.add(key)
        out.append({k: v for k, v in r.items() if k != "_id"})  # bỏ field nội bộ _id khỏi output
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--apple-id")
    p.add_argument("--google-pkg")
    p.add_argument("--countries", default="us",
                   help="Danh sách mã quốc gia (us,vn,gb...) hoặc 'all' để bung danh sách store lớn.")
    p.add_argument("--count", type=int, default=300)
    p.add_argument("--out", default="reviews.json")
    a = p.parse_args()
    countries = expand_countries(a.countries)

    raw = []
    if a.apple_id:
        raw += fetch_apple(a.apple_id, countries)
    if a.google_pkg:
        raw += fetch_google(a.google_pkg, countries, a.count)
    if not (a.apple_id or a.google_pkg):
        print("Cần --apple-id và/hoặc --google-pkg"); sys.exit(1)

    all_revs = dedupe(raw)
    json.dump(all_revs, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"Đã lưu {len(all_revs)} review (unique) vào {a.out} — raw {len(raw)} trước dedup")


if __name__ == "__main__":
    main()
