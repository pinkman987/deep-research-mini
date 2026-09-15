import json
import time
from concurrent.futures import ThreadPoolExecutor
from search_tool import search, fetch
from llm import ask


def relevant(body, question, ratio=0.5):
    """关键词覆盖率过滤：正文覆盖问题中 ratio 比例以上的字才算相关
    预筛时用宽松的 0.3，终筛用严格的 0.5"""
    chars = [c for c in question if c not in " ？?，,。、/"]
    hit = sum(1 for c in chars if c in body)
    return hit >= len(chars) * ratio


def _fetch_one(r):
    """并发抓取的工人函数：线程池里每个线程跑一个它"""
    final_url, body = fetch(r["url"], retries=1)
    return r, final_url, body


def collect(question, queries, sources, seen, max_new=4):
    """搜索+抓取一轮；三个提速手段：
    1. 摘要预筛：snippet 就不相关的页面根本不抓
    2. 并发抓取：候选页面同时抓，耗时=最慢的一篇
    3. 早停：本轮新增够 max_new 篇就不再抓"""
    round_start = len(sources)
    for q in queries:
        if len(sources) - round_start >= max_new:
            print("  本轮材料已够，提前停止抓取")
            break
        hits = search(q, max_results=8)
        print(f"  搜索「{q}」得到 {len(hits)} 条结果")
        if not hits:
            time.sleep(2)
            hits = search(q, max_results=8)
            print(f"  重试得到 {len(hits)} 条结果")
        # 预筛：标题去重 + 摘要相关性，筛出值得抓的候选
        candidates = []
        for r in hits:
            key = "".join(r["title"].split())
            if key in seen:
                print(f"  跳过（同一篇文章）: {r['title']}")
                continue
            seen.add(key)
            if not relevant(r["snippet"] + r["title"], question, ratio=0.3):
                print(f"  淘汰（摘要就不相关）: {r['title']}")
                continue
            candidates.append(r)
            if len(candidates) >= max_new:
                break
        # 并发抓取：4 个线程同时开工
        with ThreadPoolExecutor(max_workers=4) as pool:
            fetched = list(pool.map(_fetch_one, candidates))
        for r, final_url, body in fetched:
            if final_url:
                r = {**r, "url": final_url}     # 引用里存真实网址
            if len(body) <= 200:
                body = r["snippet"]             # 正文抓不到就退而用搜索摘要
            if not relevant(body, question):
                print(f"  淘汰（相关性不够）: {r['title']}")
                continue
            sources.append({**r, "body": body})
            print(f"  有效材料 +1：{r['title']}（{len(body)} 字）")
        time.sleep(0.5)


def summarize(question, sources):
    """让千问读多篇材料，输出带来源编号的要点摘要"""
    materials = ""
    for i, s in enumerate(sources, 1):
        materials += f"[{i}] 标题：{s['title']}\n正文：{s['body'][:3000]}\n\n"
    prompt = (
        f"问题：{question}\n\n"
        f"以下是搜索到的材料：\n{materials}"
        "请从材料中提取能回答问题的要点。要求：\n"
        "1. 每条要点一行，行末用 [n] 标注它来自第几篇材料；\n"
        "2. 只使用材料中存在的信息，不得自行编造；\n"
        "3. 材料不足以回答时，输出：材料不足。"
    )
    return ask(prompt)


def reflect(question, notes):
    """反思：判断摘要够不够；不够就给出换角度的新搜索词"""
    prompt = (
        f"研究问题：{question}\n\n"
        f"目前已获得的要点摘要：\n{notes}\n\n"
        "请判断这些摘要是否足以回答研究问题。\n"
        '如果足够，只输出：{"done": true, "queries": []}\n'
        '如果不足，给出 2 个新搜索关键词，要求与之前的搜索角度不同'
        '（例如在：故障排查手册 / 报警代码表 / 品牌说明书 / 维修论坛经验 之间换角度），格式：'
        '{"done": false, "queries": ["关键词1", "关键词2"]}\n'
        "只输出 JSON，不要输出其他任何文字。"
    )
    answer = ask(prompt)
    start, end = answer.find("{"), answer.rfind("}")
    data = json.loads(answer[start:end + 1])
    return data.get("done", False), data.get("queries", [])


def write_report(question, notes, sources):
    """把最终摘要组织成带章节的 Markdown 研究报告"""
    src_list = "\n".join(
        f"{i}. {s['title']}  {s['url']}" for i, s in enumerate(sources, 1))
    prompt = (
        f"研究问题：{question}\n\n"
        f"研究要点（带来源编号）：\n{notes}\n\n"
        f"来源列表：\n{src_list}\n\n"
        "请写一份 Markdown 研究简报。要求：\n"
        "1. 用 ## 标题分成 2-4 个小节（如：常见原因 / 排查思路 / 品牌差异）；\n"
        "2. 保留结论末尾的 [n] 来源编号；\n"
        "3. 文末加一节 ## 参考文献，原样列出来源列表。"
    )
    return ask(prompt)


def research(question, max_rounds=3):
    """主循环：搜索→摘要→反思→（不够就换词再搜）→直到结束或轮数用尽"""
    sources, seen, notes = [], set(), ""
    queries = [question]
    for round_no in range(1, max_rounds + 1):
        print(f"== 第 {round_no} 轮，搜索词：{queries} ==")
        before = len(sources)
        collect(question, queries, sources, seen)
        if len(sources) == before:
            print("  本轮零新增，下一轮强制换站点搜索")
            queries = [question + " site:csdn.net", question + " site:zhihu.com"]
            continue
        notes = summarize(question, sources)
        print(notes[:200], "...\n")
        done, queries = reflect(question, notes)
        if done:
            print("模型判断：材料已足够，结束循环")
            break
        print(f"模型判断：还不够，下一轮搜 {queries}\n")
    return notes, sources


if __name__ == "__main__":
    import sys
    # 运行时带问题就用带的，不带就用默认问题
    question = sys.argv[1] if len(sys.argv) > 1 else "伺服电机过载报警的原因有哪些？"
    notes, sources = research(question)
    report = write_report(question, notes, sources)
    with open("report.md", "w", encoding="utf-8") as f:
        f.write(f"# 研究报告：{question}\n\n" + report)
    print(report)
    print("\n报告已保存到 report.md")