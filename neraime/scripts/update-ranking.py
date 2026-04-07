#!/usr/bin/env python3
"""
DMMぱちタウンからパチスロ勝率ランキングを取得し、
machines.jsonの並び順を更新するスクリプト。
GitHub Actionsで毎日実行される。
"""

import json
import re
import urllib.request

RANKING_URL = "https://p-town.dmm.com/machines/popularity/slot"
MACHINES_JSON = "neraime/data/machines.json"


def fetch_ranking():
    """DMMぱちタウンからパチスロ勝率ランキングを取得"""
    req = urllib.request.Request(
        RANKING_URL,
        headers={"User-Agent": "Mozilla/5.0"}
    )
    with urllib.request.urlopen(req, timeout=15) as res:
        html = res.read().decode("utf-8")

    # 「パチスロ人気機種」以降の機種名を抽出
    idx = html.find("パチスロ人気機種")
    if idx < 0:
        print("Warning: popularity section not found")
        return []

    section_html = html[idx:]
    pattern = r'<p class="title">([^<]+)</p>'
    matches = re.findall(pattern, section_html)
    # 「パチスロ人気機種」自体を除外
    matches = [m for m in matches if "人気機種" not in m]

    # ナビゲーション項目を除外
    ignore = {"店舗", "取材", "レポート", "ランキング", "看板", "グランド",
              "機種情報", "カレンダー", "天井情報", "ボーダー", "検定",
              "メーカー", "特集", "動画", "ブログ", "ぱちモ", "コミュニティ",
              "業界", "人気機種"}

    # 重複除去しつつ順番維持
    seen = set()
    ranking = []
    for name in matches:
        name = name.strip()
        if not name or name in seen:
            continue
        if any(kw in name for kw in ignore):
            continue
        seen.add(name)
        ranking.append(name)

    return ranking


def normalize(name):
    """機種名の表記揺れを吸収するための正規化"""
    n = name.replace("　", "").replace(" ", "").lower()
    for prefix in ["l", "p", "pa", "スマスロ", "パチスロ"]:
        if n.startswith(prefix):
            n = n[len(prefix):]
    return n


def update_machines_order(ranking):
    """machines.jsonの並び順をランキング順に更新"""
    with open(MACHINES_JSON, "r", encoding="utf-8") as f:
        machines = json.load(f)

    rank_map = {}
    for i, name in enumerate(ranking):
        rank_map[normalize(name)] = i

    for m in machines:
        norm = normalize(m["name"])
        m["_rank"] = 9999
        if norm in rank_map:
            m["_rank"] = rank_map[norm]
        else:
            for rname, rindex in rank_map.items():
                if rname in norm or norm in rname:
                    m["_rank"] = rindex
                    break

    machines.sort(key=lambda m: m["_rank"])

    for m in machines:
        del m["_rank"]

    with open(MACHINES_JSON, "w", encoding="utf-8") as f:
        json.dump(machines, f, ensure_ascii=False, indent=2)

    return machines


if __name__ == "__main__":
    print("Fetching ranking from DMMぱちタウン...")
    ranking = fetch_ranking()
    print(f"Got {len(ranking)} machines in ranking:")
    for i, name in enumerate(ranking[:20]):
        print(f"  {i+1}. {name}")

    print("\nUpdating machines.json order...")
    machines = update_machines_order(ranking)
    print("New order:")
    for i, m in enumerate(machines):
        print(f"  {i+1}. {m['name']}")

    print("\nDone!")
