# MySQL 中 InnoDB 和 MyISAM 在事务支持上的区别是什么？

# MySQL 中 InnoDB 和 MyISAM 在事务支持上的区别研究简报

## 核心区别总结

- **InnoDB 支持事务**：InnoDB 的最大特色是支持 ACID 兼容的事务功能，类似于 PostgreSQL [2]。  
- **MyISAM 不支持事务**：MySQL 数据库引擎 MyISAM 不支持事务 [4]。  
- **唯一事务性存储引擎**：在 MySQL 5.7 版本的所有存储引擎中，只有 InnoDB 是事务性存储引擎，也就是说只有 InnoDB 支持事务 [7]。  
- **MyISAM 明确不提供事务支持**：MyISAM 强调性能，每次查询具有原子性，执行速度比 InnoDB 更快，但不提供事务支持 [7]。  
- **InnoDB 提供完整事务能力**：InnoDB 提供事务支持、外键等高级数据库功能 [7]；其表为事务安全（ACID 兼容）型表，具有事务（commit）、回滚（rollback）和崩溃修复能力（crash recovery capabilities）[7]。

## 无法确认的内容

- 当前材料未提供关于其他 MySQL 版本（如 8.0 或更早版本）中事务支持情况的明确陈述，因此无法确认 InnoDB 是否在所有版本中均为唯一事务性引擎，或 MyISAM 在任何版本中是否曾支持事务。  
- 当前材料未说明事务相关 SQL 语句（如 `START TRANSACTION`、`SAVEPOINT` 等）在 MyISAM 上的具体行为表现，亦未提及隐式事务或自动提交模式在两种引擎下的差异细节。  
- 当前材料未涉及事务隔离级别、并发控制机制、日志实现方式等深层技术对比，相关内容无法确认。

## 参考文献

1. InnoDB 事务支持 的更多内容_CSDN技术社区  /link?url=hedJjaC291OHSfRZxx--pdfZ45aIPvhNrynoH4S1IZp3dsjpqTIyDSP7_M7SRJYMmbd81KS93tsHMo4p6_ln22pI6DDGXOhJo8AY5MRYlgF8A57ec-LBvcLoYy-WK0saxjqGia_jeKet5pUc3zy0dg..  
2. innodb - 搜狗百科  /link?url=DOb0bgH2eKjRiy6S-EyBciCDFRTZxEJgR5kAXAVaboSuCsIPhglAipg7m_GwxbWQxkMRt-xq-z0.  
3. MySql系列:1、 InnoDB 的 事务 以及锁_知乎  /link?url=hedJjaC291OfPyaFZYFLI4KQWvqt63NBKf04XdE8LXFSYsCxGXD-RA..  
4. MyISAM 事务限制 的更多内容_CSDN技术社区  /link?url=hedJjaC291OHSfRZxx--pdfZ45aIPvhNrynoH4S1IZp3dsjpqTIyDdU2evuK2Yydmbd81KS93tsHMo4p6_ln2y0BeOzZZRldY7H0idZGB8r7xfUm3Vf5b8LoYy-WK0saxjqGia_jeKet5pUc3zy0dg..  
5. mysql 报错 代码 汇总 - 爱笙灬 - 博客园  /link?url=hedJjaC291P3yGwc7N55kLSc2ls_Ks2xwWc3j52l8vIWlGhSmJGIeY7ig65r5gTY  
6. MySQL InnoDB 事务支持 报警代码表 的更多内容_CSDN技术社区  /link?url=hedJjaC291OHSfRZxx--pdfZ45aIPvhNrynoH4S1IZp3dsjpqTIyDf_4puy1TTxOI_v8ztJElgyZt3zUpL3e2wcyjinr-WfbakjoMMZc6EmjwBjkxFiWAY8u4Hd9sAMuW3R5TxBxSm1Mu5dzHngQJwX8xhUwX6SBw68CYiz5yXFYEfjv6j1-lW_J1zK3RX4FwuhjL5YrSxrGOoaJr-N4p63mlRzfPLR2  
7. MySQL 知识点总结[修订版]  https://mp.weixin.qq.com/s?src=11&timestamp=1789477298&ver=6968&signature=iFDUrZT*Xycgptfj5J4ndq37fMWXdP-7t7RIuo1sDPb*MKSJjfYFM2ZYuIbm*5j6aiy2ISj*eQXbUznKF7de4xIwyzrRciaVIZYOZArYhh5tQwAlgvBzf3CVFiPLuoT1&new=1