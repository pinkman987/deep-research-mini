# HTTP 429状态码表示什么？客户端应如何设计重试策略？

# HTTP 429状态码与客户端重试策略研究简报

## 一、HTTP 429状态码的含义

HTTP 429状态码表示“Too Many Requests”（请求过多），即客户端在给定时间内发送了过多请求，触发了服务端的限流机制[6]。该状态码通常意味着API已被限流[3]。

## 二、429错误的成因多样性

429状态码可能由多种具体原因触发，包括但不限于：  
- 请求频率或token速率超限；  
- 免费模型每日次数用完；  
- 余额不足或消费上限；  
- 上游容量限制[5]。

## 三、重试策略设计原则

### 1. 不应一视同仁地重试所有429响应  
部分429错误（如配额用尽、计费异常等）无法通过等待或重试解决。OpenAI明确指出：Retry-After「does not mean that quota, billing, or other errors that require user action can be resolved by retrying」[5]。对所有429统一重试可能导致持续无效请求，直至告警触发[5]。

### 2. 优先服从Retry-After响应头  
当429响应中包含`Retry-After`头时，该字段为服务端指定的**硬下限**——客户端不得早于该时间重试；未提供该头时，才启用客户端自定义退避策略[2]。

### 3. 决策依据需升级为“状态码 + error.code”  
仅依赖HTTP状态码不足以区分处置方式。应解析响应体中的`error.code`字段（如`'slow_down'`、`'rate_limit_exceeded'`、`'server_is_overloaded'`），并据此映射语义化错误类型，选择对应退避参数与恢复策略[2]。

### 4. 按error.code分类实施差异化处置  
- 若`error.code = 'slow_down'`：表明请求速率上升过快导致模型侧过载；处置方式是**压低当前请求速率并保持稳定一段时间，再缓慢爬升**；单纯退避后原速重试无效[2]。  
- 若`error.code = 'rate_limit_exceeded'`：表明组织级额度（如每分钟请求数、每分钟token数或月度配额）已耗尽；此时应**严格按Retry-After提示等待额度窗口重置**，调整发送速率无意义[2]。  

### 5. 无Retry-After时的兜底策略  
当429响应未提供`Retry-After`头，且错误类型属于可重试的限流场景时，客户端应采用**带抖动的指数退避策略**，并**限制总重试次数**[5]。

## 四、可观测性要求

日志中应**同时记录HTTP状态码和响应体中的error.code**，且两个维度需**分开聚合**；否则仅统计“429变多了”无法识别问题根源（例如无法区分是自身流量突增还是上游容量抖动）[2]。

## 参考文献

1. HTTP状态码 :完整列表  https://mp.weixin.qq.com/s?src=11&timestamp=1789476155&ver=6968&signature=sUkRtiUfLvTDHGEdtZNs-jmHW5i3zQqLgZvEDAFs2AYi5bv8C5E9hVbSGMQA6IPfoieZXDAg3cy1C6iXVhwvrOt0EZlCEP2WMQebmhnufhX9Fy4SWZhRoYHFQ*Tqqoqc&new=1  
2. OpenAI把含糊的 429 拆成了三种错: 重试 逻辑只认状态码的日子...  https://mp.weixin.qq.com/s?src=11&timestamp=1789476159&ver=6968&signature=M22tJdckMmb0nPJEs07nzs3YUVhnGaON0Gk*UlR4Krwa-P7aC7xdbhQg43Il6LLEB2DsSW46SDuLkyM8pY7YZrj6v56tIzntYvXi*H*P8gharAvYyEBBFMjCR5ckyZiu&new=1  
3. HTTP429 ,这个 Code 你可见过?  https://mp.weixin.qq.com/s?src=11&timestamp=1789476163&ver=6968&signature=si-if7e08qs1EThHc6vdUAM1dKQScPGiHyV-8mrjdyf30qFRQFJGTk8OdlyGN*O9lg1U2h3avOGpFoHDoC*kNt-aR57S4ic8gyRZyT7e7QBwGQu6xhqXTJK5*DoYlphX&new=1  
4. 深入理解：HTTP状态码 429 的含义_ 429 too many requests ...  https://blog.csdn.net/q7w8e9r4/article/details/133639163  
5. 遇到 429 Too Many Requests 怎么办？什么时候重试才有效？  https://ofox.io/zh/blog/429-too-many-requests-rate-limit-exceeded-when-to-retry-2026/  
6. 429 Too Many Requests - HTTP | MDN  https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Reference/Status/429  
7. HTTP _百度百科  https://baike.baidu.com/item/http/243074  
8. HTTP 协议详解（ HyperText Transfer Protocol 超文本传输 ...  https://blog.csdn.net/Dontla/article/details/121189955  
9. HTTP 概述 - MDN Web Docs  https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Guides/Overview  
10. HTTP 协议 | 菜鸟教程  https://www.runoob.com/np/http-protocol.html