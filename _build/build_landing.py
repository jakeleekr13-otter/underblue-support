"""Build the localized UnderBlue landing pages.

Store copy comes from the app repo's docs/AppStoreMetadata.md and
scripts/app_store_screenshots/captions.json. Only page chrome is written here.

Usage: python3 -I _build/build_landing.py <path to the underblue app repo>
Pages: / (en), /ko/, /ja/, /zh-hans/, /zh-hant/, /es/ and sitemap.xml.

Guides: _build/guides/<locale key>.json holds the guide articles for one
language. Each guide is written to <locale dir>/guides/<slug>/index.html.
A language without a JSON file, or without a slug, has no page for it.
The landing page of a language links to its guides. Guide text is site-only
copy, so it lives here and not in the app repo.
"""
import html
import json
import re
import sys
from pathlib import Path

SITE = "https://jakeleekr13-otter.github.io/underblue-support"
APP_STORE = "https://apps.apple.com/app/id6815881625"
# A sister app by the same seller (Enheart), linked from every landing page (Jake, 5 Nov 2026).
SISTER_APP = "https://apps.apple.com/app/id6813368660"
# The Mac app is a separate App Store record. Set its link when it is live;
# the Mac section then shows a Mac App Store badge instead of "coming soon".
MAC_APP_STORE = None
ROOT = Path(__file__).resolve().parent.parent
GUIDES_DIR = ROOT / "_build" / "guides"
GUIDE_ORDER = ["underwater-photo-tips", "underwater-video-tips",
               "smartphone-underwater-housing", "action-camera-underwater",
               "underwater-color-correction-apps"]

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
        "sister_h": "Also by Enheart", "sister_p": "a dive logbook for scuba divers and freedivers.",
    },
    "ko": {
        "title": "UnderBlue — 수중 사진·영상 색보정 앱 (iPhone)",
        "mac_name": "Mac 버전", "soon": "출시 예정",
        "mac_p": "다이빙 한 번의 사진과 영상을 Mac에서 한꺼번에 보정하세요.",
        "mac_alt": "여러 다이빙 사진과 영상을 한 번에 보정하는 Mac용 UnderBlue",
        "cta_h": "무료로 써 보세요",
        "support": "지원", "privacy": "개인정보 처리방침", "lang": "언어",
        "shots": "스크린샷",
        "sister_h": "Enheart의 다른 앱", "sister_p": "스쿠버 다이버와 프리다이버를 위한 다이브 로그북입니다.",
    },
    "ja": {
        "title": "UnderBlue — 水中写真・水中動画の色補正アプリ（iPhone）",
        "mac_name": "Mac版", "soon": "近日公開",
        "mac_p": "1回のダイビングの写真とビデオを、Macでまとめて補正できます。",
        "mac_alt": "ダイビングの写真とビデオをまとめて補正するMac版UnderBlue",
        "cta_h": "無料で試せます",
        "support": "サポート", "privacy": "プライバシーポリシー", "lang": "言語",
        "shots": "スクリーンショット",
        "sister_h": "Enheartのほかのアプリ", "sister_p": "スクーバダイバーとフリーダイバーのためのダイブログブックです。",
    },
    "zh-hans": {
        "title": "UnderBlue — 水下照片与视频色彩校正 App（iPhone）",
        "mac_name": "Mac 版", "soon": "即将推出",
        "mac_p": "在 Mac 上一次批量校正整次潜水的照片和视频。",
        "mac_alt": "在 Mac 上批量校正潜水照片和视频的 UnderBlue",
        "cta_h": "免费试用",
        "support": "支持", "privacy": "隐私政策", "lang": "语言",
        "shots": "截图",
        "sister_h": "Enheart 的其他应用", "sister_p": "为水肺潜水员和自由潜水员打造的潜水日志。",
    },
    "zh-hant": {
        "title": "UnderBlue — 水下照片與影片色彩校正 App（iPhone）",
        "mac_name": "Mac 版", "soon": "即將推出",
        "mac_p": "在 Mac 上一次批次校正整趟潛水的照片與影片。",
        "mac_alt": "在 Mac 上批次校正潛水照片與影片的 UnderBlue",
        "cta_h": "免費試用",
        "support": "支援", "privacy": "隱私權政策", "lang": "語言",
        "shots": "螢幕截圖",
        "sister_h": "Enheart 的其他 App", "sister_p": "為水肺潛水員與自由潛水員打造的潛水日誌。",
    },
    "es": {
        "title": "UnderBlue — Corrige el color de tus fotos y vídeos submarinos (iPhone)",
        "mac_name": "UnderBlue para Mac", "soon": "muy pronto",
        "mac_p": "Corrige toda una inmersión en un solo lote. Fotos y vídeos juntos, en tu Mac.",
        "mac_alt": "UnderBlue para Mac corrigiendo un lote de fotos y vídeos de buceo",
        "cta_h": "Pruébala gratis",
        "support": "Soporte", "privacy": "Política de privacidad", "lang": "Idioma",
        "shots": "Capturas de pantalla",
        "sister_h": "Más apps de Enheart", "sister_p": "un diario de inmersiones para buceadores y apneístas.",
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


def load_guides():
    out = {}
    for loc in LOCALES:
        f = GUIDES_DIR / f"{loc[0]}.json"
        if f.exists():
            data = json.loads(f.read_text())
            unknown = set(data["guides"]) - set(GUIDE_ORDER)
            assert not unknown, f"{f.name}: unknown guide slugs {unknown}"
            out[loc[0]] = data
    return out


def guide_list(key, guides, up, skip=None):
    g = guides[key]["guides"]
    return "\n".join(
        f'      <li><img src="{up}assets/guides/{s}.svg" width="640" height="320" loading="lazy" alt="{html.escape(g[s]["h1"])}">'
        f'<a href="{up}{dict((l[0], l[1]) for l in LOCALES)[key]}guides/{s}/">{html.escape(g[s]["h1"])}</a>'
        f'<span class="muted small">{html.escape(g[s]["description"])}</span></li>'
        for s in GUIDE_ORDER if s in g and s != skip
    )


def page(loc, md, captions, guides):
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
    guides_html = ""
    if key in guides:
        gui = guides[key]["ui"]
        guides_html = f"""  <section>
    <h2>{e(gui["guides_h"])}</h2>
    <ul class="guides">
{guide_list(key, guides, up)}
    </ul>
  </section>

"""
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

{guides_html}  <section class="card cta">
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

  <section class="card sister">
    <h2>{e(ui["sister_h"])}</h2>
    <p><a href="{SISTER_APP}">Bubbly Dive Logbook</a> — {e(ui["sister_p"])}</p>
  </section>
  </main>

  <footer>
    <p><a href="{up}support/">{e(ui["support"])}</a> · <a href="{up}privacy/">{e(ui["privacy"])}</a></p>
    <p class="muted small">© 2026 Enheart</p>
  </footer>
</body>
</html>
"""


def guide_page(loc, slug, guides):
    key, rel, lang, _, _, og_locale = loc
    e = html.escape
    data = guides[key]
    ui, g = data["ui"], data["guides"][slug]
    path = f"{rel}guides/{slug}/"
    url = f"{SITE}/{path}"
    up = "../" * path.count("/")
    have = [l for l in LOCALES if l[0] in guides and slug in guides[l[0]]["guides"]]
    alternates = "\n".join(
        f'  <link rel="alternate" hreflang="{l[2]}" href="{SITE}/{l[1]}guides/{slug}/">' for l in have
    )
    if any(l[0] == "en" for l in have):
        alternates += f'\n  <link rel="alternate" hreflang="x-default" href="{SITE}/guides/{slug}/">'
    langs = "\n".join(
        f'      <li><a href="{up}{l[1]}guides/{slug}/" hreflang="{l[2]}" lang="{l[2]}"'
        + (' aria-current="page"' if l[0] == key else "") + f">{NATIVE[l[0]]}</a></li>"
        for l in have
    )
    ld = {
        "@context": "https://schema.org", "@type": "Article",
        "headline": g["h1"], "description": g["description"], "inLanguage": lang,
        "image": f"{SITE}/assets/og.jpg", "mainEntityOfPage": url,
        # A guide can carry its own dates; otherwise the file's dates apply.
        "datePublished": g.get("published", data["published"]),
        "dateModified": g.get("modified", data.get("modified", g.get("published", data["published"]))),
        "author": {"@type": "Organization", "name": "Enheart"},
        "publisher": {"@type": "Organization", "name": "Enheart"},
        "about": {"@type": "SoftwareApplication", "name": "UnderBlue", "operatingSystem": "iOS",
                  "applicationCategory": "MultimediaApplication", "installUrl": APP_STORE},
    }

    def block(sec):
        out = [f'    <h2>{e(sec["h"])}</h2>']
        out += [f"    <p>{e(t)}</p>" for t in sec.get("p", [])]
        if sec.get("ul"):
            out.append('    <ul>\n' + "\n".join(f"      <li>{e(t)}</li>" for t in sec["ul"]) + "\n    </ul>")
        if sec.get("table"):
            # table: {"head": [...], "rows": [[...], ...]}; the first cell of a row is its header.
            t = sec["table"]
            head = "".join(f'<th scope="col">{e(c)}</th>' for c in t["head"])
            rows = "\n".join(
                f'        <tr><th scope="row">{e(r[0])}</th>' + "".join(f"<td>{e(c)}</td>" for c in r[1:]) + "</tr>"
                for r in t["rows"]
            )
            assert all(len(r) == len(t["head"]) for r in t["rows"]), f'{sec["h"]}: row width'
            out.append(f'    <div class="table-wrap"><table>\n      <thead><tr>{head}</tr></thead>\n'
                       f'      <tbody>\n{rows}\n      </tbody>\n    </table></div>')
        out += [f"    <p>{e(t)}</p>" for t in sec.get("p_after", [])]
        if sec.get("src"):
            srcs = sec["src"] if isinstance(sec["src"], list) else [sec["src"]]
            links = ", ".join(f'<a href="{e(x["href"])}">{e(x["label"])}</a>' for x in srcs)
            out.append(f'    <p class="muted small">{e(ui["source"])}: {links}</p>')
        return "  <section>\n" + "\n".join(out) + "\n  </section>"

    body = "\n\n".join(block(sec) for sec in g["sections"])
    intro = "\n".join(f'    <p class="lead">{e(t)}</p>' for t in g["intro"])
    more = guide_list(key, guides, up, skip=slug)
    return f"""<!doctype html>
<html lang="{lang}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{e(g["title"])}</title>
  <meta name="description" content="{e(g["description"])}">
  <link rel="canonical" href="{url}">
{alternates}
  <meta property="og:type" content="article">
  <meta property="og:site_name" content="UnderBlue">
  <meta property="og:title" content="{e(g["title"])}">
  <meta property="og:description" content="{e(g["description"])}">
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
    <a class="brand" href="{up}{rel}"><img src="{up}assets/apple-touch-icon.png" width="36" height="36" alt="">UnderBlue</a>
    <nav aria-label="{e(UI[key]["lang"])}">
      <ul class="langs">
{langs}
      </ul>
    </nav>
  </header>

  <main class="article">
  <article>
  <header class="article-head">
    <p class="muted small"><a href="{up}{rel}">UnderBlue</a> › {e(ui["guides_h"])}</p>
    <h1>{e(g["h1"])}</h1>
    <img class="art" src="{up}assets/guides/{slug}.svg" width="640" height="320" alt="{e(g["h1"])}">
{intro}
  </header>

{body}

  <section class="card cta">
    <h2>{e(ui["cta_h"])}</h2>
    <p>{e(g["cta"])}</p>
    <p>{e(ui["cta_p"])}</p>
    <a class="badge" href="{APP_STORE}"><img src="{up}assets/badges/{key}.svg" width="180" height="60" alt="Download on the App Store"></a>
    <img class="cta-img" src="{up}assets/hero.jpg" width="1600" height="960" loading="lazy" alt="{e(ui["hero_alt"])}">
  </section>
  </article>

  <nav class="more" aria-label="{e(ui["more"])}">
    <h2>{e(ui["more"])}</h2>
    <ul class="guides">
{more}
    </ul>
  </nav>
  </main>

  <footer>
    <p><a href="{up}{rel}">UnderBlue</a> · <a href="{up}support/">{e(UI[key]["support"])}</a> · <a href="{up}privacy/">{e(UI[key]["privacy"])}</a></p>
    <p class="muted small">© 2026 Enheart</p>
  </footer>
</body>
</html>
"""


def sitemap(guides):
    urls = [f"{SITE}/{l[1]}" for l in LOCALES] + [f"{SITE}/support/", f"{SITE}/privacy/"]
    alt = "".join(
        f'\n    <xhtml:link rel="alternate" hreflang="{l[2]}" href="{SITE}/{l[1]}"/>' for l in LOCALES
    )
    rows = []
    for u in urls:
        extra = alt if u in urls[:len(LOCALES)] else ""
        rows.append(f"  <url>\n    <loc>{u}</loc>{extra}\n  </url>")
    for slug in GUIDE_ORDER:
        have = [l for l in LOCALES if l[0] in guides and slug in guides[l[0]]["guides"]]
        galt = "".join(
            f'\n    <xhtml:link rel="alternate" hreflang="{l[2]}" href="{SITE}/{l[1]}guides/{slug}/"/>'
            for l in have
        )
        for l in have:
            rows.append(f"  <url>\n    <loc>{SITE}/{l[1]}guides/{slug}/</loc>{galt}\n  </url>")
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
            'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n' + "\n".join(rows) + "\n</urlset>\n")


def main():
    app = Path(sys.argv[1])
    md = (app / "docs/AppStoreMetadata.md").read_text()
    captions = json.loads((app / "scripts/app_store_screenshots/captions.json").read_text())
    guides = load_guides()
    for loc in LOCALES:
        out = ROOT / loc[1] / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(page(loc, md, captions, guides))
        print("wrote", out.relative_to(ROOT))
        for slug in GUIDE_ORDER:
            if loc[0] in guides and slug in guides[loc[0]]["guides"]:
                out = ROOT / loc[1] / "guides" / slug / "index.html"
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text(guide_page(loc, slug, guides))
                print("wrote", out.relative_to(ROOT))
    (ROOT / "sitemap.xml").write_text(sitemap(guides))
    print("wrote sitemap.xml")


if __name__ == "__main__":
    main()
