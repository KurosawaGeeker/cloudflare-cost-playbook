# 贡献说明

优先提交能复现的修正：价格或平台能力提供当前官方来源；代码提供最小复现及有意义的测试；文章说明原统计窗口和修正依据。

分支使用 `type/scope-subject`，提交使用 `type(scope): subject`。PR 标题遵循相同语义。提交 PR 或 issue 前先检查仓库是否新增了相应模板；本次初始发布没有专门模板。

基础检查：

```sh
python3 -m unittest discover -s tests -v
python3 tools/check_package.py
```

示例在 [独立源码仓库](https://github.com/KurosawaGeeker/ds-vs-ds-voting)，有自己的 README 和检查命令。不要把模拟器通过写成 CDN、WAF 或账单已在云端验证；也不要为了验证保护向线上制造大流量。

保留改写前原稿和截图来源信息。账号账期、Worker 时间窗口、Zone 请求、日志子操作、访客数和票数分别表述。累计用量费不是最终发票或实际扣款。

公开证据是白名单整理，不是完整原始记录。禁止提交密钥、真实 IP、Cookie、个人身份材料、私人联系方式或原始会话。新截图需审核；脱敏不是仅把文件改名。历史代码示例只用于复盘，不应无意把它变成新的默认部署入口。

维护 Skill 时保持 `SKILL.md`、`agents/`、`references/`、`scripts/` 可以独立复制安装。文档、工具和示例引用须随目录变更一起更新。复核许可证与第三方素材边界见 [NOTICE](../NOTICE.md)。
