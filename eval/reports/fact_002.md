# Python 3.13的free-threaded build是否默认启用？目前有哪些限制？

# Python 3.13 free-threaded build 研究简报

## 默认启用状态  
Python 3.13 的 free-threaded build **不是默认启用的**，而是作为实验性功能提供 [7]。

## 实验性状态  
Python 3.13 的 free-threaded build 模式被明确定义为**实验性功能** [8]。

## 平台支持范围  
该构建模式在 **Windows 和 macOS 安装程序中作为实验性功能提供** [7]。  
Linux 及其他平台是否提供该构建模式，当前材料未提及，**无法确认**。

## 技术依赖  
Python 3.13 的 free-threaded build 模式**需要 mimalloc 支持**；其配套使用的修改版 mimalloc 虽为可选组件，但在受支持平台上默认启用，且对该构建模式为**必需** [7]。

## GIL 状态  
该构建模式**禁用了全局解释器锁（GIL）** [7]。

## 并发行为  
该构建模式**允许线程更并发地运行** [7]。

## 命名与定位  
该构建模式被描述为“**实验性的自由线程构建模式**” [10]。

## 参考文献  
1. 体验无GIL的自由线程 Python :Python 3.13 新特征之一_知乎  /link?url=hedJjaC291OfPyaFZYFLI4KQWvqt63NB4nZo5dI7lLBsyNTvsQISkQ..  
2. Welcome to Python .org  https://www.python.org/  
3. Download Python | Python .org  https://www.python.org/downloads/  
4. 欢迎来到 Python .org - Python 编程语言  https://pythonlang.cn/  
5. Python 基础教程 | 菜鸟教程  https://www.runoob.com/python/python-tutorial.html  
6. Python 3.14.7 文档  https://docs.python.org/zh-cn/3/  
7. Python Release Python 3.13 .0 | Python .org  https://www.python.org/downloads/release/python-3130/  
8. Python Release Python 3.13 .3 | Python .org  https://www.python.org/downloads/release/python-3133/  
9. python3.13 安装教程（附安装包），【2025】 python3.13 ...  https://blog.csdn.net/helanfe/article/details/154210519  
10. Python 3.13 .0 发布 | Python .org - Python 编程语言  https://pythonlang.cn/downloads/release/python-3130/