#!/usr/bin/env python3
"""
Lestrarstund – generate the Icelandic audio clips once.

Creates audio/<name>.mp3 for every letter name and word the app says, plus
audio/clips.js, which tells the app which clips exist.
Put the audio folder next to index.html.

Usage (run inside the lestrarstund-web folder):
    pip install requests edge-tts
    python make_audio.py                 # Google's Icelandic voice (default)
    python make_audio.py --engine edge   # Guðrún via edge-tts
    python make_audio.py --engine auto   # Tiró first, edge-tts if Tiró fails
    python make_audio.py --engine tiro --voice Alfur
    python make_audio.py --list-voices   # show Tiró's voices
    python make_audio.py --force         # remake clips that already exist
    python make_audio.py --try api       # make several versions of one word to compare,
                                         # in candidates/ with a page to listen to them

To replace a clip with your own recording, save it under the same name in
audio/ and the app will play it. Run without --force so it isn't overwritten.
"""
import argparse, asyncio, json, re, sys
from pathlib import Path

# Same lists as in index.html
NAMES = {"A":"a","Á":"á","B":"bé","D":"dé","Ð":"eð","E":"e","É":"é","F":"eff","G":"ge","H":"há","I":"i","Í":"í",
         "J":"joð","K":"ká","L":"ell","M":"emm","N":"enn","O":"o","Ó":"ó","P":"pé","R":"err","S":"ess","T":"té",
         "U":"u","Ú":"ú","V":"vaff","X":"ex","Y":"ufsilon i","Ý":"ufsilon í","Þ":"þorn","Æ":"æ","Ö":"ö"}
LETTER_WORDS = ["api","álft","bíll","dúkka","bað","epli","ég","fiskur","geit","hestur","ilmur","ís","jól","köttur",
                "lamb","mús","nef","ostur","ólífa","pera","rós","sól","tré","ugla","úr","vatn","lax","yfir","ýsa",
                "þak","æfing","önd"]
WORDS = ["sól","ís","mús","hús","nef","api","úr","bók","bað","kýr","tré","rós","lamb","epli",
         "mamma","pabbi","ég","og","já","nei"]
EXTRA = ["Halló"]

# Sentences are read from index.html, so adding one there is enough.
def sentences():
    html = Path(__file__).with_name("index.html")
    if not html.exists(): return []
    m = re.search(r"const SENTENCES=(\[.*?\]);", html.read_text(encoding="utf-8"), re.S)
    return [row[0] for row in json.loads(m.group(1))] if m else []

def norm(text):  # same as norm() in index.html
    return " ".join(re.sub(r"[^a-záðéíóúýþæö\s]", " ", text.lower()).split())

# File name for each clip. Must match slug() in index.html.
MAP = {"á":"a1","é":"e1","í":"i1","ó":"o1","ú":"u1","ý":"y1","ð":"d1","þ":"th1","æ":"ae1","ö":"o2"," ":"_"}
def slug(text):
    out = ""
    for ch in text.lower():
        if ch in MAP: out += MAP[ch]
        elif "a" <= ch <= "z": out += ch
    return out

TIRO = "https://tts.tiro.is/v0"
TIRO_PREFERRED = ["Dilja_v2", "Dilja", "Alfur_v2", "Alfur"]

def tiro_voices():
    import requests
    r = requests.get(TIRO + "/voices", timeout=20)
    r.raise_for_status()
    return r.json()

def tiro_pick(wanted):
    ids = [v.get("VoiceId") for v in tiro_voices()]
    if wanted:
        if wanted not in ids:
            sys.exit(f"Tiró has no voice '{wanted}'. Choose one of: {', '.join(ids)}")
        return wanted
    for v in TIRO_PREFERRED:
        if v in ids: return v
    return ids[0]

def tiro_say(text, voice, path):
    import requests
    body = {"Engine": "standard", "LanguageCode": "is-IS", "OutputFormat": "mp3", "SampleRate": "22050",
            "Text": text, "TextType": "text", "VoiceId": voice}
    r = requests.post(TIRO + "/speech", json=body, timeout=60)
    r.raise_for_status()
    if len(r.content) < 500:
        raise RuntimeError("audio too short")
    path.write_bytes(r.content)

def edge_say(text, voice, rate, path):
    import edge_tts
    asyncio.run(edge_tts.Communicate(text, voice, rate=rate).save(str(path)))

def google_say(text, path):
    import requests, urllib.parse
    url = ("https://translate.google.com/translate_tts?ie=UTF-8&client=tw-ob&tl=is&q="
           + urllib.parse.quote(text))
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
    r.raise_for_status()
    if len(r.content) < 500:
        raise RuntimeError("audio too short")
    path.write_bytes(r.content)

def try_word(word):
    """Several versions of one word, to pick the one that sounds right."""
    out = Path("candidates"); out.mkdir(exist_ok=True)
    cap = word[:1].upper() + word[1:] + "."
    variants = [
        ("Guðrún, eins og núna", lambda p: edge_say(word, "is-IS-GudrunNeural", "-20%", p)),
        (f"Guðrún, „{cap}“",     lambda p: edge_say(cap, "is-IS-GudrunNeural", "-20%", p)),
        ("Guðrún, venjulegur hraði", lambda p: edge_say(word, "is-IS-GudrunNeural", "+0%", p)),
        ("Gunnar",               lambda p: edge_say(word, "is-IS-GunnarNeural", "-20%", p)),
        (f"Gunnar, „{cap}“",     lambda p: edge_say(cap, "is-IS-GunnarNeural", "-20%", p)),
        ("Google",               lambda p: google_say(word, p)),
    ]
    rows = []
    for i, (label, make) in enumerate(variants, 1):
        name = f"{slug(word)}-{i}.mp3"
        try:
            make(out / name)
            rows.append(f'<li><b>{i}.</b> {label}<br><audio controls preload="none" src="{name}"></audio></li>')
            print(f"  ✓ {i}. {label}")
        except Exception as e:
            print(f"  ✗ {i}. {label}: {e}")
    page = (f'<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>„{word}“</title><body style="font:18px system-ui;max-width:32em;margin:2em auto;padding:0 1em">'
            f'<h1>„{word}“</h1><p>Hlustaðu og veldu besta númerið.</p>'
            f'<ol style="list-style:none;padding:0;display:grid;gap:1em">{"".join(rows)}</ol>')
    (out / f"{slug(word)}.html").write_text(page, encoding="utf-8")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", choices=["google", "auto", "tiro", "edge"], default="google")
    ap.add_argument("--voice", help="Tiró VoiceId, or an Edge voice such as is-IS-GunnarNeural")
    ap.add_argument("--rate", default="-20%", help="edge-tts speed, e.g. -20%% is a little slower")
    ap.add_argument("--out", default="audio")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--list-voices", action="store_true")
    ap.add_argument("--try", dest="try_word", metavar="WORD", help="make versions of one word to compare")
    a = ap.parse_args()

    if a.try_word:
        try_word(a.try_word)
        return

    if a.list_voices:
        for v in tiro_voices():
            print(v.get("VoiceId"), "-", v.get("Gender"), v.get("LanguageName", ""))
        return

    sents = sentences()
    sent_words = [w for t in sents for w in norm(t).split()]
    texts = list(dict.fromkeys(list(NAMES.values()) + LETTER_WORDS + WORDS + EXTRA + sents + sent_words))
    out = Path(a.out); out.mkdir(exist_ok=True)

    engine, tiro_voice = a.engine, None
    if engine in ("auto", "tiro"):
        try:
            tiro_voice = tiro_pick(a.voice if engine == "tiro" else None)
            print(f"Using Tiró, voice {tiro_voice}")
        except Exception as e:
            if engine == "tiro": sys.exit(f"Tiró is not answering: {e}")
            print(f"Tiró is not answering ({e}), using edge-tts instead")
            engine = "edge"
    edge_voice = a.voice if (a.engine == "edge" and a.voice) else "is-IS-GudrunNeural"

    done, failed = [], []
    for t in texts:
        p = out / (slug(t) + ".mp3")
        if p.exists() and not a.force:
            done.append(slug(t)); continue
        try:
            if engine == "google":
                google_say(t, p)
            elif engine != "edge" and tiro_voice:
                try:
                    tiro_say(t, tiro_voice, p)
                except Exception as e:
                    if a.engine == "tiro": raise
                    print(f"  Tiró failed on '{t}' ({e}), trying edge-tts")
                    edge_say(t, edge_voice, a.rate, p)
            else:
                edge_say(t, edge_voice, a.rate, p)
            print(f"  ✓ {t:12} → {p.name}")
            done.append(slug(t))
        except Exception as e:
            print(f"  ✗ {t}: {e}")
            failed.append(t)

    (out / "clips.js").write_text("window.CLIPS=" + json.dumps(sorted(set(done))) + ";\n", encoding="utf-8")
    print(f"\n{len(done)} clips ready in {out}/", "" if not failed else f"– failed: {', '.join(failed)}")

if __name__ == "__main__":
    main()
