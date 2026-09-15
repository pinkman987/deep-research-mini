# LangChain与LangGraph在构建有状态Agent时有什么区别？

# LangChain与LangGraph在构建有状态Agent时的区别研究简报

本简报严格依据已验证的结论与对应原文证据，聚焦二者在**有状态Agent构建**维度的核心差异，不引入任何未证实信息。

## 一、状态管理机制的根本差异

LangGraph通过**显式状态（State）建模**实现有状态Agent，其状态通常为类字典结构，并支持为各字段单独配置Reducer函数，以精细控制新数据如何与旧状态合并 [3]。  
LangChain的Chain与Agent默认是**无状态的**，一次仅能处理单一输入，必须额外引入Memory模块（如`ConversationBufferMemory`）来记录和管理历史消息，从而间接实现有状态行为 [7]。

## 二、状态更新语义的本质区别

在LangGraph中，节点返回值（如`{"messages": [...]}`）**不是“最终想要的样子”，而是“要合并的东西”**；该语义由Reducer机制定义——返回值触发合并操作，而非直接赋值 [2]。  
LangChain Agent无此基于Reducer的状态更新语义，其Memory模块采用隐式追加或缓冲策略，未体现“返回即补丁”“配置即合并逻辑”的契约化设计 [2]。

## 三、字段级更新策略的可控性

LangGraph允许为状态中任意字段单独指定Reducer函数：  
- 若某字段**未配置Reducer**，默认行为为**直接替换**（如`return {"count": 2}`使`state["count"]`变为2）[2]；  
- 若**配置了Reducer**（如`add_messages`或自定义`replace_reducer`），则返回值被视为“更新补丁”，执行聚合逻辑（如`old_val + update_val`）[2]；  
- 可通过为消息指定**固定`id`**（如`"id": "system-prompt"`），使`add_messages`执行替换而非追加，实现细粒度控制 [2]；  
- 支持**自定义Reducer**（如`def replace_reducer(old_val, new_val): return new_val`）以实现完全替换等特殊语义 [2]。  

LangChain未在材料中体现任何字段级、可配置的更新策略，其Memory模块不提供类似Reducer的聚合函数接口，亦无`id`驱动的智能合并能力 [2][7]。

## 四、消息（messages）处理的典型对比

LangGraph内置`add_messages` Reducer，专用于消息列表的智能合并：依据消息`id`判断是追加新消息还是替换已有消息；若返回消息缺失固定`id`，将导致旧消息被重复追加 [2]。  
LangChain Agent本身**不提供此类细粒度消息合并机制**，其Memory模块（如`ConversationBufferMemory`）仅按顺序缓存消息，无`id`识别、无自动去重/替换逻辑，故不存在由Reducer语义引发的消息重复问题 [2][7]。

## 五、设计哲学与开发认知要求

LangGraph要求开发者对状态流转保持清晰认知：**必须区分“返回补丁”与“设置终态”**，否则易引发意外行为（如消息翻倍）[2]。  
LangChain Agent无此语义约定，其状态依赖外部Memory注入，返回值语义为常规输出，不承载状态合并意图 [2]。

## 六、无法确认的内容

- LangChain是否支持任何形式的自定义状态合并逻辑（如类似Reducer的扩展机制）；  
- LangGraph是否完全替代LangChain Agent的所有功能（如工具调用、规划等），或仅专注状态建模；  
- 两种框架在性能、调试支持、生产部署成熟度等方面的比较；  
- 除`add_messages`外，LangGraph是否提供其他内置Reducer及其具体行为；  
- LangChain Memory模块是否存在未在材料中披露的底层状态聚合能力。

以上内容均因证据不足而无法确认。

## 参考文献

1. LangChain LangGraph 状态管理 的更多内容_CSDN技术社区  /link?url=hedJjaC291OHSfRZxx--pdfZ45aIPvhNrynoH4S1IZp3dsjpqTIyDRKuVF6C9pY-4qyWgo0gksiJZjEOqOmMNi7uKIFQxHwQp3FUAcHfRxRQwT2iBljST4ZWRckoRH6HfwrJdNpOrMe3iIOdaIhcdDuXXWNwxqZvddrlsJDQAUkVxG_Zyvmx6t9MkawnU5TuKowmiO2tnm2zfJgcX9cNiccMhw0KSNF3HNkCnvczYxwYh6gJ0EYIZQ..  
2. 理解Reducer(归约函数/聚合函数),掌握 LangGraph 状态管理  https://mp.weixin.qq.com/s?src=11&timestamp=1789476485&ver=6968&signature=3g4V62yBbEq*NZXo*9CQhtZetdz*RtcNeSBOWUBY4K2HA4EFKG7kMhVN7JcHyF1DNHduc5TT*s*9oLx7LdBaKc7oqWdqs-qBArlLtko2Jvw67o3wEGnR824ZIUQntSDh&new=1  
3. LangChain Agent 有状态对比 的更多内容_CSDN技术社区  /link?url=hedJjaC291OHSfRZxx--pdfZ45aIPvhNrynoH4S1IZp3dsjpqTIyDRKuVF6C9pY-d9dHPPyvQgJrT5ejdfFmq1Rp14TGQVcHUuH4FIN19b_XhORCOUTyu5Uw88i--YGOVTY3lrQOwfJQvOuzjm1-HZwFFqjtHK1fBNQ_1-Sa-wTz-2-Rw99_K-ZWIz3fH7VaCWqQW8gJf_mefdFaIIO3RV0gkUoIn8tpmDrhs7j6yGbC6GMvlitLGsY6homv43inreaVHN88tHY.  
4. 学习小结: LangChain 中使用Chain和 Agent 查询数据库的异同与底层实...  /link?url=hedJjaC291NiO7MhDUZdGN5Pslaa4FLa0w-yaj8sx57zOchGRgEHlPDOdTQeKgH8  
5. LangChain 系列之 Agent 的记忆(上):上下  https://mp.weixin.qq.com/s?src=11&timestamp=1789476489&ver=6968&signature=5QjFTH2lPal*QMEkvnFpZp7JVgwTKaSbGpd2qS0XGcAfUV3hRq2CHB7Dx3kWnUEMTEVBz5c0OwgWwEgLCaxNc*s2CdqSRsIk*-U5XiRIi8eBH0UXqa4lnfRBAeLjpsqM&new=1  
6. LangGraph state reducer configuration error codes 的更多内容_CSDN技术社区  /link?url=hedJjaC291OHSfRZxx--pdfZ45aIPvhNrynoH4S1IZp3dsjpqTIyDaJTZJs-SwYcokgGU50h_GfVEi3s4UJOl5Iq2s1ldx-JR0e2YmNcDNLZMluDz0yjC_qpTMNGKn_Wxg5zFAJsZxgc2QKe9zNjHBiHqAnQRghl  
7. 从零开始学 LangChain (3): Memory 模块和Chain模块  https://mp.weixin.qq.com/s?src=11&timestamp=1789476527&ver=6968&signature=5lR5iYDzqQUrnaWRTiS7vVw-SYsUZQcWQelPEiLSANYAddvfa6DOhADY3F2WaqqLe*iKq12EE2wxXqM1VUN6hLn9Uv70shRrcZCX08epmS5wUvtnY-X2vFz1NplCUU*m&new=1