# 大模型推理中 KV Cache 的作用是什么？有哪些常见优化手段？

# KV Cache 在大模型推理中的作用与常见优化手段研究简报

## 一、KV Cache 的作用

KV Cache 的作用是缓存已生成 token 的 Key 和 Value 向量，避免在自回归推理中重复计算这些中间结果，从而降低注意力计算复杂度 [7]。

在 Transformer 解码（文本生成）过程中，每生成一个新的 token，模型都会重新计算整个输入序列的注意力。这种 O(N²) 的计算复杂度在序列较长时会导致推理速度大幅下降，主要问题包括：  
- 计算冗余：在每个时间步，模型都会重新计算所有已生成 token 的 Key 和 Value；  
- 但这些 Key 和 Value 在过去的计算中已经得到，理论上可以复用，避免重复计算 [7]。

## 二、KV Cache 对计算复杂度的影响

KV Cache 将自回归解码的注意力计算复杂度从 O(N²) 降低到 O(N) [7]。  
通过缓存 Key 和 Value，解码器在生成新 token 时只需要计算当前 token 的 Query 并与缓存的 KV 交互，计算复杂度从 O(N²) 降到 O(N)，显著加速推理 [7]。

## 三、常见优化手段

当前材料中未提供关于 KV Cache 常见优化手段的具体描述或验证结论。  
来源列表中虽包含题为“LLM 推理优化全指南：从 KV Cache 到 Speculative Decoding”[2]、“KV Cache 深度解析：从原理到工程优化的完整指南”[5]等标题暗示可能涉及优化手段，但所提供的已验证结论中**未出现任何具体优化手段（如 PagedAttention、KV 剪枝、量化、分组/压缩缓存、内存布局优化等）的定义、效果或实现方式**。  
因此，关于“有哪些常见优化手段”这一子问题，**无法确认**。

## 参考文献

1. 一文读懂 KV Cache  https://mp.weixin.qq.com/s?src=11&timestamp=1789477676&ver=6968&signature=H*yXg7LJwh7JXQ7hhr7ON1QcRkQtWPzqhz*uFmaC8MYgoKw2ClbjNT9eEEN4eaKGpNmZImTIsVCr6lDwr1ju0MF3bNdTWtpOuZmWV1KWeDSBZIclPj*-0yNCh823qGm-&new=1  
2. LLM 推理优化全指南：从 KV Cache 到 Speculative Decoding  https://guijiagi.com/posts/llm-inference-optimization/  
3. Llm Inference Optimization - ZhengWei's Homepage  https://zw510644628.github.io/LLM-Inference-Optimization/  
4. 广告设计中常说的 KV 指的是什么？和海报的区别在哪里？ - 知乎  https://zhuanlan.zhihu.com/p/579445053  
5. KV Cache 深度解析：从原理到工程优化的完整指南 - 知乎  https://zhuanlan.zhihu.com/p/2016843212178882587  
6. 大模型推理加速：看图学 KV Cache - 知乎  https://zhuanlan.zhihu.com/p/662498827  
7. Transformer 中的 KV Cache ：原理、作用与应用-CSDN博客  https://blog.csdn.net/shizheng_Li/article/details/145804229  
8. 什么是 KV Cache （Key-Value Cache ）-CSDN博客  https://blog.csdn.net/u013172930/article/details/147387537  
9. 算法 - 手撕大模型｜ KVCache 原理及代码解析 - 个人文章 ...  https://segmentfault.com/a/1190000047263593  
10. KV Cache 原理详解：LLM 推理加速与复用机制-阿里云开发 ...  https://developer.aliyun.com/article/1762406  
11. KV Cache 详解：显存容量、前缀复用与生产调优 | QubitTool  https://qubittool.com/zh/blog/llm-inference-kv-cache-guide