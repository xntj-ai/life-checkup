#!/usr/bin/env python3
"""《高性价比人生指南》本地副本：同步、解析、列目录、取全文。

  book.py sync                      clone / pull 到缓存目录并重建 entries.jsonl
  book.py sections                  34 节一览（节号、标题、条数）
  book.py list  --brief             全书一行一条：条号、证据级、成本三字(钱时毅)、收益、标题
  book.py list  --value --brief     性价比线候选池（收益大、成本低、正向动作）
  book.py list  --sections 1,12     紧凑目录：条号、证据级、成本标签、标题、说人话
  book.py show  12.2 26.1           条目全文
  book.py grep  担保 代运营         标题或说人话命中关键词的条目（紧凑格式）
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO_URL = "https://github.com/eternity4719/HowToLiveBetter.git"
CACHE_DIR = Path(os.environ.get("LIFE_CHECKUP_BOOK_DIR", Path.home() / ".cache" / "howtolivebetter"))
INDEX_PATH = CACHE_DIR.parent / "howtolivebetter-entries.jsonl"
FIELDS = ("成本", "说人话", "收益", "证据等级", "来源", "备注")
TAG_RE = re.compile(r"<!--\s*成本标签:(.*?)-->")
HEAD_RE = re.compile(r"^### (\d+)\. (.+)$")
SECTION_RE = re.compile(r"^# (\d+)\. (.+)$")


def run_git(args, cwd=None):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)


def sync():
    if (CACHE_DIR / ".git").exists():
        result = run_git(["pull", "-q", "--ff-only"], cwd=CACHE_DIR)
    else:
        CACHE_DIR.parent.mkdir(parents=True, exist_ok=True)
        result = run_git(["clone", "-q", "--depth", "1", REPO_URL, str(CACHE_DIR)])
    if result.returncode != 0:
        print(f"git 失败（沿用本地副本）：{result.stderr.strip()}", file=sys.stderr)
    entries = parse_book()
    with INDEX_PATH.open("w", encoding="utf-8") as fh:
        for entry in entries:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    commit = run_git(["log", "-1", "--format=%h %ci"], cwd=CACHE_DIR).stdout.strip()
    print(f"书版本 {commit} · 条目 {len(entries)} · 索引 {INDEX_PATH}")


def parse_tags(raw):
    return dict(pair.split("=", 1) for pair in raw.split() if "=" in pair)


def parse_file(path):
    section_no, section_title = None, ""
    entries, current = [], None
    for line in path.read_text(encoding="utf-8").splitlines():
        if section_no is None and (m := SECTION_RE.match(line)):
            section_no, section_title = int(m.group(1)), m.group(2).strip()
            continue
        if m := HEAD_RE.match(line):
            current = {
                "id": f"{section_no}.{m.group(1)}",
                "section": section_no,
                "section_title": section_title,
                "no": int(m.group(1)),
                "title": m.group(2).strip(),
                "tags": {},
                "file": str(path.relative_to(CACHE_DIR)),
            }
            entries.append(current)
            continue
        if current is None:
            continue
        if m := TAG_RE.search(line):
            current["tags"] = parse_tags(m.group(1))
            continue
        for field in FIELDS:
            prefix = f"- {field}："
            if line.startswith(prefix):
                current[field] = line[len(prefix):].strip()
                break
    return entries


def parse_book():
    files = sorted((CACHE_DIR / "book").glob("*.md"))
    if not files:
        sys.exit(f"没有找到书的正文：{CACHE_DIR}/book，先跑 sync")
    return [entry for path in files for entry in parse_file(path)]


def load():
    if not INDEX_PATH.exists():
        sync()
    with INDEX_PATH.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh]


def brief(entry):
    tags = entry.get("tags", {})
    short = "".join(tags.get(k, "?")[:1] for k in ("钱", "时间", "毅力"))
    return f"{entry['id']} {entry.get('证据等级', '?')} {short} {tags.get('收益', '?')} {entry['title']}"


def is_value_action(entry):
    """性价比线候选：收益大、钱 0/少、时间少/中、毅力否/些，且是要做的动作而不是「不/别」开头的红线。"""
    tags = entry.get("tags", {})
    cheap = tags.get("钱") in ("0", "少") and tags.get("时间") in ("少", "中") and tags.get("毅力") in ("否", "些")
    return cheap and tags.get("收益") == "大" and not entry["title"].startswith(("不", "别"))


def compact(entry):
    tags = entry.get("tags", {})
    tag_text = " ".join(f"{k}={v}" for k, v in tags.items())
    plain = entry.get("说人话", "")
    return f"[{entry['id']}] {entry.get('证据等级', '?')} | {tag_text} | {entry['title']} —— {plain}"


def full(entry):
    lines = [f"### {entry['id']} {entry['title']}（第 {entry['section']} 节 {entry['section_title']}）"]
    lines += [f"- {field}：{entry[field]}" for field in FIELDS if field in entry]
    lines.append(f"- 原文：https://github.com/eternity4719/HowToLiveBetter/blob/main/{entry['file']}")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("sync")
    sub.add_parser("sections")
    list_cmd = sub.add_parser("list")
    list_cmd.add_argument("--sections", default="", help="逗号分隔的节号，如 1,2,12；不给则全书")
    list_cmd.add_argument("--brief", action="store_true", help="只要条号、证据级、成本三字、收益、标题")
    list_cmd.add_argument("--value", action="store_true", help="只列性价比线候选：收益大、成本低的正向动作")
    show_cmd = sub.add_parser("show")
    show_cmd.add_argument("ids", nargs="+")
    grep_cmd = sub.add_parser("grep")
    grep_cmd.add_argument("words", nargs="+")
    args = parser.parse_args()

    if args.cmd == "sync":
        sync()
        return
    entries = load()
    if args.cmd == "sections":
        seen = {}
        for entry in entries:
            seen.setdefault(entry["section"], [entry["section_title"], 0])[1] += 1
        for no, (title, count) in sorted(seen.items()):
            print(f"{no:>2}. {title}（{count} 条）")
    elif args.cmd == "list":
        wanted = {int(x) for x in args.sections.split(",") if x.strip()}
        render = brief if args.brief else compact
        for entry in entries:
            if (not wanted or entry["section"] in wanted) and (not args.value or is_value_action(entry)):
                print(render(entry))
    elif args.cmd == "show":
        by_id = {entry["id"]: entry for entry in entries}
        for entry_id in args.ids:
            print(full(by_id[entry_id]) if entry_id in by_id else f"### {entry_id} 不存在", end="\n\n")
    elif args.cmd == "grep":
        for entry in entries:
            haystack = entry["title"] + entry.get("说人话", "")
            if any(word in haystack for word in args.words):
                print(compact(entry))


if __name__ == "__main__":
    main()
