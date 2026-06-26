import json
import time
import urllib.parse
import urllib.request

# Languages users actually care about, ordered by global usage
TRANSLATION_LANGUAGES = {
    "🇪🇸 Spanish":               "es",
    "🇫🇷 French":                "fr",
    "🇩🇪 German":                "de",
    "🇧🇷 Portuguese":            "pt",
    "🇮🇳 Hindi":                 "hi",
    "🇨🇳 Chinese (Simplified)":  "zh-CN",
    "🇯🇵 Japanese":              "ja",
    "🇰🇷 Korean":                "ko",
    "🇸🇦 Arabic":                "ar",
    "🇮🇹 Italian":               "it",
    "🇷🇺 Russian":               "ru",
    "🇳🇱 Dutch":                 "nl",
    "🇹🇷 Turkish":               "tr",
    "🇵🇱 Polish":                "pl",
    "🇸🇪 Swedish":               "sv",
    "🇮🇩 Indonesian":            "id",
    "🇵🇭 Filipino":              "tl",
    "🇻🇳 Vietnamese":            "vi",
    "🇹🇭 Thai":                  "th",
    "🇬🇷 Greek":                 "el",
    "🇮🇱 Hebrew":                "iw",
    "🇺🇦 Ukrainian":             "uk",
}

_BATCH_SIZE = 15
_HEADERS = {"User-Agent": "Mozilla/5.0"}


def _google_translate(text: str, target: str) -> str:
    """Call Google Translate's free endpoint with stdlib urllib only."""
    url = (
        "https://translate.googleapis.com/translate_a/single"
        f"?client=gtx&sl=auto&tl={target}&dt=t&q={urllib.parse.quote(text)}"
    )
    req = urllib.request.Request(url, headers=_HEADERS)
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read())
    return "".join(part[0] for part in data[0] if part[0])


def translate_chunks(chunks: list, target_lang_code: str) -> list:
    """Translate subtitle chunks to target language.

    Translates each segment individually. Uses stdlib urllib — no extra
    packages required. Falls back to the original text on any error.
    """
    if not chunks:
        return chunks

    translated = []
    for i, chunk in enumerate(chunks):
        text = chunk.get("text", "").strip()
        if text:
            try:
                text = _google_translate(text, target_lang_code)
                if i < len(chunks) - 1:
                    time.sleep(0.05)   # gentle rate-limit
            except Exception:
                pass  # keep original on failure
        translated.append({"timestamp": chunk["timestamp"], "text": text})

    return translated

