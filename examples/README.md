# 两种投票示例

| 示例 | 用途 | 读取票数的路径 |
|---|---|---|
| [voting-snapshot](voting-snapshot/README.md) | 新项目可参考的读写分离实现 | 浏览器读独立快照入口，写票进入 Worker |
| [original-voting-site](original-voting-site/README.md) | 对照事故时的缓存与轮询设计 | 结果 GET 先进入 Worker，再查内部 Cache API |

先读各自 README 再运行。两个例子不连接原投票站数据，默认配置没有公开路由。本地测试证明的行为和实际云端的费用效果分开看；没有把历史方案重新部署到线上。
