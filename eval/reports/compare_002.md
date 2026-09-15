# LangChain与LangGraph在构建有状态Agent时有什么区别？

# LangChain 与 LangGraph 在构建有状态 Agent 中的区别：研究简报

## 核心定位与抽象层级差异  
LangChain 是面向快速开发的通用 LLM 应用框架，提供模型无关、工具无关、数据库无关的抽象层，强调“快建快用”，内置 ReAct 等预构建 agent 模式及标准化工具集成能力，适合敏捷接入真实业务场景 [1][2][3]。而 LangGraph 并非替代 LangChain 的独立框架，而是其生态内**专门面向有状态、可编排、可持久化 agent 系统的底层运行时与建模层**：它以有向图（Directed Graph）显式描述状态流转逻辑，将 agent 行为建模为节点（stateful nodes）与边（conditional transitions），从而实现比 LangChain 链式调用更精细、确定性更强的流程控制，尤其适用于生产级高可靠性要求场景 [3]。

## 有状态能力的实现机制对比  
LangChain 自身的记忆组件（如 `ConversationBufferMemory`、`EntityMemory`）仅提供轻量级会话状态管理，**不具备原生持久化、检查点或断点续跑能力**；其有状态 agent 的完整生命周期管理（如 durable execution、checkpointing、rewind、long-running task 调度）实际依赖 LangGraph 的**持久运行时（durable runtime）** 提供底层支撑 [2][3]。换言之，LangChain 的高级 agent 功能（如 `create_react_agent` 的持久化版本）在启用 `checkpointer` 后，其状态保存、恢复与回放均由 LangGraph 运行时接管——LangChain 负责“定义做什么”，LangGraph 负责“可靠地、可追溯地、分步地做完” [2][3]。

## 多智能体协同与复杂编排能力  
LangGraph 原生支持**多级编排（multi-level orchestration）**，可构建包含 human-in-the-loop（人工确认关键步骤）、异步子任务、条件分支、循环重试与跨 agent 状态共享的复合系统 [1][2][3]。典型应用是将多个 LangChain agent 封装为图中节点，实现分工协作：例如，Agent A 负责网络搜索，Agent B 执行深度分析，Agent C 生成报告，三者通过共享状态图协调输入输出与执行顺序 [3]。这种能力远超 LangChain 单一 agent 的串行/并行工具调用范式，使复杂多智能体系统具备可观测性、可调试性与可审计性 [1][3]。

## 参考文献  
1. LangChain 中文教程 | LangChain 中文文档  https://langchain-doc.cn/  
2. LangChain: Open Source AI Agent Framework for Any Model  https://www.langchain.com/langchain  
3. LangChain — 为大模型驱动的应用程序而设计的开源框架  https://langchaincn.cn/  
4. LangChain 教程 | 菜鸟教程  https://www.runoob.com/langchain/langchain-tutorial.html