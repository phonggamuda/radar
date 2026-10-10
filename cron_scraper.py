#!/usr/bin/env python3
"""
Headless Automated Scanner for Pure GitHub Automation.
Outputs:
1. data.json (for web reader)
2. BAO_CAO_HOM_NAY.md (for reading directly inside GitHub / GitHub Mobile App)
3. index.html (standalone mobile reader)
"""

import os
import sys
import json
from datetime import datetime

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

import scraper
import ai_engine

def generate_markdown_report(repositories, exported_time):
    md = f"""# 📡 BÁO CÁO TOPGIT RADAR - {exported_time}
> **Tổng số kho mã nguồn đã quét:** {len(repositories)} | **Phân loại AI:** OpenAI (#1) >> Gemini (#2) >> Claude (#3)

---

## 📊 THỐNG KÊ NHANH
"""
    cnt_openai = sum(1 for r in repositories if 'openai' in (r.get('ai_ecosystem') or '').lower() or 'chatgpt' in (r.get('ai_ecosystem') or '').lower())
    cnt_gemini = sum(1 for r in repositories if 'gemini' in (r.get('ai_ecosystem') or '').lower() or 'google' in (r.get('ai_ecosystem') or '').lower())
    cnt_claude = sum(1 for r in repositories if 'claude' in (r.get('ai_ecosystem') or '').lower() or 'anthropic' in (r.get('ai_ecosystem') or '').lower())
    cnt_other = len(repositories) - cnt_openai - cnt_gemini - cnt_claude

    md += f"- 🟢 **OpenAI / ChatGPT (#1):** {cnt_openai} repo
"
    md += f"- 🔵 **Google Gemini (#2):** {cnt_gemini} repo
"
    md += f"- 🟠 **Anthropic Claude (#3):** {cnt_claude} repo
"
    md += f"- 🟣 **AI Khác & Tiện ích (#4/#5):** {cnt_other} repo

---

"

    md += "## 🚀 DANH SÁCH CHI TIẾT CÁC KHO MÃ NGUỒN

"

    for idx, r in enumerate(repositories, 1):
        name = r.get('repo_name', 'N/A')
        gh_url = r.get('github_url') or f"https://github.com/{name}"
        eco = r.get('ai_ecosystem', 'Không rõ')
        stars = r.get('stars_text') or str(r.get('stars', 0))
        growth = f" ({r.get('stars_growth')})" if r.get('stars_growth') else ""
        lang = f" | Ngôn ngữ: `{r.get('language')}`" if r.get('language') else ""
        purpose = r.get('purpose_summary') or 'Chưa có bản tóm tắt tiếng Việt.'
        practical = r.get('practical_use') or 'Dùng tham khảo mã nguồn, cắm API hoặc chạy theo README.'

        # Emoji badge
        badge = "🟢 [OpenAI #1]" if 'openai' in eco.lower() or 'chatgpt' in eco.lower() else (
            "🔵 [Gemini #2]" if 'gemini' in eco.lower() or 'google' in eco.lower() else (
                "🟠 [Claude #3]" if 'claude' in eco.lower() or 'anthropic' in eco.lower() else "🟣 [AI Khác]"
            )
        )

        md += f"### {idx}. [{name}]({gh_url})
"
        md += f"- **Phân loại:** {badge} **{eco}** | ⭐ **{stars} stars**{growth}{lang}
"
        md += f"- **🎯 Công cụ phục vụ gì:** {purpose}
"
        md += f"- **💡 Khả năng ứng dụng:** {practical}
"
        md += f"- **🔗 Link trực tiếp:** [{gh_url}]({gh_url})

---

"

    return md

def run_scan():
    print("=" * 65)
    print("[*] BAT DAU QUET TU DONG TREN GITHUB ACTIONS")
    print(f"[*] Thoi gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 65)

    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    github_token = os.environ.get("GH_TOKEN", "").strip()

    # 1. Scrape TopGit.dev
    print("
[*] [1/2] Dang quet TopGit.dev...")
    topgit_repos = scraper.scrape_all_topgit()

    # 2. Scrape GitHub topics
    print("
[*] [2/2] Dang quet GitHub.com search topics...")
    gh_repos = scraper.scrape_github_search_topics(token=github_token, max_items_per_query=6)

    all_raw = topgit_repos + gh_repos
    seen = set()
    unique_repos = []
    for r in all_raw:
        n = r.get("repo_name", "").strip()
        if n and n not in seen:
            seen.add(n)
            unique_repos.append(r)

    print(f"
[+] Tong so repo duy nhat tim thay: {len(unique_repos)}")

    # 3. Process with AI / Translation
    enriched = []
    for i, r in enumerate(unique_repos, 1):
        if gemini_key:
            res = ai_engine.analyze_with_gemini(r, gemini_key, model="gemini-3.8-flash")
        else:
            res = ai_engine.analyze_with_local_engine(r)
        r.update(res)
        r["last_updated_at"] = datetime.now().isoformat()
        enriched.append(r)

    # Sort
    enriched.sort(key=lambda x: (x.get("ai_priority", 5), -int(x.get("stars", 0) or 0)))
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # 4. Save data.json
    output_json = os.path.join(CURRENT_DIR, "data.json")
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump({
            "exported_at": datetime.now().isoformat(),
            "total": len(enriched),
            "repositories": enriched
        }, f, ensure_ascii=False, indent=2)

    # 5. Save BAO_CAO_HOM_NAY.md
    output_md = os.path.join(CURRENT_DIR, "BAO_CAO_HOM_NAY.md")
    with open(output_md, "w", encoding="utf-8") as f:
        f.write(generate_markdown_report(enriched, now_str))

    # Also update README.md so opening the repo immediately shows the report!
    readme_path = os.path.join(CURRENT_DIR, "README.md")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(generate_markdown_report(enriched, now_str))

    print(f"
[✓] DA TAO THANH CONG: data.json va BAO_CAO_HOM_NAY.md ({len(enriched)} repos)!")

if __name__ == "__main__":
    run_scan()
