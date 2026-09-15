# Python 3.13的free-threaded build是否默认启用？目前有哪些限制？

## Python 3.13 Free-threaded Build 默认状态

Python 3.13 的 free-threaded build（免GIL构建）**并非默认启用**，而是作为一项**实验性功能（experimental feature）提供**。标准官方安装包（如 `python-3.13.0-amd64.exe` 或 `Python-3.13.0.pkg`）仍基于传统的 GIL 启用构建；用户需显式选择并下载标注为 “Free-threaded” 的独立安装程序（例如 `python-3.13.0-amd64-freethreaded.exe`）才能使用该模式 [9]。这一设计明确体现了其非生产就绪的定位 [10]。

## 技术实现与依赖要求

Free-threaded build 的核心是**完全移除全局解释器锁（GIL）**，从而允许 Python 字节码在多个原生线程上真正并行执行，提升 CPU 密集型多线程程序的吞吐量 [9]。为保障内存分配在无锁环境下的线程安全性与性能，该构建**强制依赖一个定制修改版的 mimalloc 内存分配器**，标准系统 malloc 或 Python 默认的 pymalloc 均不满足并发安全要求 [9]。此依赖也意味着构建和分发流程需额外适配。

## 当前主要限制（基于公开材料的确认范围）

根据当前官方发布说明（Python 3.13.0 和 3.13.3），free-threaded build 仍处于**明确的实验阶段（experimental）**，其稳定性、兼容性与性能尚未达到默认启用的标准 [9][10]。值得注意的是，**现有公开材料未详细说明具体技术限制**，例如：哪些内置模块暂不支持、C API 中哪些函数存在线程安全风险、主流第三方包（如 NumPy、Pandas）的兼容性状态等关键信息均未在所列来源中披露 [材料不足]。因此，实际采用前需严格验证应用生态的适配情况。

## 参考文献

1. Welcome to Python.org  https://www.python.org/  
2. Download Python | Python.org  https://www.python.org/downloads/  
3. 欢迎来到 Python.org - Python 编程语言  https://pythonlang.cn/  
4. Python 基础教程 | 菜鸟教程  https://www.runoob.com/python/python-tutorial.html  
5. Python 3.14.7 文档  https://docs.python.org/zh-cn/3/  
6. GitHub - python/cpython: The Python programming language  https://github.com/python/cpython  
7. CPython, Pypy, MicroPython...还在傻傻分不清楚？  https://zhuanlan.zhihu.com/p/641962089  
8. CPython详解-CSDN博客  https://blog.csdn.net/KYuruyan/article/details/104455261  
9. Python Release Python 3.13.0 | Python.org  https://www.python.org/downloads/release/python-3130/  
10. Python Release Python 3.13.3 | Python.org  https://www.python.org/downloads/release/python-3133/  
11. python3.13安装教程（附安装包），【2025】python3.13 ...  https://blog.csdn.net/helanfe/article/details/154210519  
12. Python 3.13.0 发布 | Python.org - Python 编程语言  https://pythonlang.cn/downloads/release/python-3130/