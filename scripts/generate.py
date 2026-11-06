import json
import os
import re
import time
import urllib.error
import urllib.request
from datetime import datetime

# 取得金鑰並自動清理前後空格與換行
api_key = os.environ.get("GEMINI_API_KEY", "").strip().strip("'").strip('"')
if not api_key:
    raise ValueError("找不到 GEMINI_API_KEY，請確認 GitHub Secrets 設定！")

json_path = "data/words.json"
existing_words = []

if os.path.exists(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        try:
            existing_words = json.load(f)
        except Exception:
            existing_words = []

history_list = [w.get("word", "") for w in existing_words[:100]]
today_str = datetime.now().strftime("%Y-%m-%d")

prompt = f"""
你是一位專業的英文教學老師。請推薦 5 個適合中高階程度（托福、雅思、職場實用）的英文單字。
今天的日期是：{today_str}。
絕對不能挑選以下清單中出現過的單字：{', '.join(history_list)}。

請嚴格只回傳一段標準 JSON 陣列格式字串，不要加上 ```json 或任何額外的文字：
[
  {{
    "date": "{today_str}",
    "word": "單字1",
    "phonetic": "音標",
    "part_of_speech": "詞性縮寫(例如 n. / v. / adj.)",
    "definition_en": "英文解釋",
    "definition_zh": "中文釋義",
    "example_en": "實用例句",
    "example_zh": "例句中文翻譯",
    "etymology_tip": "一句話記憶法或字根拆解"
  }},
  {{
    "date": "{today_str}",
    "word": "單字2",
    "phonetic": "音標",
    "part_of_speech": "詞性縮寫",
    "definition_en": "英文解釋",
    "definition_zh": "中文釋義",
    "example_en": "實用例句",
    "example_zh": "例句中文翻譯",
    "etymology_tip": "一句話記憶法或字根拆解"
  }},
  {{
    "date": "{today_str}",
    "word": "單字3",
    "phonetic": "音標",
    "part_of_speech": "詞性縮寫",
    "definition_en": "英文解釋",
    "definition_zh": "中文釋義",
    "example_en": "實用例句",
    "example_zh": "例句中文翻譯",
    "etymology_tip": "一句話記憶法或字根拆解"
  }},
  {{
    "date": "{today_str}",
    "word": "單字4",
    "phonetic": "音標",
    "part_of_speech": "詞性縮寫",
    "definition_en": "英文解釋",
    "definition_zh": "中文釋義",
    "example_en": "實用例句",
    "example_zh": "例句中文翻譯",
    "etymology_tip": "一句話記憶法或字根拆解"
  }},
  {{
    "date": "{today_str}",
    "word": "單字5",
    "phonetic": "音標",
    "part_of_speech": "詞性縮寫",
    "definition_en": "英文解釋",
    "definition_zh": "中文釋義",
    "example_en": "實用例句",
    "example_zh": "例句中文翻譯",
    "etymology_tip": "一句話記憶法或字根拆解"
  }}
]
"""

model = "gemini-2.5-flash"
url = f"[https://generativelanguage.googleapis.com/v1beta/models/](https://generativelanguage.googleapis.com/v1beta/models/){model}:generateContent"
headers = {"Content-Type": "application/json", "x-goog-api-key": api_key}
payload = {
    "contents": [{
        "parts": [{"text": prompt}]
    }],
    "generationConfig": {"responseMimeType": "application/json"},
}

req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
max_attempts = 4
for attempt in range(1, max_attempts + 1):
    try:
        with urllib.request.urlopen(req) as res:
            res_data = json.loads(res.read().decode("utf-8"))
        break
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        if e.code in (429, 500, 502, 503, 504) and attempt < max_attempts:
            wait = 30 * attempt
            print(f"Gemini API {e.code}，{wait} 秒後重試（第 {attempt}/{max_attempts} 次）")
            time.sleep(wait)
            continue
        raise RuntimeError(f"Gemini API 錯誤 {e.code}: {body}") from e

raw_text = res_data["candidates"][0]["content"]["parts"][0]["text"].strip()
clean_text = re.sub(r"^```json\s*|\s*```$", "", raw_text, flags=re.MULTILINE).strip()
new_words = json.loads(clean_text)

# 將 5 個單字加入清單最前端
if isinstance(new_words, list):
    for w in reversed(new_words):
        existing_words.insert(0, w)
    words_added = [w.get("word") for w in new_words]
    print(f"成功生成 5 個今日單字: {', '.join(words_added)}")
else:
    existing_words.insert(0, new_words)
    print(f"成功生成今日單字: {new_words.get('word')}")

with open(json_path, "w", encoding="utf-8") as f:
    json.dump(existing_words, f, ensure_ascii=False, indent=2)
