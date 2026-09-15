"""汇总 results.jsonl 与 baseline_v1.jsonl，输出 README 可用的指标表。"""
import json
from pathlib import Path

EVAL = Path(__file__).resolve().parent


def load(path):
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def summarize(rows, label):
    total = len(rows)
    completed = [r for r in rows if r.get("status") == "completed"]
    answer_rows = [r for r in completed if r["expected_behavior"] == "answer"]
    # 非答题类（无材料/对抗/模糊）：考核点是"诚实"而非"答出"
    honesty_rows = [r for r in completed if r["expected_behavior"] != "answer"]

    point_total = sum(r["checks"]["expected_points_total"] for r in answer_rows)
    point_hit = sum(r["checks"]["expected_points_hit_count"] for r in answer_rows)
    citation_ok = sum(1 for r in completed if r["checks"]["citation_number_pass"])
    invalid_all = [
        (r["id"], r["checks"]["invalid_citations"])
        for r in completed
        if r["checks"]["invalid_citations"]
    ]
    insufficient_ok = sum(
        1
        for r in honesty_rows
        if any(
            marker in r.get("report", "")
            for marker in ("材料不足", "无法可靠回答", "⚠️", "无法确认")
        )
    )
    durations = [r["duration_seconds"] for r in completed]
    source_counts = [r["checks"]["source_count"] for r in answer_rows]

    print(f"\n===== {label}（{total} 题）=====")
    print(f"报告生成成功率: {len(completed)}/{total}")
    if point_total:
        print(f"关键点命中率: {point_hit}/{point_total} = {point_hit / point_total:.1%}")
    print(f"引用编号有效率: {citation_ok}/{len(completed)} = {citation_ok / len(completed):.1%}")
    print(f"无效引用明细: {invalid_all if invalid_all else '无'}")
    if honesty_rows:
        print(
            f"无材料/对抗/模糊题诚实处理率: {insufficient_ok}/{len(honesty_rows)} = "
            f"{insufficient_ok / len(honesty_rows):.1%}"
        )
    if durations:
        print(f"平均耗时: {sum(durations) / len(durations):.1f} 秒（最长 {max(durations):.0f} 秒）")
    if source_counts:
        print(f"答题类平均来源数: {sum(source_counts) / len(source_counts):.1f}")

    print("逐题明细（id | 来源数 | 命中/总 | 引用OK | 耗时s）:")
    for r in completed:
        c = r["checks"]
        print(
            f"  {r['id']:16s} | src={c['source_count']:2d} | "
            f"{c['expected_points_hit_count']}/{c['expected_points_total']} | "
            f"cite_ok={c['citation_number_pass']} | {r['duration_seconds']:6.1f}s"
        )

    need_manual = [
        r["id"]
        for r in completed
        if r["expected_behavior"] in ("clarify_or_limited_answer", "limited_or_refuse", "refuse")
    ]
    print(f"需人工核对报告措辞的题: {need_manual}")


summarize(load(EVAL / "results.jsonl"), "本次运行（24 题，搜狗/必应引擎）")

baseline_path = EVAL / "baseline_v1.jsonl"
if baseline_path.exists():
    summarize(load(baseline_path), "baseline_v1（10 题）")
