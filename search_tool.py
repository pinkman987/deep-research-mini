import time
import requests
from bs4 import BeautifulSoup
import trafilatura

# 假装是 Chrome 浏览器，不然很多网站拒绝 python 的请求
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}


def _parse_sogou(html, max_results):
    """解析搜狗结果页：每条结果在 <div class="vrwrap"> 里"""
    soup = BeautifulSoup(html, "html.parser")
    results = []
    for div in soup.select("div.vrwrap")[:max_results]:
        h3 = div.find("h3")
        if not h3 or not h3.find("a"):
            continue
        link = h3.find("a")
        p = div.find("p")
        results.append({
            "title": link.get_text(),
            "url": link.get("href", ""),
            "snippet": p.get_text() if p else "",
        })
    return results


def _parse_bing(html, max_results):
    """解析必应结果页：每条结果在 <li class="b_algo"> 里（备用引擎）"""
    soup = BeautifulSoup(html, "html.parser")
    results = []
    for li in soup.select("li.b_algo")[:max_results]:
        h2 = li.find("h2")
        if not h2 or not h2.find("a"):
            continue
        link = h2.find("a")
        p = li.find("p")
        results.append({
            "title": link.get_text(),
            "url": link.get("href", ""),
            "snippet": p.get_text() if p else "",
        })
    return results


def search(query, max_results=10, engine="auto"):
    """搜一次，返回 [{title, url, snippet}]
    engine="auto": 主源搜狗，0 条时降级必应；engine="bing": 只用必应"""
    results = []
    if engine in ("auto", "sogou"):
        resp = requests.get(
            "https://www.sogou.com/web",
            params={"query": query},
            headers=HEADERS,
            timeout=10,
        )
        results = _parse_sogou(resp.text, max_results)
    if not results and engine in ("auto", "bing"):
        try:
            resp = requests.get(
                "https://www.bing.com/search",
                params={"q": query},          # 注意：不加 setlang，加了你反而被路由到降级索引
                headers=HEADERS,
                timeout=10,
            )
            results = _parse_bing(resp.text, max_results)
        except Exception as e:
            print("备用引擎必应也失败:", e)
    return results


def fetch(url, retries=2):
    """抓网页正文；返回 (真实网址, 正文)，失败返回 ("", "")"""
    for i in range(retries):
        try:
            if url.startswith("/"):
                url = "https://www.sogou.com" + url
            resp = requests.get(url, timeout=10, headers=HEADERS)
            text = trafilatura.extract(resp.text) or ""
            if text:
                return resp.url, text
        except Exception as e:
            print(f"第 {i + 1} 次抓取失败:", url, e)
        time.sleep(1)
    return "", ""


if __name__ == "__main__":
    results = search("伺服电机 过载报警 原因")
    for i, r in enumerate(results, 1):
        print(i, r["title"], "|", r["url"][:60])
    for r in results:
        _, body = fetch(r["url"])
        if len(body) > 200:
            print("抓取成功:", r["title"], "| 字数:", len(body))
            print(body[:300])
            break
    else:
        print("这一轮所有网页都没抓到，换个搜索词试试")