"""Собирает сайт подбора мебели из data/mebel.json.

Результат в docs/: index.html (визуализации), planirovki.html, podbor.html (общая страница
подбора) и по странице на каждую комнату. Вариант выбирается один раз и переносится между
страницами (параметр ?v= и localStorage). Запуск: python3 tools/build.py
"""
import html
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs"
DATA = json.loads((ROOT / "data" / "mebel.json").read_text(encoding="utf-8"))
SIZES = json.loads((ROOT / "data" / "razmery.json").read_text(encoding="utf-8"))
CSS = (ROOT / "tools" / "style.css").read_text(encoding="utf-8")
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">\n'
         '<link href="https://fonts.googleapis.com/css2?family=Onest:wght@500;600;700'
         '&family=Manrope:wght@400;500;600&family=JetBrains+Mono:wght@500&display=swap" rel="stylesheet">')
VARIANTS = ("belyj", "shalfej")
TITLE = {"belyj": "Белый", "shalfej": "Шалфей"}
# (файл, подпись, вариант: all | belyj | shalfej)
PLANS = [
    ("01", "Финал 2 — выбранная планировка", "all"),
    ("02", "План", "belyj"), ("03", "Решения", "belyj"),
    ("04", "План", "shalfej"), ("05", "Решения", "shalfej"),
    ("06", "Палитра «Шалфей и олива»", "all"),
    ("07", "Декор, свет и текстиль", "all"),
    ("08", "План с размерами", "all"),
    ("09", "Что замерить", "all"),
]
# Визуализации: (файл в vizualizacii/render, подпись, вариант: all | belyj | shalfej)
SHOTS = {
    "kg1": [("belyj-1-vhod-okno.webp", "От входа на окно", "belyj"),
            ("shalfej-1-vhod-okno.webp", "От входа на окно", "shalfej")],
    "kg2": [("belyj-2-okno-tv.webp", "От окна на ТВ", "belyj"),
            ("shalfej-2-okno-tv.webp", "От окна на ТВ", "shalfej")],
    "sp1": [("spalnya-1-okno.webp", "Спальня: вид на окно и рабочее место", "all")],
    "sp2": [("spalnya-2-shkaf-dver.webp", "Спальня: шкаф-купе и дверь", "all")],
    "pr": [("prihozhaya.webp", "Прихожая от спальни к входной двери", "all")],
}
# что показывать на странице комнаты
ROOM_SHOTS = {
    "prihozhaya": ["pr"], "kuhnya": ["kg1", "kg2"], "stolovaya": ["kg1"],
    "gostinaya": ["kg1", "kg2"], "spalnya": ["sp1", "sp2"], "rabochee-mesto": ["sp1"],
}
SWATCH = {"belyj": "#F4F3EF", "shalfej": "#8E9C8F"}

EXTRA_CSS = """
.topbar{position:sticky;top:0;z-index:5;margin:-32px calc(-1*max(16px,env(safe-area-inset-left,0px))) 0;padding:10px max(16px,env(safe-area-inset-left,0px));background:var(--bg);border-bottom:1px solid var(--line)}
.topbar-in{max-width:1080px;width:100%;margin:0 auto;display:flex;flex-direction:column;gap:10px}
.vsw{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.vsw .lbl{font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);font-weight:600}
.vsw button{font:inherit;font-size:14px;display:inline-flex;align-items:center;gap:8px;padding:7px 14px;border-radius:999px;border:1px solid var(--line);background:var(--surface);color:var(--fg);cursor:pointer}
.vsw button[aria-pressed="true"]{border-color:var(--accent);background:var(--chip);font-weight:600}
.vsw button:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.sw{border:1px solid var(--line)}
.nav{display:flex;flex-wrap:wrap;gap:6px}
.nav a{font-size:13.5px;text-decoration:none;color:var(--fg);padding:6px 12px;border-radius:999px;border:1px solid var(--line);background:var(--surface)}
.nav a[aria-current="page"]{border-color:var(--accent);background:var(--chip);font-weight:600}
.nav a:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
html[data-v="belyj"] [data-only="shalfej"],html[data-v="shalfej"] [data-only="belyj"]{display:none!important}
.vcards{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}
.vcard{font:inherit;text-align:left;color:var(--fg);display:flex;flex-direction:column;gap:8px;padding:18px;border-radius:14px;border:2px solid var(--line);background:var(--surface);cursor:pointer}
.vcard[aria-pressed="true"]{border-color:var(--accent);background:var(--chip)}
.vcard:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.vcard .vt{display:flex;align-items:center;gap:10px;font-family:var(--f-display);font-size:22px;font-weight:700}
.vcard .vt i{width:22px;height:22px;border-radius:50%;border:1px solid var(--line);display:inline-block}
.vcard .vd{color:var(--muted);font-size:14px}
.vcard .vs{font-family:var(--f-mono);font-variant-numeric:tabular-nums;font-size:15px}
@media (max-width:560px){.vcards{grid-template-columns:1fr}}
.rooms{display:flex;flex-direction:column;border-top:1px solid var(--line)}
.rooms a{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:16px;align-items:baseline;padding:14px 4px;border-bottom:1px solid var(--line);text-decoration:none;color:var(--fg)}
.rooms a:hover .rn{color:var(--accent)}
.rooms a:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.rn{font-family:var(--f-display);font-size:18px;font-weight:600}
.rc{font-size:13px;color:var(--muted)}
.rs{font-family:var(--f-mono);font-variant-numeric:tabular-nums}
.note{display:block;font-size:12px;color:var(--terra);margin-top:2px}
.photo.noimg{display:flex;align-items:center;justify-content:center;background:var(--chip);color:var(--muted);font-size:12.5px;text-align:center}
.plans{display:grid;grid-template-columns:minmax(0,1fr);gap:22px}
.plan{margin:0;display:flex;flex-direction:column;gap:8px}
.plan img{width:100%;height:auto;display:block;border-radius:10px;border:1px solid var(--line);background:#fff}
.plan figcaption{font-size:13.5px;color:var(--muted)}
.total a{color:var(--accent);font-weight:600}
.shots{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}
.shots.one{grid-template-columns:minmax(0,1fr)}
.shot{margin:0;display:flex;flex-direction:column;gap:8px}
.shot img{width:100%;height:auto;display:block;border-radius:10px;border:1px solid var(--line);background:#fff}
.shot figcaption{font-size:13.5px;color:var(--muted)}
@media (max-width:760px){.shots{grid-template-columns:1fr}}
.sizes{width:100%;border-collapse:collapse;font-size:14px}
.sizes th{text-align:left;font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);font-weight:600;padding:8px 10px;border-bottom:1px solid var(--line)}
.sizes td{padding:12px 10px;border-bottom:1px solid var(--line);vertical-align:top}
.sizes td:first-child{font-family:var(--f-display);font-weight:600;white-space:nowrap}
.sizes td.mx{font-family:var(--f-mono);font-size:13px;color:var(--accent)}
.sizes td.why{color:var(--muted);font-size:13.5px}
.tblwrap{overflow-x:auto}
.chip{display:inline-block;font-family:var(--f-body);font-size:11px;font-weight:600;letter-spacing:.04em;padding:1px 8px;border-radius:999px;border:1px solid currentColor;margin-left:8px;vertical-align:2px;white-space:nowrap}
.chip.tight{color:var(--terra)}
.chip.check{color:var(--olive)}
.sizes tr.tight td:first-child{box-shadow:inset 3px 0 0 var(--terra)}
.sizes tr.check td:first-child{box-shadow:inset 3px 0 0 var(--olive)}
.flagnote{display:block;margin-top:4px;font-size:13px}
.flagnote.tight{color:var(--terra)}
.flagnote.check{color:var(--olive)}
.series{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}
.series article{padding:16px 18px;border:1px solid var(--line);border-radius:12px;background:var(--surface);display:flex;flex-direction:column;gap:8px}
.series h3{margin:0;font-family:var(--f-display);font-size:17px;font-weight:600}
.series ul{margin:0;padding-left:18px;display:flex;flex-direction:column;gap:6px;font-size:14px}
.freeline{color:var(--muted);font-size:14px;margin:0}
@media (max-width:760px){.series{grid-template-columns:1fr}}
.dots{display:inline-flex;gap:3px;vertical-align:middle;margin-right:6px}
.dots i{width:16px;height:16px;border-radius:50%;border:1px solid var(--line);display:inline-block}
.pal{display:flex;flex-wrap:wrap;gap:10px}
.pal div{display:flex;align-items:center;gap:8px;padding:6px 12px 6px 6px;border:1px solid var(--line);border-radius:999px;background:var(--surface);font-size:13.5px}
.pal i{width:26px;height:26px;border-radius:50%;border:1px solid var(--line);display:inline-block;flex:none}
.pal small{color:var(--muted);font-size:12px}
.sizes td.cl{font-size:13.5px;min-width:170px}
.sizes td.cl.sw-note{color:var(--muted)}
.pickline{display:block;margin-top:6px;color:var(--terra);font-size:12.5px}
.pickline b{font-weight:600}
.palh{margin:10px 0 0;font-family:var(--f-body);font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);font-weight:600}
.legend{display:flex;flex-direction:column;gap:6px;font-size:14px}
@media (max-width:760px){
  .sizes,.sizes tbody,.sizes tr,.sizes td{display:block}
  .sizes thead{display:none}
  .sizes tr{padding:12px 0;border-bottom:1px solid var(--line)}
  .sizes td{border:0;padding:2px 0}
  .sizes td:first-child{white-space:normal;font-size:16px}
  .sizes td.mx::before{content:"Максимум: ";font-family:var(--f-body);color:var(--muted)}
  .sizes td.hv::before{content:"Взято: ";color:var(--muted)}
  .sizes td.cl::before{content:"Цвет: ";color:var(--muted)}
}
.pager{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap}
.pager a{text-decoration:none;color:var(--fg);padding:10px 16px;border-radius:10px;border:1px solid var(--line);background:var(--surface)}
.pager a:hover{border-color:var(--accent)}
"""

# Выставляет вариант до отрисовки (без мигания) и переносит его по ссылкам.
HEAD_JS = """<script>
(function(){var d=document.documentElement,v=null;
try{v=new URLSearchParams(location.search).get('v')}catch(e){}
if(v!=='belyj'&&v!=='shalfej'){try{v=localStorage.getItem('variant')}catch(e){}}
if(v!=='belyj'&&v!=='shalfej')v='belyj';
d.setAttribute('data-v',v);})();
</script>"""
BODY_JS = """<script>
(function(){var d=document.documentElement;
function apply(v,save){
  d.setAttribute('data-v',v);
  if(save){try{localStorage.setItem('variant',v)}catch(e){}}
  document.querySelectorAll('[data-pick]').forEach(function(b){b.setAttribute('aria-pressed',String(b.dataset.pick===v))});
  document.querySelectorAll('a[data-keep]').forEach(function(a){a.setAttribute('href',a.dataset.keep+'?v='+v)});
  try{history.replaceState(null,'','?v='+v)}catch(e){}
}
document.querySelectorAll('[data-pick]').forEach(function(b){b.addEventListener('click',function(){apply(b.dataset.pick,true)})});
apply(d.getAttribute('data-v'),false);
})();
</script>"""


def rub(n):
    return f"{n:,}".replace(",", " ") + " ₽"


def items_for(room, v):
    return [i for i in room["items"] if i["variant"] in ("all", v)]


def room_sum(room, v):
    s = 0
    for i in items_for(room, v):
        s += i["main"]["price"] * i["main"]["qty"]
        s += sum(e["price"] * e["qty"] for e in i["extras"] if e["role"] == "addon")
    return s


def per_variant(fn):
    """Один и тот же текст для каждого варианта; показывается только выбранный."""
    return "".join(f'<span data-only="{v}">{fn(v)}</span>' for v in VARIANTS)


def only(i):
    return "" if i["variant"] == "all" else f' data-only="{i["variant"]}"'


def link(p, main):
    q = f" × {p['qty']}" if p["qty"] > 1 else ""
    note = f'<span class="note">{html.escape(p["note"])}</span>' if p["note"] else ""
    cls = ' class="main"' if main else ""
    return (f'<a{cls} href="{html.escape(p["url"])}" target="_blank" rel="noopener">'
            f'<span class="shop">Лемана</span><span class="pname">{html.escape(p["name"])}{note}</span>'
            f'<span class="price">{rub(p["price"])}{q}</span></a>')


def photo(p):
    if not p["photo"]:
        return '<div class="photo noimg"><span>фото<br>по ссылке</span></div>'
    return f'<div class="photo"><img src="{p["photo"]}" alt="" loading="lazy"></div>'


def switcher():
    btns = "".join(
        f'<button type="button" data-pick="{v}" aria-pressed="false">'
        f'<span class="sw" style="background:{SWATCH[v]}"></span>{TITLE[v]}</button>' for v in VARIANTS)
    return f'<div class="vsw"><span class="lbl">Вариант</span>{btns}</div>'


def shots(keys, cols=2):
    figs = "".join(
        f'<figure class="shot"{"" if v == "all" else f" data-only=\"{v}\""}>'
        f'<a href="render/{f}" target="_blank" rel="noopener"><img src="render/{f}" alt="{c}" loading="lazy"></a>'
        f'<figcaption>{c}{"" if v == "all" else f" · {TITLE[v]}"}</figcaption></figure>'
        for k in keys for f, c, v in SHOTS[k])
    return f'<div class="shots{" one" if cols == 1 else ""}">{figs}</div>'


def nav(current):
    """Порядок вкладок: визуализации (главная), планировки, общая страница подбора, комнаты."""
    def tab(file, name, key):
        cur = ' aria-current="page"' if current == key else ""
        return f'<a href="{file}" data-keep="{file}"{cur}>{name}</a>'
    links = [tab("index.html", "Визуализации", "vizualizacii"),
             tab("planirovki.html", "Планировки", "planirovki"),
             tab("razmery.html", "Размеры", "razmery"),
             tab("podbor.html", "Общая", "podbor")]
    links += [tab(f'{r["id"]}.html', r["name"], r["id"]) for r in DATA["rooms"]]
    return f'<nav class="nav" aria-label="Страницы">{"".join(links)}</nav>'


def page(title, current, body):
    return ('<!doctype html>\n<html lang="ru" data-v="belyj">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            f'<title>{title}</title>\n{HEAD_JS}\n{FONTS}\n<style>{CSS}{EXTRA_CSS}</style>\n</head>\n<body>\n'
            f'<div class="topbar"><div class="topbar-in">{switcher()}{nav(current)}</div></div>\n'
            f'<div class="wrap" style="margin-top:28px">{body}</div>\n{BODY_JS}\n</body>\n</html>\n')


def room_page(idx, room):
    rows = ""
    for i in room["items"]:
        extras = "".join(link(e, False) for e in i["extras"])
        label = '<div class="alt-label">ещё / в комплект</div>' if i["extras"] else ""
        rows += (f'<div class="item"{only(i)}>{photo(i["main"])}<div class="what"><h3>{html.escape(i["role"])}</h3>'
                 f'<div class="size">{html.escape(i["size"])}</div><div class="why">{html.escape(i["why"])}</div></div>'
                 f'<div class="links">{link(i["main"], True)}{label}{extras}</div></div>\n')
    rooms = DATA["rooms"]
    prev = rooms[idx - 1] if idx > 0 else None
    nxt = rooms[idx + 1] if idx < len(rooms) - 1 else None
    pager = (f'<a href="{prev["id"]}.html" data-keep="{prev["id"]}.html">← {prev["name"]}</a>' if prev
             else '<a href="podbor.html" data-keep="podbor.html">← Общая</a>')
    pager += (f'<a href="{nxt["id"]}.html" data-keep="{nxt["id"]}.html">{nxt["name"]} →</a>' if nxt
              else '<a href="podbor.html" data-keep="podbor.html">Общая →</a>')
    total = per_variant(lambda v: f'<b>{rub(room_sum(room, v))}</b> '
                                  f'<span>{len(items_for(room, v))} позиций</span>')
    eyebrow = per_variant(lambda v: f"вариант «{TITLE[v]}»")
    body = (f'<header><div class="eyebrow">Шишкина · {eyebrow} · {room["name"]}</div>'
            f'<h1>{room["name"]}</h1>'
            f'<div class="total">{total}<span>Цены {DATA["store"]} на {DATA["prices_date"]}.</span></div></header>'
            f'<section><h2>Визуализации</h2>{shots(ROOM_SHOTS[room["id"]], 1 if len(ROOM_SHOTS[room["id"]]) == 1 else 2)}</section>'
            f'<section><div class="list">{rows}</div></section>'
            f'<div class="pager">{pager}</div>')
    return page(f'{room["name"]} · Шишкина', room["id"], body)


def index_page():
    totals = {v: sum(room_sum(r, v) for r in DATA["rooms"]) for v in VARIANTS}
    cards = "".join(
        f'<button type="button" class="vcard" data-pick="{v}" aria-pressed="false">'
        f'<span class="vt"><i style="background:{SWATCH[v]}"></i>{TITLE[v]}</span>'
        f'<span class="vd">{html.escape(DATA["variants"][v])}</span>'
        f'<span class="vs">{rub(totals[v])}</span></button>' for v in VARIANTS)
    rows = "".join(
        f'<a href="{r["id"]}.html" data-keep="{r["id"]}.html"><span><span class="rn">{r["name"]}</span><br>'
        f'<span class="rc">{per_variant(lambda v: f"{len(items_for(r, v))} позиций")}</span></span>'
        f'<span class="rs">{per_variant(lambda v: rub(room_sum(r, v)))}</span></a>' for r in DATA["rooms"])
    body = (f'<header><div class="eyebrow">Шишкина · Финал 2 · {DATA["store"]}</div>'
            f'<h1>Мебель для квартиры</h1>'
            f'<p class="lead">Выберите цветовой вариант — он сохранится на всех страницах. '
            f'Дальше переключайтесь между комнатами сверху или в списке ниже.</p></header>'
            f'<section><h2>Вариант</h2><div class="vcards">{cards}</div></section>'
            f'<div class="total"><b>{per_variant(lambda v: rub(totals[v]))}</b>'
            f'<span>Все комнаты, без матраса, ТВ, монтажа кухни, столешницы и блока питания подсветки.</span></div>'
            f'<section><h2>Комнаты</h2><div class="rooms">{rows}</div></section>')
    return page("Мебель · Шишкина", "podbor", body)


def plans_page():
    figs = "".join(
        f'<figure class="plan"{"" if v == "all" else f" data-only=\"{v}\""}>'
        f'<a href="planirovki/{f}.png" target="_blank" rel="noopener"><img src="planirovki/{f}.png" alt="{c}" loading="lazy"></a>'
        f'<figcaption>{c}{"" if v == "all" else f" · {TITLE[v]}"}</figcaption></figure>' for f, c, v in PLANS)
    body = ('<header><div class="eyebrow">Шишкина · Финал 2</div><h1>Планировки</h1>'
            '<p class="lead">Листы выбранной планировки. Планы и решения показаны для выбранного варианта; '
            'клик по листу открывает его целиком.</p>'
            '<div class="total"><a href="planirovki/planirovki.pdf" target="_blank" rel="noopener">Все листы одним PDF</a></div></header>'
            f'<section><div class="plans">{figs}</div></section>')
    return page("Планировки · Шишкина", "planirovki", body)


def shots_page():
    body = ('<header><div class="eyebrow">Шишкина · Финал 2</div><h1>Визуализации</h1>'
            '<p class="lead">Картинки сделаны нейросетью по плану и подбору мебели. '
            'Пропорции приблизительные, цвета и размеры смотрите в планах и подборе. '
            'Вариант «Белый» или «Шалфей» переключается сверху.</p></header>'
            f'<section><h2>Кухня-гостиная</h2>{shots(["kg1", "kg2"])}</section>'
            f'<section><h2>Спальня</h2>{shots(["sp1", "sp2"])}</section>'
            f'<section><h2>Прихожая</h2>{shots(["pr"], 1)}</section>')
    return page("Визуализации · Шишкина", "vizualizacii", body)


FLAGS = {"tight": '<span class="chip tight">впритык</span>', "check": '<span class="chip check">проверить</span>'}


def series_block():
    sr = SIZES["series"]
    cards = "".join(
        f'<article><h3>{html.escape(b["h"])}</h3><ul>{"".join(f"<li>{html.escape(t)}</li>" for t in b["t"])}</ul></article>'
        for b in sr["blocks"])
    return (f'<section id="series"><h2>{html.escape(sr["title"])}</h2><div class="series">{cards}</div>'
            f'<p class="freeline">{html.escape(sr["free"])}</p></section>')


def dots(sw):
    return '<span class="dots">' + "".join(f'<i style="background:{c}"></i>' for c in sw) + '</span>'


def pick_line(pk):
    return f'<span class="pickline">{dots(pk["sw"])}<b>В подборе:</b> {html.escape(pk["t"])}</span>'


def color_cell(r):
    if "colorV" in r:
        inner = "".join(
            f'<span data-only="{v}">{dots(c["sw"])}{html.escape(c["t"])}'
            + (pick_line(r["pickV"][v]) if v in r.get("pickV", {}) else "") + '</span>'
            for v, c in r["colorV"].items())
    elif "color" in r:
        inner = f'{dots(r["color"]["sw"])}{html.escape(r["color"]["t"])}' + (pick_line(r["pick"]) if "pick" in r else "")
    else:
        inner = ""
    return f'<td class="cl">{inner}</td>'


def palette_block():
    pl = SIZES["palette"]
    groups = ""
    for g in pl["groups"]:
        chips = "".join(f'<div><i style="background:{c["h"]}"></i><span>{html.escape(c["n"])}<br><small>{html.escape(c["t"])}</small></span></div>'
                        for c in g["colors"])
        groups += f'<h3 class="palh">{html.escape(g["h"])}</h3><div class="pal">{chips}</div>'
    return f'<section><h2>Палитра <small>{html.escape(pl["note"])}</small></h2>{groups}</section>'


def sizes_page():
    secs = ""
    for g in SIZES["groups"]:
        rows = "".join(
            f'<tr class="{r.get("flag", "")}"><td>{html.escape(r["name"])}{FLAGS.get(r.get("flag"), "")}</td>'
            f'<td class="hv">{html.escape(r["have"])}</td>{color_cell(r)}<td class="mx">{html.escape(r["max"])}</td>'
            f'<td class="why">{html.escape(r["why"])}'
            + (f'<span class="flagnote {r["flag"]}">{html.escape(r["flagNote"])}</span>' if r.get("flag") else "")
            + '</td></tr>'
            for r in g["rows"])
        secs += (f'<section><h2>{g["room"]} <small><a href="{g["id"]}.html" data-keep="{g["id"]}.html">страница комнаты</a></small></h2>'
                 f'<div class="tblwrap"><table class="sizes"><thead><tr><th>Что</th><th>Взято в подборе</th><th>Цвет по дизайну</th>'
                 f'<th>Максимум</th><th>Что ограничивает</th></tr></thead><tbody>{rows}</tbody></table></div></section>')
    body = ('<header><div class="eyebrow">Шишкина · Финал 2</div><h1>Размеры и пределы</h1>'
            f'<p class="lead">{html.escape(SIZES["note"])}</p>'
            '<div class="legend">' + "".join(f'<div>{FLAGS[l["flag"]]} {html.escape(l["text"])}</div>' for l in SIZES["legend"])
            + f'</div></header>{palette_block()}{secs}{series_block()}')
    return page("Размеры · Шишкина", "razmery", body)


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "img").mkdir(parents=True)
    used = set()
    for n, r in enumerate(DATA["rooms"]):
        (OUT / f'{r["id"]}.html').write_text(room_page(n, r), encoding="utf-8")
        used |= {i["main"]["photo"] for i in r["items"] if i["main"]["photo"]}
    (OUT / "podbor.html").write_text(index_page(), encoding="utf-8")
    (OUT / "planirovki.html").write_text(plans_page(), encoding="utf-8")
    (OUT / "index.html").write_text(shots_page(), encoding="utf-8")
    (OUT / "razmery.html").write_text(sizes_page(), encoding="utf-8")
    (OUT / "render").mkdir()
    for f in {f for lst in SHOTS.values() for f, _, _ in lst}:
        shutil.copy(ROOT / "vizualizacii" / "render" / f, OUT / "render" / f)
    shutil.copytree(ROOT / "planirovki", OUT / "planirovki", ignore=shutil.ignore_patterns("README.md"))
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    for p in used:
        shutil.copy(ROOT / p, OUT / p)
    print({v: sum(room_sum(r, v) for r in DATA["rooms"]) for v in VARIANTS}, len(used), "фото")


if __name__ == "__main__":
    main()
