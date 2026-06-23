"""
Thống kê + phân loại nhanh review bằng LUẬT (không cần mạng, không cần API).
Dùng: python classify_rule.py <file_review.json>
File JSON: list các object có 'rating' (1-5) và 'content' (chuỗi; rỗng = chỉ đánh sao).
In ra: điểm TB, phân bố sao, số lượng theo nhóm bug/complaint/praise/mixed/star_only.
Kết quả này để ĐỐI CHIẾU; phần nhận xét nên do người/Claude đọc và viết.
"""
import json
import sys
from collections import Counter

ASPECTS = [
    ("lỗi/crash", "bug", ["crash", "bug", "glitch", "freeze", "won't open", "can't open",
        "force close", "black screen", "not working", "doesn't work", "error",
        "lỗi", "đơ", "treo", "văng", "không vào được", "không mở", "không chơi được"]),
    ("quảng cáo nhiều", -1, ["too many ads", "so many ads", "lots of ads", "forced ad",
        "ad after", "ads after", "full of ads", "quảng cáo", "nhiều qc"]),
    ("tốn tiền/p2w", -1, ["pay to win", "p2w", "paywall", "expensive", "money grab",
        "scam", "rip off", "moi tiền", "đắt", "mất tiền", "lừa đảo"]),
    ("quá khó", -1, ["too hard", "impossible", "too difficult", "frustrating", "unfair",
        "khó quá", "quá khó"]),
    ("quá dễ", -1, ["too easy", "dễ quá", "quá dễ"]),
    ("lag/giật", -1, ["lag", "laggy", "slow", "stutter", "giật", "chậm"]),
    ("nhàm chán", -1, ["boring", "repetitive", "dull", "tedious", "nhàm", "chán", "lặp lại"]),
    ("gameplay vui/cuốn", +1, ["fun", "addictive", "addicting", "enjoyable", "entertaining",
        "vui", "gây nghiện", "cuốn", "giải trí"]),
    ("thư giãn", +1, ["relaxing", "calm", "chill", "soothing", "stress", "thư giãn", "thoải mái"]),
    ("đồ họa đẹp", +1, ["beautiful", "gorgeous", "colorful", "graphics", "cute", "art",
        "đồ họa", "hình ảnh", "đẹp"]),
    ("khen chung", +1, ["good", "great", "love", "awesome", "amazing", "excellent", "perfect",
        "best", "nice", "recommend", "hay", "tuyệt", "thích", "đỉnh", "ngon", "tốt"]),
    ("chê chung", -1, ["bad", "terrible", "worst", "horrible", "awful", "hate", "garbage",
        "trash", "dở", "tệ", "kém"]),
]
NEG = ["not", "no", "don't", "doesn't", "never", "without", "stop", "remove", "fix",
       "không", "chẳng", "chả", "đừng", "bớt", "hết"]


def classify(text, rating=None):
    t = " " + (text or "").lower() + " "
    words = t.split()
    bug, pos, neg = [], [], []
    for label, pol, kws in ASPECTS:
        for kw in kws:
            i = t.find(kw)
            if i == -1:
                continue
            if pol in (1, -1):
                widx = len(t[:i].split())
                eff = -pol if any(w in NEG for w in words[max(0, widx-3):widx]) else pol
            else:
                eff = pol
            if pol == "bug":
                bug.append(label)
            elif eff > 0:
                pos.append(label)
            else:
                neg.append(label)
            break
    if bug:
        return "bug", "; ".join(dict.fromkeys(bug))
    pos, neg = list(dict.fromkeys(pos)), list(dict.fromkeys(neg))
    if pos and neg:
        return "mixed", "👍 " + ", ".join(pos) + " | 👎 " + ", ".join(neg)
    if pos:
        return "praise", ", ".join(pos)
    if neg:
        return "complaint", ", ".join(neg)
    if rating is not None:
        if rating >= 4:
            return "praise", "khen chung (suy từ sao cao)"
        if rating <= 2:
            return "complaint", "không hài lòng (suy từ sao thấp)"
    return "mixed", "trung tính"


def main():
    if len(sys.argv) < 2:
        print("Dùng: python classify_rule.py <file_review.json>")
        sys.exit(1)
    revs = json.load(open(sys.argv[1], encoding="utf-8"))
    cats, dist = Counter(), Counter()
    ratings = []
    for r in revs:
        rating = r.get("rating")
        if rating:
            dist[rating] += 1
            ratings.append(rating)
        if not (r.get("content") or "").strip():
            cats["star_only"] += 1
        else:
            c, _ = classify(r["content"], rating)
            cats[c] += 1
    avg = round(sum(ratings) / len(ratings), 2) if ratings else 0
    print(f"Tổng review: {len(revs)} | Điểm TB: ⭐{avg}")
    print("Phân bố sao:", {k: dist[k] for k in sorted(dist)})
    print("Phân loại:", dict(cats))


if __name__ == "__main__":
    main()
