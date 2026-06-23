"""
So sánh review TUẦN NÀY với snapshot TUẦN TRƯỚC (đã lưu trong history/).

- Đọc history/<game>.json (nếu có): {seen_ids: [...], last: {avg, count, date}}.
- Tính review MỚI = review có 'id' chưa từng thấy. Tính điểm TB & tổng hiện tại.
- In ra (stdout) JSON delta cho Claude dùng để viết card:
    {game, is_first_run, new_count, new_reviews[], avg_now, avg_prev, count_now, count_prev}
- Cập nhật history/<game>.json: seen_ids = hợp (cũ + mới), last = số liệu hiện tại.

Dùng:
  python weekly_diff.py --game tile_pyramid --reviews reviews.json --date 2026-06-29
  (history-dir mặc định: ../history so với scripts/, hoặc truyền --history-dir)
"""
import argparse
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")


def stats(reviews):
    ratings = [r.get("rating") for r in reviews if r.get("rating")]
    avg = round(sum(ratings) / len(ratings), 2) if ratings else 0
    return avg, len(reviews)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--game", required=True, help="Khóa game (vd tile_pyramid) -> tên file history")
    p.add_argument("--reviews", required=True, help="File reviews.json tuần này")
    p.add_argument("--date", default="", help="Ngày báo cáo (YYYY-MM-DD) để ghi vào history")
    p.add_argument("--history-dir",
                   default=os.path.join(os.path.dirname(__file__), "..", "history"))
    p.add_argument("--max-new", type=int, default=40, help="Số review mới tối đa xuất ra")
    a = p.parse_args()

    reviews = json.load(open(a.reviews, encoding="utf-8"))
    hist_dir = a.history_dir
    os.makedirs(hist_dir, exist_ok=True)
    hist_path = os.path.join(hist_dir, f"{a.game}.json")

    prev = {}
    if os.path.exists(hist_path):
        try:
            prev = json.load(open(hist_path, encoding="utf-8"))
        except Exception:
            prev = {}
    seen = set(prev.get("seen_ids", []))
    last = prev.get("last", {})
    is_first = not prev

    new_reviews = []
    cur_ids = set()
    for r in reviews:
        rid = (r.get("id") or "").strip()
        if rid:
            cur_ids.add(rid)
            if rid not in seen:
                new_reviews.append(r)
        # review không có id -> không xác định mới/cũ, bỏ qua khỏi "mới" để tránh nhiễu

    avg_now, count_now = stats(reviews)
    delta = {
        "game": a.game,
        "date": a.date,
        "is_first_run": is_first,
        "new_count": len(new_reviews),
        "new_reviews": new_reviews[: a.max_new],
        "avg_now": avg_now,
        "avg_prev": last.get("avg"),
        "count_now": count_now,
        "count_prev": last.get("count"),
        "prev_date": last.get("date"),
    }
    print(json.dumps(delta, ensure_ascii=False, indent=1))

    # Cập nhật history (hợp tập id để lần sau biết cái nào đã thấy)
    updated = {
        "seen_ids": sorted(seen | cur_ids),
        "last": {"avg": avg_now, "count": count_now, "date": a.date},
    }
    json.dump(updated, open(hist_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
