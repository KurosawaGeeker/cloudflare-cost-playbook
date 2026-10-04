# 费用计算器的输入口径

在仓库根目录运行：

```sh
python3 scripts/cost_model.py references/example-input.json
```

复制输入 JSON 后修改这些字段：

- `read_path` 必填：`direct_r2` 表示公共读不经过用户 Worker；`worker_proxy` 表示全部公共读先进入 Worker，缓存命中也计入口调用。
- `public_reads` 已包含首次、轮询、重试等实际请求。`vote_posts` 包含实际提交尝试，而不是仅成功票数。额外个人 GET、OPTIONS 或后台调用若存在，应归集到动态调用模型后再比较，当前示例未单独建模它们。
- `origin_fraction` 是经过所有缓存层后真正到 R2 的比例；`r2_operations_per_origin_read` 是每次回源对应 Class B 操作数，可表达 HEAD + GET；`r2_class_b_other_operations` 单独计发布器读等操作。
- `r2_class_a_operations` 和 `publisher_invocations` 是独立的实际或估算用量。30 天每分钟一次是 43,200 次；每 15 秒一次是 172,800 次，但普通 Cron 不能直接提供 15 秒调度。DO alarm 或外部发布器另核算费用，不能把 Worker 调用数填 0 就宣称发布免费。
- 输入示例对应一分钟发布：43,200 次 Worker 定时调用、43,200 次 HEAD 读取、43,200 次 PUT 写入。它把 CPU 暂按 0 处理；实际场景要补入测得 CPU、重试与竞争失败的操作数。
- `monthly_allowance` 和 `account_usage_before_window` 属于同一账号、同一账期。模型计算账单函数的增量 `F(已有用量 + 情景用量) - F(已有用量)`，避免 R2 整百万取整被跨项目重复计算。短窗口不自动按天重置月额度；跨账期请拆成多次计算。
- `freshness` 的发布周期、CDN TTL、浏览器 TTL 和轮询周期作保守相加。结果未计网络、调度延迟、重试与故障，不是服务保证；低费用不代表满足实时性。

价格快照见 [pricing.json](../references/pricing.json)，核验日期 2026-10-04。部署前重新核对官方价格、实际套餐和账号额度。模型排除了订阅、D1、DO、Queues、日志、安全付费选项及税费等，不能称为全站总账单。

原案例和模型的数字分别保存。仓库示例输出不是重新拉取的 Cloudflare 账单；验证范围见 [验收记录](verification.md)。
