#!/usr/bin/env python3
"""
DMMぱちタウンからパチスロ勝率ランキングを取得し、
machines.jsonの並び順を更新するスクリプト。
GitHub Actionsで毎日実行される。
"""

import json
import re
import urllib.request

RANKING_URL = "https://p-town.dmm.com/rankings/machines/slot"
MACHINES_JSON = "neraime/data/machines.json"


def fetch_ranking():
    """DMMぱちタウンからパチスロ勝率ランキングを取得"""
    req = urllib.request.Request(
        RANKING_URL,
        headers={"User-Agent": "Mozilla/5.0"}
    )
    with urllib.request.urlopen(req, timeout=15) as res:
        html = res.read().decode("utf-8")

    # ランキングセクション(list-winningranking)内の機種名だけ抽出
    ranking_section = re.search(
        r'list-winningranking -machine.*?</ol>', html, re.DOTALL
    )
    if not ranking_section:
        print("Warning: ranking section not found")
        return []

    section_html = ranking_section.group(0)
    pattern = r'<p class="title">([^<]+)</p>'
    matches = re.findall(pattern, section_html)

    # 重複除去しつつ順番維持
    seen = set()
    ranking = []
    for name in matches:
        name = name.strip()
        if name and name not in seen:
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
