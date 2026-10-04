# Cloudflare 核验点

本文件的产品解释与价目在 **2026-10-04** 通过官方文档核验。以后执行审查时重新检查与本项目相关的条目；产品和套餐可能变化，配置能力也可能受套餐限制。

| 问题 | 核验依据 | 审查动作 |
|---|---|---|
| 哪些请求收费 | [Workers pricing](https://developers.cloudflare.com/workers/platform/pricing/) | 区分入站、子请求、静态资产、Workers Cache；不能把整个Zone请求直接当Worker调用 |
| Workers Cache是否消除请求费 | [Workers Cache pricing](https://developers.cloudflare.com/workers/cache/#pricing) | 当前命中仍按Worker请求计费，只省脚本CPU；已有Cache API是另一机制 |
| Cache API的范围 | [Cache API](https://developers.cloudflare.com/workers/runtime-apis/cache/) | 程序先运行再查询；节点本地缓存不能自动成为全球锁 |
| 资产会不会先执行代码 | [Static assets billing](https://developers.cloudflare.com/workers/static-assets/billing-and-limitations/) | 审核`run_worker_first`和回退行为，别把动态路由当免费静态入口 |
| R2怎样走CDN | [Public buckets](https://developers.cloudflare.com/r2/buckets/public-buckets/) | 自定义域名、JSON显式可缓存、关闭非生产`r2.dev`绕过入口；Tiered Cache减少真正回源 |
| R2回源怎么收费 | [R2 pricing](https://developers.cloudflare.com/r2/pricing/) | Standard与IA分开；Class A/B/GB-month、月共享免费额和向上取整；CDN HIT不能保证下一次也HIT |
| D1单位是什么 | [D1 pricing](https://developers.cloudflare.com/d1/platform/pricing/) | 读写行数不是HTTP请求次数；索引与扫描影响行数 |
| DO是不是免费内存 | [DO pricing](https://developers.cloudflare.com/durable-objects/platform/pricing/) | 请求、执行时长与存储分项；DO按对象协调，不等于全球各节点一份一致内存 |
| 拦截发生在哪里 | [Security interoperability](https://developers.cloudflare.com/waf/feature-interoperability/) | 确认规则产品、路由、阶段、例外与终止动作；小样本对照目标调用指标 |
| 验证保护什么 | [Siteverify](https://developers.cloudflare.com/turnstile/get-started/server-side-validation/)、[Pre-clearance](https://developers.cloudflare.com/cloudflare-challenges/concepts/clearance/) | token服务端单次校验；域名/action/cdata按协议绑定；网页验证不自动保护GET |
| 挑战与JSON兼容吗 | [Challenge Pages](https://developers.cloudflare.com/cloudflare-challenges/challenge-types/challenge-pages/) | HTML挑战不适合直接JSON fetch；需要适当通行与受控重试 |
| 15秒后台任务怎么实现 | [Cron triggers](https://developers.cloudflare.com/workers/configuration/cron-triggers/)、[DO alarms](https://developers.cloudflare.com/durable-objects/api/alarms/) | Cron分钟粒度；DO alarm可用于更短间隔但需成本、并发、失败重试设计 |
| 日志本身会收费吗 | [Workers Logs](https://developers.cloudflare.com/workers/observability/logs/workers-logs/) | 记录采样率、保留期、超额日志成本，不能假定全量历史存在 |

配置入口先给使用者：

- [Cloudflare 控制台](https://dash.cloudflare.com/)：选择实际账号后确认套餐、账单、Workers入口、缓存与安全规则。
- [R2 配置入口](https://dash.cloudflare.com/?to=/:account/r2/overview)：桶绑定、自定义域名、开发地址与CORS。
- [Turnstile 配置入口](https://dash.cloudflare.com/?to=/:account/turnstile)：widget域名和Pre-clearance。

不同产品入口可在官方页面中的控制台链接确认；不要凭空拼接某个账号ID或声称用户已登录。需要凭据时使用目标项目的安全输入与secret管理流程。

## 费用解释边界

1. TTL失效通常由后续请求触发刷新，不是CDN主动访问SQL。
2. R2强一致对象读取与CDN允许旧值并不矛盾；URL版本、TTL、条件发布分别解决不同问题。
3. 共享免费额不是每接口或每个七天窗口都有一份；归集到相同账期和账号后才能估算。
4. 平台规则下拦截不进入目标程序，也须检验其他收费产品的用量；不能直接推导整账号零费。
5. DO定时、Cron、监控器、日志、写入口和订阅仍有自身成本。CPU上限与预算提醒均不是月请求数量的硬封顶。
