import argparse
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path


# 将项目根目录 D:\deep 加入模块搜索路径
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from research import knowledge_fallback, research, write_report


EVAL_DIR = Path(__file__).resolve().parent
QUESTIONS_FILE = EVAL_DIR / "questions.jsonl"
RESULTS_FILE = EVAL_DIR / "results.jsonl"
REPORTS_DIR = EVAL_DIR / "reports"


def load_cases():
    """读取JSONL评测题库。"""
    cases = []

    with QUESTIONS_FILE.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()

            if not line:
                continue

            try:
                cases.append(json.loads(line))
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"questions.jsonl 第{line_number}行格式错误：{error}"
                ) from error

    return cases


def check_result(case, report, sources):
    """执行第一版可自动判断的检查。"""
    source_count = len(sources)
    minimum_sources = case.get("min_sources", 0)
    expected_behavior = case.get("expected_behavior", "answer")
    expected_points = case.get("expected_points", [])

    # 检查关键点是否出现在报告中
    expected_points_hit = [
        point for point in expected_points
        if point.lower() in report.lower()
    ]

    # 找出报告中的[n]引用编号
    citation_numbers = sorted({
        int(number)
        for number in re.findall(r"\[(\d+)]", report)
    })

    # 检查是否引用了不存在的来源编号
    invalid_citations = [
        number
        for number in citation_numbers
        if number < 1 or number > source_count
    ]

    if expected_behavior == "answer":
        behavior_pass = source_count >= minimum_sources
    elif expected_behavior == "insufficient":
        behavior_pass = source_count == 0
    else:
        # 模糊问题暂时需要人工判断
        behavior_pass = None

    return {
        "source_count": source_count,
        "min_sources_pass": source_count >= minimum_sources,
        "expected_behavior_pass": behavior_pass,
        "expected_points_total": len(expected_points),
        "expected_points_hit": expected_points_hit,
        "expected_points_hit_count": len(expected_points_hit),
        "citation_numbers": citation_numbers,
        "invalid_citations": invalid_citations,
        "citation_number_pass": len(invalid_citations) == 0,
    }


def run_case(case, max_rounds):
    """运行一道评测题。"""
    question = case["question"]
    logs = []
    start_time = time.perf_counter()

    notes, sources = research(
        question,
        max_rounds=max_rounds,
        log=logs.append,
    )

    if sources:
        report = write_report(question, notes, sources)
    else:
        report = knowledge_fallback(question)

    duration_seconds = round(time.perf_counter() - start_time, 2)
    checks = check_result(case, report, sources)

    source_summary = [
        {
            "title": source.get("title", ""),
            "url": source.get("url", ""),
        }
        for source in sources
    ]

    return {
        "id": case["id"],
        "category": case.get("category", ""),
        "question": question,
        "expected_behavior": case.get("expected_behavior", ""),
        "source_requirement": case.get("source_requirement", ""),
        "status": "completed",
        "duration_seconds": duration_seconds,
        "checks": checks,
        "sources": source_summary,
        "logs": logs,
        "report": report,
        "evaluated_at": datetime.now().isoformat(timespec="seconds"),
    }


def main():
    parser = argparse.ArgumentParser(description="运行DeepResearch评测")
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="只运行前N道题，测试时可使用 --limit 1",
    )
    parser.add_argument(
        "--max-rounds",
        type=int,
        default=3,
        help="每道题最多检索轮数，默认3轮",
    )
    args = parser.parse_args()

    cases = load_cases()

    if args.limit is not None:
        cases = cases[:args.limit]

    if not cases:
        raise RuntimeError("questions.jsonl 中没有评测题")

    REPORTS_DIR.mkdir(exist_ok=True)

    print(f"共准备运行 {len(cases)} 道评测题")

    with RESULTS_FILE.open("w", encoding="utf-8") as result_file:
        for index, case in enumerate(cases, start=1):
            case_id = case["id"]

            print(f"\n[{index}/{len(cases)}] {case_id}")
            print(f"问题：{case['question']}")

            try:
                result = run_case(case, args.max_rounds)

                report_path = REPORTS_DIR / f"{case_id}.md"
                report_path.write_text(
                    f"# {case['question']}\n\n{result['report']}",
                    encoding="utf-8",
                )

                checks = result["checks"]
                print(f"完成，用时：{result['duration_seconds']}秒")
                print(f"来源数量：{checks['source_count']}")
                print(
                    "关键点命中："
                    f"{checks['expected_points_hit_count']}/"
                    f"{checks['expected_points_total']}"
                )
                print(f"无效引用：{checks['invalid_citations']}")

            except Exception as error:
                result = {
                    "id": case_id,
                    "category": case.get("category", ""),
                    "question": case["question"],
                    "status": "failed",
                    "error_type": type(error).__name__,
                    "error": str(error),
                    "evaluated_at": datetime.now().isoformat(
                        timespec="seconds"
                    ),
                }

                print(f"运行失败：{type(error).__name__}: {error}")

            result_file.write(
                json.dumps(result, ensure_ascii=False) + "\n"
            )
            result_file.flush()

    print("\n评测完成")
    print(f"结果文件：{RESULTS_FILE}")
    print(f"报告目录：{REPORTS_DIR}")


if __name__ == "__main__":
    main()