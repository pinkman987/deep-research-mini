# TCP 三次握手中 SYN 和 ACK 标志位的作用分别是什么？

# TCP三次握手中SYN和ACK标志位作用研究简报

## SYN标志位的作用

- SYN用于双方建立连接，TCP三次握手中的前两次中SYN=1 [2]。  
- SYN标志位在三次握手中的作用是发起连接请求和同步初始序列号 [2]。  
- 当SYN=1时，序号为初始序号ISN（Initial Sequence Number），通过算法来随机生成ISN [2]。  
- 第一次握手：Client给Server发送SYN报文，其中包含Client的初始化序号ISN(C) [2]。  
- 第二次握手：Server收到Client的SYN报文后，也会发送自己的SYN报文作为响应，其中包含Server的初始化序号ISN(S) [2]。  
- 第二次握手中Server发送的报文同时包含SYN=1和ACK=1，即SYN+ACK报文 [2]。

## ACK标志位的作用

- ACK为1标识确认序号字段有效，该报文段中包含对方已经成功接收报文段的确认 [2]。  
- ACK标志位在三次握手中的作用是确认已收到对方的SYN报文，并携带期望接收的下一个字节的序号 [2]。  
- 确认序号（Acknowledgement Number）占32位，如果设置了ACK控制标志位，确认序号的值就是接收方期望下一接收到的数据包的序列号 [2]。  
- 第二次握手：Server会将Client发送的ISN(C)+1作为ACK发送给Client [2]。  
- 第三次握手：Client收到Server的SYN报文后，会将Server发送的ISN(S)+1作为ACK发送给Server [2]。  
- 第三次握手中Client发送的报文包含ACK=1，但SYN=0 [2]。

## 其他关键事实

- 第一次握手后，Client进入SYN_SEND状态 [2]。  
- 第二次握手后，Server进入SYN_RCVD（半连接）状态 [2]。  
- 第三次握手后，Client处于ESTABLISHED状态；当Server收到来自Client的ACK报文后，也进入ESTABLISHED状态；双方建立连接成功 [2]。

## 无法确认的内容

- 当前材料未说明SYN或ACK在非三次握手场景（如数据传输阶段、异常重传、RST处理等）中的具体行为差异。  
- 当前材料未说明SYN=1且ACK=0、或ACK=1且SYN=0在其他TCP状态（如关闭过程、异常恢复）中是否出现及含义。  
- 当前材料未提供SYN或ACK标志位在TCP首部中的确切比特位置、编码方式或与其他标志位（如FIN、RST、PSH、URG）的互斥/共存规则。  
- 材料中未涉及SYN洪泛攻击、SYN Cookie机制、或ACK风暴等相关安全或优化机制，故相关作用无法确认。

## 参考文献

1. TCP （传输控制协议）_百度百科  https://baike.baidu.com/item/TCP/33012  
2. 一文详解 TCP 协议 [图文并茂, 明了易懂]-CSDN博客  https://blog.csdn.net/m0_70094411/article/details/144410381  
3. TCP三次握手 与四 次 挥手详解：全网最全攻略-CSDN博客  https://blog.csdn.net/by__csdn/article/details/155613108  
4. 深入浅出 TCP三次握手 （多图详解） - 知乎  https://zhuanlan.zhihu.com/p/670040600  
5. 一文彻底搞懂 TCP三次握手 、四 次 挥手过程及原理 - 知乎  https://zhuanlan.zhihu.com/p/108504297