from deep_translator import GoogleTranslator

# Languages users actually care about, ordered by global usage
TRANSLATION_LANGUAGES = {
    "🇪🇸 Spanish":            "es",
    "🇫🇷 French":             "fr",
    "🇩🇪 German":             "de",
    "🇧🇷 Portuguese":         "pt",
    "🇮🇳 Hindi":              "hi",
    "🇨🇳 Chinese (Simplified)": "zh-CN",
    "🇯🇵 Japanese":           "ja",
    "🇰🇷 Korean":             "ko",
    "🇸🇦 Arabic":             "ar",
    "🇮🇹 Italian":            "it",
    "🇷🇺 Russian":            "ru",
    "🇳🇱 Dutch":              "nl",
    "🇹🇷 Turkish":            "tr",
    "🇵🇱 Polish":             "pl",
    "🇸🇪 Swedish":            "sv",
    "🇮🇩 Indonesian":         "id",
    "🇵🇭 Filipino":           "tl",
    "🇻🇳 Vietnamese":         "vi",
    "🇹🇭 Thai":               "th",
    "🇬🇷 Greek":              "el",
    "🇮🇱 Hebrew":             "iw",
    "🇺🇦 Ukrainian":          "uk",
}

_DELIMITER = "\n<|>\n"
_BATCH_SIZE = 15


def translate_chunks(chunks: list, target_lang_code: str) -> list:
    """Translate subtitle chunks to target language using Google Translate.

    Batches multiple segments into a single API call (separated by a
    distinctive delimiter) to minimise latency and request count.
    Falls back to the original text for any segment that fails.
    """
    if not chunks:
        return chunks

    texts = [c.get("text", "").strip() for c in chunks]
    translated_texts = list(texts)  # start as copy, overwrite on success

    translator = GoogleTranslator(source="auto", target=target_lang_code)

    for i in range(0, len(texts), _BATCH_SIZE):
        batch = texts[i : i + _BATCH_SIZE]
        joined = _DELIMITER.join(batch)
        try:
            result = translator.translate(joined) or joined
            parts = result.split("<|>")
            parts = [p.strip() for p in parts]
            # Guard against translator collapsing/expanding delimiters
            if len(parts) == len(batch):
                for j, part in enumerate(parts):
                    translated_texts[i + j] = part or batch[j]
            else:
                # Fallback: translate each segment individually
                for j, text in enumerate(batch):
                    try:
                        translated_texts[i + j] = translator.translate(text) or text
                    except Exception:
                        pass  # keep original
        except Exception:
            pass  # keep originals for this batch

    return [
        {"timestamp": c["timestamp"], "text": t}
        for c, t in zip(chunks, translated_texts)
    ]
