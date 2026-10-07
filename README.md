# 人生体检 · life-checkup

**把一本人生建议书，变成只属于你的待办清单。** 一个 Claude Code skill。

《[高性价比人生指南](https://github.com/eternity4719/HowToLiveBetter)》是一本写给「一般人」的书：600 多条建议，每条都写了要花多少钱、多少时间、能换来什么，后面跟着论文和官方文件。
但书不认识你。同一句「该买保险吗」，存款扛得住的人和扛不住的人，答案是反的。

Claude Code 认识你——你跟它聊过的项目、待办、身体状况，都在它的记忆里。
这个 skill 把两边对起来，只留下**书里有证据、而你的情况也证明它落在你身上**的那几条。

## 它做的四件事

1. **先翻记忆**：从 Claude Code 的记忆文件里取证，给你写一份画像，每条事实都标出处和可信度（读到的 / 你说的 / 推测的——推测的一律标「待验」）。
2. **整本书过两遍**：一遍挑「花得少、换得多」的性价比清单，一遍对照你身上正在发生的风险。
3. **不知道就问你**：保险、父母年纪、收入结构这类你从没跟它聊过的事，它不猜，出选择题问你（每轮最多 4 道，最多两轮），只问会让建议改判的。
4. **落成小习惯**：按斯坦福 BJ Fogg《福格行为模型》，每条建议都写成「在我【你每天本来就会做的事】之后，我会【30 秒内做得完的小动作】」，做完马上夸自己一句。要重复的写成习惯配方，做一次就完的写最小第一步 + 截止日。锚点从你的真实日常里找——这是书给不了、只有 Claude Code 能给的部分。

## 安装

需要 `git` 和 `python3`（只用标准库）。

```bash
git clone https://github.com/xntj-ai/life-checkup ~/.claude/skills/life-checkup
```

书不打包在仓库里，第一次运行时自动 clone 到 `~/.cache/howtolivebetter`（可用环境变量 `LIFE_CHECKUP_BOOK_DIR` 改位置），之后每次 `git pull` 跟着书更新。

## 怎么用

在 Claude Code 里直接说：

| 你说 | 它做 |
|---|---|
| 「给我做个人生体检」 | 完整流程：画像 → 筛书 → 访谈 → 报告 → 小习惯 |
| 「按那本人生指南，我该不该 ×××」 | 只看这一件事 |
| 「问我几个问题，把画像补全」 | 只做访谈，改写受影响的建议 |
| 「这些怎么做到 / 变成小习惯」 | 只做第 4 步 |

手动查书也行：

```bash
python3 scripts/book.py sync                 # 拉书、建索引
python3 scripts/book.py list --value --brief # 性价比候选池
python3 scripts/book.py show 11.19           # 看某一条全文
python3 scripts/book.py grep 疫苗
```

## 隐私

报告里会有你的健康、钱、家人和法律风险，所以：

- 报告只写到本地 `~/deliverables/<年-月>/`，画像在 `~/.local/share/life-checkup/profile.md`，**不上传、不部署网页**。
- 扫描记忆时自动跳过文件名带 credential / secret / password / token / .env 的文件，内容里像密钥的串会被打码。
- 想拿去公开演示，请另编一份虚构画像来跑。

## 边界

- 不做医疗诊断、不出法律意见。涉及具体病情和法律风险的条目，只写成「带着书的第几节第几条去问谁、问哪三个问题」。
- 效果取决于 Claude Code 对你了解多少：记忆越少，访谈问得越多。
- 这是从作者自己用的版本里提炼出来的第一版，会持续迭代，见 [CHANGELOG](CHANGELOG.md)。

## 致谢与许可

- 书：《高性价比人生指南》by [eternity4719](https://github.com/eternity4719/HowToLiveBetter)，内容采用 [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) 许可。本仓库不包含书的正文，运行时从原仓库获取；生成的报告末尾会保留书的署名与许可链接。
- 小习惯方法：BJ Fogg，《福格行为模型》（*Tiny Habits*）。
- 本 skill 代码：[MIT](LICENSE)。

当前版本 **v1.0.0** · [更新日志](CHANGELOG.md)
