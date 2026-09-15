# deep-research-mini

一个手写的迷你版 Deep Research 智能体：给定一个研究问题，自主完成
"搜索 → 抓取 → 阅读摘要 → 反思补充检索 → 多轮迭代 → 生成带引用的研究报告"。

纯 Python 实现，约 200 行，不依赖任何 Agent 框架。

## 工作流程

```
用户问题
   ↓
[搜索] 搜狗网页搜索（BeautifulSoup 解析）
   ↓
[抓取] requests + trafilatura 提取正文（重试 + 反爬兜底）
   ↓
[摘要] 千问 qwen-plus 阅读材料，输出带 [n] 来源编号的要点
   ↓
[反思] 千问判断材料是否足够：
       足够 → 结束循环
       不足 → 生成新搜索词（换角度），进入下一轮
   ↓
[成稿] 汇总多轮摘要，生成 Markdown 研究简报（report.md）
```

## 快速开始

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows
pip install requests beautifulsoup4 trafilatura
# 配置千问 API Key：设置环境变量 QWEN_API_KEY，或把 Key 写入 my_key.txt
python research.py
```

## 项目结构

| 文件 | 职责 |
|---|---|
| search_tool.py | 搜索（搜狗 SERP 解析）与网页正文抓取 |
| llm.py | 千问 OpenAI 兼容接口的裸 HTTP 调用 |
| research.py | 主循环：摘要、反思、报告生成 |
| report.md | 运行产物：研究报告示例 |

## 工程设计要点

- **三级去重**：URL 层 → 跳转解析后的真实 URL 层 → 标题层（对付带时间戳参数的网址）
- **失败兜底链**：抓取重试 → 退而使用搜索摘要 → 整轮零新增时强制 site: 换源
- **并发抓取**：ThreadPoolExecutor 并行拉取候选页面
- **早停与预筛**：snippet 相关性预筛减少无效抓取；单轮材料够数即停
- **循环保险丝**：max_rounds 硬上限 + 模型 FINISHED 自判，防止无限检索

## 示例

研究问题："伺服电机过载报警的原因有哪些？"
3 轮检索后产出带 5 篇参考文献的分章节简报，见 report.md。
