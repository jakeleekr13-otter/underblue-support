"""Build the localized UnderBlue landing pages.

Store copy comes from the app repo's docs/AppStoreMetadata.md and
scripts/app_store_screenshots/captions.json. Only page chrome is written here.

Usage: python3 -I _build/build_landing.py <path to the underblue app repo>
Pages: / (en), /ko/, /ja/, /zh-hans/, /zh-hant/, /es/ and sitemap.xml.
"""
import html
import json
import re
import sys
from pathlib import Path

SITE = "https://jakeleekr13-otter.github.io/underblue-support"
APP_STORE = "https://apps.apple.com/app/id6815881625"
# The Mac app is a separate App Store record. Set its link when it is live;
# the Mac section then shows a Mac App Store badge instead of "coming soon".
MAC_APP_STORE = None
ROOT = Path(__file__).resolve().parent.parent

# key: url dir, html lang, metadata name, captions.json key, og locale
LOCALES = [
    ("en", "", "en", "English", None, "en_US"),
    ("ko", "ko/", "ko", "Korean", "ko", "ko_KR"),
    ("ja", "ja/", "ja", "Japanese", "ja", "ja_JP"),
    ("zh-hans", "zh-hans/", "zh-Hans", "Simplified Chinese", "zh-Hans", "zh_CN"),
    ("zh-hant", "zh-hant/", "zh-Hant", "Traditional Chinese", "zh-Hant", "zh_TW"),
    ("es", "es/", "es", "Spanish (Spain)", "es-ES", "es_ES"),
]

NATIVE = {"en": "English", "ko": "한국어", "ja": "日本語", "zh-hans": "简体中文",
          "zh-hant": "繁體中文", "es": "Español"}

# English captions live in the screenshot README, not in captions.json.
EN_CAPTIONS = ["Bring back the real colour.", "Reef colour, restored.", "Video, fixed too.",
               "Pick a look. Set the strength.", "Stays on your iPhone."]

UI = {
    "en": {
        "title": "UnderBlue — Underwater Photo & Video Color Correction for iPhone",
        "mac_name": "UnderBlue for Mac", "soon": "coming soon",
        "mac_p": "Fix a whole dive in one batch. Photos and videos together, on your Mac.",
        "mac_alt": "UnderBlue for Mac correcting a batch of dive photos and videos",
        "cta_h": "Try it free",
        "support": "Support", "privacy": "Privacy Policy", "lang": "Language",
        "shots": "Screenshots",
    },
    "ko": {
        "title": "UnderBlue — 수중 사진·영상 색보정 앱 (iPhone)",
        "mac_name": "Mac 버전", "soon": "출시 예정",
        "mac_p": "다이빙 한 번의 사진과 영상을 Mac에서 한꺼번에 보정하세요.",
        "mac_alt": "여러 다이빙 사진과 영상을 한 번에 보정하는 Mac용 UnderBlue",
        "cta_h": "무료로 써 보세요",
        "support": "지원", "privacy": "개인정보 처리방침", "lang": "언어",
        "shots": "스크린샷",
    },
    "ja": {
        "title": "UnderBlue — 水中写真・水中動画の色補正アプリ（iPhone）",
        "mac_name": "Mac版", "soon": "近日公開",
        "mac_p": "1回のダイビングの写真とビデオを、Macでまとめて補正できます。",
        "mac_alt": "ダイビングの写真とビデオをまとめて補正するMac版UnderBlue",
        "cta_h": "無料で試せます",
        "support": "サポート", "privacy": "プライバシーポリシー", "lang": "言語",
        "shots": "スクリーンショット",
    },
    "zh-hans": {
        "title": "UnderBlue — 水下照片与视频色彩校正 App（iPhone）",
        "mac_name": "Mac 版", "soon": "即将推出",
        "mac_p": "在 Mac 上一次批量校正整次潜水的照片和视频。",
        "mac_alt": "在 Mac 上批量校正潜水照片和视频的 UnderBlue",
        "cta_h": "免费试用",
        "support": "支持", "privacy": "隐私政策", "lang": "语言",
        "shots": "截图",
    },
    "zh-hant": {
        "title": "UnderBlue — 水下照片與影片色彩校正 App（iPhone）",
        "mac_name": "Mac 版", "soon": "即將推出",
        "mac_p": "在 Mac 上一次批次校正整趟潛水的照片與影片。",
        "mac_alt": "在 Mac 上批次校正潛水照片與影片的 UnderBlue",
        "cta_h": "免費試用",
        "support": "支援", "privacy": "隱私權政策", "lang": "語言",
        "shots": "螢幕截圖",
    },
    "es": {
        "title": "UnderBlue — Corrige el color de tus fotos y vídeos submarinos (iPhone)",
        "mac_name": "UnderBlue para Mac", "soon": "muy pronto",
        "mac_p": "Corrige toda una inmersión en un solo lote. Fotos y vídeos juntos, en tu Mac.",
        "mac_alt": "UnderBlue para Mac corrigiendo un lote de fotos y vídeos de buceo",
        "cta_h": "Pruébala gratis",
        "support": "Soporte", "privacy": "Política de privacidad", "lang": "Idioma",
        "shots": "Capturas de pantalla",
    },
}


def section(md, heading):
    m = re.search(rf"^## {re.escape(heading)}\n(.*?)(?=^## |\Z)", md, re.S | re.M)
    assert m, f"missing section: {heading}"
    return m.group(1).strip()


def field(md, label):
    m = re.search(rf"^\*\*{re.escape(label)}:\*\* (.+)$", md, re.M)
    assert m, f"missing field: {label}"
    return m.group(1).strip()


def parse_description(text):
    blocks = [b.strip() for b in text.split("\n\n") if b.strip()]
    i = next(n for n, b in enumerate(blocks) if b.endswith((":", "：")))
    bullets = [line[2:].strip() for b in blocks for line in b.splitlines() if line.startswith("• ")]
    rest = [b for b in blocks[i + 1:] if not b.startswith("• ")]
    assert len(rest) == 2 and bullets, "description shape changed"
    return blocks[:i], blocks[i].rstrip(":："), bullets, rest[0], rest[1]


def strip_tags(s):
    return re.sub(r"<[^>]+>", "", s.replace("<br>", " ")).strip()


def page(loc, md, captions):
    key, rel, lang, meta_name, cap_key, og_locale = loc
    ui = UI[key]
    e = html.escape
    subtitle = field(md, f"{meta_name} subtitle")
    promo = field(md, f"{meta_name} promotional text")
    intro, feat_h, bullets, pricing, note = parse_description(section(md, f"{meta_name} description"))
    keywords = field(section(md, "Keywords"), meta_name).split(" (")[0]
    if cap_key:
        c = captions[cap_key]
        alts = [f"{strip_tags(c[f's{n}.title'])} {c[f's{n}.sub']}" for n in range(1, 6)]
    else:
        alts = EN_CAPTIONS
    url = f"{SITE}/{rel}"
    up = "../" if rel else ""
    alternates = "\n".join(
        f'  <link rel="alternate" hreflang="{l[2]}" href="{SITE}/{l[1]}">' for l in LOCALES
    ) + f'\n  <link rel="alternate" hreflang="x-default" href="{SITE}/">'
    langs = "\n".join(
        f'      <li><a href="{(up + l[1]) or "./"}" hreflang="{l[2]}" lang="{l[2]}"'
        + (' aria-current="page"' if l[0] == key else "") + f">{NATIVE[l[0]]}</a></li>"
        for l in LOCALES
    )
    ld = {
        "@context": "https://schema.org", "@type": "SoftwareApplication",
        "name": "UnderBlue", "operatingSystem": "iOS", "applicationCategory": "MultimediaApplication",
        "description": promo, "url": url, "image": f"{SITE}/assets/og.jpg", "inLanguage": lang,
        "installUrl": APP_STORE, "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
    }
    shots = "\n".join(
        f'      <li><img src="{up}assets/shots/{key}/0{n}.jpg" width="600" height="1304" '
        f'loading="lazy" alt="{e(alts[n - 1])}"></li>' for n in range(1, 6)
    )
    feats = "\n".join(f"      <li>{e(b)}</li>" for b in bullets)
    intro_html = "\n".join(f"    <p>{e(p)}</p>" for p in intro)
    if MAC_APP_STORE:
        mac_h = ui["mac_name"]
        mac_badge = (f'\n    <a class="badge" href="{MAC_APP_STORE}"><img src="{up}assets/badges/mac-{key}.svg" '
                     'width="220" height="55" alt="Download on the Mac App Store"></a>')
    else:
        mac_h, mac_badge = f'{ui["mac_name"]} — {ui["soon"]}', ""
    return f"""<!doctype html>
<html lang="{lang}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{e(ui["title"])}</title>
  <meta name="description" content="{e(promo)}">
  <meta name="keywords" content="{e(keywords)}">
  <link rel="canonical" href="{url}">
{alternates}
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="UnderBlue">
  <meta property="og:title" content="{e(ui["title"])}">
  <meta property="og:description" content="{e(promo)}">
  <meta property="og:url" content="{url}">
  <meta property="og:image" content="{SITE}/assets/og.jpg">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="628">
  <meta property="og:locale" content="{og_locale}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="apple-itunes-app" content="app-id=6815881625">
  <link rel="icon" type="image/png" href="{up}assets/favicon.png">
  <link rel="apple-touch-icon" href="{up}assets/apple-touch-icon.png">
  <link rel="stylesheet" href="{up}landing.css">
  <script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
</head>
<body>
  <header class="top">
    <a class="brand" href="{up or './'}"><img src="{up}assets/apple-touch-icon.png" width="36" height="36" alt="">UnderBlue</a>
    <nav aria-label="{e(ui["lang"])}">
      <ul class="langs">
{langs}
      </ul>
    </nav>
  </header>

  <main>
  <section class="hero">
    <h1>{e(subtitle)}</h1>
    <p class="lead">{e(promo)}</p>
    <img class="hero-img" src="{up}assets/hero.jpg" width="1600" height="960" alt="{e(alts[0])}">
  </section>

  <section class="intro">
{intro_html}
  </section>

  <section aria-label="{e(ui["shots"])}">
    <ul class="shots">
{shots}
    </ul>
  </section>

  <section>
    <h2>{e(feat_h)}</h2>
    <ul class="features">
{feats}
    </ul>
  </section>

  <section class="card cta">
    <h2>{e(ui["cta_h"])}</h2>
    <p>{e(pricing)}</p>
    <a class="badge" href="{APP_STORE}"><img src="{up}assets/badges/{key}.svg" width="180" height="60" alt="Download on the App Store"></a>
    <p class="muted small">{e(note)}</p>
  </section>

  <section class="card mac">
    <h2>{e(mac_h)}</h2>
    <p>{e(ui["mac_p"])}</p>{mac_badge}
    <img src="{up}assets/mac-batch.jpg" width="1200" height="750" loading="lazy" alt="{e(ui["mac_alt"])}">
  </section>
  </main>

  <footer>
    <p><a href="{up}support/">{e(ui["support"])}</a> · <a href="{up}privacy/">{e(ui["privacy"])}</a></p>
    <p class="muted small">© 2026 Enheart</p>
  </footer>
</body>
</html>
"""


def sitemap():
    urls = [f"{SITE}/{l[1]}" for l in LOCALES] + [f"{SITE}/support/", f"{SITE}/privacy/"]
    alt = "".join(
        f'\n    <xhtml:link rel="alternate" hreflang="{l[2]}" href="{SITE}/{l[1]}"/>' for l in LOCALES
    )
    rows = []
    for u in urls:
        extra = alt if u in urls[:len(LOCALES)] else ""
        rows.append(f"  <url>\n    <loc>{u}</loc>{extra}\n  </url>")
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
            'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n' + "\n".join(rows) + "\n</urlset>\n")


def main():
    app = Path(sys.argv[1])
    md = (app / "docs/AppStoreMetadata.md").read_text()
    captions = json.loads((app / "scripts/app_store_screenshots/captions.json").read_text())
    for loc in LOCALES:
        out = ROOT / loc[1] / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(page(loc, md, captions))
        print("wrote", out.relative_to(ROOT))
    (ROOT / "sitemap.xml").write_text(sitemap())
    print("wrote sitemap.xml")


if __name__ == "__main__":
    main()
