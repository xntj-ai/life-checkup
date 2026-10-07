#!/usr/bin/env python3
"""从 Claude Code 会话记录里量出「这个人亲手敲字的时间分布」，给作息、工时类条目当证据。

只数人类亲手发的消息：跳过工具回传、系统注入（以 < 开头）、子代理、headless（sdk-cli）会话。
口径与局限会随结果一起打印——它量的是「在跟 CC 说话的时间」，不是全部工作时间。

  activity.py                 近 30 天，按北京时间
  activity.py --days 60 --tz 8
"""
import argparse
import collections
import datetime as dt
import glob
import json
import os
from pathlib import Path


def typed_text(message):
    content = message.get("content")
    if isinstance(content, list):
        if any(isinstance(part, dict) and part.get("type") == "tool_result" for part in content):
            return ""
        return " ".join(part.get("text", "") for part in content if isinstance(part, dict))
    return str(content or "")


def iter_typed_times(root, since, tz):
    for path in glob.glob(str(root / "projects" / "*" / "*.jsonl")):
        try:
            if os.path.getmtime(path) < since.timestamp():
                continue
            fh = open(path, encoding="utf-8", errors="ignore")
        except OSError:
            continue
        with fh:
            for line in fh:
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if row.get("type") != "user" or row.get("isMeta") or row.get("isSidechain"):
                    continue
                if row.get("entrypoint") not in ("cli", None):
                    continue
                text = typed_text(row.get("message", {})).strip()
                if not text or text.startswith("<") or not row.get("timestamp"):
                    continue
                when = dt.datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00")).astimezone(tz)
                if when >= since:
                    yield when


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(Path.home() / ".claude"))
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--tz", type=float, default=8, help="UTC 偏移小时数，北京时间为 8")
    args = parser.parse_args()
    tz = dt.timezone(dt.timedelta(hours=args.tz))
    since = dt.datetime.now(tz) - dt.timedelta(days=args.days)

    by_hour = collections.Counter()
    quarter_bins = collections.defaultdict(set)
    for when in iter_typed_times(Path(args.root).expanduser(), since, tz):
        by_hour[when.hour] += 1
        quarter_bins[when.date()].add((when.hour, when.minute // 15))
    total = sum(by_hour.values())
    if not total:
        print("这段时间没有亲手发的消息")
        return

    print(f"# 亲手发消息的时间分布（近 {args.days} 天，UTC{args.tz:+g}，共 {total} 条）\n")
    peak = max(by_hour.values())
    for hour in range(24):
        print(f"{hour:02d} 点 {by_hour[hour]:5d} {'█' * (by_hour[hour] * 40 // peak)}")
    late = sum(by_hour[h] for h in range(0, 6))
    print(f"\n零点到六点占 {late / total:.1%}")
    weekly = collections.defaultdict(float)
    for day, bins in quarter_bins.items():
        year, week, _ = day.isocalendar()
        weekly[f"{year}-W{week:02d}"] += len(bins) / 4
    print("每周「有亲手发消息的 15 分钟格」折合小时：")
    for week, hours in sorted(weekly.items()):
        print(f"  {week}: {hours:.1f} h")
    print("\n口径：一格 15 分钟里发过至少一条就算这格在场。会高估（发一条算 15 分钟），"
          "也会低估（读、想、开会、不经 CC 的工作都不算）。首尾两周通常不满一周。只当方向证据用。")


if __name__ == "__main__":
    main()
