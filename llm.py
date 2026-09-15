import os
from pathlib import Path

import requests

# Key 从不写进代码：优先读环境变量，其次读本地的 my_key.txt（该文件已被 .gitignore 排除）
_key_file = Path(__file__).parent / "my_key.txt"
API_KEY = os.environ.get("QWEN_API_KEY") or (
    _key_file.read_text().strip() if _key_file.exists() else "")
BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"


def ask(prompt, model="qwen-plus"):
    """向千问发一次对话请求，返回回答的文本"""
    if not API_KEY:
        raise RuntimeError("没找到 API Key：设置环境变量 QWEN_API_KEY 或创建 my_key.txt")
    resp = requests.post(
        BASE_URL + "/chat/completions",
        headers={
            "Authorization": "Bearer " + API_KEY,   # 身份凭证放请求头里
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=60,          # 大模型生成慢，超时给足 60 秒
    )
    resp.raise_for_status()  # 状态码不是 200 就直接抛错，别让错误悄悄溜过去
    # 返回的 JSON 里，回答藏在 choices[0].message.content 这个路径下
    return resp.json()["choices"][0]["message"]["content"]


if __name__ == "__main__":
    print(ask("用一句话介绍什么是伺服电机"))
