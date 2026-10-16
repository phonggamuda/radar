#!/usr/bin/env python3
"""
TopGit Radar v4.0 - All-in-One Standalone GitHub Actions Scanner
Nâng cấp toàn diện:
1. Dịch thuật độc bản 100% Tiếng Việt cho từng kho mã nguồn (Batch Gemini 3.8 Flash + Google GTX Translate + Phân tích ngữ cảnh sâu).
   Tự động phát hiện và dịch lại toàn bộ các kho cũ đang bị trùng lặp câu mô tả chung chung.
2. Hệ thống Phát hiện Tăng trưởng Sao Đột biến (Star Spike & 3-Day Comparison):
   Lưu lịch sử điểm sao (star_history), tự động làm mới điểm sao định kỳ và so sánh mức tăng trưởng sau 3 ngày
   để tìm ra các công cụ đang tăng vọt (🚀 TĂNG ĐỘT BIẾN) hoặc đang tăng đều (📈 ĐANG TĂNG).
"""

import os
import sys
import re
import json
import time
import urllib.parse
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

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
    ("featured_reviews", "https://topgit.dev/reviews", "TopGit Bài Đánh Giá Nổi Bật"),
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

# Các câu mẫu chung chung từ phiên bản cũ cần được phát hiện và dịch lại độc bản
OLD_GENERIC_SUMMARIES = {
    "Công cụ ứng dụng và tích hợp mô hình OpenAI ChatGPT vào trò chơi, tác vụ hoặc tiện ích mở rộng.",
    "Bộ mã nguồn và tiện ích xây dựng trên hệ sinh thái mô hình trí tuệ nhân tạo Google Gemini.",
    "Ứng dụng và thư viện hỗ trợ tương tác với mô hình Anthropic Claude.",
    "Trò chơi tương tác 3D WebGL hoặc mã nguồn tạo ra bằng công nghệ sinh mã tự động.",
    "Dự án phần mềm tiện ích mã nguồn mở trên GitHub.",
    "Chưa có bản tóm tắt tiếng Việt.",
    ""
}


def is_generic_summary(summary: Optional[str]) -> bool:
    if not summary:
        return True
    s = summary.strip()
    if s in OLD_GENERIC_SUMMARIES:
        return True
    for g in OLD_GENERIC_SUMMARIES:
        if g and g in s and len(s) < len(g) + 15:
            return True
    return False


def parse_stars(stars_str: str) -> int:
    if not stars_str:
        return 0
    s = str(stars_str).strip().lower().replace(",", "").replace("+", "").replace("stars", "").strip()
    try:
        if "k" in s:
            return int(float(s.replace("k", "")) * 1000)
        if "m" in s:
            return int(float(s.replace("m", "")) * 1000000)
        return int(float(s))
    except Exception:
        return 0


def format_stars_text(stars: int) -> str:
    if stars >= 1000:
        return f"{stars / 1000:.1f}k"
    return str(stars)


def parse_topgit_growth(growth_str: str) -> int:
    """Trích xuất số sao tăng từ chuỗi như '+177/d' hoặc '+520'."""
    if not growth_str:
        return 0
    m = re.search(r"\+\s*(\d+(\.\d+)?)\s*(k)?", str(growth_str).lower())
    if m:
        val = float(m.group(1))
        if m.group(3) == "k":
            val *= 1000
        return int(val)
    return 0


# ============================================================================
# BỘ DỊCH THUẬT ĐỘC BẢN ĐA TẦNG (GOOGLE GTX + GEMINI 3.8 BATCH + PHÂN TÍCH SÂU)
# ============================================================================

def translate_to_vietnamese_gtx(text: str) -> str:
    """Dịch văn bản bất kỳ (Anh, Trung, Nhật...) sang Tiếng Việt tự nhiên qua Google GTX."""
    if not text or not text.strip():
        return ""
    clean = text.strip()[:600]
    # Kiểm tra nếu đã có nhiều dấu tiếng Việt thì không cần dịch lại
    vi_chars = set("ăâđêôơưáàảãạấầẩẫậắằẳẵặéèẻẽẹếềểễệíìỉĩịóòỏõọốồổỗộớờởỡợúùủũụứừửữựýỳỷỹỵ")
    if sum(1 for c in clean.lower() if c in vi_chars) >= 4:
        return clean

    try:
        q = urllib.parse.quote(clean)
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=vi&dt=t&q={q}"
        resp = requests.get(url, headers=HEADERS, timeout=6)
        if resp.status_code == 200:
            data = resp.json()
            if data and isinstance(data, list) and data[0]:
                translated = "".join(part[0] for part in data[0] if part and part[0])
                if translated and translated.strip():
                    return translated.strip()
    except Exception:
        pass
    return ""


def humanize_repo_slug(repo_name: str) -> str:
    """Biến đổi tên slug như 'freestylefly/awesome-gpt-image-2' thành cụm từ dễ hiểu."""
    slug = repo_name.split("/")[-1] if "/" in repo_name else repo_name
    words = re.sub(r"[-_]+", " ", slug)
    return words.strip()


def classify_ecosystem(repo: Dict[str, Any]) -> tuple:
    text = f"{repo.get('repo_name', '')} {repo.get('description', '')} {repo.get('source_section', '')}".lower()
    if any(k in text for k in ["chatgpt", "openai", "gpt-4", "gpt-3", "gpt-image", "sora", "codex", "whisper", "dall-e", "o1-", "o3-"]):
        return "OpenAI / ChatGPT", 1
    if any(k in text for k in ["gemini", "google-gemini", "gemma", "aistudio", "vertex", "deepmind", "notebooklm"]):
        return "Google Gemini", 2
    if any(k in text for k in ["claude", "anthropic", "sonnet", "haiku", "mcp-server", "claude-code"]):
        return "Anthropic Claude", 3
    if any(k in text for k in ["llm", "ai", "agent", "rag", "ollama", "deepseek", "qwen", "llama", "diffusion", "comfyui", "cursor", "v0", "bolt", "prompt"]):
        return "AI Khác", 4
    return "Tiện ích / Game", 5


def build_specific_practical_use(repo: Dict[str, Any], eco: str) -> str:
    text = f"{repo.get('repo_name', '')} {repo.get('description', '')}".lower()
    lang = (repo.get("language") or "").lower()
    name = repo.get("repo_name", "")

    if "prompt" in text:
        return f"Mở kho {name} để tra cứu và sao chép các mẫu câu lệnh (prompts) đã tối ưu, dán trực tiếp vào {eco if 'Tiện ích' not in eco else 'ChatGPT/Gemini'} để khai thác ngay."
    if "mcp" in text:
        return f"Cài đặt làm máy chủ MCP (Model Context Protocol) từ {name} để kết nối AI Agent với công cụ và dữ liệu bên ngoài."
    if any(k in text for k in ["threejs", "webgl", "3d", "canvas"]) or any(k in text for k in ["game", "chess", "rpg", "simulator", "arcade", "puzzle"]):
        if lang in ["javascript", "typescript", "html", "vue", "css"]:
            return f"Tải mã nguồn {name} hoặc chạy trực tiếp trên trình duyệt (npm install && npm run dev / mở index.html) để trải nghiệm game/đồ họa 3D và tùy biến giao diện."
        return f"Clone dự án {name} ({repo.get('language') or 'Code'}) về máy để chạy thử nghiệm cơ chế gameplay và học hỏi thuật toán xử lý trong game."
    if any(k in text for k in ["extension", "plugin", "Tampermonkey", "chrome"]):
        return f"Cài đặt tiện ích mở rộng từ {name} vào trình duyệt để tích hợp trợ lý AI trực tiếp trên các trang web đang lướt."
    if any(k in text for k in ["awesome-", "list", "roadmap", "collection", "curated", "tutorial", "course", "guide"]):
        return f"Dùng {name} làm cẩm nang tra cứu tài liệu, công cụ và lộ trình học tập chọn lọc cho dự án thực tế."
    if any(k in text for k in ["cli", "terminal", "shell", "command"]):
        return f"Cài đặt công cụ dòng lệnh từ {name} và cấu hình API Key để tự động hóa tác vụ ngay trong Terminal."
    if any(k in text for k in ["ui", "chat-ui", "webui", "dashboard", "frontend", "nextjs"]):
        return f"Triển khai giao diện {name} trên localhost hoặc Vercel, điền API Key ({eco}) để có bảng điều khiển AI cá nhân."
    if lang == "python":
        return f"Clone kho {name}, cài đặt qua pip (requirements.txt) và chạy script Python để xử lý tác vụ tự động."
    if lang in ["javascript", "typescript", "html"]:
        return f"Chạy dự án web {name} bằng Node.js hoặc mở trên trình duyệt để tích hợp tính năng vào sản phẩm của bạn."
    return f"Tải mã nguồn {name} trên GitHub, xem hướng dẫn ở README để cấu hình và chạy thử nghiệm."


def build_unique_analysis_for_repo(repo: Dict[str, Any], use_gtx: bool = True) -> Dict[str, Any]:
    """Tạo bản tóm tắt tiếng Việt ĐỘC BẢN cho từng kho dựa trên mô tả thực tế + tên kho + ngôn ngữ."""
    eco, pri = classify_ecosystem(repo)
    repo_name = repo.get("repo_name", "unknown/repo")
    owner = repo.get("owner") or (repo_name.split("/")[0] if "/" in repo_name else "")
    slug_human = humanize_repo_slug(repo_name)
    raw_desc = (repo.get("description") or "").strip()
    lang = repo.get("language") or "Mã nguồn mở"
    section = repo.get("source_section") or "GitHub"

    translated_desc = ""
    if raw_desc and use_gtx:
        translated_desc = translate_to_vietnamese_gtx(raw_desc)

    if translated_desc:
        # Đảm bảo câu dịch có ngữ cảnh riêng biệt của repo
        purpose = f"{translated_desc}"
        if not purpose.endswith("."):
            purpose += "."
        purpose += f" (Dự án {slug_human} của {owner}, phát triển bằng {lang})."
    elif raw_desc:
        # Nếu không gọi được mạng GTX, phân tích từ khóa chi tiết từ raw_desc + slug
        purpose = synthesize_vietnamese_from_keywords(repo_name, raw_desc, lang, eco, section)
    else:
        purpose = synthesize_vietnamese_from_keywords(repo_name, "", lang, eco, section)

    practical = build_specific_practical_use(repo, eco)

    return {
        "purpose_summary": purpose,
        "practical_use": practical,
        "ai_ecosystem": eco,
        "ai_priority": pri
    }


def synthesize_vietnamese_from_keywords(repo_name: str, raw_desc: str, lang: str, eco: str, section: str) -> str:
    """Tổng hợp tiếng Việt chi tiết từ tên repo và từ khóa mô tả khi không có mô tả hoặc offline."""
    owner, _, slug = repo_name.partition("/")
    slug_clean = humanize_repo_slug(slug or repo_name)
    combined = f"{slug} {raw_desc}".lower()

    features = []
    if "prompt" in combined:
        features.append("bộ sưu tập câu lệnh (prompts) chuyên dụng")
    if "image" in combined or "vision" in combined or "draw" in combined or "paint" in combined:
        features.append("xử lý và khởi tạo hình ảnh bằng AI")
    if "video" in combined or "sora" in combined or "movie" in combined:
        features.append("dựng và biên tập video tự động")
    if "voice" in combined or "audio" in combined or "speech" in combined or "tts" in combined:
        features.append("nhận diện và tổng hợp giọng nói")
    if "agent" in combined or "autonomous" in combined or "workflow" in combined:
        features.append("tác nhân AI tự hành (AI Agent) xử lý đa tác vụ")
    if "mcp" in combined:
        features.append("giao thức kết nối ngữ cảnh mô hình (MCP Server)")
    if "threejs" in combined or "3d" in combined or "webgl" in combined:
        features.append("đồ họa 3D tương tác trên trình duyệt (Three.js/WebGL)")
    if "game" in combined or "chess" in combined or "play" in combined or "puzzle" in combined or "rpg" in combined:
        features.append("trò chơi giải trí/giáo dục tương tác")
    if "bot" in combined or "telegram" in combined or "discord" in combined or "wechat" in combined:
        features.append("chatbot tự động tích hợp nền tảng nhắn tin")
    if "rag" in combined or "knowledge" in combined or "pdf" in combined or "doc" in combined:
        features.append("truy xuất tri thức từ tài liệu (RAG)")
    if "code" in combined or "coder" in combined or "dev" in combined or "copilot" in combined:
        features.append("hỗ trợ lập trình và sinh mã nguồn tự động")
    if "ui" in combined or "web" in combined or "dashboard" in combined or "chat" in combined:
        features.append("giao diện tương tác người dùng trực quan")
    if "awesome" in combined:
        features.append("danh sách tổng hợp tài nguyên và công cụ chọn lọc")

    feat_str = ", ".join(features[:3]) if features else f"ứng dụng thuộc chuyên mục {section}"
    if raw_desc:
        return f"Dự án '{slug_clean}' (bởi {owner}) tập trung vào {feat_str} trên nền tảng {eco}, viết bằng {lang}. Nội dung gốc: {raw_desc[:180]}"
    return f"Dự án '{slug_clean}' do {owner} phát triển bằng {lang}, cung cấp giải pháp {feat_str} trong hệ sinh thái {eco}."


def analyze_batch_with_gemini(repos_batch: List[Dict[str, Any]], api_key: str) -> Dict[str, Dict[str, Any]]:
    """Phân tích hàng loạt (Batch 15-20 repo/lần) bằng Gemini 3.8 Flash để tránh chạm giới hạn 15 RPM và tạo mô tả độc bản."""
    if not api_key or not repos_batch:
        return {}

    items_input = []
    for r in repos_batch:
        items_input.append({
            "repo_name": r.get("repo_name"),
            "description": (r.get("description") or "")[:300],
            "language": r.get("language") or "Unknown",
            "topic": r.get("source_section") or ""
        })

    prompt = f"""Bạn là chuyên gia phân tích mã nguồn GitHub. Hãy dịch và phân tích danh sách {len(items_input)} kho mã nguồn dưới đây sang Tiếng Việt.
YÊU CẦU BẮT BUỘC:
1. Mỗi kho mã nguồn PHẢI có "purpose_summary" và "practical_use" HOÀN TOÀN KHÁC NHAU, bám sát vào tên repo và description riêng của kho đó. TUYỆT ĐỐI KHÔNG dùng câu mẫu giống nhau cho nhiều kho.
2. "purpose_summary": Giải thích cụ thể kho này dùng để làm gì bằng tiếng Việt tự nhiên, rõ ràng (1-2 câu).
3. "practical_use": Cách ứng dụng thực tế của riêng kho này (1 câu).
4. "ai_ecosystem": Chọn 1 trong ['OpenAI / ChatGPT', 'Google Gemini', 'Anthropic Claude', 'AI Khác', 'Tiện ích / Game'].
5. "ai_priority": 1 (OpenAI), 2 (Gemini), 3 (Claude), 4 (AI Khác), 5 (Tiện ích/Game).

Danh sách kho cần phân tích:
{json.dumps(items_input, ensure_ascii=False)}

Trả về DUY NHẤT một JSON Object có key là "repo_name" và value là object chứa (purpose_summary, practical_use, ai_ecosystem, ai_priority):
"""
    for m in ["gemini-3.8-flash", "gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.25, "responseMimeType": "application/json"}
        }
        try:
            resp = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=25)
            if resp.status_code == 200:
                data = resp.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                clean_text = re.sub(r"^```json\s*", "", text.strip())
                clean_text = re.sub(r"\s*```$", "", clean_text)
                parsed = json.loads(clean_text)
                if isinstance(parsed, dict):
                    return parsed
            elif resp.status_code == 429:
                time.sleep(2)
                continue
        except Exception:
            continue
    return {}


# ============================================================================
# BỘ THEO DÕI LỊCH SỬ SAO & PHÁT HIỆN TĂNG ĐỘT BIẾN SAU 3 NGÀY
# ============================================================================

def compute_star_growth_metrics(repo: Dict[str, Any], old_repo: Optional[Dict[str, Any]], now_iso: str) -> None:
    """
    Cập nhật lịch sử điểm sao (star_history) và tính toán chênh lệch điểm sao
    so với mốc cũ / mốc 3 ngày trước để phát hiện công cụ tăng đột biến.
    """
    today_date = now_iso[:10]
    current_stars = int(repo.get("stars", 0) or 0)

    # Khôi phục lịch sử sao từ dữ liệu cũ nếu có
    history: List[Dict[str, Any]] = []
    if old_repo:
        old_hist = old_repo.get("star_history")
        if isinstance(old_hist, list):
            history = [dict(h) for h in old_hist if isinstance(h, dict) and "stars" in h]
        # Nếu dữ liệu cũ chưa có mảng star_history, khởi tạo mốc gốc từ old_repo
        if not history:
            old_stars = int(old_repo.get("stars", 0) or 0)
            old_ts = old_repo.get("first_seen_at") or old_repo.get("last_updated_at") or "2026-10-10T06:00:00"
            history.append({
                "date": old_ts[:10],
                "ts": old_ts,
                "stars": old_stars
            })

    # Cập nhật hoặc thêm điểm sao của ngày hôm nay vào history
    if history and history[-1].get("date") == today_date:
        history[-1]["stars"] = current_stars
        history[-1]["ts"] = now_iso
    else:
        history.append({
            "date": today_date,
            "ts": now_iso,
            "stars": current_stars
        })

    # Giữ tối đa 30 mốc ngày gần nhất
    if len(history) > 30:
        history = history[-30:]

    repo["star_history"] = history
    initial_stars = int(history[0].get("stars", current_stars))
    repo["initial_stars"] = initial_stars
    repo["initial_date"] = history[0].get("date", today_date)

    # Tìm mốc so sánh ~3 ngày trước (hoặc mốc cũ gần nhất trước ngày hôm nay)
    target_date_3d = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
    ref_entry = history[0]
    if len(history) >= 2:
        # Tìm mốc có date <= target_date_3d gần nhất, nếu chưa đủ 3 ngày thì lấy mốc đầu tiên (history[0])
        candidates = [h for h in history[:-1] if h.get("date", "") <= target_date_3d]
        if candidates:
            ref_entry = candidates[-1]
        else:
            ref_entry = history[0]

    prev_stars = int(ref_entry.get("stars", current_stars))
    ref_date_str = ref_entry.get("date", today_date)

    # Tính số ngày chênh lệch
    try:
        d1 = datetime.strptime(ref_date_str[:10], "%Y-%m-%d")
        d2 = datetime.strptime(today_date, "%Y-%m-%d")
        days_diff = max((d2 - d1).days, 0)
    except Exception:
        days_diff = 0

    diff_3d = current_stars - prev_stars
    diff_total = current_stars - initial_stars

    # Kiểm tra nếu có thông số tăng trưởng trực tiếp từ TopGit (ví dụ '+177/d')
    topgit_gain = parse_topgit_growth(repo.get("stars_growth", ""))
    if diff_3d == 0 and topgit_gain > 0 and prev_stars == current_stars:
        # Nếu mới quét lần đầu nhưng TopGit báo đang tăng +X sao/ngày
        prev_stars = max(current_stars - topgit_gain, 0)
        diff_3d = topgit_gain
        days_diff = 1

    pct_3d = round((diff_3d / max(prev_stars, 1)) * 100, 1) if prev_stars > 0 and diff_3d != 0 else (100.0 if diff_3d > 0 else 0.0)
    per_day = round(diff_3d / max(days_diff, 1), 1) if diff_3d > 0 else 0.0

    repo["prev_stars"] = prev_stars
    repo["prev_stars_date"] = ref_date_str
    repo["days_compared"] = days_diff
    repo["stars_diff_3d"] = diff_3d
    repo["stars_diff_total"] = diff_total
    repo["stars_growth_pct"] = pct_3d
    repo["stars_per_day"] = per_day

    # Phân loại mức độ tăng trưởng sao để người dùng nhận diện ngay công cụ nào đang tốt lên
    # Đột biến (SPIKE): Tăng >= 30 sao, hoặc (tăng >= 10 sao và tăng >= 15%), hoặc tốc độ >= 15 sao/ngày
    if diff_3d >= 30 or (diff_3d >= 10 and pct_3d >= 15.0) or per_day >= 15.0:
        repo["growth_tier"] = "SPIKE"
        repo["is_star_spike"] = True
        repo["growth_label"] = f"🚀 Tăng đột biến +{diff_3d:,} sao ({'+' + str(pct_3d) + '%' if pct_3d > 0 else ''})"
    elif diff_3d > 0:
        repo["growth_tier"] = "GROWING"
        repo["is_star_spike"] = False
        repo["growth_label"] = f"📈 Đang tăng +{diff_3d:,} sao ({'+' + str(pct_3d) + '%' if pct_3d > 0 else ''})"
    else:
        repo["growth_tier"] = "STABLE"
        repo["is_star_spike"] = False
        repo["growth_label"] = f"➖ Ổn định ({current_stars:,} sao)"


def refresh_existing_repos_stars(existing_map: Dict[str, Dict[str, Any]], already_scraped: set, gh_token: str = "", max_refresh: int = 240) -> int:
    """
    Làm mới điểm sao (và bổ sung description nếu thiếu) cho các kho cũ trong data.json
    bằng cách gộp truy vấn theo lô lên GitHub Search API (20 kho / 1 request).
    Giúp so sánh điểm sao cũ và điểm sao sau 3 ngày một cách chính xác!
    """
    candidates = [
        r for name, r in existing_map.items()
        if name not in already_scraped and "/" in name
    ]
    if not candidates:
        return 0

    # Ưu tiên làm mới các kho đã lâu chưa kiểm tra sao hoặc các kho có nhiều sao / thiếu description
    candidates.sort(key=lambda x: (
        0 if is_generic_summary(x.get("purpose_summary")) else 1,
        x.get("last_star_check_at", ""),
        -int(x.get("stars", 0) or 0)
    ))

    to_refresh = candidates[:max_refresh]
    req_headers = dict(HEADERS)
    if gh_token:
        req_headers["Authorization"] = f"Bearer {gh_token}"
    req_headers["Accept"] = "application/vnd.github.v3+json"

    updated_count = 0
    batch_size = 20
    now_iso = datetime.now().isoformat()

    print(f"\n[*] Đang kiểm tra biến động điểm sao cho {len(to_refresh)} kho mã nguồn cũ...")
    for i in range(0, len(to_refresh), batch_size):
        batch = to_refresh[i:i + batch_size]
        query_parts = [f"repo:{r['repo_name']}" for r in batch if r.get("repo_name")]
        if not query_parts:
            continue
        q_str = " ".join(query_parts)
        api_url = f"https://api.github.com/search/repositories?q={urllib.parse.quote(q_str)}&per_page=30"
        try:
            resp = requests.get(api_url, headers=req_headers, timeout=12)
            if resp.status_code == 200:
                items = resp.json().get("items", [])
                for item in items:
                    full_name = item.get("full_name", "")
                    # Tìm key khớp (không phân biệt hoa thường)
                    match_key = None
                    if full_name in existing_map:
                        match_key = full_name
                    else:
                        fl = full_name.lower()
                        for k in existing_map:
                            if k.lower() == fl:
                                match_key = k
                                break
                    if match_key:
                        old_obj = existing_map[match_key]
                        old_copy = dict(old_obj)
                        new_stars = int(item.get("stargazers_count", old_obj.get("stars", 0)))
                        old_obj["stars"] = new_stars
                        old_obj["stars_text"] = format_stars_text(new_stars)
                        if item.get("description") and not old_obj.get("description"):
                            old_obj["description"] = item.get("description")
                        if item.get("language") and (not old_obj.get("language") or old_obj.get("language") == "Unknown"):
                            old_obj["language"] = item.get("language")
                        old_obj["last_star_check_at"] = now_iso
                        compute_star_growth_metrics(old_obj, old_copy, now_iso)
                        updated_count += 1
            elif resp.status_code == 403:
                # Chạm giới hạn rate limit của GitHub Search
                print("    [!] Chạm giới hạn tốc độ GitHub Search API, dừng làm mới lô tiếp theo.")
                break
            time.sleep(1.2)
        except Exception as e:
            print(f"    [!] Lỗi khi làm mới điểm sao lô {i}: {e}")
            break

    print(f"[+] Đã cập nhật và so sánh điểm sao mới nhất cho {updated_count} kho cũ!")
    return updated_count


# ============================================================================
# CÀO DỮ LIỆU TỪ TOPGIT.DEV & GITHUB SEARCH
# ============================================================================

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

                growth_el = card.find(string=re.compile(r"\+\s*\d+"))
                growth_txt = growth_el.strip() if growth_el else "+Mới"

                desc_el = card.find("p") or card.find("div", class_=re.compile(r"desc|summary|text-sm"))
                desc = desc_el.get_text(strip=True) if desc_el else ""

                lang_el = card.find("span", class_=re.compile(r"language|lang|badge"))
                lang = lang_el.get_text(strip=True) if lang_el else "Unknown"

                stars_num = parse_stars(stars_txt)
                results.append({
                    "repo_name": repo_name,
                    "owner": owner,
                    "repo_slug": repo_slug,
                    "title": repo_name,
                    "description": desc,
                    "stars": stars_num,
                    "stars_text": format_stars_text(stars_num),
                    "stars_growth": growth_txt,
                    "language": lang,
                    "source_platform": "topgit",
                    "source_section": sec_title,
                    "topgit_url": f"https://topgit.dev{href}",
                    "github_url": f"https://github.com/{repo_name}",
                    "hot_alert": "HOT_RED" if stars_num > 500 else "NORMAL"
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
            api_url = f"https://api.github.com/search/repositories?q={requests.utils.quote(query)}&sort=updated&order=desc&per_page=30"
            resp = requests.get(api_url, headers=req_headers, timeout=12)
            if resp.status_code == 200:
                items = resp.json().get("items", [])
                for item in items:
                    name = item.get("full_name")
                    if not name or name in seen:
                        continue
                    seen.add(name)
                    stars = int(item.get("stargazers_count", 0))
                    results.append({
                        "repo_name": name,
                        "owner": item.get("owner", {}).get("login", ""),
                        "repo_slug": item.get("name", ""),
                        "title": name,
                        "description": item.get("description") or "",
                        "stars": stars,
                        "stars_text": format_stars_text(stars),
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
            time.sleep(0.8)
        except Exception as e:
            print(f"    [!] Lỗi tìm kiếm GitHub '{query}': {e}")
    return results


def generate_compact_readme(repositories: List[Dict[str, Any]], update_time: str, new_count: int = 0) -> str:
    """Tạo bảng điều khiển ngắn gọn, có mục Top Công Cụ Tăng Sao Đột Biến."""
    cnt_openai = sum(1 for r in repositories if r.get("ai_priority") == 1)
    cnt_gemini = sum(1 for r in repositories if r.get("ai_priority") == 2)
    cnt_claude = sum(1 for r in repositories if r.get("ai_priority") == 3)
    cnt_other = len(repositories) - cnt_openai - cnt_gemini - cnt_claude

    spikes = [r for r in repositories if r.get("growth_tier") == "SPIKE" or int(r.get("stars_diff_3d", 0) or 0) > 0]
    spikes.sort(key=lambda x: (-int(x.get("stars_diff_3d", 0) or 0), -float(x.get("stars_growth_pct", 0) or 0)))

    spike_lines = []
    for idx, r in enumerate(spikes[:8], 1):
        name = r.get("repo_name", "")
        gh_url = r.get("github_url", f"https://github.com/{name}")
        prev_s = int(r.get("prev_stars", r.get("stars", 0)) or 0)
        curr_s = int(r.get("stars", 0) or 0)
        diff_s = int(r.get("stars_diff_3d", 0) or 0)
        pct_s = r.get("stars_growth_pct", 0)
        purpose = r.get("purpose_summary", "")
        spike_lines.append(
            f"{idx}. **[{name}]({gh_url})** — ⭐ `{prev_s:,}` ➔ **`{curr_s:,}`** (**🚀 +{diff_s:,} sao / +{pct_s}%**): {purpose}"
        )
    spike_text = "\n".join(spike_lines) if spike_lines else "*(Đang tích lũy mốc lịch sử sao qua các ngày để so sánh)*"

    newest_samples = [r for r in repositories if r.get("is_new_in_last_scan")][:5]
    if not newest_samples:
        newest_samples = repositories[:5]

    preview_lines = []
    for idx, r in enumerate(newest_samples, 1):
        name = r.get("repo_name", "")
        gh_url = r.get("github_url", f"https://github.com/{name}")
        stars = r.get("stars_text", "0")
        purpose = r.get("purpose_summary", "")
        badge = "🟢 OpenAI" if r.get("ai_priority") == 1 else ("🔵 Gemini" if r.get("ai_priority") == 2 else ("🟠 Claude" if r.get("ai_priority") == 3 else "🟣 AI Khác"))
        preview_lines.append(f"{idx}. **[{name}]({gh_url})** ({badge} | ⭐ {stars}): {purpose}")

    preview_text = "\n".join(preview_lines) if preview_lines else "Đang cập nhật kho mới."

    md = f"""# 📡 TopGit Radar v4.0 - Bảng Điều Khiển & Phát Hiện Đột Biến Sao

> **Hệ thống tự động truy quét GitHub & TopGit.dev, dịch độc bản 100% Tiếng Việt và theo dõi biến động điểm sao.**
> **Mở ứng dụng Web: [https://phonggamuda.github.io/radar/](https://phonggamuda.github.io/radar/)**

[![Web App](https://img.shields.io/badge/Truy_C%E1%BA%ADp-Web_App_Mobile-0284c7?style=for-the-badge&logo=google-chrome&logoColor=white)](https://phonggamuda.github.io/radar/)
[![GitHub Actions](https://img.shields.io/badge/Tr%E1%BA%A1ng_Th%C3%A1i-T%E1%BB%B1_%C4%90%E1%BB%99ng_Qu%C3%A9t-emerald?style=for-the-badge&logo=githubactions&logoColor=white)](https://github.com/phonggamuda/radar/actions)

---

### 🌐 MỞ GIAO DIỆN WEB ĐỂ LỌC CÔNG CỤ TĂNG SAO ĐỘT BIẾN
👉 **Bấm vào đây để mở:** **[https://phonggamuda.github.io/radar/](https://phonggamuda.github.io/radar/)**

---

## 📊 THỐNG KÊ KHO DỮ LIỆU TÍCH LŨY
- **Thời gian cập nhật:** `{update_time}` (Phát hiện mới: **{new_count}** kho | Đang tăng sao: **{len(spikes)}** kho).
- **Tổng số kho mã nguồn tích lũy:** **{len(repositories)} kho**.

| Hệ Sinh Thái AI | Độ Ưu Tiên | Số Lượng Repo | Ghi Chú |
| :--- | :---: | :---: | :--- |
| 🟢 **OpenAI / ChatGPT** | #1 | **{cnt_openai}** | Game ChatGPT, Prompt Engineering, Plugin |
| 🔵 **Google Gemini** | #2 | **{cnt_gemini}** | Gemini Pro, Multimodal, SDK |
| 🟠 **Anthropic Claude** | #3 | **{cnt_claude}** | Claude Sonnet, Artifacts, MCP |
| 🟣 **AI Khác & Tiện ích** | #4 / #5 | **{cnt_other}** | Three.js 3D, Game HTML5, Sinh mã |

---

## 🚀 TOP CÔNG CỤ TĂNG SAO ĐỘT BIẾN ĐÁNG QUAN TÂM
{spike_text}

---

## 🔥 ĐIỂM TIN 5 KHO MỚI QUÉT GẦN NHẤT
{preview_text}

---
👉 *Xem toàn bộ {len(repositories)} kho mã nguồn đầy đủ tại: [https://phonggamuda.github.io/radar/](https://phonggamuda.github.io/radar/)*
"""
    return md


def main():
    print("=" * 70)
    print("🚀 TOPGIT RADAR v4.0 - DỊCH ĐỘC BẢN & PHÁT HIỆN TĂNG SAO ĐỘT BIẾN")
    print(f"🕒 Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    gh_token = os.environ.get("GH_TOKEN", "").strip()
    now_iso = datetime.now().isoformat()

    # 1. Nạp dữ liệu cũ từ data.json để tích lũy và đối chiếu lịch sử sao
    existing_map: Dict[str, Dict[str, Any]] = {}
    if os.path.exists("data.json"):
        try:
            with open("data.json", "r", encoding="utf-8") as f:
                old_data = json.load(f)
                old_list = old_data.get("repositories", [])
                for item in old_list:
                    item["is_new_in_last_scan"] = False
                    rname = item.get("repo_name", "").strip()
                    if rname:
                        existing_map[rname] = item
            print(f"[*] Đã nạp {len(existing_map)} kho mã nguồn từ data.json để đối chiếu lịch sử sao!")
        except Exception as e:
            print(f"[!] Không thể đọc data.json cũ: {e}")

    # 2. Cào dữ liệu mới từ TopGit & GitHub
    topgit_list = scrape_topgit()
    github_list = scrape_github_topics(gh_token)
    all_raw = topgit_list + github_list

    seen = set()
    scraped_repos = []
    for r in all_raw:
        n = r.get("repo_name", "").strip()
        if n and n not in seen:
            seen.add(n)
            scraped_repos.append(r)

    print(f"\n[+] Thu thập được {len(scraped_repos)} kho trong phiên quét này.")

    # 3. Hợp nhất dữ liệu mới và tính toán biến động điểm sao (Star Growth Metrics)
    new_count = 0
    repos_needing_translation: List[Dict[str, Any]] = []

    for r in scraped_repos:
        rname = r["repo_name"]
        old_item = existing_map.get(rname)

        r["is_new_in_last_scan"] = True
        r["last_updated_at"] = now_iso
        r["last_star_check_at"] = now_iso

        if old_item is None:
            r["first_seen_at"] = now_iso
            r["is_new_discovery"] = True
            new_count += 1
            compute_star_growth_metrics(r, None, now_iso)
            repos_needing_translation.append(r)
        else:
            r["first_seen_at"] = old_item.get("first_seen_at", now_iso)
            r["is_new_discovery"] = False
            if not r.get("description") and old_item.get("description"):
                r["description"] = old_item.get("description")
            # Giữ lại bản dịch cũ nếu bản dịch cũ ĐÃ LÀ ĐỘC BẢN (không phải câu mẫu chung chung)
            old_summary = old_item.get("purpose_summary", "")
            if not is_generic_summary(old_summary):
                r["purpose_summary"] = old_summary
                r["practical_use"] = old_item.get("practical_use", "")
                r["ai_ecosystem"] = old_item.get("ai_ecosystem", "AI Khác")
                r["ai_priority"] = old_item.get("ai_priority", 4)
            else:
                repos_needing_translation.append(r)

            compute_star_growth_metrics(r, old_item, now_iso)

        existing_map[rname] = r

    # 4. Làm mới điểm sao cho các kho cũ trong data.json (để phát hiện tăng đột biến sau 3 ngày)
    refresh_existing_repos_stars(existing_map, seen, gh_token, max_refresh=200)

    # 5. Tìm tất cả các kho cũ trong existing_map đang bị câu dịch trùng lặp để dịch lại độc bản!
    for rname, item in existing_map.items():
        # Đảm bảo mọi kho cũ đều có thông số star_history chuẩn
        if "star_history" not in item or "growth_tier" not in item:
            compute_star_growth_metrics(item, item, now_iso)
        if is_generic_summary(item.get("purpose_summary")) and item not in repos_needing_translation:
            repos_needing_translation.append(item)

    print(f"\n[*] Tổng số kho cần dịch và phân tích độc bản: {len(repos_needing_translation)}")

    # 6. Dịch thuật độc bản bằng Gemini 3.8 Batch + Google GTX + Phân tích ngữ cảnh
    if gemini_key and repos_needing_translation:
        print("[*] Đang chạy phân tích hàng loạt với Gemini 3.8 Flash (20 kho/lô)...")
        batch_size = 20
        # Ưu tiên gọi Gemini cho tối đa 200 kho đầu tiên để đảm bảo thời gian chạy nhanh
        gemini_targets = repos_needing_translation[:200]
        for i in range(0, len(gemini_targets), batch_size):
            batch = gemini_targets[i:i + batch_size]
            batch_res = analyze_batch_with_gemini(batch, gemini_key)
            for r in batch:
                rname = r["repo_name"]
                if rname in batch_res and isinstance(batch_res[rname], dict):
                    info = batch_res[rname]
                    if info.get("purpose_summary") and not is_generic_summary(info.get("purpose_summary")):
                        r["purpose_summary"] = info["purpose_summary"]
                        r["practical_use"] = info.get("practical_use") or build_specific_practical_use(r, info.get("ai_ecosystem", ""))
                        r["ai_ecosystem"] = info.get("ai_ecosystem") or classify_ecosystem(r)[0]
                        r["ai_priority"] = int(info.get("ai_priority") or classify_ecosystem(r)[1])
            time.sleep(1.5)

    # Với các kho còn lại (hoặc khi Gemini không trả về), dịch độc bản bằng Google GTX + Context Analyzer
    gtx_budget = 250  # Số lượng gọi GTX trực tiếp mỗi lần chạy
    gtx_used = 0
    for r in repos_needing_translation:
        if is_generic_summary(r.get("purpose_summary")):
            use_network_gtx = (gtx_used < gtx_budget) and bool(r.get("description"))
            if use_network_gtx:
                gtx_used += 1
            unique_info = build_unique_analysis_for_repo(r, use_gtx=use_network_gtx)
            r.update(unique_info)

    # 7. Sắp xếp: Mặc định đưa các mục mới quét lên đầu, sau đó ưu tiên các mục tăng sao mạnh
    final_repos = list(existing_map.values())
    final_repos.sort(key=lambda x: (
        0 if x.get("is_new_in_last_scan") else 1,
        -int(x.get("stars_diff_3d", 0) or 0),
        x.get("ai_priority", 5),
        -int(x.get("stars", 0) or 0)
    ))

    spike_cnt = sum(1 for r in final_repos if r.get("growth_tier") == "SPIKE")
    growing_cnt = sum(1 for r in final_repos if int(x_diff := r.get("stars_diff_3d", 0) or 0) > 0)

    print(f"[+] Hoàn tất xử lý {len(final_repos)} kho! (Tăng đột biến: {spike_cnt} | Đang tăng sao: {growing_cnt})")

    # 8. Lưu ra data.json và README.md
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump({
            "exported_at": now_str,
            "total": len(final_repos),
            "spike_count": spike_cnt,
            "growing_count": growing_cnt,
            "repositories": final_repos
        }, f, ensure_ascii=False, indent=2)

    md_content = generate_compact_readme(final_repos, now_str, new_count)
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(md_content)

    print("\n" + "=" * 70)
    print(f"✅ THÀNH CÔNG! Đã lưu {len(final_repos)} kho vào data.json & README.md!")
    print("=" * 70)


if __name__ == "__main__":
    main()
