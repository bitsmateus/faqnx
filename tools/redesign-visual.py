# -*- coding: utf-8 -*-
"""Redesign visual da Central de Ajuda NX — patch cirurgico no index.html.
Nao altera conteudo salvo no Postgres: so render + CSS."""
import re, os, sys, json

SRC = 'index.html'
html = open(SRC, encoding='utf-8').read()
orig_len = len(html)
applied = []

def sub1(pattern, repl, name, flags=0, count=1):
    global html
    new, n = re.subn(pattern, lambda m: repl, html, count=count, flags=flags)
    if n == 0:
        print('!! FALHOU:', name); sys.exit(1)
    html = new; applied.append(name)

def rep(old, new, name):
    global html
    if old not in html:
        print('!! FALHOU (literal):', name); sys.exit(1)
    html = html.replace(old, new, 1); applied.append(name)

# ══════════════════════════════════════════════════════════
# 1. ICONES — extrai o corpo dos SVGs do lucide-static
# ══════════════════════════════════════════════════════════
ICON_DIR = 'node_modules/lucide-static/icons'
NEEDED = """message-circle send camera thumbs-up thumbs-down mail clipboard-list megaphone
smartphone phone chart-column trending-up image calendar alarm-clock cake users user id-card
zap globe columns-3 filter contact pin type tag circle-check ticket clock file-text bookmark
star plug link webhook building building-2 target bot brain settings wrench house headset lock
signal scroll-text download shuffle compass life-buoy rocket key shopping-cart play music
briefcase bell database palette circle-alert puzzle paperclip hand refresh-cw satellite-dish
circle-help graduation-cap search chevron-right x plus trash-2 pencil menu lightbulb
triangle-alert octagon-alert flask-conical arrow-right folder book-open sparkles upload
inbox layout-grid list-checks""".split()

def body_of(name):
    s = open(os.path.join(ICON_DIR, name + '.svg'), encoding='utf-8').read()
    s = re.sub(r'<!--.*?-->', '', s, flags=re.S)          # tira o comentario de licenca
    inner = re.search(r'<svg\b[^>]*>(.*)</svg>', s, re.S).group(1)
    return re.sub(r'\s+', ' ', inner).strip()

icons = {n: body_of(n) for n in NEEDED}
ICONS_JS = 'const ICONS=' + json.dumps(icons, ensure_ascii=False, separators=(',', ':')) + ';'

def data_uri(name, color):
    inner = icons[name]
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
           'stroke="%s" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">%s</svg>' % (color, inner))
    for a, b in [('#', '%23'), ('"', "'"), ('<', '%3C'), ('>', '%3E'), ('\n', '')]:
        svg = svg.replace(a, b)
    return 'url("data:image/svg+xml,%s")' % svg

# ══════════════════════════════════════════════════════════
# 2. TOKENS + TIPOGRAFIA
# ══════════════════════════════════════════════════════════
rep("""<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">""",
    """<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:opsz,wght@14..32,400..700&display=swap" rel="stylesheet">""",
    'fonte Inter variavel + preconnect')

rep(""":root{
  --brand:#5A64F2;--brand-dark:#4550d4;--brand-bg:#f0f1fe;
  --t1:#1f2937;--t2:#374151;--t3:#6b7280;--t4:#9ca3af;
  --bd:#e5e7eb;--bd2:#f3f4f6;--bg:#fff;--bg2:#f9fafb;
  --font:'Inter',-apple-system,sans-serif;
  --sb:268px;--hh:56px;--rp:240px;
}
html{font-size:15px;scroll-behavior:smooth}
body{font-family:var(--font);color:var(--t2);background:var(--bg);-webkit-font-smoothing:antialiased}""",
""":root{
  --brand:#5A64F2;--brand-dark:#434ee0;--brand-bg:#f2f3fe;--brand-bd:#d8dbfb;
  --t1:#101728;   /* titulos */
  --t2:#3d4557;   /* corpo */
  --t3:#5b6478;   /* secundario  (6.6:1 em branco) */
  --t4:#767f92;   /* meta        (4.6:1 em branco) */
  --bd:#e6e8ee;--bd2:#f0f1f5;--bg:#fff;--bg2:#f8f9fb;--bg3:#f2f4f8;
  --font:'Inter',ui-sans-serif,-apple-system,'Segoe UI',sans-serif;
  --mono:ui-monospace,'SF Mono','Cascadia Mono','Roboto Mono',Menlo,monospace;
  --measure:43rem;
  --sb:272px;--hh:60px;--rp:236px;
  --r:10px;
  --sh1:0 1px 2px rgba(16,23,40,.04),0 1px 3px rgba(16,23,40,.06);
  --sh2:0 4px 8px -2px rgba(16,23,40,.06),0 12px 28px -6px rgba(16,23,40,.10);
}
html{font-size:16px;scroll-behavior:smooth;-webkit-text-size-adjust:100%}
body{font-family:var(--font);color:var(--t2);background:var(--bg);-webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale;font-feature-settings:'cv05' 1,'ss03' 1,'zero' 1;text-rendering:optimizeLegibility}
::selection{background:var(--brand-bg);color:var(--brand-dark)}
:focus-visible{outline:2px solid var(--brand);outline-offset:2px;border-radius:4px}""",
    'tokens de design + base tipografica')

# ══════════════════════════════════════════════════════════
# 3. HEADER
# ══════════════════════════════════════════════════════════
rep(""".hdr-search{display:flex;align-items:center;gap:8px;border:1px solid var(--bd);border-radius:8px;padding:0 10px;height:34px;min-width:220px;background:var(--bg);cursor:text;transition:border-color .15s,box-shadow .15s}""",
""".hdr-search{display:flex;align-items:center;gap:9px;border:1px solid var(--bd);border-radius:9px;padding:0 12px;height:38px;min-width:340px;background:var(--bg2);cursor:text;transition:border-color .15s,box-shadow .15s,background .15s}
.hdr-search:hover{background:var(--bg);border-color:#d5d9e2}""",
    'busca maior e mais visivel')
rep(""".hdr-search:focus-within{border-color:var(--brand);box-shadow:0 0 0 3px rgba(90,100,242,.12)}
.hdr-search svg{width:13px;height:13px;color:var(--t4);flex-shrink:0}
.hdr-search input{border:none;outline:none;background:transparent;font-size:13px;color:var(--t1);font-family:var(--font);width:100%}""",
""".hdr-search:focus-within{background:var(--bg);border-color:var(--brand);box-shadow:0 0 0 3px rgba(90,100,242,.14)}
.hdr-search svg{width:15px;height:15px;color:var(--t4);flex-shrink:0}
.hdr-search input{border:none;outline:none;background:transparent;font-size:14px;color:var(--t1);font-family:var(--font);width:100%}""",
    'busca: foco e tamanho de texto')
rep(""".hdr-mid{flex:1;display:flex;align-items:center;justify-content:flex-end;gap:4px;padding:0 16px}""",
    """.hdr-mid{flex:1;display:flex;align-items:center;justify-content:center;gap:4px;padding:0 16px}""",
    'busca centralizada')
rep(""".hdr-nav a{font-size:13px;color:var(--t3);padding:5px 10px;border-radius:6px;transition:background .13s,color .13s}""",
""".hdr-nav a{display:inline-flex;align-items:center;gap:6px;font-size:13.5px;font-weight:500;color:var(--t3);padding:7px 11px;border-radius:7px;transition:background .13s,color .13s;white-space:nowrap}
.hdr-nav a svg{width:15px;height:15px;flex-shrink:0}""",
    'links do header: peso e icone')
rep(""".lnk-treinamentos{font-size:12.5px!important;font-weight:700!important;letter-spacing:.4px;color:#fff!important;background:var(--brand);padding:7px 14px!important;border-radius:7px;white-space:nowrap}""",
""".lnk-treinamentos{font-size:13.5px!important;font-weight:600!important;color:#fff!important;background:var(--brand);padding:8px 15px!important;border-radius:8px;white-space:nowrap;box-shadow:var(--sh1)}""",
    'botao Treinamentos sem caixa alta')
rep(""".btn-admin{font-size:12px;color:var(--t4)!important;border:1px solid var(--bd)!important;padding:4px 10px!important;border-radius:6px}""",
""".btn-admin{font-size:13px;color:var(--t4)!important;border:1px solid var(--bd)!important;padding:6px 11px!important;border-radius:7px}""",
    'botao admin')

rep("""    <a href="/" class="lnk-treinamentos" onclick="event.preventDefault();goTreinamentos()">\U0001F393 TREINAMENTOS</a>
    <a href="/central-de-ajuda" class="lnk-central" onclick="event.preventDefault();goCentral()">CENTRAL DE AJUDA</a>
    <a href="mailto:suporte@nxdigital.com.br" class="lnk-suporte">SUPORTE</a>
    <a href="#" class="btn-admin" onclick="openAdmin(event)">⚙<span class="lbl-admin"> Admin</span></a>""",
"""    <a href="/" class="lnk-treinamentos" onclick="event.preventDefault();goTreinamentos()"><svg class="i" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" data-i="graduation-cap"></svg>Treinamentos</a>
    <a href="/central-de-ajuda" class="lnk-central" onclick="event.preventDefault();goCentral()">Central de ajuda</a>
    <a href="mailto:suporte@nxdigital.com.br" class="lnk-suporte">Suporte</a>
    <a href="#" class="btn-admin" onclick="openAdmin(event)"><svg class="i" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" data-i="settings"></svg><span class="lbl-admin">Admin</span></a>""",
    'header: caixa alta e emoji removidos')
rep("""<button class="hdr-search-close" type="button" aria-label="Fechar busca" onclick="closeMobileSearch()">✕</button>""",
    """<button class="hdr-search-close" type="button" aria-label="Fechar busca" onclick="closeMobileSearch()"><svg class="i" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" data-i="x"></svg></button>""",
    'X da busca mobile vira SVG')

# ══════════════════════════════════════════════════════════
# 4. SIDEBAR
# ══════════════════════════════════════════════════════════
rep(""".sb-group{font-size:10.5px;font-weight:700;color:var(--t4);letter-spacing:.7px;text-transform:uppercase;padding:18px 16px 6px;margin-top:2px}""",
""".sb-group{font-size:11px;font-weight:600;color:var(--t4);letter-spacing:.06em;text-transform:uppercase;padding:22px 18px 7px;margin-top:2px}""",
    'grupos da sidebar')
rep(""".sb-ic{flex-shrink:0;width:20px;text-align:center;font-size:14.5px;line-height:1}""",
""".sb-ic{flex-shrink:0;width:17px;height:17px;display:inline-flex;align-items:center;justify-content:center;color:var(--t4);transition:color .12s}
.sb-item .sb-ic svg,.sb-sub-item .sb-ic svg,.sb-ic svg{width:16px;height:16px;stroke-width:1.9}
.sb-item:hover .sb-ic,.sb-sub-item:hover .sb-ic{color:var(--t2)}
.sb-item.active .sb-ic,.sb-sub-item.active .sb-ic{color:var(--brand)}
.sb-sub-item .sb-ic{margin-top:1px}
.sb-hint{font-size:11px;color:var(--t4);font-weight:400;margin-left:5px;white-space:nowrap}""",
    'icones SVG na sidebar')
rep(""".sb-item{display:flex;align-items:center;gap:8px;padding:7px 12px 7px 14px;font-size:13px;""",
    """.sb-item{display:flex;align-items:center;gap:10px;padding:7px 12px 7px 14px;font-size:13.5px;""",
    'item da sidebar')
rep(""".sb-sub-item{display:flex;align-items:center;gap:8px;width:100%;padding:6px 12px 6px 26px;font-size:12.5px;""",
    """.sb-sub-item{display:flex;align-items:flex-start;gap:10px;width:100%;padding:6px 12px 6px 26px;font-size:13px;""",
    'subitem da sidebar')

# ══════════════════════════════════════════════════════════
# 5. CONTEUDO / TIPOGRAFIA DE LEITURA
# ══════════════════════════════════════════════════════════
rep(""".content{flex:1;min-width:0;padding:40px 48px 80px;max-width:860px}""",
    """.content{flex:1;min-width:0;padding:52px 56px 104px;max-width:calc(var(--measure) + 112px)}""",
    'medida de linha ~72 caracteres')
rep(""".eyebrow{font-size:12px;color:var(--t4);margin-bottom:8px}
.page-title{font-size:32px;font-weight:700;color:var(--t1);letter-spacing:-.5px;line-height:1.2;margin-bottom:16px;display:flex;align-items:center;gap:12px}
.page-lead{font-size:16.5px;color:var(--t3);line-height:1.7;margin-bottom:32px}
h2.sh{font-size:22px;font-weight:600;color:var(--t1);margin:40px 0 20px;scroll-margin-top:72px}
h3.sh3{font-size:16px;font-weight:600;color:var(--t1);margin:24px 0 12px;scroll-margin-top:72px}
hr.div{border:none;border-top:1px solid var(--bd);margin:32px 0}
p.prose{font-size:15.5px;color:var(--t2);margin-bottom:10px;line-height:1.75}
ul.prose,ol.prose{font-size:15.5px;color:var(--t2);padding-left:18px;margin:8px 0}""",
""".eyebrow{font-size:12.5px;font-weight:500;color:var(--t4);margin-bottom:10px;letter-spacing:.01em}
.page-title{font-size:2.15rem;font-weight:700;color:var(--t1);letter-spacing:-.028em;line-height:1.14;margin-bottom:14px;display:flex;align-items:flex-start;gap:13px}
.page-title .ti{flex-shrink:0;width:34px;height:34px;border-radius:9px;background:var(--brand-bg);color:var(--brand);display:inline-flex;align-items:center;justify-content:center;margin-top:4px}
.page-title .ti svg{width:19px;height:19px;stroke-width:2}
.page-lead{font-size:1.0625rem;color:var(--t3);line-height:1.68;margin-bottom:36px;max-width:var(--measure)}
h2.sh{font-size:1.3125rem;font-weight:600;color:var(--t1);letter-spacing:-.012em;margin:44px 0 18px;scroll-margin-top:84px}
h3.sh3{font-size:1.0625rem;font-weight:600;color:var(--t1);letter-spacing:-.006em;margin:28px 0 10px;scroll-margin-top:84px}
hr.div{border:none;border-top:1px solid var(--bd);margin:40px 0}
p.prose{font-size:1rem;color:var(--t2);margin-bottom:14px;line-height:1.72}
ul.prose,ol.prose{font-size:1rem;color:var(--t2);padding-left:20px;margin:10px 0}""",
    'escala tipografica da pagina')
rep("""code.ic{font-size:12.5px;background:var(--bg2);border:1px solid var(--bd);border-radius:4px;padding:1px 6px;color:var(--brand);font-family:'Courier New',monospace}""",
    """code.ic{font-size:.8125rem;background:var(--bg3);border:1px solid var(--bd);border-radius:5px;padding:1.5px 6px;color:var(--t1);font-family:var(--mono);font-weight:500}""",
    'code inline')

rep(""".sec-heading{font-size:22px;font-weight:700;color:var(--t1);margin:40px 0 12px;padding-bottom:12px;border-bottom:2px solid var(--bd);scroll-margin-top:72px;line-height:1.3}
.sec-heading:first-of-type{margin-top:8px}
.content-body{padding:4px 0 32px 0}
.content-body h3{font-size:17px;font-weight:600;color:var(--t1);margin:22px 0 8px;line-height:1.4}
.content-body p{font-size:16px;color:var(--t2);line-height:1.85;margin-bottom:14px}
.content-body ul,.content-body ol{font-size:16px;color:var(--t2);padding-left:24px;margin:10px 0 16px}
.content-body li{margin-bottom:8px;line-height:1.75}""",
""".sec-heading{font-size:1.375rem;font-weight:650;color:var(--t1);margin:52px 0 16px;padding-bottom:0;border-bottom:none;scroll-margin-top:84px;line-height:1.28;letter-spacing:-.017em}
.sec-heading:first-of-type{margin-top:4px}
.content-body{padding:4px 0 32px 0;max-width:var(--measure)}
.content-body h3{font-size:1.0625rem;font-weight:600;color:var(--t1);margin:30px 0 9px;line-height:1.4;letter-spacing:-.006em}
.content-body p{font-size:1rem;color:var(--t2);line-height:1.72;margin-bottom:16px}
.content-body ul,.content-body ol{font-size:1rem;color:var(--t2);padding-left:22px;margin:12px 0 18px}
.content-body li{margin-bottom:7px;line-height:1.7;padding-left:2px}
.content-body li::marker{color:var(--t4)}""",
    'tipografia do corpo do artigo')
rep(""".content-body code{font-size:13.5px;background:var(--bg2);border:1px solid var(--bd);border-radius:4px;padding:2px 7px;color:var(--brand);font-family:'Courier New',monospace}""",
    """.content-body code{font-size:.8438rem;background:var(--bg3);border:1px solid var(--bd);border-radius:5px;padding:2px 6px;color:var(--t1);font-family:var(--mono);font-weight:500}""",
    'code no artigo')
rep(""".content-body table{width:100%;border-collapse:collapse;margin:14px 0;font-size:15px}
.content-body th{background:var(--bg2);font-weight:600;color:var(--t1);padding:10px 14px;text-align:left;border:1px solid var(--bd)}
.content-body td{padding:10px 14px;border:1px solid var(--bd);vertical-align:top;line-height:1.65}""",
""".content-body table{width:100%;border-collapse:separate;border-spacing:0;margin:22px 0;font-size:.9375rem;border:1px solid var(--bd);border-radius:var(--r);overflow:hidden}
.content-body th{background:var(--bg2);font-weight:600;color:var(--t1);padding:11px 15px;text-align:left;border:none;border-bottom:1px solid var(--bd);font-size:.8125rem;letter-spacing:.02em;text-transform:uppercase}
.content-body td{padding:12px 15px;border:none;border-bottom:1px solid var(--bd2);vertical-align:top;line-height:1.62}
.content-body tr:last-child td{border-bottom:none}
.content-body table+p{margin-top:4px}""",
    'tabelas com cara de docs')
rep(""".content-body pre{background:var(--bg2);border:1px solid var(--bd);border-radius:6px;padding:14px 18px;margin:12px 0;overflow-x:auto}""",
    """.content-body pre{background:var(--bg3);border:1px solid var(--bd);border-radius:var(--r);padding:15px 18px;margin:18px 0;overflow-x:auto;font-family:var(--mono);font-size:.8438rem;line-height:1.6}""",
    'blocos de codigo')

# ══════════════════════════════════════════════════════════
# 6. CALLOUTS  (emoji sai por CSS — conteudo no banco fica intacto)
# ══════════════════════════════════════════════════════════
rep(""".hint{border-radius:6px;padding:11px 14px;font-size:14px;line-height:1.65;display:flex;gap:10px;align-items:flex-start;margin:8px 0}
.hint-info{background:#eff6ff;border-left:3px solid #3b82f6}
.hint-warn{background:#fffbeb;border-left:3px solid #f59e0b}
.hint-danger{background:#fef2f2;border-left:3px solid #ef4444}
.hint-ok{background:#f0fdf4;border-left:3px solid #22c55e}
.hi{flex-shrink:0;font-size:15px;margin-top:1px}
.hint-b{color:var(--t2)}
.hint-b strong{color:var(--t1)}""",
""".hint{position:relative;display:block;border-radius:var(--r);padding:14px 17px 14px 47px;font-size:.9375rem;line-height:1.62;margin:22px 0;border:1px solid var(--h-bd);background:var(--h-bg);color:var(--t2);max-width:var(--measure)}
.hint::before{content:'';position:absolute;left:16px;top:15px;width:18px;height:18px;background-color:var(--h-fg);-webkit-mask:var(--h-ic) center/18px 18px no-repeat;mask:var(--h-ic) center/18px 18px no-repeat}
.hi{display:none!important}
.hint-b{color:inherit;display:block}
.hint-b strong{color:var(--h-fg);font-weight:600}
.hint p{margin:0 0 8px}.hint p:last-child{margin-bottom:0}
.hint ul,.hint ol{margin:8px 0;padding-left:20px;font-size:inherit}
.hint-info{--h-bg:#f4f6ff;--h-bd:#dde2fa;--h-fg:#4550d4;--h-ic:%(ic_info)s}
.hint-warn{--h-bg:#fffaf0;--h-bd:#f6e6c4;--h-fg:#a1670a;--h-ic:%(ic_warn)s}
.hint-danger{--h-bg:#fef5f5;--h-bd:#f7d9d9;--h-fg:#b4262c;--h-ic:%(ic_danger)s}
.hint-ok{--h-bg:#f2fbf5;--h-bd:#cfeddb;--h-fg:#12703b;--h-ic:%(ic_ok)s}""" % {
        'ic_info': data_uri('lightbulb', '#000'),
        'ic_warn': data_uri('triangle-alert', '#000'),
        'ic_danger': data_uri('octagon-alert', '#000'),
        'ic_ok': data_uri('circle-check', '#000'),
    },
    'callouts sem emoji (icone por CSS)')

# ══════════════════════════════════════════════════════════
# 7. FEEDBACK  — sem emoji, sem duplicacao
# ══════════════════════════════════════════════════════════
rep(""".fb-row{margin-top:48px;padding-top:20px;border-top:1px solid var(--bd);display:flex;align-items:center;gap:12px}
.fb-label{font-size:13px;color:var(--t3)}""",
""".fb-row{margin-top:56px;padding:20px 22px;border:1px solid var(--bd);border-radius:12px;background:var(--bg2);display:flex;align-items:center;gap:14px;flex-wrap:wrap;max-width:var(--measure)}
.fb-label{font-size:.9375rem;font-weight:600;color:var(--t1)}
.fb-btn{display:inline-flex;align-items:center;gap:7px;font-family:var(--font);font-size:.875rem;font-weight:500;color:var(--t2);background:var(--bg);border:1px solid var(--bd);border-radius:8px;padding:8px 15px;cursor:pointer;transition:all .13s}
.fb-btn svg{width:15px;height:15px}
.fb-btn:hover{border-color:var(--brand);color:var(--brand);background:var(--brand-bg)}
.fb-btn.sel{border-color:var(--brand);color:var(--brand);background:var(--brand-bg)}""",
    'widget de feedback: Sim/Nao com icone')
rep("""  html += `<div class="fb-row"><span class="fb-label">Isto foi útil?</span>
    <button class="rp-star" onclick="fbk(this)">\U0001F60A</button>
    <button class="rp-star" onclick="fbk(this)">\U0001F610</button>
    <button class="rp-star" onclick="fbk(this)">\U0001F61E</button>
  </div>`;""",
"""  html += `<div class="fb-row"><span class="fb-label">Esta página foi útil?</span>
    <button class="fb-btn" onclick="fbk(this)">${svgIcon('thumbs-up')}Sim</button>
    <button class="fb-btn" onclick="fbk(this)">${svgIcon('thumbs-down')}Não</button>
  </div>`;""",
    'feedback no rodape do artigo')
rep("""    <hr class="rp-div" id="rpDiv">
    <div class="rp-fb-label">Isto foi útil?</div>
    <div class="rp-stars">
      <button class="rp-star" onclick="fbk(this)">\U0001F60A</button>
      <button class="rp-star" onclick="fbk(this)">\U0001F610</button>
      <button class="rp-star" onclick="fbk(this)">\U0001F61E</button>
    </div>""",
    """    <hr class="rp-div" id="rpDiv" style="display:none">""",
    'remove o feedback duplicado do painel direito')
rep("""  const row = btn.closest('.fb-row,.rp-stars');""",
    """  const row = btn.closest('.fb-row,.rp-stars');
  if (row) row.querySelectorAll('.fb-btn').forEach(b => b.classList.remove('sel'));
  btn.classList.add('sel');""",
    'estado selecionado do feedback')

# ══════════════════════════════════════════════════════════
# 8. PAINEL DIREITO
# ══════════════════════════════════════════════════════════
rep(""".rp-title{font-size:11.5px;font-weight:600;color:var(--t4);text-transform:uppercase;letter-spacing:.5px;margin-bottom:10px}
.rp-link{display:block;font-size:13.5px;color:var(--t3);padding:4px 0;cursor:pointer;transition:color .12s}""",
""".rp-title{font-size:11px;font-weight:600;color:var(--t4);text-transform:uppercase;letter-spacing:.06em;margin-bottom:12px}
.rp-link{display:block;font-size:.8125rem;line-height:1.5;color:var(--t3);padding:6px 0 6px 13px;cursor:pointer;transition:color .12s,border-color .12s;border-left:2px solid var(--bd2);margin-left:-2px}
.rp-link:hover{border-left-color:var(--t4)}
.rp-link.active{border-left-color:var(--brand)}""",
    'sumario "Nesta pagina" com trilha')

# ══════════════════════════════════════════════════════════
# 9. MOBILE
# ══════════════════════════════════════════════════════════
rep("""  .page-title{font-size:24px;gap:8px;margin-bottom:12px}""",
    """  .page-title{font-size:1.6rem;gap:10px;margin-bottom:12px;letter-spacing:-.024em}
  .page-title .ti{width:28px;height:28px;border-radius:8px;margin-top:2px}
  .page-title .ti svg{width:16px;height:16px}
  .content-body p,.acc-body p{line-height:1.68}
  .sec-heading{font-size:1.1875rem;margin:38px 0 12px}""",
    'ritmo de leitura no mobile')

# ══════════════════════════════════════════════════════════
# 10. JS — sistema de icones substitui o de emoji
# ══════════════════════════════════════════════════════════
ICON_RULES_JS = r"""
// ── Sistema de icones (Lucide). Substitui o antigo mapa de emojis. ──
%(ICONS_JS)s
function svgIcon(name, cls) {
  const b = ICONS[name] || ICONS['file-text'];
  return '<svg class="' + (cls || 'i') + '" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + b + '</svg>';
}
// hidrata os <svg data-i="..."> escritos direto no HTML
function hydrateIcons(root) {
  (root || document).querySelectorAll('svg[data-i]').forEach(el => {
    el.innerHTML = ICONS[el.getAttribute('data-i')] || '';
    el.removeAttribute('data-i');
  });
}
const EMOJI_RE = /[\u{1F000}-\u{1FAFF}\u{2600}-\u{27BF}\u{2B00}-\u{2BFF}\u{1F1E6}-\u{1F1FF}\u{FE0F}\u{20E3}]/gu;
// tira o emoji que ficou salvo no nome (o conteudo no banco nao muda)
function cleanName(s) { return (s || '').replace(EMOJI_RE, '').replace(/\s{2,}/g, ' ').trim(); }
const ICON_RULES = [
  [/whats\s*app|whatsapp|baileys|webjs|evolution|uazapi|waba|\bzap\b/, 'message-circle'],
  [/telegram/, 'send'], [/instagram/, 'camera'], [/facebook|messenger/, 'thumbs-up'],
  [/e-?mail|smtp|imap|gmail|webmail/, 'mail'], [/webchat/, 'message-circle'],
  [/template/, 'clipboard-list'], [/envio|massa|disparo/, 'upload'], [/campanha/, 'megaphone'], [/\bsms\b/, 'smartphone'],
  [/wavoip|liga(ç|c)|voip|chamada|telefon/, 'phone'],
  [/relat(ó|o)rio|an(á|a)lise|indicador|estat(í|i)stic/, 'chart-column'], [/dashboard/, 'trending-up'],
  [/galeria/, 'image'], [/calend(á|a)rio|calendar|agenda(?!mento)/, 'calendar'], [/agendamento|agendad/, 'alarm-clock'], [/anivers(á|a)rio/, 'cake'],
  [/grupo/, 'users'], [/equipe/, 'users'], [/usu(á|a)rio|perfil de acesso|perfis/, 'user'], [/conta|meu perfil/, 'id-card'],
  [/mensagens? r(á|a)pid|resposta r(á|a)pid/, 'zap'], [/mensagem|mensagens/, 'message-circle'],
  [/rede.?s? sociais|coment(á|a)rio/, 'globe'], [/kanban/, 'columns-3'], [/funil/, 'filter'], [/\bcrm\b/, 'contact'], [/demanda/, 'pin'], [/vari(á|a)ve/, 'type'],
  [/etiqueta|\btag/, 'tag'], [/fechamento/, 'circle-check'], [/\bfila/, 'ticket'], [/hor(á|a)rio/, 'clock'], [/\bnota/, 'file-text'], [/protocolo/, 'bookmark'], [/avalia(ç|c)/, 'star'],
  [/\bapi\b/, 'plug'], [/integra(ç|c)|\bmeta\b/, 'link'], [/webhook/, 'webhook'], [/bsp/, 'building'], [/rastreamento|convers(ã|a)o/, 'target'],
  [/automa(ç|c)|chat.?flow|fluxo|\bbot/, 'bot'], [/copiloto|\bia\b|intelig(ê|e)ncia/, 'brain'],
  [/configura(ç|c)|ajuste|geral/, 'settings'], [/administra(ç|c)|painel admin|\badmin/, 'wrench'], [/gest(ã|a)o|comercial|opera(ç|c)/, 'chart-column'],
  [/home/, 'house'], [/atendimento/, 'headset'], [/comunica(ç|c)|marketing/, 'megaphone'],
  [/seguran(ç|c)|2 fatores|autentica(ç|c)|senha/, 'lock'], [/sess(ã|õ|a|o)/, 'signal'], [/log|auditoria/, 'scroll-text'], [/importar|import/, 'download'], [/transbordo/, 'shuffle'],
  [/vis(ã|a)o geral|vis(ã|a)o/, 'compass'], [/central de ajuda|\bajuda/, 'life-buoy'], [/contato/, 'contact'], [/onboarding/, 'rocket'], [/instalar/, 'download'], [/primeiro acesso/, 'key'],
  [/woocommerce|mercado livre|\bolx\b|loja/, 'shopping-cart'], [/youtube/, 'play'], [/tiktok/, 'music'], [/linkedin/, 'briefcase'], [/mercado/, 'shopping-cart'],
  [/notifica(ç|c)|push/, 'bell'], [/banco de dados/, 'database'], [/customiza(ç|c)|frontend/, 'palette'], [/\berro/, 'circle-alert'], [/boas.?pr(á|a)ticas|infra/, 'building-2'],
  [/hub|notificame/, 'plug'], [/apps?/, 'puzzle'], [/distribui(ç|c)/, 'shuffle'], [/exemplo/, 'paperclip'], [/boas.?vindas/, 'hand'], [/atualiza(ç|c)|status/, 'refresh-cw'],
  [/treinamento|curso|aula/, 'graduation-cap']
];
function iconFor(name, fallback) {
  const n = cleanName(name).toLowerCase();
  for (const [re, ic] of ICON_RULES) { if (re.test(n)) return ic; }
  return fallback || 'file-text';
}
""" % {'ICONS_JS': ICONS_JS}

# corta o bloco antigo de emojis inteiro (de startsWithEmoji ate o fim de withEmoji)
start = html.index('// ── Emoji automático nos menus')
end = html.index("  return (fallback || '📄') + ' ' + name;\n}\n")
end += len("  return (fallback || '📄') + ' ' + name;\n}\n")
old_block = html[start:end]
html = html[:start] + ICON_RULES_JS + """
// compatibilidade com o resto do arquivo (admin, treinamentos)
function startsWithEmoji(s) { return EMOJI_RE.test(s || ''); }
function withEmoji(name) { return name; }
""" + html[end:]
applied.append('bloco de emojis substituido pelo sistema de icones')

# renderNavNode — icone SVG no lugar do emoji
rep("""  const named = withEmoji(sec.name);
  const emoji = named === sec.name ? '' : named.slice(0, named.indexOf(' '));
  const label = emoji ? named.slice(named.indexOf(' ') + 1) : sec.name;""",
"""  const label = cleanName(sec.name);
  const emoji = svgIcon(iconFor(sec.name), 'i');
  const hint = depth === 0 ? navHint(sec) : '';""",
    'renderNavNode usa icone SVG')
rep("""        <span class="sb-tx">${label}</span>""",
    """        <span class="sb-tx">${label}${hint}</span>""",
    'desambiguacao de menus repetidos')
rep("""      const fn = withEmoji(f.q, '❓');
      const fAlready = (fn === f.q);
      const fe = fAlready ? '' : fn.slice(0, fn.indexOf(' '));
      const fl = fAlready ? f.q : fn.slice(fn.indexOf(' ') + 1);""",
"""      const fe = svgIcon('circle-help', 'i');
      const fl = cleanName(f.q);""",
    'subitens de FAQ com icone neutro')

# navHint: quando dois menus raiz tem o mesmo nome, mostra o grupo
rep("""function renderSidebar() {""",
"""// Dois menus raiz com o mesmo nome (ex.: "Automação" em Config. Admin e em
// Ferramentas) confundem o leitor. Quando isso acontece, mostramos o grupo.
function navHint(sec) {
  if (sec.parentId) return '';
  const nm = cleanName(sec.name).toLowerCase();
  const twins = DATA.sections.filter(s => !s.parentId && cleanName(s.name).toLowerCase() === nm);
  if (twins.length < 2) return '';
  const g = GROUP_LABELS[sec.group || 'geral'] || '';
  if (!g) return '';
  const short = g.replace(/^(Configuração|Ferramentas do|Ferramentas)\\s*/i, '').trim() || g;
  return `<span class="sb-hint">· ${short.toLowerCase()}</span>`;
}
function renderSidebar() {""",
    'funcao navHint')

# botoes de admin da sidebar -> SVG
rep("""      <button class="sb-act" title="Editar menu" onclick="editSecFromNav('${sec.id}',event)">✏️</button>
      <button class="sb-act" title="Adicionar submenu" onclick="addSubSection('${sec.id}',event)">➕</button>
      <button class="sb-act" title="Excluir menu" onclick="deleteSecInline('${sec.id}',event)">🗑️</button>""",
"""      <button class="sb-act" title="Editar menu" onclick="editSecFromNav('${sec.id}',event)">${svgIcon('pencil')}</button>
      <button class="sb-act" title="Adicionar submenu" onclick="addSubSection('${sec.id}',event)">${svgIcon('plus')}</button>
      <button class="sb-act" title="Excluir menu" onclick="deleteSecInline('${sec.id}',event)">${svgIcon('trash-2')}</button>""",
    'acoes de admin na sidebar com SVG')
rep("""    html += `<button class="sb-addmenu" onclick="addRootSection()">➕ Adicionar menu principal</button>`;""",
    """    html += `<button class="sb-addmenu" onclick="addRootSection()">${svgIcon('plus')} Adicionar menu principal</button>`;""",
    'botao adicionar menu')
html = html.replace(""".sb-act{""", """.sb-act svg{width:13px;height:13px}
.sb-act{""", 1)

# titulos das paginas -> icone + nome limpo
rep("""    html += `<div class="eyebrow">Central de Ajuda · ${DATA.settings.company}</div>
             <h1 class="page-title">${sec.name}</h1>""",
"""    html += `<div class="eyebrow">Central de Ajuda · ${DATA.settings.company}</div>
             <h1 class="page-title"><span class="ti">${svgIcon(iconFor(sec.name))}</span><span>${cleanName(sec.name)}</span></h1>""",
    'titulo da capa')
rep("""    html += `<div class="eyebrow">${grpLabel} · ${DATA.settings.company}</div>
             <h1 class="page-title">${sec.name}</h1>`;""",
"""    html += `<div class="eyebrow">${grpLabel} · ${DATA.settings.company}</div>
             <h1 class="page-title"><span class="ti">${svgIcon(iconFor(sec.name))}</span><span>${cleanName(sec.name)}</span></h1>`;""",
    'titulo das secoes')

# hidrata os icones do HTML estatico assim que a pagina carrega
rep("""<header class="hdr" id="hdr">""", """<header class="hdr" id="hdr">""", 'noop')
html = html.replace("""</body>""", """<script>document.addEventListener('DOMContentLoaded',function(){try{hydrateIcons(document)}catch(e){}});</script>
</body>""", 1)
applied.append('hidratacao dos icones estaticos')

open(SRC, 'w', encoding='utf-8').write(html)
print('OK — %d patches aplicados (%d → %d bytes)' % (len(applied), orig_len, len(html)))
for a in applied: print('   ·', a)

# ══════════════════════════════════════════════════════════
# 11. CARDS DA CAPA — sem emoji
# ══════════════════════════════════════════════════════════
h2 = open(SRC, encoding='utf-8').read()
h2 = h2.replace('<div class="intro-card-icon">\U0001F50D</div>',
                "<div class=\"intro-card-icon\">${svgIcon('search')}</div>", 1)
h2 = h2.replace('<div class="intro-card-icon">\U0001F4C2</div>',
                "<div class=\"intro-card-icon\">${svgIcon('layout-grid')}</div>", 1)
open(SRC, 'w', encoding='utf-8').write(h2)
print('   · cards da capa com icone SVG')

h3 = open(SRC, encoding='utf-8').read()
h3 = h3.replace(""".intro-card-icon{""",
""".intro-card-icon svg{width:20px;height:20px;stroke-width:2}
.intro-card-icon{width:38px;height:38px;border-radius:10px;background:var(--brand-bg);color:var(--brand);display:flex;align-items:center;justify-content:center;""", 1)
open(SRC, 'w', encoding='utf-8').write(h3)
print('   · icone dos cards da capa dimensionado')

# ══════════════════════════════════════════════════════════
# 12. Ajustes finais: emoji em titulos de FAQ + contraste WCAG AA
# ══════════════════════════════════════════════════════════
h4 = open(SRC, encoding='utf-8').read()

def r4(a, b, name):
    global h4
    assert a in h4, 'FALHOU: ' + name
    h4 = h4.replace(a, b, 1); print('   ·', name)

# titulo do artigo e sumario da direita tambem passam pelo cleanName
r4("""      <h2 class="sec-heading" data-title="${(faq.q||'').replace(/"/g,'&quot;')}">${faq.q}${pencil}</h2>""",
   """      <h2 class="sec-heading" data-title="${cleanName(faq.q||'').replace(/"/g,'&quot;')}">${cleanName(faq.q)}${pencil}</h2>""",
   'titulo de FAQ sem emoji')
r4("""      faqHits.push({ kind: 'faq', id: f.id, title: f.q, cat: secMap[f.secId] || '' });""",
   """      faqHits.push({ kind: 'faq', id: f.id, title: cleanName(f.q), cat: secMap[f.secId] || '' });""",
   'resultados de busca sem emoji')

# contraste: --t4 escurecido para passar em 4.5:1 sobre branco
r4("""  --t4:#767f92;   /* meta        (4.6:1 em branco) */""",
   """  --t4:#646d7e;   /* meta        (5.2:1 em branco — WCAG AA) */""",
   'contraste do texto meta')
r4(""".rp-link.active{border-left-color:var(--brand)}""",
   """.rp-link.active{border-left-color:var(--brand);color:var(--brand-dark);font-weight:500}""",
   'contraste do sumario ativo')
r4(""".kbd{font-size:11px;color:var(--t4);""", """.kbd{font-size:11px;color:var(--t3);""", 'contraste do atalho Ctrl K')
r4(""".logo-sep{color:var(--bd);""", """.logo-sep{color:#c4cad6;""", 'separador do logo')
h4 = h4.replace('.btn-danger{background:#fef2f2;color:#dc2626', '.btn-danger{background:#fef2f2;color:#b3211b')
open(SRC, 'w', encoding='utf-8').write(h4)

h5 = open(SRC, encoding='utf-8').read()
# .hdr-nav a e mais especifico que .lnk-central: a regra de esconder precisa subir junto
h5 = h5.replace("""@media(max-width:1100px){.lnk-central,.lnk-suporte{display:none}}""",
                """@media(max-width:1100px){.hdr-nav a.lnk-central,.hdr-nav a.lnk-suporte{display:none}}""", 1)
# busca larga no desktop, mas encolhe antes de estourar o header
h5 = h5.replace(""".hdr-search:hover{background:var(--bg);border-color:#d5d9e2}""",
                """.hdr-search:hover{background:var(--bg);border-color:#d5d9e2}
@media(max-width:1240px){.hdr-search{min-width:240px}}""", 1)
open(SRC, 'w', encoding='utf-8').write(h5)
print('   · header nao estoura em telas estreitas')
