"""Builds the AnkiWeb promo HTML pages; each is rendered to PNG with tools/render.py."""
from pathlib import Path

D = Path(__file__).parent

BASE_CSS = """
@font-face{font-family:F;src:url(fredoka-latin-wght-normal.woff2) format('woff2');font-weight:300 700}
*{box-sizing:border-box;margin:0}
html,body{width:WIDTHpx;height:HEIGHTpx;overflow:hidden}
body{font-family:F,sans-serif;color:#3b2416;-webkit-font-smoothing:antialiased}
.shot{display:block;border-radius:18px;box-shadow:0 0 0 1px rgba(59,36,22,.10),0 24px 50px -22px rgba(59,36,22,.45)}
.k{display:inline-block;font-size:15px;font-weight:600;letter-spacing:.2px;color:#5e9447;background:#e7f0dc;border-radius:999px;padding:5px 13px;margin-bottom:14px}
h2{font-size:40px;line-height:1.08;font-weight:650;letter-spacing:-.4px}
p.s{font-size:19px;line-height:1.45;color:#7a5a44;margin-top:12px;max-width:440px}
.awn{position:absolute;left:0;right:0;top:0;height:30px;background:repeating-linear-gradient(90deg,#8dbf6a 0 44px,#fff4df 44px 88px)}
.sc{position:absolute;left:0;right:0;top:30px;height:22px;
 background:radial-gradient(circle at 22px 0,#8dbf6a 21px,transparent 22px) 0 0/88px 22px repeat-x,radial-gradient(circle at 66px 0,#fff4df 21px,transparent 22px) 0 0/88px 22px repeat-x;
 filter:drop-shadow(0 4px 3px rgba(0,0,0,.2))}
"""


def page(name, w, h, body, extra_css=""):
    html = f"<!doctype html><html><head><meta charset=utf-8><style>{BASE_CSS.replace('WIDTH', str(w)).replace('HEIGHT', str(h))}{extra_css}</style></head><body>{body}</body></html>"
    (D / f"{name}.html").write_text(html, encoding="utf-8")
    print(name, w, h)


# 1. hero ---------------------------------------------------------------------
page("hero", 1400, 640, """
<div class=awn></div><div class=sc></div>
<div class=left>
  <img src=cookie.svg class=logo>
  <h1>Cookie Recall</h1>
  <p class=tag>The Cookie Clicker that only bakes<br>when you review.</p>
  <ul>
    <li><img src=cookie.svg>Every review bakes cookies</li>
    <li><img src=golden.svg>Golden cookies, combos &amp; streaks</li>
    <li><span>✓</span>Built for honest learning</li>
  </ul>
</div>
<img class="shot bk" src=bk_pistachio.png>
""", """
body{background:radial-gradient(120% 90% at 15% 10%,#2a4d44,#1e3b34 60%,#173029);color:#f3efe2;position:relative}
body::after{content:"";position:absolute;inset:0;background-image:radial-gradient(rgba(255,255,255,.05) 1px,transparent 1.4px);background-size:7px 9px;pointer-events:none}
.left{position:absolute;left:70px;top:110px;width:470px;z-index:2}
.logo{width:76px;height:76px;filter:drop-shadow(0 8px 10px rgba(0,0,0,.35))}
h1{font-size:68px;font-weight:700;letter-spacing:-1px;line-height:1;margin-top:14px;color:#fff4df;text-shadow:0 4px 0 rgba(0,0,0,.25)}
.tag{font-size:25px;line-height:1.35;color:#d9e4d6;margin-top:14px}
ul{list-style:none;padding:0;margin-top:28px;display:flex;flex-direction:column;gap:12px}
li{display:flex;align-items:center;gap:12px;font-size:19px;font-weight:550;color:#f3efe2}
li img{width:30px;height:30px}
li span{width:30px;height:30px;border-radius:50%;background:#8dbf6a;color:#1e3b34;display:grid;place-items:center;font-weight:700}
.bk{position:absolute;right:-40px;top:110px;width:820px;transform:rotate(-2.5deg);box-shadow:0 0 0 6px #6b4a33,0 0 0 9px #4d3323,0 40px 70px -20px rgba(0,0,0,.6);border-radius:16px;z-index:1}
""")

# 2. study -----------------------------------------------------------------------
page("study", 1400, 460, """
<div class=t><span class=k>One click</span><h2>From your decks straight<br>into reviews</h2>
<p class=s>A "Study now" card sits above your decks, and every deck gets its own ▶ Study button. Or just press <b>S</b>. No detour through the overview screen.</p></div>
<img class="shot st" src=study.png>
""", """
body{background:#f6eedf;position:relative}
.t{position:absolute;left:80px;top:95px;width:480px}
.st{position:absolute;right:80px;top:80px;width:700px;background:#f6eedf}
""")

# 3. review ------------------------------------------------------------------------
page("review", 1400, 700, """
<div class=t><span class=k>While you review</span><h2>Every answer bakes.<br>Catch the golden cookie.</h2>
<p class=s>A small counter shows "+N" on every answer, your combo and your next purchase. Golden cookies pop up next to the card: Lucky, a ×7 Frenzy or a cookie rain.</p></div>
<div class=frame><img src=review_top.png class=top><img src=review_buttons.png class=btns></div>
""", """
body{background:#efe5d2;position:relative}
.t{position:absolute;left:80px;top:60px;width:1240px;display:grid;grid-template-columns:560px 1fr;column-gap:60px}
.t .k{grid-column:1;justify-self:start}.t h2{grid-column:1}.t p.s{grid-column:2;grid-row:2;align-self:end;max-width:520px;margin:0}
.frame{position:absolute;left:80px;right:80px;top:250px;height:400px;border-radius:22px;background:#f6eedf;overflow:hidden;
 box-shadow:0 0 0 1px rgba(59,36,22,.1),0 30px 60px -28px rgba(59,36,22,.5)}
.top{position:absolute;left:44px;top:16px;width:1100px}
.btns{position:absolute;left:50%;bottom:16px;width:560px;transform:translateX(-50%)}
""")

# 4. palettes ------------------------------------------------------------------------
cards = "".join(
    f'<figure><img class=shot src=bk_{p}.png><figcaption><i style="background:{c}"></i>{n}</figcaption></figure>'
    for p, n, c in [("pistachio", "Pistachio", "#8dbf6a"), ("raspberry", "Raspberry", "#f29bb8"), ("blueberry", "Blueberry", "#8cc4ef"),
                    ("chocolate", "Chocolate", "#e3a857"), ("lavender", "Lavender", "#b9a2ec")])
page("palettes", 1400, 740, f"""
<div class=t><span class=k>Make it yours</span><h2>Five flavours, light or dark</h2>
<p class=s>Pick a palette and the bakery, the review counter, your cards and all of Anki follow along.</p></div>
<div class=grid>{cards}</div>
""", """
body{background:#f6eedf;position:relative}
.t{position:absolute;left:80px;top:56px;width:1240px}
.t p.s{max-width:none}
.grid{position:absolute;left:80px;right:80px;top:250px;display:grid;grid-template-columns:repeat(6,1fr);gap:28px 26px}
figure{grid-column:span 2;margin:0}
figure:nth-child(4){grid-column:2/span 2}
figure img{width:100%}
figcaption{display:flex;align-items:center;gap:8px;justify-content:center;margin-top:10px;font-size:17px;font-weight:600}
figcaption i{width:14px;height:14px;border-radius:50%}
""")

# 5. progression ---------------------------------------------------------------------
page("progression", 1400, 640, """
<div class=t><span class=k>Months of progression</span><h2>14 buildings,<br>142 upgrades,<br>135 achievements</h2>
<p class=s>Buildings never bake on their own: they multiply what each review is worth. Daily missions, streaks and diplomas keep the long game going.</p></div>
<img class="shot a" src=shop.png><img class="shot b" src=ach.png>
""", """
body{background:#efe5d2;position:relative}
.t{position:absolute;left:80px;top:120px;width:470px}
.a{position:absolute;left:600px;top:50px;width:500px;transform:rotate(-1.5deg)}
.b{position:absolute;left:920px;top:150px;width:410px;transform:rotate(2deg)}
""")

# 6. dark ---------------------------------------------------------------------------------
page("dark", 1400, 600, """
<div class=t><span class=k>Night mode</span><h2>Just as cosy at night</h2>
<p class=s>Paper-card reviews, coloured answer buttons and a matching theme for every Anki window. Your card templates are never modified.</p></div>
<div class=frame><img src=dark_top.png class=top><img src=dark_buttons.png class=btns></div>
""", """
body{background:#132420;color:#f3efe2;position:relative}
.k{background:#2c5249;color:#b9dca0}
p.s{color:#b5c2b6}
.t{position:absolute;left:80px;top:150px;width:440px}
.frame{position:absolute;left:580px;top:80px;width:740px;height:420px;border-radius:22px;background:#1b302a;overflow:hidden;box-shadow:0 0 0 1px rgba(255,255,255,.08),0 30px 60px -24px rgba(0,0,0,.7)}
.top{position:absolute;left:0;top:14px;width:740px}
.btns{position:absolute;left:50%;bottom:22px;width:420px;transform:translateX(-50%)}
""")
