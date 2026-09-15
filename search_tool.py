import os
import time
from pathlib import Path

import requests
import trafilatura
from bs4 import BeautifulSoup


BASE_DIR = Path(__file__).resolve().parent
TAVILY_ENDPOINT = "https://api.tavily.com/search"

# 模拟普通浏览器，供网页正文抓取和旧搜索引擎兜底使用。
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    )
}


def _read_tavily_key():
    """优先读取环境变量，其次读取项目根目录的 tavily_key.txt。"""
    env_key = os.getenv("TAVILY_API_KEY", "").strip()
    if env_key:
        return env_key

    key_file = BASE_DIR / "tavily_key.txt"
    if key_file.exists():
        return key_file.read_text(encoding="utf-8").strip()

    return ""


def _search_tavily(query, max_results):
    """调用 Tavily Search API，并统一为项目原有的结果格式。"""
    api_key = _read_tavily_key()
    if not api_key:
        return []

    response = requests.post(
        TAVILY_ENDPOINT,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "query": query,
            "topic": "general",
            "search_depth": "basic",
            "max_results": min(max(int(max_results), 1), 20),
            "include_answer": False,
            "include_raw_content": "text",
        },
        timeout=30,
    )
    response.raise_for_status()

    results = []
    for item in response.json().get("results", []):
        url = str(item.get("url", "")).strip()
        if not url:
            continue

        results.append({
            "title": str(item.get("title", "")).strip(),
            "url": url,
            "snippet": str(item.get("content", "")).strip(),
            "raw_content": str(item.get("raw_content") or "").strip(),
            "provider": "tavily",
        })

    return results


def _parse_sogou(html, max_results):
    """解析搜狗结果页。"""
    soup = BeautifulSoup(html, "html.parser")
    results = []

    for div in soup.select("div.vrwrap")[:max_results]:
        h3 = div.find("h3")
        if not h3 or not h3.find("a"):
            continue

        link = h3.find("a")
        paragraph = div.find("p")
        results.append({
            "title": link.get_text(" ", strip=True),
            "url": link.get("href", ""),
            "snippet": (
                paragraph.get_text(" ", strip=True)
                if paragraph else ""
            ),
            "provider": "sogou",
        })

    return results


def _parse_bing(html, max_results):
    """解析必应结果页。"""
    soup = BeautifulSoup(html, "html.parser")
    results = []

    for li in soup.select("li.b_algo")[:max_results]:
        h2 = li.find("h2")
        if not h2 or not h2.find("a"):
            continue

        link = h2.find("a")
        paragraph = li.find("p")
        results.append({
            "title": link.get_text(" ", strip=True),
            "url": link.get("href", ""),
            "snippet": (
                paragraph.get_text(" ", strip=True)
                if paragraph else ""
            ),
            "provider": "bing",
        })

    return results


def _search_sogou(query, max_results):
    response = requests.get(
        "https://www.sogou.com/web",
        params={"query": query},
        headers=HEADERS,
        timeout=10,
    )
    response.raise_for_status()
    return _parse_sogou(response.text, max_results)


def _search_bing(query, max_results):
    response = requests.get(
        "https://www.bing.com/search",
        params={"q": query},
        headers=HEADERS,
        timeout=10,
    )
    response.raise_for_status()
    return _parse_bing(response.text, max_results)


def search(query, max_results=10, engine="auto"):
    """搜索并返回 [{title, url, snippet, raw_content?, provider}]。

    auto 模式优先使用 Tavily；未配置 Key 或请求失败时，依次使用
    搜狗和必应兜底。也可显式传入 tavily、sogou 或 bing。
    """
    if engine not in {"auto", "tavily", "sogou", "bing"}:
        raise ValueError(f"不支持的搜索引擎：{engine}")

    providers = {
        "tavily": _search_tavily,
        "sogou": _search_sogou,
        "bing": _search_bing,
    }
    order = (
        ["tavily", "sogou", "bing"]
        if engine == "auto"
        else [engine]
    )

    for provider_name in order:
        if provider_name == "tavily" and not _read_tavily_key():
            continue

        try:
            results = providers[provider_name](query, max_results)
            if results:
                return results
        except Exception as exc:
            # 不打印请求头和 Key，只记录搜索源及异常类型。
            print(
                f"搜索源 {provider_name} 失败："
                f"{type(exc).__name__}: {exc}"
            )

    return []


def fetch(url, retries=2):
    """抓取网页正文；返回 (最终网址, 正文)，失败返回 ("", "")。"""
    for attempt in range(retries):
        try:
            if url.startswith("/"):
                url = "https://www.sogou.com" + url

            response = requests.get(
                url,
                timeout=15,
                headers=HEADERS,
            )
            response.raise_for_status()
            body = trafilatura.extract(
                response.text,
                include_comments=False,
                include_tables=True,
            ) or ""

            if body:
                return response.url, body
        except Exception as exc:
            print(
                f"第 {attempt + 1} 次抓取失败：{url} "
                f"({type(exc).__name__})"
            )

        time.sleep(1)

    return "", ""


if __name__ == "__main__":
    demo_results = search("伺服电机过载报警 原因")
    for index, result in enumerate(demo_results, start=1):
        print(
            index,
            result["provider"],
            result["title"],
            "|",
            result["url"][:80],
        )
