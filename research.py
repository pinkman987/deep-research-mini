import json
import re
import time
from concurrent.futures import ThreadPoolExecutor

from llm import ask
from search_tool import fetch, search


# 疑问词和虚词黑名单
STOP = set("谁什么怎么为什么吗呢的了是在有和与及哪些多少如何怎样请问请")


def relevant(body, question, ratio=0.3):
    """使用问题实词字符的覆盖率进行初步相关性过滤。"""
    chars = [
        char
        for char in question
        if char not in " ？?，,。、/" and char not in STOP
    ]

    if not chars:
        return True

    hit = sum(1 for char in chars if char in body)
    return hit >= len(chars) * ratio


def title_key(title):
    """标题去重键：去掉所有空白，空格差异视为同一篇文章。"""
    return "".join(title.split())


def _fetch_one(result):
    """在线程池中抓取一个搜索结果。"""
    # Tavily 可直接返回提取后的网页正文。优先复用，避免再次访问
    # 原网站时遇到反爬、超时或内容动态加载。
    raw_content = result.get("raw_content", "").strip()
    if len(raw_content) > 200:
        return result, result["url"], raw_content

    final_url, body = fetch(result["url"], retries=1)
    return result, final_url, body


def collect(
    question,
    queries,
    sources,
    seen,
    max_new=4,
    log=print,
):
    """执行一轮搜索和网页抓取。"""
    round_start = len(sources)

    for query in queries:
        if len(sources) - round_start >= max_new:
            log("  本轮材料已够，提前停止抓取")
            break

        hits = search(query, max_results=8)
        log(f"  搜索「{query}」得到 {len(hits)} 条结果")

        if not hits:
            time.sleep(2)
            hits = search(query, max_results=8)
            log(f"  重试得到 {len(hits)} 条结果")

        candidates = []

        for result in hits:
            key = title_key(result["title"])

            if key in seen:
                log(f"  跳过（同一篇文章）: {result['title']}")
                continue

            seen.add(key)

            preview = result["snippet"] + result["title"]

            if not relevant(preview, question, ratio=0.3):
                log(f"  淘汰（摘要就不相关）: {result['title']}")
                continue

            candidates.append(result)

            if len(candidates) >= max_new:
                break

        if not candidates:
            # 主搜索源没有可用结果时切换必应。
            # 同时逐步缩短搜索词，避免长搜索词失效。
            short_query = " ".join(query.split()[:2])
            bare_query = query.split(" site:")[0]

            retry_queries = []

            for retry_query in [
                query,
                short_query,
                bare_query,
                " ".join(bare_query.split()[:2]),
            ]:
                if retry_query and retry_query not in retry_queries:
                    retry_queries.append(retry_query)

            for retry_query in retry_queries:
                log(f"  换必应重搜「{retry_query}」")

                backup_hits = search(
                    retry_query,
                    max_results=8,
                    engine="bing",
                )

                for result in backup_hits:
                    key = title_key(result["title"])

                    if key in seen:
                        continue

                    seen.add(key)

                    preview = result["snippet"] + result["title"]

                    if not relevant(preview, question, ratio=0.3):
                        continue

                    candidates.append(result)

                    if len(candidates) >= max_new:
                        break

                if candidates:
                    break

        if not candidates:
            continue

        with ThreadPoolExecutor(max_workers=4) as pool:
            fetched_results = list(
                pool.map(_fetch_one, candidates)
            )

        for result, final_url, body in fetched_results:
            if final_url:
                result = {
                    **result,
                    "url": final_url,
                }

            if len(body) <= 200:
                body = result["snippet"]

            if not relevant(body, question):
                log(f"  淘汰（相关性不够）: {result['title']}")
                continue

            sources.append({
                **result,
                "body": body,
            })

            log(
                f"  有效材料 +1："
                f"{result['title']}（{len(body)} 字）"
            )

        time.sleep(0.5)


def _normalize_text(text):
    """去掉空白并转为小写，用于核对证据原文。"""
    return "".join(str(text).split()).lower()


def summarize(question, sources):
    """提取直接回答问题、且能通过原文验证的结论。"""
    materials = ""

    for index, source in enumerate(sources, start=1):
        materials += (
            f"[{index}] 标题：{source['title']}\n"
            f"正文：{source['body'][:3000]}\n\n"
        )

    prompt = (
        f"研究问题：{question}\n\n"
        f"以下是搜索到的材料：\n{materials}\n"
        "请从材料中提取能够直接回答研究问题的结论。\n"
        "每条结论必须附带来源编号和原文证据。\n\n"
        "要求：\n"
        "1. claim只能包含证据原文能够直接支持的内容；\n"
        "2. evidence必须逐字复制材料中的一段连续原文；\n"
        "3. 不得添加证据中不存在的数字、型号、日期、标准或因果关系；\n"
        "4. source_id必须对应材料前面的编号；\n"
        "5. 最多输出12条结论；\n"
        "6. 只输出JSON，不要输出Markdown或解释文字；\n"
        "7. 只提取能够直接回答研究问题的结论；\n"
        "8. 如果问题询问原因，claim必须明确描述一个"
        "有证据支持的具体原因；\n"
        "9. 如果问题询问排查方法，claim必须明确描述一个"
        "有证据支持的可执行步骤；\n"
        "10. 仅介绍概念、组成、工作原理或应用场景的"
        "材料一律忽略；\n"
        "11. 找不到直接回答问题的证据时，输出："
        '{"claims":[]}。\n'
        '输出格式：{"claims":[{"claim":"结论",'
        '"source_id":1,"evidence":"材料中的连续原文"}]}'
    )

    answer = ask(prompt)

    start = answer.find("{")
    end = answer.rfind("}")

    if start == -1 or end == -1 or end <= start:
        return "材料不足：模型没有返回可解析的证据结构。"

    try:
        data = json.loads(answer[start:end + 1])
    except json.JSONDecodeError:
        return "材料不足：模型返回的证据JSON格式错误。"

    validated_claims = []
    seen_claims = set()

    for item in data.get("claims", []):
        claim = str(item.get("claim", "")).strip()
        evidence = str(item.get("evidence", "")).strip()

        try:
            source_id = int(item.get("source_id"))
        except (TypeError, ValueError):
            continue

        if not claim or not evidence:
            continue

        if source_id < 1 or source_id > len(sources):
            continue

        normalized_evidence = _normalize_text(evidence)
        normalized_body = _normalize_text(
            sources[source_id - 1].get("body", "")
        )

        # 证据过短时容易出现偶然匹配
        if len(normalized_evidence) < 12:
            continue

        # 模型返回的证据必须真实存在于抓取正文中
        if normalized_evidence not in normalized_body:
            continue

        normalized_claim = _normalize_text(claim)

        if normalized_claim in seen_claims:
            continue

        seen_claims.add(normalized_claim)

        validated_claims.append(
            f"- 结论：{claim} [{source_id}]\n"
            f"  证据原文：{evidence}"
        )

    if not validated_claims:
        return "材料不足：没有获得能够直接回答问题并通过原文验证的结论。"

    return "\n".join(validated_claims)


def plan_queries(question):
    """将用户问题规划为2至3个搜索关键词。"""
    prompt = (
        f"研究问题：{question}\n"
        "请为这个问题生成2至3个搜索引擎搜索词。\n"
        "要求：\n"
        "1. 使用关键词风格，不要使用完整问句；\n"
        "2. 每个搜索词不超过3个词；\n"
        "3. 各搜索词应从不同角度进行检索；\n"
        "4. 不要在同一个搜索词中使用斜杠连接多个品牌；\n"
        "5. 涉及技术故障时，优先考虑故障手册、报警代码表、"
        "厂商说明书等角度；\n"
        "6. 只输出JSON字符串数组。\n"
        '示例：["伺服过载 故障手册", "伺服过载 报警代码"]。'
    )

    answer = ask(prompt)
    start = answer.find("[")
    end = answer.rfind("]")

    try:
        queries = json.loads(answer[start:end + 1])

        if isinstance(queries, list) and queries:
            cleaned_queries = []

            for query in queries[:3]:
                query = str(query).strip().replace("/", " ")

                if query:
                    cleaned_queries.append(query)

            if cleaned_queries:
                return cleaned_queries

    except Exception:
        pass

    return [question]


def reflect(question, notes):
    """判断当前证据是否足够，并生成新的检索方向。"""
    prompt = (
        f"研究问题：{question}\n\n"
        f"目前已获得的验证结论：\n{notes}\n\n"
        "请判断这些结论是否能够直接回答研究问题。\n"
        "仅有背景概念、组成或工作原理不算足够。\n"
        '如果足够，只输出：{"done":true,"queries":[]}\n'
        "如果不足，生成2个新的搜索关键词。\n"
        "新关键词必须：\n"
        "1. 与上一轮搜索角度不同；\n"
        "2. 保留研究问题的核心对象和核心故障词；\n"
        "3. 优先从故障手册、报警代码表、品牌说明书、"
        "维修文档等角度搜索；\n"
        "4. 不要用斜杠连接多个品牌；\n"
        '输出格式：{"done":false,'
        '"queries":["关键词1","关键词2"]}\n'
        "只输出JSON，不要输出其他文字。"
    )

    answer = ask(prompt)
    start = answer.find("{")
    end = answer.rfind("}")

    if start == -1 or end == -1 or end <= start:
        return False, [question]

    try:
        data = json.loads(answer[start:end + 1])
    except json.JSONDecodeError:
        return False, [question]

    queries = data.get("queries", [])

    if not isinstance(queries, list):
        queries = []

    cleaned_queries = []

    for query in queries[:2]:
        query = str(query).strip().replace("/", " ")

        if query:
            cleaned_queries.append(query)

    return bool(data.get("done", False)), cleaned_queries


def validate_citations(report, source_count):
    """报告级引用一致性校验，返回问题列表（空列表=全部通过）：
    1. 引用编号不得超出来源总数（模型编造不存在的编号）；
    2. 每条结论行（列表项）必须至少挂一个引用（无依据结论）。"""
    issues = []
    numbers = sorted({int(n) for n in re.findall(r"\[(\d+)\]", report)})

    for number in numbers:
        if number < 1 or number > source_count:
            issues.append(
                f"无效引用编号 [{number}]（来源总数 {source_count}）"
            )

    for line in report.splitlines():
        stripped = line.strip()
        is_bullet = stripped.startswith(("-", "*", "•"))
        has_citation = re.search(r"\[\d+\]", stripped)

        if is_bullet and len(stripped) > 20 and not has_citation:
            issues.append(f"无引用结论: {stripped[:30]}...")

    return issues


def knowledge_fallback(question):
    """无网络来源时给出带有明确警告的模型知识回答。"""
    prompt = (
        f"问题：{question}\n\n"
        "未能检索到任何能够回答问题的网络材料。\n"
        "请基于模型自身知识回答，并严格遵守：\n"
        "1. 第一行必须输出："
        "> ⚠️ 未检索到可靠网络来源，以下内容基于模型自身知识，"
        "未经联网核实，仅供参考；\n"
        "2. 禁止使用任何[n]引用编号；\n"
        "3. 禁止编造型号、故障码、日期、标准或具体数值；\n"
        "4. 不确定的内容必须明确说明不确定。"
    )

    return ask(prompt)


def write_report(question, notes, sources):
    """根据已验证的结论生成Markdown研究报告。"""
    source_list = "\n".join(
        f"{index}. {source['title']}  {source['url']}"
        for index, source in enumerate(sources, start=1)
    )

    prompt = (
        f"研究问题：{question}\n\n"
        f"已经通过原文验证的结论与证据：\n{notes}\n\n"
        f"来源列表：\n{source_list}\n\n"
        "请根据已经验证的结论撰写Markdown研究简报。\n"
        "要求：\n"
        "1. 只能改写给定结论，不得增加结论中没有的新事实；\n"
        "2. 禁止自行补充数字、型号、日期、标准、故障码或因果关系；\n"
        "3. 每项事实必须保留对应的[n]来源编号；\n"
        "4. 证据不足的部分必须明确写为无法确认；\n"
        "5. 不要把推测写成确定事实；\n"
        "6. 文末添加## 参考文献，并原样列出来源列表；\n"
        "7. 如果验证后的材料不能直接回答研究问题，"
        "只输出“当前材料不足，无法可靠回答”，"
        "不要撰写背景知识。"
    )

    return ask(prompt)


def research(
    question,
    max_rounds=3,
    log=print,
):
    """执行搜索、摘要、反思和补充检索循环。"""
    sources = []
    seen = set()
    notes = ""

    queries = plan_queries(question)
    log(f"规划搜索词：{queries}")

    for round_number in range(1, max_rounds + 1):
        log(
            f"== 第 {round_number} 轮，"
            f"搜索词：{queries} =="
        )

        before = len(sources)

        collect(
            question,
            queries,
            sources,
            seen,
            log=log,
        )

        if len(sources) == before:
            log("  本轮零新增，下一轮反思会重新规划搜索词")

        if sources:
            notes = summarize(question, sources)
            log(notes[:200] + " ...\n")

        done, new_queries = reflect(question, notes)

        if done:
            log("模型判断：材料已足够，结束循环")
            break

        if new_queries:
            queries = new_queries
        else:
            queries = [question]

        log(f"模型判断：还不够，下一轮搜 {queries}\n")

    if not sources:
        return (
            "材料不足：未检索到任何有效网页材料，"
            "请更换问法或稍后重试。",
            [],
        )

    return notes, sources


if __name__ == "__main__":
    import sys

    question = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "伺服电机过载报警的原因有哪些？"
    )

    notes, sources = research(question)

    if not sources:
        report = knowledge_fallback(question)
        print(report)
        print(
            "\n（注意：未检索到网络来源，"
            "以上为模型知识回答，未经联网核实）"
        )
    else:
        report = write_report(question, notes, sources)
        issues = validate_citations(report, len(sources))

        if issues:
            print("\n引用校验发现问题：")
            for issue in issues:
                print(" -", issue)

        with open("report.md", "w", encoding="utf-8") as file:
            file.write(
                f"# 研究报告：{question}\n\n"
                + report
            )

        print(report)
        print("\n报告已保存到 report.md")
