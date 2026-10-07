#!/usr/bin/env python3
"""从 Claude Code 的本地记忆里找「关于这个人」的材料，供画像取证。

只读、只列线索：输出①必读全文清单 ②按生活领域分组的命中行（path:line）。
凭据类文件整份跳过，命中行里的长 token 打码。画像结论由读完原文的人下，脚本不下。

  sources.py                 默认扫 ~/.claude
  sources.py --root DIR      换一个 CC 配置根目录
  sources.py --per-domain 80 每个领域最多列多少行
"""
import argparse
import re
from collections import defaultdict
from pathlib import Path

SKIP_NAME = re.compile(r"credential|secret|security|password|\.env|token", re.I)
SECRET = re.compile(r"(sk-[A-Za-z0-9_-]{12,}|gsk_[A-Za-z0-9]{12,}|[A-Fa-f0-9]{32,}|[A-Za-z0-9+/]{40,}={0,2})")
USER_TYPE = re.compile(r"^\s*type:\s*user\s*$", re.M)
PERSONAL_NAME = re.compile(r"^user[_-]|persona|personal|health-(profile|log)|finance|founder|family|tax|business-status", re.I)

DOMAINS = {
    "身体与作息": r"体检|血压|血糖|血脂|尿酸|心率|HRV|睡眠|失眠|熬夜|作息|久坐|体重|BMI|减肥|运动|健身|跑步|抽烟|吸烟|喝酒|饮酒|咖啡|过敏|颈椎|腰椎|视力|牙|基因|疫苗|感冒|发烧|生病|住院|吃药",
    "家庭与关系": r"老婆|妻子|爱人|太太|配偶|孩子|儿子|女儿|父母|爸爸|妈妈|母亲|父亲|老人|家人|结婚|离婚|彩礼",
    "钱与资产": r"房贷|车贷|贷款|理财|基金|股票|保险|存款|资产|负债|收入|营收|月入|年入|现金流|报销|个税|余额|订阅|月费|年费|欠款|借钱",
    "公司与合规": r"公司|营业执照|个体户|合同|股东|担保|备案|ICP|许可证|收款|支付|商户号|分账|资质|数据|隐私|版权|爬虫|员工|雇|劳动|社保|医保|公积金|发票|开票|税务",
    "账号与信息安全": r"被盗|泄露|密码|二次验证|2FA|钓鱼|诈骗|骗子|实名|身份证",
    "居住与出行": r"租房|房东|买房|搬家|出国|签证|护照|境外|海外|旅行|机票|酒店|时差",
    "时间与精力": r"凌晨|深夜|半夜|通宵|加班|周末|休息|假期|放假|节奏|累|疲|专注|打断|拖延|会议太多",
    "学习与职业": r"职涯|履历|跳槽|离职|晋升|面试|创业|课程|培训|证书|考证|英语",
}


def iter_markdown(root):
    patterns = ["projects/*/memory/**/*.md", "affairs/**/*.md", "docs/*.md", "CLAUDE.md", "rules/*.md"]
    seen = set()
    for pattern in patterns:
        for path in root.glob(pattern):
            if path in seen or not path.is_file() or SKIP_NAME.search(path.name):
                continue
            if "/archive/" in str(path) or "/_archive/" in str(path):
                continue
            seen.add(path)
            yield path


def must_read(root, path, text):
    rel = str(path.relative_to(root))
    if USER_TYPE.search(text[:600]):
        return True
    return bool(PERSONAL_NAME.search(path.stem)) and not rel.startswith("rules/")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(Path.home() / ".claude"))
    parser.add_argument("--per-domain", type=int, default=80)
    parser.add_argument("--per-file", type=int, default=3)
    args = parser.parse_args()
    root = Path(args.root).expanduser()

    full_read, hits = [], defaultdict(list)
    compiled = {name: re.compile(rx, re.I) for name, rx in DOMAINS.items()}
    for path in iter_markdown(root):
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        rel = path.relative_to(root)
        if must_read(root, path, text):
            full_read.append((rel, len(text)))
        per_file = defaultdict(int)
        for line_no, line in enumerate(text.splitlines(), 1):
            for name, rx in compiled.items():
                if per_file[name] >= args.per_file or not rx.search(line):
                    continue
                per_file[name] += 1
                snippet = SECRET.sub("<已打码>", line.strip())[:180]
                hits[name].append((rel, line_no, snippet))

    print(f"# 画像取证线索（根目录 {root}）\n")
    print("## 一、必读全文（user 类记忆 / 人格与健康、财务、个人事务档案）\n")
    for rel, size in sorted(full_read, key=lambda x: str(x[0])):
        print(f"- {root / rel}（{size} 字符）")
    print("\n## 二、按领域的命中行（线索，不是结论；要用就回原文读上下文）\n")
    for name in DOMAINS:
        rows = hits.get(name, [])
        print(f"### {name}（共 {len(rows)} 行，列前 {min(len(rows), args.per_domain)}）\n")
        for rel, line_no, snippet in rows[: args.per_domain]:
            print(f"- `{rel}:{line_no}` {snippet}")
        print()


if __name__ == "__main__":
    main()
