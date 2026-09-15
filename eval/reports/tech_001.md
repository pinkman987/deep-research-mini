# FastAPI 与 Flask 在异步支持和类型校验上的主要区别是什么？

# FastAPI 与 Flask 在异步支持和类型校验上的主要区别研究简报

## 异步支持对比

- FastAPI 原生支持 `async`/`await`，可高效处理 IO 密集型任务 [3]。  
- FastAPI 的异步支持归功于 Starlette [3]；FastAPI 是 Starlette 的子类，因此可使用 Starlette 的所有功能 [3]。  
- FastAPI 使用 `async def` 定义异步路由处理函数 [1]。  
- Flask 的异步支持需扩展 [3]；其运行模式为同步、基于 WSGI [3]。  
- Flask 的性能被描述为“中（同步，WSGI）”，而 FastAPI 为“高（异步，ASGI）” [3]。  

## 类型校验对比

- FastAPI 基于标准 Python 类型提示进行数据校验 [3]；FastAPI 使用 Python 3.8+ 并基于标准的 Python 类型提示 [3]；FastAPI 是一个使用 Python 并基于标准的 Python 类型提示的 Web 框架 [1]。  
- FastAPI 内置类型校验（Pydantic）[3]；Pydantic 作为其数据校验层，负责基于 Python 类型提示进行数据校验、序列化和文档生成 [3]。  
- FastAPI 完全兼容 Pydantic，包括基于 Pydantic 的 ORM（如 SQLModel）等外部库 [3]。  
- Flask 的类型校验需手动实现 [3]；其在对比维度中明确列为“需手动实现” [3]。  

## 其他相关事实

- FastAPI 构建在 Starlette（Web 框架层）和 Pydantic（数据校验层）之上 [3]；Uvicorn 为其 ASGI 服务器 [3]。  
- FastAPI 的关键特性中，“快速”归功于 Starlette 和 Pydantic [1]。  
- Flask 在异步支持和类型校验两项上均未被描述为原生或内置，仅标注为“需扩展”与“需手动实现” [3]。  

## 无法确认的内容

- 当前材料未说明 Flask 具体需通过何种扩展实现异步支持（例如是否依赖 Flask 2.0+ 的有限异步能力或特定插件）。  
- 当前材料未说明 Flask 是否完全不支持类型提示，或仅不提供自动校验机制。  
- 当前材料未提供 Flask 手动实现类型校验的具体方式（如是否可集成 Pydantic 或其他库）。  
- 当前材料未说明 FastAPI 的类型校验是否覆盖全部请求生命周期（如路径参数、查询参数、请求体、响应体等）的所有细节，仅确认其“基于类型提示进行数据校验”[3]及“内置（Pydantic）”[3]。

## 参考文献

1. FastAPI - FastAPI  https://fastapi.tiangolo.com/zh/  
2. FastAPI - FastAPI - FastAPI 框架  https://fastapi.org.cn/  
3. FastAPI 教程 | 菜鸟教程  https://www.runoob.com/fastapi/fastapi-tutorial.html  
4. FastAPI 从入门到精通，一篇就够（超详细实战教程）  https://blog.csdn.net/inuex/article/details/159203950