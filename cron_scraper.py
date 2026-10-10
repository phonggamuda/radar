#!/usr/bin/env python3
"""
TopGit Radar - All-in-One Standalone GitHub Actions Scanner
Tự động cào dữ liệu từ TopGit.dev + GitHub Search, phân tích và dịch 100% tiếng Việt
bằng Google Gemini 3.8 Flash, tự động xuất kết quả ra README.md và data.json.
"""

import os
import sys
import re
import json
import time
from datetime import datetime
from typing import Dict, Any, List

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "vi,en-US;q=0.9,en;q=0.8"
}

TOPGIT_SECTIONS = [
    ("trending_daily", "https://topgit.dev/trending/daily", "TopGit Thịnh hành Hôm nay"),
    ("trending_weekly", "https://topgit.dev/trending/weekly", "TopGit Thịnh hành Tuần"),
    ("trending_monthly", "https://topgit.dev/trending/monthly", "TopGit Thịnh hành Tháng"),
    ("recently_added", "https://topgit.dev/", "TopGit Mới Thêm Gần Đây"),
]

GITHUB_TOPICS = [
    ("gh_chatgpt_games", "chatgpt-games", "GitHub: Game ChatGPT"),
    ("gh_ai_generated", "ai-generated", "GitHub: Sinh mã AI"),
    ("gh_threejs", "threejs", "GitHub: 3D Three.js WebGL"),
    ("gh_awesome_prompts", "awesome chatgpt prompts", "GitHub: Câu lệnh AI Prompts"),
    ("gh_gemini_pro", "gemini-pro", "GitHub: Google Gemini Pro"),
    ("gh_google_gemini", "google-gemini", "GitHub: Hệ sinh thái Gemini"),
    ("gh_educational_game", "educational-game", "GitHub: Game Giáo Dục"),
    ("gh_html5_game", "html5-game", "GitHub: Game HTML5"),
    ("gh_ai_generated_code", "ai-generated-code", "GitHub: Mã nguồn do AI tạo")
]

def parse_stars(stars_str: str) -> int:
    if not stars_str:
        return 0
    s = stars_str.strip().lower().replace(",", "").replace("+", "").replace("stars", "").strip()
    try:
        if "k" in s:
            return int(float(s.replace("k", "")) * 1000)
        return int(float(s))
    except Exception:
        return 0

def scrape_topgit() -> List[Dict[str, Any]]:
    results = []
    seen = set()
    for sec_id, url, sec_title in TOPGIT_SECTIONS:
        try:
            print(f"[*] Đang cào TopGit: {sec_title} ({url})...")
            resp = requests.get(url, headers=HEADERS, timeout=15)
            if resp.status_code != 200:
                print(f"    [!] HTTP {resp.status_code} khi tải {url}")
                continue
            soup = BeautifulSoup(resp.text, "html.parser")
            cards = soup.find_all("div", class_=re.compile(r"repo-card|repository-item|border"))
            for card in cards:
                repo_link = card.find("a", href=re.compile(r"^/repo/"))
                if not repo_link:
                    continue
                href = repo_link["href"]
                slug_match = re.match(r"^/repo/([^/]+)/([^/]+)", href)
                if not slug_match:
                    continue
                owner, repo_slug = slug_match.group(1), slug_match.group(2)
                repo_name = f"{owner}/{repo_slug}"
                if repo_name in seen:
                    continue
                seen.add(repo_name)

                stars_el = card.find(string=re.compile(r"\b\d+(\.\d+)?[kK]?\b"))
                stars_txt = stars_el.strip() if stars_el else "0"
                
                desc_el = card.find("p") or card.find("div", class_=re.compile(r"desc|summary|text-sm"))
                desc = desc_el.get_text(strip=True) if desc_el else ""

                lang_el = card.find("span", class_=re.compile(r"language|lang|badge"))
                lang = lang_el.get_text(strip=True) if lang_el else "Unknown"

                results.append({
                    "repo_name": repo_name,
                    "owner": owner,
                    "repo_slug": repo_slug,
                    "title": repo_name,
                    "description": desc,
                    "stars": parse_stars(stars_txt),
                    "stars_text": stars_txt,
                    "stars_growth": "+Mới",
                    "language": lang,
                    "source_platform": "topgit",
                    "source_section": sec_title,
                    "topgit_url": f"https://topgit.dev{href}",
                    "github_url": f"https://github.com/{repo_name}",
                    "hot_alert": "HOT_RED" if parse_stars(stars_txt) > 500 else "NORMAL"
                })
        except Exception as e:
            print(f"    [!] Lỗi khi cào TopGit {sec_id}: {e}")
    return results

def scrape_github_topics(gh_token: str = "") -> List[Dict[str, Any]]:
    results = []
    seen = set()
    req_headers = dict(HEADERS)
    if gh_token:
        req_headers["Authorization"] = f"Bearer {gh_token}"
    req_headers["Accept"] = "application/vnd.github.v3+json"

    for sec_id, query, sec_title in GITHUB_TOPICS:
        try:
            print(f"[*] Đang tìm kiếm GitHub: '{query}'...")
            api_url = f"https://api.github.com/search/repositories?q={requests.utils.quote(query)}&sort=updated&order=desc&per_page=6"
            resp = requests.get(api_url, headers=req_headers, timeout=12)
            if resp.status_code == 200:
                items = resp.json().get("items", [])
                for item in items:
                    name = item.get("full_name")
                    if not name or name in seen:
                        continue
                    seen.add(name)
                    stars = item.get("stargazers_count", 0)
                    results.append({
                        "repo_name": name,
                        "owner": item.get("owner", {}).get("login", ""),
                        "repo_slug": item.get("name", ""),
                        "title": name,
                        "description": item.get("description") or "",
                        "stars": stars,
                        "stars_text": f"{stars/1000:.1f}k" if stars >= 1000 else str(stars),
                        "stars_growth": "+Mới",
                        "language": item.get("language") or "Other",
                        "source_platform": "github",
                        "source_section": sec_title,
                        "topgit_url": f"https://topgit.dev/repo/{name}",
                        "github_url": item.get("html_url") or f"https://github.com/{name}",
                        "hot_alert": "HOT_RED" if stars > 500 else "NORMAL"
                    })
            else:
                print(f"    [!] GitHub API phản hồi mã {resp.status_code}")
        except Exception as e:
            print(f"    [!] Lỗi tìm kiếm GitHub '{query}': {e}")
    return results

def analyze_with_gemini(repo: Dict[str, Any], api_key: str) -> Dict[str, Any]:
    prompt = f"""
Bạn là chuyên gia thẩm định công nghệ GitHub. Hãy phân tích kho mã nguồn sau:
- Tên Repository: {repo.get('repo_name')}
- Mô tả gốc: {repo.get('description')}
- Ngôn ngữ: {repo.get('language')}
- Số sao: {repo.get('stars_text')}

YÊU CẦU:
1. "purpose_summary": DỊCH VÀ DIỄN ĐẠT 100% SANG TIẾNG VIỆT (1-2 câu ngắn gọn). Nêu rõ công cụ phục vụ gì.
2. "practical_use": Nêu cách người dùng có thể xài được ngay (chạy web, copy prompt, cắm API...).
3. "ai_ecosystem": Chọn chính xác 1 trong: 'OpenAI / ChatGPT' | 'Google Gemini' | 'Anthropic Claude' | 'AI Khác' | 'Tiện ích / Game'
4. "ai_priority": 1 (nếu là OpenAI), 2 (nếu là Gemini), 3 (nếu là Claude), 4 (nếu là AI Khác), 5 (nếu là Tiện ích/Khác)

Trả về DUY NHẤT một chuỗi JSON hợp lệ:
{{
  "purpose_summary": "Tóm tắt tiếng Việt",
  "practical_use": "Cách sử dụng thực tế",
  "ai_ecosystem": "OpenAI / ChatGPT",
  "ai_priority": 1
}}
"""
    # Try gemini-3.8-flash first
    for m in ["gemini-3.8-flash", "gemini-3.8-pro", "gemini-2.0-flash", "gemini-1.5-flash"]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"}
        }
        try:
            r = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=12)
            if r.status_code == 200:
                data = r.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                clean_text = re.sub(r"^```json\s*", "", text.strip())
                clean_text = re.sub(r"\s*```$", "", clean_text)
                return json.loads(clean_text)
        except Exception:
            continue
    return analyze_with_local(repo)

def analyze_with_local(repo: Dict[str, Any]) -> Dict[str, Any]:
    text = (repo.get("repo_name", "") + " " + repo.get("description", "")).lower()
    if any(k in text for k in ["chatgpt", "openai", "gpt-4", "gpt-3", "gpt"]):
        eco = "OpenAI / ChatGPT"
        pri = 1
        purpose = "Công cụ ứng dụng và tích hợp mô hình OpenAI ChatGPT vào trò chơi, tác vụ hoặc tiện ích mở rộng."
        use = "Copy prompt mẫu, tích hợp OpenAI API key để sử dụng ngay."
    elif any(k in text for k in ["gemini", "google-gemini", "gemma"]):
        eco = "Google Gemini"
        pri = 2
        purpose = "Bộ mã nguồn và tiện ích xây dựng trên hệ sinh thái mô hình trí tuệ nhân tạo Google Gemini."
        use = "Điền Gemini API Key từ Google AI Studio để kết nối và chạy ứng dụng."
    elif any(k in text for k in ["claude", "anthropic"]):
        eco = "Anthropic Claude"
        pri = 3
        purpose = "Ứng dụng và thư viện hỗ trợ tương tác với mô hình Anthropic Claude."
        use = "Tích hợp Claude API Key hoặc chạy lệnh theo tài liệu hướng dẫn."
    elif any(k in text for k in ["ai-generated", "threejs", "game", "webgl"]):
        eco = "AI Khác"
        pri = 4
        purpose = "Trò chơi tương tác 3D WebGL hoặc mã nguồn tạo ra bằng công nghệ sinh mã tự động."
        use = "Mở file index.html hoặc chạy máy chủ web cục bộ để chơi game trực tiếp."
    else:
        eco = "Tiện ích / Game"
        pri = 5
        purpose = "Dự án phần mềm tiện ích mã nguồn mở trên GitHub."
        use = "Clone mã nguồn về máy tính và chạy theo hướng dẫn trong README."

    return {
        "purpose_summary": purpose,
        "practical_use": use,
        "ai_ecosystem": eco,
        "ai_priority": pri
    }

def generate_markdown(repositories: List[Dict[str, Any]], update_time: str) -> str:
    cnt_openai = sum(1 for r in repositories if r.get("ai_priority") == 1)
    cnt_gemini = sum(1 for r in repositories if r.get("ai_priority") == 2)
    cnt_claude = sum(1 for r in repositories if r.get("ai_priority") == 3)
    cnt_other = len(repositories) - cnt_openai - cnt_gemini - cnt_claude

    md = f"""# 📡 BẢN TIN TOPGIT RADAR - {update_time}
> **Tổng số kho mã nguồn phát hiện:** {len(repositories)} | **Phân loại ưu tiên:** OpenAI (#1) >> Gemini (#2) >> Claude (#3)
> **Động cơ phân tích & dịch thuật:** Google Gemini 3.8 Flash (Tự động cập nhật mỗi ngày)

---

## 📊 THỐNG KÊ HỆ SINH THÁI AI
| Hệ Sinh Thái | Độ Ưu Tiên | Số Lượng Repo | Ghi Chú |
| :--- | :---: | :---: | :--- |
| 🟢 **OpenAI / ChatGPT** | #1 | **{cnt_openai}** | Game ChatGPT, Prompt Engineering, Plugin |
| 🔵 **Google Gemini** | #2 | **{cnt_gemini}** | Gemini Pro, Multimodal, SDK |
| 🟠 **Anthropic Claude** | #3 | **{cnt_claude}** | Claude Sonnet, Artifacts, Tool Use |
| 🟣 **AI Khác & Tiện ích** | #4 / #5 | **{cnt_other}** | Three.js 3D, Game HTML5, Sinh mã |

---

## 🚀 DANH SÁCH CHI TIẾT CÁC KHO MÃ NGUỒN MỚI NHẤT
"""
    for idx, r in enumerate(repositories, 1):
        name = r.get("repo_name", "")
        gh_url = r.get("github_url", f"https://github.com/{name}")
        stars = r.get("stars_text", "0")
        lang = f" | Ngôn ngữ: `{r.get('language')}`" if r.get("language") else ""
        eco = r.get("ai_ecosystem", "")
        pri = r.get("ai_priority", 5)
        purpose = r.get("purpose_summary", "")
        practical = r.get("practical_use", "")

        badge = "🟢 OpenAI #1" if pri == 1 else ("🔵 Gemini #2" if pri == 2 else ("🟠 Claude #3" if pri == 3 else "🟣 AI Khác"))

        md += f"""
### {idx}. [{name}]({gh_url})
- **Phân loại:** **{badge}** ({eco}) | ⭐ **{stars} stars**{lang} | Nguồn: *{r.get('source_section', '')}*
- **🎯 Công cụ phục vụ gì (Tiếng Việt):** {purpose}
- **💡 Khả năng ứng dụng thực tế:** {practical}
- **🔗 Truy cập:** [{gh_url}]({gh_url})

---
"""
    return md

def main():
    print("=" * 65)
    print("🚀 TOPGIT RADAR - TỰ ĐỘNG QUÉT VÀ XUẤT BÁO CÁO GITHUB")
    print(f"🕒 Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 65)

    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    gh_token = os.environ.get("GH_TOKEN", "").strip()

    if gemini_key:
        print(f"[✓] Đã nạp GEMINI_API_KEY ({gemini_key[:6]}...) - Sử dụng Gemini 3.8 Flash!")
    else:
        print("[!] Không tìm thấy GEMINI_API_KEY, kích hoạt bộ dịch tiếng Việt Smart Local Engine.")

    # 1. Scrape
    topgit_list = scrape_topgit()
    github_list = scrape_github_topics(gh_token)
    all_raw = topgit_list + github_list

    # Deduplicate
    seen = set()
    repos = []
    for r in all_raw:
        n = r.get("repo_name", "").strip()
        if n and n not in seen:
            seen.add(n)
            repos.append(r)

    print(f"\n[+] Tổng số kho mã nguồn duy nhất: {len(repos)}")

    # 2. Enrich & Translate
    print("\n[*] Đang dịch tóm tắt sang 100% tiếng Việt...")
    for i, r in enumerate(repos, 1):
        print(f"  -> [{i}/{len(repos)}] Phân tích: {r.get('repo_name')}")
        if gemini_key:
            analysis = analyze_with_gemini(r, gemini_key)
        else:
            analysis = analyze_with_local(r)
        r.update(analysis)

    # Sort
    repos.sort(key=lambda x: (x.get("ai_priority", 5), -int(x.get("stars", 0) or 0)))

    # 3. Export files
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Save data.json
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump({"exported_at": now_str, "total": len(repos), "repositories": repos}, f, ensure_ascii=False, indent=2)

    # Save README.md
    md_content = generate_markdown(repos, now_str)
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(md_content)

    # Save BAO_CAO_HOM_NAY.md
    with open("BAO_CAO_HOM_NAY.md", "w", encoding="utf-8") as f:
        f.write(md_content)

    print("\n" + "=" * 65)
    print(f"✅ HOÀN TẤT! Đã xuất {len(repos)} kho mã nguồn vào README.md và data.json!")
    print("=" * 65)

if __name__ == "__main__":
    main()
