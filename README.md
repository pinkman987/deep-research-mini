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
pip install requests beautifulsoup4 trafilatura streamlit
# 配置千问 API Key：设置环境变量 QWEN_API_KEY，或把 Key 写入 my_key.txt
python research.py                # 命令行模式（可带问题参数：python research.py "你的问题"）
streamlit run app.py              # Web 界面模式
```

## Web 界面

浏览器打开 http://localhost:8501 ：输入研究问题 → 点击"开始研究" →
实时查看多轮搜索/抓取/反思进度日志 → 自动生成带来源引用的 Markdown 报告，
支持一键下载。

## 项目结构

| 文件 | 职责 |
|---|---|
| search_tool.py | 搜索（搜狗 SERP 解析）与网页正文抓取 |
| llm.py | 千问 OpenAI 兼容接口的裸 HTTP 调用 |
| research.py | 主循环：摘要、反思、报告生成 |
| app.py | Streamlit Web 界面（进度日志 + 报告展示与下载） |
| report.md | 运行产物：研究报告示例 |

## 工程设计要点

- **三级去重**：规范化搜索结果原始 URL → 抓取跳转后的最终 URL → 归一化标题；URL 会忽略片段、常见跟踪参数和默认端口
- **失败兜底链**：抓取重试 → 退而使用搜索摘要 → 整轮零新增时强制 site: 换源
- **并发抓取**：ThreadPoolExecutor 并行拉取候选页面
- **早停与预筛**：snippet 相关性预筛减少无效抓取；单轮材料够数即停
- **循环保险丝**：max_rounds 硬上限 + 模型 FINISHED 自判，防止无限检索

## 示例

研究问题："伺服电机过载报警的原因有哪些？"
3 轮检索后产出带 5 篇参考文献的分章节简报，见 report.md。

## 评测结果

评测集 24 题（事实检索 / 技术研究 / 多来源对比 / 综合研究 / 时效信息 /
无材料 / 对抗 / 模糊），复现命令：

```bash
python eval/run_eval.py          # 全量评测，结果写入 eval/results.jsonl
python eval/analyze_results.py   # 汇总指标表
```

2026-09-15 实测（搜狗/必应引擎，千问 qwen-plus）：

| 指标 | 结果 |
|---|---|
| 评测问题数 | 24 |
| 报告生成成功率 | 24/24 = 100% |
| 引用编号有效率 | 24/24 = 100%（零无效引用） |
| 无材料/对抗/模糊题诚实处理率 | 7/7 = 100% |
| 关键点命中率 | 31/51 = 60.8% |
| 答题类平均来源数 | 7.9 |
| 平均耗时 | 85.7 秒（最长 211 秒） |

与 baseline_v1（10 题旧版）对比：关键点命中率 58.3% → 60.8%，
诚实处理率 50% → 100%，代价是平均耗时 59.6s → 85.7s（证据校验增加的轮次）。

### 已知 Bad Case

- compare_003（PostgreSQL vs MySQL 的 JSON 支持）：检索到 13 个来源但关键点
  0/3——来源多为概述页，证据校验正确地拒绝了无直接证据的结论，报告退化为
  "材料不足"。检索命中 ≠ 证据命中，这是当前最大短板。
- research_001（chunk size 影响）：仅 2 个来源通过过滤，关键点 0/4。
- 时效类问题依赖搜索引擎索引新鲜度，搜狗/必应对部分新事件收录滞后。

### 已知局限

- 爬虫型搜索引擎（搜狗/必应）对长尾词和型号级问题索引质量差，
  专业问题建议接入 Tavily 等 Agent 专用搜索 API（已预留接口）。
- 相关性过滤为字符覆盖率启发式，存在误杀与误放，未上 embedding 重排。
- 单线程轮次串行，耗时随轮数线性增长；未做搜索/抓取缓存。
