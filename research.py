import json
import time
from concurrent.futures import ThreadPoolExecutor
from search_tool import search, fetch
from llm import ask


# 疑问词/虚词黑名单：这些字只出现在问句里，正文中几乎不会出现，
# 若计入覆盖率会误杀真正相关的文章（"谁解决了挂谷猜想"教训）
STOP = set("谁什么怎么为什么吗呢的了是在有和与及哪些多少如何怎样请问请")


def relevant(body, question, ratio=0.3):
    """关键词覆盖率过滤：只统计问题中的实词字，覆盖 ratio 以上才算相关"""
    chars = [c for c in question if c not in " ？?，,。、/" and c not in STOP]
    if not chars:
        return True          # 问题全是疑问词时不做过滤，宁可放过
    hit = sum(1 for c in chars if c in body)
    return hit >= len(chars) * ratio


def _fetch_one(r):
    """并发抓取的工人函数：线程池里每个线程跑一个它"""
    final_url, body = fetch(r["url"], retries=1)
    return r, final_url, body


def collect(question, queries, sources, seen, max_new=4, log=print):
    """搜索+抓取一轮；log 是进度输出函数（终端传 print，网页传界面函数）
    三个提速手段：
    1. 摘要预筛：snippet 就不相关的页面根本不抓
    2. 并发抓取：候选页面同时抓，耗时=最慢的一篇
    3. 早停：本轮新增够 max_new 篇就不再抓"""
    round_start = len(sources)
    for q in queries:
        if len(sources) - round_start >= max_new:
            log("  本轮材料已够，提前停止抓取")
            break
        hits = search(q, max_results=8)
        log(f"  搜索「{q}」得到 {len(hits)} 条结果")
        if not hits:
            time.sleep(2)
            hits = search(q, max_results=8)
            log(f"  重试得到 {len(hits)} 条结果")
        # 预筛：标题去重 + 摘要相关性，筛出值得抓的候选
        candidates = []
        for r in hits:
            key = "".join(r["title"].split())
            if key in seen:
                log(f"  跳过（同一篇文章）: {r['title']}")
                continue
            seen.add(key)
            if not relevant(r["snippet"] + r["title"], question, ratio=0.3):
                log(f"  淘汰（摘要就不相关）: {r['title']}")
                continue
            candidates.append(r)
            if len(candidates) >= max_new:
                break
        if not candidates:
            # 主源结果全被过滤（索引垃圾）：换备用引擎；
            # 爬虫搜索引擎对长尾堆词敏感，再截短成前 2 个词重试一次
            short = " ".join(q.split()[:2])
            bare = q.split(" site:")[0]            # 去掉站点限定再截短，避免双重限定互相污染
            retry_queries = []
            for rq in [q, short, bare, " ".join(bare.split()[:2])]:
                if rq not in retry_queries:
                    retry_queries.append(rq)
            for rq in retry_queries:
                log(f"  换必应重搜「{rq}」")
                for r in search(rq, max_results=8, engine="bing"):
                    key = "".join(r["title"].split())
                    if key in seen:
                        continue
                    seen.add(key)
                    if not relevant(r["snippet"] + r["title"], question, ratio=0.3):
                        continue
                    candidates.append(r)
                    if len(candidates) >= max_new:
                        break
                if candidates:
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
                log(f"  淘汰（相关性不够）: {r['title']}")
                continue
            sources.append({**r, "body": body})
            log(f"  有效材料 +1：{r['title']}（{len(body)} 字）")
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


def plan_queries(question):
    """让模型把口语问题转成 2-3 个关键词式搜索词
    （搜索引擎吃关键词不吃整句，"最近谁获得了菲尔兹奖"会被拆错重点）"""
    prompt = (
        f"研究问题：{question}\n"
        "请为这个问题生成 2-3 个搜索引擎搜索词。要求：关键词风格而非整句、"
        "每个搜索词不超过 3 个词（爬虫搜索引擎对长尾堆词会失效）、"
        "角度互补（如官方名单/新闻报道/百科解释）、只输出 JSON 字符串数组，"
        '例如 ["菲尔兹奖 获奖者", "2026 菲尔兹奖"]。'
    )
    answer = ask(prompt)
    start, end = answer.find("["), answer.rfind("]")
    try:
        queries = json.loads(answer[start:end + 1])
        if isinstance(queries, list) and queries:
            return [str(q) for q in queries][:3]
    except Exception:
        pass
    return [question]          # 模型输出格式坏了就退回用原问题


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


def knowledge_fallback(question):
    """零材料兜底：明确告知用户"无网络来源"，让模型凭自身知识回答且禁止编造引用
    （与空编报告的区别：身份和局限说得明明白白）"""
    prompt = (
        f"问题：{question}\n\n"
        "未能检索到任何网络材料。请基于你自身的知识回答，并遵守：\n"
        "1. 第一行必须输出：> ⚠️ 未检索到网络来源，以下内容基于模型自身知识，未经联网核实，仅供参考；\n"
        "2. 禁止使用任何 [n] 引用编号；\n"
        "3. 不确定的部分明确说'不确定'。"
    )
    return ask(prompt)


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


def research(question, max_rounds=3, log=print):
    """主循环：搜索→摘要→反思→（不够就换词再搜）→直到结束或轮数用尽
    log 参数把进度输出注入进来：命令行传 print，网页传界面函数"""
    sources, seen, notes = [], set(), ""
    queries = plan_queries(question)
    log(f"规划搜索词：{queries}")
    for round_no in range(1, max_rounds + 1):
        log(f"== 第 {round_no} 轮，搜索词：{queries} ==")
        before = len(sources)
        collect(question, queries, sources, seen, log=log)
        if len(sources) == before:
            log("  本轮零新增，下一轮反思会重新规划搜索词")
        if sources:
            notes = summarize(question, sources)
            log(notes[:200] + " ...\n")
        done, queries = reflect(question, notes)
        if done:
            log("模型判断：材料已足够，结束循环")
            break
        log(f"模型判断：还不够，下一轮搜 {queries}\n")
    if not sources:
        # 硬约束：一篇材料都没有时绝不让模型空编，诚实报告失败
        return "材料不足：未检索到任何有效网页材料，请更换问法或稍后重试。", []
    return notes, sources


if __name__ == "__main__":
    import sys
    # 运行时带问题就用带的，不带就用默认问题
    question = sys.argv[1] if len(sys.argv) > 1 else "伺服电机过载报警的原因有哪些？"
    notes, sources = research(question)
    if not sources:
        report = knowledge_fallback(question)
        print(report)
        print("\n（注意：未检索到网络来源，以上为模型知识回答，未经联网核实）")
    else:
        report = write_report(question, notes, sources)
        with open("report.md", "w", encoding="utf-8") as f:
            f.write(f"# 研究报告：{question}\n\n" + report)
        print(report)
        print("\n报告已保存到 report.md")