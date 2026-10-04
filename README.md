# Cloudflare Cost Playbook

**给一句话 vibe coding 带上成本护栏。** 面向独立开发者、创业者和 AI 编程助手的 Cloudflare 成本审查 Skill 与仓库启动规则。

我做过一个两张图、两个按钮的投票站。我以为它和过去随手做的小网站一样，几十个人看过就会归于沉寂，于是为了快点上线，省掉了提前准备风险处理的工作。后来账号显示了 800 多美元的累计用量费，绝大部分来自 Worker 请求，而不是数据库。

这个仓库就是为了少重复一次这样的教训：**即使你只说一句“做一个投票网站”，agent 也应该从仓库规则里读到成本审查要求。** Serverless 帮我们少管服务器、自动扩容，却不会自动控制账单。

## 先用起来

点击 GitHub 的 **Use this template** 创建自己的仓库，或者克隆后用支持 `AGENTS.md` 的编程助手打开：

```sh
git clone --depth 1 https://github.com/KurosawaGeeker/cloudflare-cost-playbook.git
cd cloudflare-cost-playbook
```

然后直接提出业务需求，例如：

> 做一个极简的单页投票网站，手机和电脑都能用，实时展示票数。

根目录 [AGENTS.md](AGENTS.md) 要求助手在涉及 Cloudflare 公共接口、轮询或推送时，先读取 [SKILL.md](SKILL.md)，梳理请求与计费路径、流量模型、缓存验证和**账号级全局账单报警**。这些要求留在仓库里，不需要每次重新写进提示词。仍需确认你的工具确实读取了仓库规则；预算缺失时，助手应记录假设或询问，不能擅自替你购买服务。

这是启动和审查模板，**不是开箱即有费用硬上限的托管服务**。克隆不会创建云资源。本仓库当前版本不包含投票网站源码，也不通过 submodule、安装脚本或自动下载拉取源码。需要看代码时，再单独打开或克隆 [投票源码仓库](https://github.com/KurosawaGeeker/cloudflare-voting-examples)；实际 CDN、安全规则、告警送达与费用效果需要上线验收。

## 仓库里有什么

```text
SKILL.md                 成本审查入口
AGENTS.md                项目启动规则，给 agent 自动读取
agents/                  Skill 的工具展示与触发配置
references/              官方核验点、价格快照、模型输入、审查记录
scripts/                 标准库费用计算器
docs/
  articles/              事故长文、改写前原稿与图片
  evidence/              脱敏数字、统计口径与公开执行选段
  editorial/             DeepSeek 文风改写指令与调用记录
  social/                X 长帖和其他平台短稿
  verification.md        实际验收记录与待验证项
  project-brief.md        项目启动卡
tests/                   费用模型回归测试
tools/                   包结构、相对链接和隐私标记检查
```

| 你想做什么 | 入口 |
|---|---|
| 看事故怎么发生 | [事故长文](docs/articles/incident-review.md) |
| 给已有项目加规则 | 合并 [AGENTS.md](AGENTS.md)，连同 Skill 资源一起放入项目 |
| 做自己的投票原型 | [独立源码仓库：快照示例](https://github.com/KurosawaGeeker/cloudflare-voting-examples/tree/feat/voting-examples/voting-snapshot) |
| 对照原站的缓存和轮询代码 | [独立源码仓库：原站脱敏示例](https://github.com/KurosawaGeeker/cloudflare-voting-examples/tree/feat/voting-examples/original-voting-site) |
| 核对数字和执行记录 | [案例数字](docs/evidence/case-facts.json)、[证据说明](docs/evidence/case-notes.md) |
| 准备分享这个案例 | [X 长帖](docs/social/x-thread.md)、[短稿](docs/social/short-posts.md) |
| 看什么真的测过 | [验收记录](docs/verification.md) |

## 单独安装 Skill

在 Codex 中，可把以下四项复制到自己的 `~/.codex/skills/cloudflare-cost-review/`：

```text
SKILL.md
agents/
references/
scripts/
```

不要只复制入口文件。也不需要把事故图片或独立源码仓库装进 Skill。安装后可以显式调用 `$cloudflare-cost-review`；其他支持 skills 的工具使用自己的安装目录。仅把文件放在本仓库顶层，不代表每个工具都会把它注册成全局 Skill。

## 在本地计算和检查

只需 Python 3 标准库，计算器不连接 Cloudflare：

```sh
python3 scripts/cost_model.py references/example-input.json
python3 -m unittest discover -s tests -v
python3 tools/check_package.py
```

输入有两个容易填错的字段：`read_path` 区分公共读取直达 R2 和先经过 Worker 代理；`origin_fraction` 表示经过所有缓存层后，实际到 R2 的比例。Worker 代理命中缓存仍然有入口调用，CDN 缓存失效也可能把费用转移到存储读取。

完整单位、共享额度和排除项见 [计算器说明](docs/cost-model.md)。[价格快照](references/pricing.json)用于复算，不代替上线时核对套餐和官方价格；模型覆盖指定 Workers/R2 用量，不是全站总账单。

## 使用边界与贡献

累计用量不是已核实的最终扣款，请求不等于真人访问，正常增长与异常请求都需要建模。[独立源码仓库](https://github.com/KurosawaGeeker/cloudflare-voting-examples)中的原站示例是所有者本地工作区的脱敏副本，不能据此声称完整还原了高峰期线上版本。快照示例只通过了本地检查，没有替原站完成迁移或恢复服务。

代码与原创文字采用 [MIT](LICENSE)；案例截图里的第三方人物作品和标识不随仓库重新授权，详见 [NOTICE](NOTICE.md)。依赖保留各自许可证。

当前版本已将示例源码拆出，旧提交保留当时的目录记录。上面的 `--depth 1` 只克隆当前版本；若主动获取完整历史，仍会取得拆分前的示例。GitHub 的 **Use this template** 复制当前文件树。

欢迎提交可复现的修正；贡献前阅读 [贡献说明](docs/contributing.md)。不要提交账号密钥、原始 IP、私人身份材料或未经审核的原始日志。
