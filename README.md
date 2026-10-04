# Cloudflare 成本事故复盘与项目启动包

给独立开发者和使用 AI 编程的人：把“能运行”与“成本可解释、风险可响应”一起验收。

本仓库依据一个公开投票站的费用事故整理，提供文章、可执行审查 skill、项目规则、可运行示例和传播稿。所有材料只在本地准备；原站没有因本次任务恢复，仓库没有推送、发布或部署。

## 从这里开始

| 需要什么 | 文件 | 当前状态 |
|---|---|---|
| 读完整事故复盘 | [事故文章](articles/incident-review.md) | 可供审阅的中文长文，含代码、架构图、数字与执行选段 |
| 让 AI 审查自己的项目 | [Cloudflare 成本审查 skill](skills/cloudflare-cost-review/SKILL.md) | 带价格快照、计算器、审查记录模板；没有安装到全局目录 |
| 为已有项目加启动约束 | [可复制 AGENTS.md](templates/AGENTS.md)、[启动卡与提示词](templates/project-brief.md) | 合并到已有规则，不覆盖原规则 |
| 复制读写分离示例 | [投票快照项目模板](templates/voting-snapshot/README.md) | 本地运行时验证；实际资源、CDN/WAF和计费效果待线上验收 |
| 发 X 长帖或短文案 | [16条长帖](social/x-thread.md)、[各平台短稿](social/short-posts.md) | 草稿，未发送 |
| 核对数字与执行口径 | [案例数据](evidence/case-facts.json)、[证据说明](evidence/case-notes.md) | 人工白名单摘要，不是最终发票或全量日志 |
| 查看实际检查范围 | [本地验收记录](VERIFICATION.md) | 记录测试和剩余线上验证项 |

## 最重要的区别

“缓存省了数据库查询”和“请求不再进入动态收费程序”是两件事。业务防刷、流量防护、费用响应也需要分别验收。

本案例截至 2026-10-04 的账号累计用量费用为 **$816.52**，其中请求费 **$785.40**，占 **96.19%**。这是当时的用量读回，不是已经核实的扣款。近7天投票 Worker 约26.1亿次调用，账号账期约26.3亿次请求，范围不同；这些数不能当真人访问或投票数量。

示例选择公共结果由 R2 自定义域名/CDN 分发，受保护动态接口处理投票，Cron 每分钟发布固定快照。它是一个权衡示例，不是所有 Cloudflare 项目的标准答案，也没有在原站上线。若业务要求15秒发布或20秒以内更新，需要另评估调度、推送及相应成本。

## 使用 skill

可以直接让 AI 阅读 `skills/cloudflare-cost-review/SKILL.md`。若要让支持 skills 的工具发现它，把整个 `skills/cloudflare-cost-review/` 文件夹复制到该工具的 skills 目录；保留 `scripts/`、`references/` 和 `agents/`。不要只复制入口文件。

示例任务：

> 使用 $cloudflare-cost-review 审查我的项目。先画出请求和计费路径，分别计算正常、增长、异常流量成本；核对缓存减少了哪一层的用量，并给出上线证据和剩余风险。先不要部署或发线上负载。

## 本地费用计算器

只需 Python 3 标准库，不连接 Cloudflare：

```sh
python3 tools/cost_model.py skills/cloudflare-cost-review/references/example-input.json
python3 -m unittest discover -s tests -v
python3 tools/check_package.py
```

复制输入 JSON 后修改：

- `read_path` 必填：`direct_r2` 表示公共读不经过用户 Worker；`worker_proxy` 表示全部公共读先进入 Worker，缓存命中也计入口调用。
- `public_reads` 已包含首次、轮询、重试等实际请求。`vote_posts` 包含实际提交尝试，而不是仅成功票数。额外个人GET、OPTIONS或后台调用若存在，应归集到动态调用模型后再比较，当前示例未建模它们。
- `origin_fraction` 是经过所有缓存层后真正到R2的比例；`r2_operations_per_origin_read` 是每次回源对应Class B操作数，可表达HEAD+GET；`r2_class_b_other_operations` 单独计发布器读等操作。
- `r2_class_a_operations` 和 `publisher_invocations` 是独立的实际/估算用量。30天每分钟一次是43,200次；每15秒一次是172,800次，但普通Cron不能直接提供15秒调度。DO alarm或外部发布器要另外核算其费用，不能把Worker调用数填0就宣称发布免费。
- 输入示例对应一分钟发布：43,200次Worker定时调用、43,200次HEAD读取、43,200次PUT写入。它把CPU暂按0处理；实际场景要补入测得CPU、重试和竞争失败的操作数。
- `monthly_allowance` 和 `account_usage_before_window` 属于同一账号、同一账期。模型计算账单函数的增量 `F(已有用量+情景用量)-F(已有用量)`，避免R2整百万取整被跨项目重复计算。短窗口不自动按天重置月额度；跨账期请拆成多次计算。
- `freshness` 的发布周期、CDN TTL、浏览器TTL和轮询周期作保守相加。结果没有计入网络、调度延迟、重试与故障，不能当服务保证；低费用不代表满足实时性。

价格快照见 [pricing.json](skills/cloudflare-cost-review/references/pricing.json)，核验日期2026-10-04。部署前重新核对官方价格、实际套餐和账号额度。结果排除了订阅、D1、DO、Queues、日志、安全付费选项及税费等，不能称为全站总账单。

## 发布时怎样使用

先审阅文章与证据口径，再选择仓库许可证和对外地址。推文中的文件链接可替换为发布后的实际链接。文章与宣传稿都保留“累计用量不是扣款”“请求不等于真人”和“示例未线上验证”的边界，不能为了传播效果去掉。

仓库未选择对外许可证。任何依赖保留其原许可证；示例不是原站源码的完整复制，也没有收入原始凭据、IP、私人材料或原始会话。公开证据摘要是本地材料的白名单整理，散列用于版本核对，不构成第三方审计认证。

本地提交使用仓库专用的通用作者信息，避免自动写入本机用户名和主机名；未改动全局Git配置。对外发布时可由所有者设置正式署名。
