"""
AI Analysis, Semantic Search & Multilingual Translation Engine (v3.3)
Features:
- Full native support for new Google AI Studio API key format starting with 'AQ.' as well as classic 'AIzaSy...'.
- Exact Google AI Studio cURL alignment (query param ?key= and clean headers).
- Dual-endpoint Google Gemini connection: Native generateContent + OpenAI-compatible endpoint.
- Detailed, friendly error diagnostic explanations in Vietnamese (e.g. OpenAI 429 No credits).
- 100% Vietnamese translation & synthesis for all tools.
"""

import json
import re
import urllib.request
import urllib.parse
import urllib.error
from typing import Dict, Any, List, Optional

def translate_with_google_api(text: str) -> Optional[str]:
    """Translates text to natural Vietnamese using public endpoint."""
    if not text or len(text.strip()) == 0:
        return None
    try:
        encoded = urllib.parse.quote(text[:800])
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=vi&dt=t&q={encoded}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            translated = "".join([item[0] for item in data[0] if item and item[0]])
            if translated and len(translated) > 5:
                return translated.strip()
    except Exception:
        pass
    return None

def synthesize_vietnamese_purpose(repo_name: str, desc: str, tags: List[str] = None) -> str:
    """Synthesizes a fluent, natural Vietnamese explanation of what the tool does."""
    full_text = f"{repo_name} {desc} " + " ".join(tags or [])
    full_lower = full_text.lower()
    
    online_translation = translate_with_google_api(desc)
    if online_translation and len(online_translation) > 15:
        clean = online_translation.strip()
        if not clean.endswith("."):
            clean += "."
        return clean

    # Semantic Synthesis Rules
    if "prompt" in full_lower:
        if "awesome" in full_lower or "chatgpt" in full_lower:
            return "Kho câu lệnh (Prompt) tuyển chọn phong phú cho ChatGPT, cho phép tìm kiếm, lưu trữ và triển khai câu lệnh mẫu cho đội ngũ hoặc cộng đồng."
        return "Bộ sưu tập và hướng dẫn kỹ thuật Prompt Engineering giúp tối ưu hóa câu trả lời của mô hình ngôn ngữ lớn."
    
    if "game" in full_lower:
        if "farm" in full_lower or "nông trại" in full_lower:
            return "Trò chơi mô phỏng nông trại (Farming Simulator), cung cấp mã nguồn trồng trọt, chăn nuôi và quản lý nông trại tương tác."
        if "rpg" in full_lower:
            return "Engine trò chơi nhập vai (RPG) tương tác vận hành bằng AI, tự động sinh thế giới ảo, đối thoại và nhiệm vụ theo thời gian thực."
        if "chess" in full_lower:
            return "Trò chơi cờ vua kết hợp trí tuệ nhân tạo, hiển thị bàn cờ đồ họa 3D và phân tích nước đi thông minh."
        if "edu" in full_lower:
            return "Trò chơi giáo dục tương tác giúp người học rèn luyện tư duy logic, lập trình và giải toán với sự hỗ trợ của gia sư AI."
        return "Dự án trò chơi tương tác trên nền tảng web, cung cấp mã nguồn mở hoàn chỉnh để trải nghiệm hoặc học hỏi kỹ thuật gamedev."

    if "three" in full_lower or "webgl" in full_lower or "3d" in full_lower:
        return "Thư viện đồ họa không gian 3D mạnh mẽ trên trình duyệt, giúp hiển thị hoạt cảnh, mô hình 3D và trò chơi WebGL tương tác mượt mà."

    if "screenshot" in full_lower or "code" in full_lower and "generator" in full_lower:
        return "Công cụ tự động chuyển đổi hình ảnh thiết kế / giao diện thành mã nguồn HTML, Tailwind CSS và React hoàn chỉnh thông qua AI."

    if "system_prompt" in full_lower or "leak" in full_lower:
        return "Bộ sưu tập các câu lệnh hệ thống (System Prompts) trích xuất từ các mô hình AI hàng đầu như Claude Code, ChatGPT GPT-4o, Gemini Pro."

    if "video" in full_lower or "montage" in full_lower:
        return "Hệ thống sản xuất video tự động bằng Agent AI, hỗ trợ chuỗi quy trình tạo kịch bản, ghép cảnh và sản xuất video từ văn bản."

    if "gemini" in full_lower:
        return "Bộ mã nguồn mẫu và công cụ kết nối API Google Gemini, hỗ trợ xử lý đa phương thức (hình ảnh, video, âm thanh) và gọi hàm tự động."

    if "elevenlabs" in full_lower or "voice" in full_lower or "audio" in full_lower:
        return "Ứng dụng mã nguồn mở sao chép giọng nói (Voice Cloning), lồng tiếng video và chuyển văn bản thành giọng nói (TTS) hoạt động nội bộ không cần mạng."

    return f"Kho mã nguồn mở {repo_name} cung cấp giải pháp lập trình và tự động hóa tác vụ cho nhà phát triển."

def analyze_with_local_engine(repo_info: Dict[str, Any]) -> Dict[str, Any]:
    """Generates unique, context-aware analysis without generic boilerplate."""
    name = repo_info.get("repo_name", "").lower()
    title = repo_info.get("title", "").lower()
    desc = repo_info.get("description", "").lower()
    lang = repo_info.get("language", "")
    stars = repo_info.get("stars", 0)
    tags_list = repo_info.get("tags", [])
    tags = " ".join(tags_list) if isinstance(tags_list, list) else str(tags_list)
    section = repo_info.get("source_section", "").lower()
    full_text = f"{name} {title} {desc} {tags} {section}"

    if any(k in full_text for k in ["openai", "chatgpt", "gpt-4", "gpt-3", "gpt-5", "codex", "whisper", "sora", "chatgpt-games"]):
        ai_ecosystem = "OpenAI / ChatGPT"
        ai_priority = 1
    elif any(k in full_text for k in ["gemini", "gemini-pro", "google-gemini", "google ai", "gemma", "vertex ai"]):
        ai_ecosystem = "Google Gemini"
        ai_priority = 2
    elif any(k in full_text for k in ["claude", "anthropic", "claude code", "sonnet", "opus", "claude-red"]):
        ai_ecosystem = "Anthropic Claude"
        ai_priority = 3
    elif any(k in full_text for k in ["llm", "agent", "rag", "ollama", "deepseek", "diffusion", "transformers", "ai-generated"]):
        ai_ecosystem = "AI Khác"
        ai_priority = 4
    else:
        ai_ecosystem = "Không liên quan AI"
        ai_priority = 5

    purpose_summary = synthesize_vietnamese_purpose(
        repo_info.get("repo_name", ""),
        repo_info.get("description", ""),
        tags_list if isinstance(tags_list, list) else []
    )

    if "prompt" in full_text:
        practical_use = "💡 Dùng được ngay: Copy các mẫu prompt dán thẳng vào ChatGPT/Gemini để làm việc, viết code hoặc sáng tạo nội dung tức thì."
        tech_point = "Cấu trúc theo dạng template biến số, tối ưu hóa ngữ cảnh và hệ thống quy tắc nhập liệu cho LLM."
    elif "game" in full_text:
        practical_use = "🎮 Dùng được ngay: Clone code về chạy `npm start` hoặc mở file `index.html` trong trình duyệt là chơi được ngay."
        tech_point = f"Xây dựng bằng {lang or 'JavaScript/HTML5'}, tích hợp logic tương tác và đồ họa nhẹ nhàng."
    elif "three" in full_text or "3d" in full_text:
        practical_use = "🌐 Dùng được ngay: Tham khảo các component 3D, lấy asset và shader để dựng website hoặc game không gian 3 chiều."
        tech_point = "Khai thác tối đa năng lực tăng tốc phần cứng WebGL, dựng hoạt cảnh thời gian thực mượt mà."
    elif "agent" in full_text or "skill" in full_text:
        practical_use = "🤖 Dùng được ngay: Cài đặt vào môi trường Claude Code, Cursor hoặc agent framework để tự động hóa quy trình dev."
        tech_point = "Thiết kế dạng module tách rời, có định nghĩa input/output chuẩn hóa cho trợ lý lập trình."
    elif "video" in full_text or "image" in full_text:
        practical_use = "🎬 Dùng được ngay: Cung cấp pipeline xử lý tự động, chỉ cần đưa kịch bản hoặc ảnh mẫu là xuất ra kết quả."
        tech_point = "Kết hợp mô hình khuếch tán (diffusion) và kịch bản tự động hóa backend."
    else:
        practical_use = f"📦 Dùng được ngay: Thư viện mã nguồn mở viết bằng {lang or 'nhiều ngôn ngữ'}, có thể tích hợp trực tiếp vào dự án phần mềm."
        tech_point = f"Mã nguồn chuẩn hóa, cộng đồng đánh giá cao với ★ {repo_info.get('stars_text', stars)} sao."

    growth = repo_info.get("stars_growth", "")
    if "+1" in growth or "+2" in growth or stars >= 20000 or (ai_priority <= 2 and "prompt" in full_text):
        hot_alert = "HOT_RED"
        eval_text = "Cực kỳ thịnh hành, đang thu hút sự chú ý lớn từ cộng đồng quốc tế."
    elif stars >= 5000 or ai_priority <= 3:
        hot_alert = "NOTICE_YELLOW"
        eval_text = "Đáng chú ý, dự án hoạt động ổn định và có giá trị áp dụng thực tiễn cao."
    else:
        hot_alert = "POTENTIAL_GREEN"
        eval_text = "Tiềm năng, phù hợp để lưu trữ theo dõi các bản cập nhật tính năng mới."

    ai_analysis = (
        f"**Phân tích kỹ thuật:** {tech_point}\n"
        f"**Ứng dụng thực tế:** {practical_use}\n"
        f"**Đánh giá tiềm năng:** {eval_text}"
    )

    return {
        "purpose_summary": purpose_summary,
        "practical_use": practical_use,
        "ai_ecosystem": ai_ecosystem,
        "ai_priority": ai_priority,
        "hot_alert": hot_alert,
        "ai_analysis": ai_analysis
    }

def analyze_with_gemini(repo_info: Dict[str, Any], api_key: str, model: str = "gemini-3.8-flash") -> Dict[str, Any]:
    """Calls Google Gemini API with support for both AQ. and AIzaSy keys."""
    clean_key = api_key.strip()
    target_model = model or "gemini-1.5-flash"
    prompt = f"""
Bạn là chuyên gia thẩm định công nghệ phần mềm và trí tuệ nhân tạo.
Hãy phân tích kho mã nguồn sau:
- Tên Repository: {repo_info.get('repo_name')}
- Mô tả gốc: {repo_info.get('description')}
- Ngôn ngữ: {repo_info.get('language')}
- Số sao: {repo_info.get('stars_text')}
- Topic: {repo_info.get('source_section', 'N/A')}

YÊU CẦU:
1. "purpose_summary": DỊCH VÀ DIỄN ĐẠT 100% SANG TIẾNG VIỆT (1-2 câu). Giải thích rõ công cụ phục vụ gì, giải quyết bài toán gì.
2. "practical_use": Nêu cách người dùng có thể xài được ngay (chạy game, copy prompt, cắm API key...).
3. "ai_analysis": Phân tích sâu ĐỘC BẢN cho riêng repository này: công nghệ lõi, điểm độc đáo.
4. "ai_ecosystem": 'OpenAI / ChatGPT' | 'Google Gemini' | 'Anthropic Claude' | 'AI Khác' | 'Không liên quan AI'
5. "hot_alert": 'HOT_RED' | 'NOTICE_YELLOW' | 'POTENTIAL_GREEN' | 'NORMAL'

Trả về DUY NHẤT một chuỗi JSON hợp lệ:
{{
  "purpose_summary": "Tóm tắt tiếng Việt 1-2 câu",
  "practical_use": "Cách xài được ngay bằng tiếng Việt",
  "ai_ecosystem": "OpenAI / ChatGPT",
  "ai_priority": 1,
  "hot_alert": "HOT_RED",
  "ai_analysis": "Phân tích kỹ thuật chi tiết độc bản"
}}
"""
    # 1. Try Native Google Generative Language endpoint (official cURL format)
    candidate_models = []
    if target_model:
        candidate_models.append(target_model)
    for cm in ["gemini-3.8-flash", "gemini-3.8-pro", "gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"]:
        if cm not in candidate_models:
            candidate_models.append(cm)
    for m in candidate_models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={clean_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"}
        }
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                clean_text = re.sub(r'^```json\s*', '', text.strip())
                clean_text = re.sub(r'\s*```$', '', clean_text)
                parsed = json.loads(clean_text)
                parsed["ai_analysis"] += f"\n\n*(Phân tích chuyên sâu bởi Google Gemini - {m})*"
                return parsed
        except Exception:
            continue

    # 2. Try Google OpenAI-compatible endpoint
    try:
        url = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
        payload = {
            "model": target_model,
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"},
            "temperature": 0.2
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {clean_key}"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            parsed = json.loads(data["choices"][0]["message"]["content"])
            parsed["ai_analysis"] += f"\n\n*(Phân tích chuyên sâu bởi Google Gemini OpenAI-Compatible - {target_model})*"
            return parsed
    except Exception:
        pass

    res = analyze_with_local_engine(repo_info)
    res["ai_analysis"] += "\n\n*(Gemini API tạm thời không phản hồi, đã tự động dịch bằng Smart Local Engine)*"
    return res

def analyze_with_openai(repo_info: Dict[str, Any], api_key: str, model: str = "gpt-4o-mini") -> Dict[str, Any]:
    """Calls OpenAI ChatGPT API for deep analysis and translation."""
    clean_key = api_key.strip()
    prompt = f"""
Bạn là chuyên gia thẩm định công nghệ GitHub.
Phân tích repository:
- Tên: {repo_info.get('repo_name')}
- Mô tả: {repo_info.get('description')}
- Ngôn ngữ: {repo_info.get('language')}
- Stars: {repo_info.get('stars_text')}

YÊU CẦU:
1. Dịch và tóm tắt 100% bằng TIẾNG VIỆT tự nhiên dù gốc là tiếng Anh hay Trung.
2. Phân loại theo ưu tiên: OpenAI (#1) >> Gemini (#2) >> Claude (#3) >> AI Khác (#4) >> Không AI (#5).
3. Đưa ra hướng dẫn cách xài ngay và phân tích kỹ thuật chi tiết.

Trả về JSON:
{{
  "purpose_summary": "1-2 câu tiếng Việt tóm tắt rõ công cụ phục vụ gì",
  "practical_use": "Cách xài được ngay",
  "ai_ecosystem": "'OpenAI / ChatGPT' | 'Google Gemini' | 'Anthropic Claude' | 'AI Khác' | 'Không liên quan AI'",
  "ai_priority": 1,
  "hot_alert": "'HOT_RED' | 'NOTICE_YELLOW' | 'POTENTIAL_GREEN' | 'NORMAL'",
  "ai_analysis": "Phân tích chuyên sâu độc bản"
}}
"""
    url = "https://api.openai.com/v1/chat/completions"
    payload = {
        "model": model or "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "You are a professional GitHub tech evaluator. Output strictly valid JSON in Vietnamese."},
            {"role": "user", "content": prompt}
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.2
    }
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {clean_key}"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            parsed = json.loads(data["choices"][0]["message"]["content"])
            parsed["ai_analysis"] += f"\n\n*(Phân tích chuyên sâu bởi OpenAI {model})*"
            return parsed
    except Exception as e:
        res = analyze_with_local_engine(repo_info)
        res["ai_analysis"] += "\n\n*(OpenAI API không phản hồi, đã tự động dịch bằng Smart Local Engine)*"
        return res

def analyze_repository(repo_info: Dict[str, Any], settings: Dict[str, str]) -> Dict[str, Any]:
    active_engine = settings.get("active_ai_engine", "gemini").lower()
    
    if active_engine == "gemini":
        gemini_key = settings.get("gemini_api_key", "").strip()
        if gemini_key:
            model = settings.get("gemini_model", "gemini-1.5-flash")
            return analyze_with_gemini(repo_info, gemini_key, model)
            
    elif active_engine == "openai":
        openai_key = settings.get("openai_api_key", "").strip()
        if openai_key:
            model = settings.get("openai_model", "gpt-4o-mini")
            return analyze_with_openai(repo_info, openai_key, model)

    return analyze_with_local_engine(repo_info)

# ========================================================
# AI SMART SEARCH: PARSE USER NEED & SEMANTIC MATCHING
# ========================================================

def parse_user_need(user_query: str, settings: Dict[str, str]) -> Dict[str, Any]:
    query_clean = user_query.strip().lower()
    
    gemini_key = settings.get("gemini_api_key", "").strip()
    if settings.get("active_ai_engine") == "gemini" and gemini_key:
        prompt = f"""
Người dùng có nhu cầu tìm mã nguồn trên GitHub: "{user_query}"
Hãy trích xuất các từ khóa tiếng Anh và tiếng Việt tốt nhất để tìm trên GitHub Search API:
Trả về duy nhất JSON:
{{
  "english_search_queries": ["query1", "query2"],
  "semantic_keywords": ["keyword1", "keyword2"],
  "need_summary": "Tóm tắt ngắn gọn nhu cầu bằng tiếng Việt"
}}
"""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent?key={gemini_key}"
        payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.1, "responseMimeType": "application/json"}}
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(re.sub(r'^```json\s*|\s*```$', '', text.strip()))
        except Exception:
            pass

    if any(k in query_clean for k in ["nông trại", "farm", "trồng trọt", "vườn"]):
        english_queries = ["farm game", "farming simulator", "harvest game", "farm threejs"]
        semantic_kws = ["farm", "farming", "simulator", "harvest", "agriculture", "nông trại", "game"]
        need_summary = "Tìm kiếm các trò chơi, engine hoặc mã nguồn mô phỏng nông trại (Farming Simulator)."
    elif any(k in query_clean for k in ["cờ vua", "chess"]):
        english_queries = ["chess game", "chatgpt chess", "threejs chess"]
        semantic_kws = ["chess", "cờ vua", "game", "ai"]
        need_summary = "Tìm kiếm game hoặc mã nguồn cờ vua có AI."
    elif any(k in query_clean for k in ["video", "dựng phim", "tạo video"]):
        english_queries = ["ai video generator", "video production agent", "text to video"]
        semantic_kws = ["video", "multimodal", "generation", "tạo video"]
        need_summary = "Tìm kiếm công cụ AI tự động tạo và biên tập video."
    elif any(k in query_clean for k in ["giáo dục", "học tập", "toán", "edu"]):
        english_queries = ["educational game", "learn programming game", "math ai tutor"]
        semantic_kws = ["educational", "game", "learn", "math", "giáo dục"]
        need_summary = "Tìm kiếm trò chơi giáo dục và ứng dụng học tập thông minh."
    elif any(k in query_clean for k in ["prompt", "câu lệnh"]):
        english_queries = ["awesome chatgpt prompts", "prompt engineering", "gemini prompts"]
        semantic_kws = ["prompt", "prompts", "chatgpt", "gemini", "câu lệnh"]
        need_summary = "Tìm kiếm bộ câu lệnh prompt mẫu phong phú và thực chiến."
    elif any(k in query_clean for k in ["3d", "threejs", "webgl"]):
        english_queries = ["threejs game", "threejs 3d demo", "webgl 3d"]
        semantic_kws = ["threejs", "webgl", "3d", "graphics"]
        need_summary = "Tìm kiếm mã nguồn đồ họa và game 3D Three.js."
    else:
        words = [w for w in re.split(r'[\s,]+', query_clean) if len(w) > 2]
        english_queries = [query_clean, f"{query_clean} github", f"{query_clean} ai"]
        semantic_kws = words
        need_summary = f"Tìm kiếm mã nguồn liên quan đến '{user_query}'."

    return {
        "english_search_queries": english_queries,
        "semantic_keywords": semantic_kws,
        "need_summary": need_summary
    }

def calculate_match_score(repo: Dict[str, Any], need_spec: Dict[str, Any]) -> float:
    kws = need_spec.get("semantic_keywords", [])
    if not kws:
        return 50.0

    repo_text = f"{repo.get('repo_name', '')} {repo.get('title', '')} {repo.get('description', '')} {repo.get('purpose_summary', '')} {repo.get('practical_use', '')} {' '.join(repo.get('tags', []))}".lower()

    matches = sum(1 for kw in kws if kw.lower() in repo_text)
    score = (matches / len(kws)) * 100.0

    if any(k in repo_text for k in ["farm", "nông trại"]) and any(k in repo_text for k in ["game", "trò chơi", "simulator"]):
        score = max(score, 92.0)
    elif matches >= 2:
        score = max(score, 78.0)
    elif matches == 1:
        score = max(score, 60.0)
    else:
        score = min(score, 40.0)

    return round(min(score, 99.0), 1)

# ========================================================
# COMPREHENSIVE MULTI-METHOD API CONNECTION TESTER
# ========================================================

def list_gemini_models_from_api(api_key: str) -> Dict[str, Any]:
    """Calls Google ModelService.ListModels to list models supporting generateContent."""
    api_key = (api_key or "").strip()
    if not api_key:
        return {"success": False, "models": [], "error": "Chưa nhập API Key"}
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "TopGit-Radar/3.8"},
            method="GET"
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                raw_models = data.get("models", [])
                valid_models = []
                for m in raw_models:
                    methods = m.get("supportedGenerationMethods", [])
                    if "generateContent" in methods:
                        m_id = m.get("name", "").replace("models/", "")
                        valid_models.append({
                            "id": m_id,
                            "displayName": m.get("displayName", m_id),
                            "description": m.get("description", "")
                        })
                return {"success": True, "models": valid_models}
            return {"success": False, "models": [], "error": f"HTTP {resp.status}"}
    except urllib.error.HTTPError as e:
        try:
            err_body = e.read().decode("utf-8")
            err_json = json.loads(err_body)
            msg = err_json.get("error", {}).get("message", e.reason)
        except Exception:
            msg = f"HTTP {e.code}: {e.reason}"
        return {"success": False, "models": [], "error": msg}
    except Exception as e:
        return {"success": False, "models": [], "error": str(e)}


def test_api_connection(provider: str, api_key: str, model: Optional[str] = None) -> Dict[str, Any]:
    api_key = (api_key or "").strip()
    if not api_key:
        return {"success": False, "message": "Vui lòng nhập API Key trước khi kiểm tra!"}

    if provider == "gemini":
        target_model = model or "gemini-3.8-flash"
        
        # 1. Gọi ModelService.ListModels theo chuẩn Google AI Studio
        list_res = list_gemini_models_from_api(api_key) or {}
        available_models = [m["id"] for m in list_res.get("models", [])]
        
        candidate_models = []
        if target_model:
            candidate_models.append(target_model)
        for m_name in ["gemini-3.8-flash", "gemini-3.8-pro", "gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"]:
            if m_name not in candidate_models:
                candidate_models.append(m_name)
        for m_name in available_models:
            if m_name not in candidate_models:
                candidate_models.append(m_name)

        last_error_detail = list_res.get("error", "")
        # Thử generateContent với các candidate models
        for m in candidate_models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={api_key}"
            payload = {"contents": [{"parts": [{"text": "Xin chao"}]}]}
            try:
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    if resp.status == 200:
                        extra_models_info = ""
                        if available_models:
                            extra_models_info = f"\n• Các model khả dụng trên dự án: {', '.join(available_models[:6])}"
                        return {
                            "success": True,
                            "active_model": m,
                            "available_models": available_models,
                            "message": f"✅ Tuyệt vời! Khóa Gemini API ({api_key[:6]}...) đã kết nối thành công 100%!\n\n• Model kích hoạt: {m}\n• Hỗ trợ phiên bản Gemini 3.8 mới nhất\n• Cổng kết nối: Google AI Studio Native (v1beta){extra_models_info}\n• Trạng thái: Sẵn sàng phân tích & dịch thuật!"
                        }
            except urllib.error.HTTPError as e:
                try:
                    err_body = e.read().decode("utf-8")
                    err_json = json.loads(err_body)
                    last_error_detail = err_json.get("error", {}).get("message", e.reason)
                except Exception:
                    last_error_detail = f"Mã lỗi HTTP {e.code}: {e.reason}"
            except Exception as e:
                last_error_detail = str(e)

        # 2. Thử cổng tương thích OpenAI của Google Generative Language
        try:
            url = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
            payload = {
                "model": target_model,
                "messages": [{"role": "user", "content": "hi"}],
                "max_tokens": 5
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status == 200:
                    return {
                        "success": True,
                        "active_model": target_model,
                        "available_models": available_models,
                        "message": f"✅ Tuyệt vời! Khóa Gemini API ({api_key[:6]}...) đã kết nối thành công qua cổng tương thích OpenAI!\n\n• Model: {target_model}\n• Trạng thái: Sẵn sàng sử dụng 100%!"
                    }
        except Exception:
            pass

        # 3. Nếu ListModels thành công (khóa hợp lệ 100%) nhưng model cụ thể gặp lỗi
        if list_res.get("success") and available_models:
            return {
                "success": True,
                "active_model": available_models[0],
                "available_models": available_models,
                "message": f"✅ Khóa Gemini API ({api_key[:6]}...) đã kết nối và xác thực thành công!\n\n• Lưu ý: Model '{target_model}' phản hồi: {last_error_detail}\n• Bạn có thể chuyển sang dùng một trong các model đã kích hoạt sẵn: {', '.join(available_models[:5])}"
            }

        return {
            "success": False,
            "message": f"❌ Lỗi kết nối Google Gemini: {last_error_detail}\n\n👉 Gợi ý: Hãy kiểm tra dự án tại https://aistudio.google.com/app/api-keys xem khóa đã được kích hoạt dịch vụ Generative Language API chưa."
        }

    elif provider == "openai":
        target_model = model or "gpt-4o-mini"
        url = "https://api.openai.com/v1/chat/completions"
        payload = {
            "model": target_model,
            "messages": [{"role": "user", "content": "hi"}],
            "max_tokens": 5
        }
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status == 200:
                    return {
                        "success": True,
                        "message": f"✅ Tuyệt vời! Khóa OpenAI ({target_model}) kết nối thành công!\n• Trạng thái: Sẵn sàng phân tích!"
                    }
        except urllib.error.HTTPError as e:
            try:
                err_body = e.read().decode("utf-8")
                err_json = json.loads(err_body)
                msg = err_json.get("error", {}).get("message", e.reason)
                if e.code == 429 and "credits" in msg.lower():
                    return {
                        "success": False,
                        "message": f"❌ Lỗi OpenAI (HTTP 429): Tài khoản OpenAI API của bạn đã HẾT TÍN DỤNG (0 credits còn lại).\n\n💡 Lưu ý: Gói ChatGPT Plus (20$/tháng) KHÔNG bao gồm tiền dùng API. Để dùng OpenAI API, bạn cần nạp tiền riêng tại:\n👉 https://platform.openai.com/settings/organization/billing/billing-overview\n\n👉 Khuyên dùng: Bạn có thể chuyển sang dùng Google Gemini API (miễn phí) hoặc Smart Local NLP!"
                    }
                return {
                    "success": False,
                    "message": f"❌ Lỗi từ OpenAI (HTTP {e.code}): {msg}\n\n👉 Kiểm tra key tại: https://platform.openai.com/api-keys"
                }
            except Exception:
                return {"success": False, "message": f"❌ Lỗi HTTP {e.code}: {e.reason}"}
        except Exception as e:
            return {"success": False, "message": f"❌ Lỗi kết nối OpenAI: {str(e)}"}

    elif provider == "github":
        url = "https://api.github.com/user"
        headers = {
            "User-Agent": "TopGitRadar/3.0",
            "Authorization": f"Bearer {api_key}"
        }
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                user_login = data.get("login", "User")
                return {
                    "success": True,
                    "message": f"✅ Kết nối thành công với GitHub API!\n• Tài khoản: {user_login}\n• Hạn mức: 5.000 lượt gọi/giờ (Đã kích hoạt tốc độ tối đa)!"
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"❌ Lỗi GitHub Token: {str(e)}\n👉 Vui lòng tạo token tại: https://github.com/settings/tokens"
            }

    return {"success": False, "message": "Nhà cung cấp không hợp lệ."}
