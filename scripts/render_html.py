"""
Render báo cáo review ra 1 file HTML đơn giản, đứng-một-mình (standalone) để demo / xem nhanh.

- Số liệu định lượng (điểm TB, phân bố sao, số review) được TÍNH bằng code từ reviews.json
  → không bịa số.
- Phần định tính (khen / chê / bug / đề xuất / tóm tắt) do Claude phân tích rồi truyền vào
  qua --report report.json (tùy chọn). Bỏ qua thì HTML chỉ có dashboard định lượng.

Ví dụ:
  python render_html.py reviews.json --title "Snake Go (App Store)" \
      --report report.json --out report.html

report.json (tất cả khóa đều tùy chọn):
{
  "summary": "Một câu tổng quan...",
  "praises":     ["Khen điểm A — dẫn chứng", "..."],
  "complaints":  ["Phàn nàn B (nặng nhất)", "..."],
  "bugs":        ["Lỗi C", "..."],
  "suggestions": ["Đề xuất D", "..."]
}
"""
import argparse
import html
import json
import sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")


def esc(s):
    return html.escape(str(s or ""))


def sentiment(rating):
    if rating is None:
        return "neutral"
    if rating >= 4:
        return "pos"
    if rating <= 2:
        return "neg"
    return "neutral"


def li_list(items):
    if not items:
        return '<li class="muted">— (không có)</li>'
    return "\n".join(f"<li>{esc(x)}</li>" for x in items)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("reviews", help="file reviews.json")
    p.add_argument("--title", default="Báo cáo Review")
    p.add_argument("--report", help="report.json chứa phần phân tích định tính (tùy chọn)")
    p.add_argument("--out", default="report.html")
    a = p.parse_args()

    revs = json.load(open(a.reviews, encoding="utf-8"))
    report = json.load(open(a.report, encoding="utf-8")) if a.report else {}

    n = len(revs)
    ratings = [r.get("rating") for r in revs if isinstance(r.get("rating"), int)]
    avg = round(sum(ratings) / len(ratings), 2) if ratings else 0
    dist = Counter(ratings)
    max_bar = max(dist.values()) if dist else 1

    # thanh phân bố sao 5 -> 1
    bars = ""
    for star in range(5, 0, -1):
        c = dist.get(star, 0)
        pct = round(c / max_bar * 100) if max_bar else 0
        bars += (
            f'<div class="bar-row"><span class="bar-label">{star}★</span>'
            f'<span class="bar-track"><span class="bar-fill" style="width:{pct}%"></span></span>'
            f'<span class="bar-num">{c}</span></div>'
        )

    # bảng review (sắp xếp sao tăng dần để nhóm tiêu cực lên trên)
    rows = ""
    for r in sorted(revs, key=lambda x: (x.get("rating") or 0)):
        rt = r.get("rating")
        rows += (
            f'<tr class="{sentiment(rt)}"><td class="c-star">{esc(rt)}★</td>'
            f'<td class="c-meta">{esc(r.get("country","")).upper()} · {esc(r.get("version",""))}</td>'
            f'<td class="c-body">{esc(r.get("content","")) or "<span class=muted>(chỉ đánh sao)</span>"}</td></tr>'
        )

    summary = esc(report.get("summary", ""))

    doc = f"""<!doctype html>
<html lang="vi"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(a.title)}</title>
<style>
  :root{{--pos:#16a34a;--neg:#dc2626;--neu:#d97706;--ink:#1f2937;--muted:#9ca3af;--line:#e5e7eb;--bg:#f8fafc}}
  *{{box-sizing:border-box}}
  body{{font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;color:var(--ink);margin:0;background:var(--bg);line-height:1.55}}
  .wrap{{max-width:880px;margin:0 auto;padding:28px 20px 60px}}
  h1{{font-size:24px;margin:0 0 4px}}
  .sub{{color:var(--muted);font-size:13px;margin-bottom:22px}}
  .cards{{display:flex;gap:14px;flex-wrap:wrap;margin-bottom:24px}}
  .card{{background:#fff;border:1px solid var(--line);border-radius:14px;padding:16px 18px;flex:1;min-width:150px}}
  .kpi{{font-size:34px;font-weight:700}}
  .kpi small{{font-size:15px;color:var(--muted);font-weight:400}}
  .card .lbl{{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.04em}}
  .bar-row{{display:flex;align-items:center;gap:10px;margin:5px 0;font-size:13px}}
  .bar-label{{width:26px;color:var(--muted)}}
  .bar-track{{flex:1;height:10px;background:#eef2f7;border-radius:6px;overflow:hidden}}
  .bar-fill{{display:block;height:100%;background:linear-gradient(90deg,#fbbf24,#f59e0b)}}
  .bar-num{{width:26px;text-align:right;color:var(--muted)}}
  .summary{{background:#fff;border:1px solid var(--line);border-left:4px solid #6366f1;border-radius:10px;padding:14px 16px;margin:0 0 24px;font-size:15px}}
  .grid{{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:24px}}
  @media(max-width:620px){{.grid{{grid-template-columns:1fr}}}}
  .sec{{background:#fff;border:1px solid var(--line);border-radius:12px;padding:14px 18px}}
  .sec h3{{margin:0 0 8px;font-size:15px}}
  .sec ul{{margin:0;padding-left:18px}}
  .sec li{{margin:4px 0;font-size:14px}}
  .sec.praise{{border-top:3px solid var(--pos)}}
  .sec.complaint{{border-top:3px solid var(--neg)}}
  .sec.bug{{border-top:3px solid #7c3aed}}
  .sec.sugg{{border-top:3px solid #2563eb}}
  table{{width:100%;border-collapse:collapse;background:#fff;border:1px solid var(--line);border-radius:12px;overflow:hidden;font-size:13.5px}}
  th,td{{text-align:left;padding:9px 12px;border-bottom:1px solid var(--line);vertical-align:top}}
  th{{background:#f1f5f9;font-size:12px;text-transform:uppercase;letter-spacing:.03em;color:#475569}}
  .c-star{{white-space:nowrap;font-weight:600}}
  .c-meta{{white-space:nowrap;color:var(--muted);font-size:12px}}
  tr.pos .c-star{{color:var(--pos)}}
  tr.neg .c-star{{color:var(--neg)}}
  tr.neutral .c-star{{color:var(--neu)}}
  .muted{{color:var(--muted)}}
  h2{{font-size:16px;margin:26px 0 10px}}
</style></head>
<body><div class="wrap">
  <h1>{esc(a.title)}</h1>
  <div class="sub">Báo cáo tổng hợp review · {n} review</div>

  <div class="cards">
    <div class="card"><div class="lbl">Điểm trung bình</div><div class="kpi">{avg}<small> / 5 ⭐</small></div></div>
    <div class="card"><div class="lbl">Tổng review</div><div class="kpi">{n}</div></div>
    <div class="card" style="flex:2;min-width:240px"><div class="lbl">Phân bố sao</div>{bars}</div>
  </div>

  {f'<div class="summary">{summary}</div>' if summary else ''}

  <div class="grid">
    <div class="sec praise"><h3>👍 Khen</h3><ul>{li_list(report.get("praises"))}</ul></div>
    <div class="sec complaint"><h3>👎 Phàn nàn</h3><ul>{li_list(report.get("complaints"))}</ul></div>
    <div class="sec bug"><h3>🐞 Bug / lỗi</h3><ul>{li_list(report.get("bugs"))}</ul></div>
    <div class="sec sugg"><h3>💡 Đề xuất</h3><ul>{li_list(report.get("suggestions"))}</ul></div>
  </div>

  <h2>Chi tiết review</h2>
  <table><thead><tr><th>Sao</th><th>Nguồn</th><th>Nội dung</th></tr></thead>
  <tbody>{rows}</tbody></table>
</div></body></html>"""

    open(a.out, "w", encoding="utf-8").write(doc)
    print(f"Đã render HTML ({n} review, TB {avg}★) -> {a.out}")


if __name__ == "__main__":
    main()
