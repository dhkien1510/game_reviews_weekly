"""
Cào review (CẦN INTERNET — không chạy được trên sandbox web bị chặn mạng).
Lưu kết quả ra file JSON để bước phân tích dùng.

Ví dụ:
  # iOS (App Store) qua RSS — chỉ cần requests
  python fetch_reviews.py --apple-id 6755671033 --countries us,vn --out reviews.json

  # Android (Google Play) — cần: pip install google-play-scraper
  python fetch_reviews.py --google-pkg com.skl.pyramid.quest.match3.tile.puzzle.games \
      --countries us --count 300 --out reviews.json
"""
import argparse
import json
import sys


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
            revs = [e for e in entries if "im:rating" in e]
            if not revs:
                break
            for e in revs:
                out.append({"platform": "iOS", "rating": int(e["im:rating"]["label"]),
                            "content": (e.get("content", {}).get("label", "") or "").strip(),
                            "version": e.get("im:version", {}).get("label", ""), "country": c})
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
                        "version": r.get("reviewCreatedVersion") or "", "country": c})
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--apple-id")
    p.add_argument("--google-pkg")
    p.add_argument("--countries", default="us")
    p.add_argument("--count", type=int, default=300)
    p.add_argument("--out", default="reviews.json")
    a = p.parse_args()
    countries = [c.strip() for c in a.countries.split(",") if c.strip()]

    all_revs = []
    if a.apple_id:
        all_revs += fetch_apple(a.apple_id, countries)
    if a.google_pkg:
        all_revs += fetch_google(a.google_pkg, countries, a.count)
    if not (a.apple_id or a.google_pkg):
        print("Cần --apple-id và/hoặc --google-pkg"); sys.exit(1)

    json.dump(all_revs, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"Đã lưu {len(all_revs)} review vào {a.out}")


if __name__ == "__main__":
    main()
