# Scene-building helpers for video.py files, and the page assembler used by build.py.
# Every helper returns an HTML string. Times are output seconds (the cut voice), coordinates are 1920x1080 pixels.
import json, os

ENGINE = os.path.dirname(os.path.abspath(__file__))


def W(words, times, cls="up"):
    """Word spans for kinetic text. Prefix a word with * to colour it (cls: up = green, down = red)."""
    out = []
    for w, t in zip(words, times):
        c = "w" + (" " + cls if w.startswith("*") else "")
        out.append(f'<span class="{c}" data-wt="{t}">{w.lstrip("*")}&nbsp;</span>')
    return "".join(out)


def cap(cid, l1, t1, l2, t2, top=80, acc="up"):
    """Two-tier caption: line 1 regular, line 2 bold, each word on its spoken time. Register it in CAPS too."""
    return (f'<div class="cap" id="{cid}" style="top:{top}px"><div class="l1">{W(l1, t1, acc)}</div>'
            f'<div class="l2">{W(l2, t2, acc)}</div></div>')


def ico(name, size=40, cls=""):
    """Line icon from the built-in set: rocket hex chip cloud bank bell person up down drop mic chat search warn globe
    coin doc cal lock shield cart wallet."""
    return f'<svg class="ico {cls}" width="{size}" height="{size}" viewBox="0 0 64 64"><use href="#i-{name}"/></svg>'


def pill(text, x, y, at, kind="", icon=None, fx="pop", extra="", pid=""):
    """Rounded label. kind: '' | 'g' (green glow) | 'r' (red glow) | 'sm' | 'dim' | 'xl', combine with spaces."""
    i = ico(icon, 38) if icon else ""
    idp = f' id="{pid}"' if pid else ""
    return f'<div{idp} class="pill {kind}" style="left:{x}px;top:{y}px;{extra}" data-at="{at}" data-fx="{fx}">{i}<span>{text}</span></div>'


def glass(x, y, w, h, at, inner="", gid="", fx="tilt", cls=""):
    """Frosted glass card. Put charts, numbers and pills inside (inner coordinates are relative to the card)."""
    idp = f' id="{gid}"' if gid else ""
    return f'<div{idp} class="glass {cls}" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px" data-at="{at}" data-fx="{fx}">{inner}</div>'


def counter(to, at, dur=0.9, prefix="$", suffix="", dec=0, frm=0):
    """Counting number (put inside bignum()). It counts silently; add one 'bell' cue where it lands if it matters."""
    return (f'{prefix}<span class="count" data-from="{frm}" data-to="{to}" data-dec="{dec}" data-c="{at}" '
            f'data-d="{dur}">{frm}</span>{suffix}')


def bignum(x, y, at, inner, cls="g", size=170):
    return f'<div class="bignum {cls}" style="left:{x}px;top:{y}px;font-size:{size}px" data-at="{at}" data-fx="in">{inner}</div>'


def stat(x, y, at, label, value_html, icon="up", w=640, h=400):
    """Glass stat card: small label on top, big green number below."""
    return (f'<div class="glass stat" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px" data-at="{at}" data-fx="tilt">'
            f'<div class="lbl">{ico(icon, 34)} {label}</div><div class="bignum">{value_html}</div></div>')


def line(d, start, dur, cls="", vb="0 0 1920 1080", full=True, pid=""):
    """Self-drawing glowing line. cls: '' | 'thick' | 'faint' | 'red'. d is an SVG path in the viewBox."""
    idp = f' id="{pid}"' if pid else ""
    svg_cls = "full" if full else "inner"
    return f'<svg class="{svg_cls}" viewBox="{vb}"><path{idp} class="ln {cls}" d="{d}" pathLength="1" data-draw="{start},{dur}"/></svg>'


def chart_card(x, y, w, h, at, d, draw_at, draw_dur, label=None, label_at=None, bars=0, bars_at=None, cid="", dot=True, red=False):
    """Glass chart card with grid, area fill, a drawn line with a riding dot, optional rising bar wave and a label pill.
    d is a path in the card's own w x h space."""
    col = "#ff2d3a" if red else "#22e55c"
    gid = (cid or f"cc{int(at*100)}")
    grid = "".join(f'<line x1="0" y1="{yy}" x2="{w}" y2="{yy}"/>' for yy in range(40, h, 60)) + \
           "".join(f'<line x1="{xx}" y1="0" x2="{xx}" y2="{h}"/>' for xx in range(40, w, 80))
    last_x = d.replace(",", " ").split()[-2]
    first_x = d.replace("M", "").replace(",", " ").split()[0]
    bars_html = ""
    if bars:
        bw = (w - 140) / bars
        bars_html = '<div class="wave">' + "".join(
            f'<i class="wb" style="left:{70 + i*bw:.0f}px;width:{bw*0.68:.0f}px;height:{40 + int(60*((i*37) % 23)/23) + i*int(160/bars)}px;'
            f'background:linear-gradient(180deg,{col},rgba(0,0,0,.1))" data-at="{(bars_at or at) + i*0.03:.2f}" data-fx="growy"></i>'
            for i in range(bars)) + '</div>'
    dot_html = f'<circle id="{gid}_dot" class="hd" r="11" cx="0" cy="0" data-ride="{gid}_p,{draw_at},{draw_dur}"/>' if dot else ""
    lab = pill(label, 40, 34, label_at if label_at is not None else at + 0.4, "sm " + ("r" if red else "g"), "down" if red else "up") if label else ""
    return (f'<div class="glass" id="{gid}" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px" data-at="{at}" data-fx="tilt">'
            f'<svg class="gridsvg" viewBox="0 0 {w} {h}"><defs><linearGradient id="{gid}_g" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="{col}" stop-opacity=".5"/><stop offset="1" stop-color="{col}" stop-opacity="0"/></linearGradient></defs>'
            f'<g class="grid">{grid}</g>'
            f'<path d="{d} L{last_x} {h} L{first_x} {h}Z" fill="url(#{gid}_g)" data-at="{draw_at + draw_dur*0.4:.2f}" data-fx="fade"/>'
            f'<path id="{gid}_p" class="ln{" red" if red else ""}" d="{d}" pathLength="1" data-draw="{draw_at},{draw_dur}"/>{dot_html}</svg>'
            f'{bars_html}{lab}</div>')


def bar(x, bottom, w, h, at, grow_at=None, cls="g", bid=""):
    """Vertical bar that grows from its base at grow_at (fills to h)."""
    idp = f' id="{bid}"' if bid else ""
    ga = grow_at if grow_at is not None else at
    return f'<div{idp} class="vbar {cls}" style="left:{x}px;bottom:{bottom}px;width:{w}px;height:{h}px" data-at="{ga}" data-fx="growbar"></div>'


def hbar(x, y, label, at, width, grow2_at=None, width2=None, icon="up", cls="g", bid="hb"):
    """Horizontal bar that grows to width at `at`, and optionally on to width2 at grow2_at (e.g. passing a record)."""
    extra = f' data-w2="{width2}" data-t2="{grow2_at}"' if grow2_at else ""
    return f'<div id="{bid}" class="hb {cls}" style="left:{x}px;top:{y}px" data-w="{width}" data-t="{at}"{extra}>{ico(icon, 40)}<span>{label}</span></div>'


def threshold(x, at, break_at=None, tid="thr", label_html=""):
    """Dashed vertical record line; breaks apart at break_at."""
    b = f' data-break="{break_at}"' if break_at else ""
    return f'<div class="thr" id="{tid}" style="left:{x}px" data-at="{at}" data-fx="fade"{b}><i class="t1"></i><i class="t2"></i></div>' + label_html


def lanes(y0, gap, entries, finish_x=1640, finish_at=None, finish_label=None, go_at=None, go_x=None, rid="rc", lane_at=None):
    """Race lanes. entries: [(name, icon, at, kind)]. At go_at the racers move to go_x[i]. lane_at draws all lanes early
    (use it when the racers are named a few seconds into the scene, so the scene never starts empty)."""
    out = []
    if finish_at is not None:
        out.append(f'<div class="finish" style="left:{finish_x}px" data-at="{finish_at}" data-fx="fade"></div>')
        if finish_label:
            out.append(pill(finish_label, finish_x - 80, y0 - 170, finish_at + 0.1, "sm", "bell"))
    for i, (name, icon, at, kind) in enumerate(entries):
        y = y0 + i * gap
        go = f' data-go="{go_at}" data-gox="{go_x[i]}"' if go_at else ""
        la = (lane_at + i * 0.15) if lane_at is not None else at - 0.1
        out.append(f'<div class="lane" style="top:{y}px" data-at="{la:.2f}" data-fx="growx"></div>')
        out.append(f'<div class="racer pill {kind}" id="{rid}{i}" style="left:180px;top:{y - 36}px" data-at="{at}" data-fx="left"{go}>{ico(icon, 38)}<span>{name}</span></div>')
    return "".join(out)


def cal(x, y, at, month, day, cls=""):
    return f'<div class="cal {cls}" style="left:{x}px;top:{y}px" data-at="{at}" data-fx="tilt"><b>{month}</b><span>{day}</span></div>'


def timeline(x0, x1, y, at, travel_from, travel_to, tid="tl"):
    """Horizontal line that draws at `at`, with a glowing dot travelling from travel_from to travel_to seconds."""
    return (f'<svg class="full" viewBox="0 0 1920 1080"><path class="ln" d="M{x0} {y} L{x1} {y}" pathLength="1" data-draw="{at},1.2"/></svg>'
            f'<i class="hd8" id="{tid}" style="left:{x0 + 20}px;top:{y - 18}px" data-travel="{travel_from},{travel_to},{x1 - x0 - 80}"></i>')


def doc(x, y, at, title, subtitle, stamp_word=None, stamp_at=None, button=None, did="doc"):
    """Glass document with text lines, optional button and a stamp that lands at stamp_at."""
    lines = "".join(f'<i style="width:{[86,72,90,64,80,58,88,70][i]}%"></i>' for i in range(8))
    btn = f'<div class="btn g" id="{did}_btn">{button}</div>' if button else ""
    st = (f'<div class="stamp" id="{did}_stamp" style="left:{x + 80}px;top:{y + 270}px" data-stamp="{stamp_at}">{stamp_word}</div>'
          if stamp_word else "")
    return (f'<div class="doc" id="{did}" style="left:{x}px;top:{y}px" data-at="{at}" data-fx="tilt">'
            f'<div class="dh">{ico("doc", 40)}<b>{title}</b><span>{subtitle}</span></div><div class="dl">{lines}</div>{btn}</div>{st}')


def blob(x, y, s=1.0, cls="", at=None, fx="up", bid=""):
    """Soft 3D person. cls: '' (neutral) | 'gr' (green, happy) | 'rd' (red, worried)."""
    a = f' data-at="{at}" data-fx="{fx}"' if at is not None else ""
    idp = f' id="{bid}"' if bid else ""
    return (f'<div{idp} class="blob {cls}" style="left:{x}px;top:{y}px;transform:scale({s})"{a}>'
            f'<i class="hd"><b></b><b></b></i><i class="bd"></i></div>')


def crowd(at, rows=2, n=18, cls="gr", y=760):
    return "".join(blob(140 + i * 96 - (r * 48), y + r * 80, 0.55 - r * 0.06, cls, at + i * 0.025 + r * 0.08)
                   for r in range(rows) for i in range(n))


def cursor(cid, x, y, to_x, to_y, move_at, click_at):
    """Mouse cursor that glides from (x,y) to (to_x,to_y) and clicks at click_at (add a 'click' cue there)."""
    return (f'<div class="cur" id="{cid}" style="left:{x}px;top:{y}px" data-click="{to_x - x},{to_y - y},{move_at},{click_at}">'
            '<svg width="44" height="60" viewBox="0 0 30 42"><path d="M2 2 L2 34 L10 27 L16 40 L22 37 L16 25 L27 25 Z" '
            'fill="#fff" stroke="#05070c" stroke-width="2" stroke-linejoin="round"/></svg><i class="rip"></i></div>')


def button(x, y, at, text, icon="bell", bid="btn", on_at=None):
    """Large pill button; turns green at on_at (pair it with cursor())."""
    o = f' data-on="{on_at}"' if on_at else ""
    return f'<div class="btn xl" id="{bid}" style="left:{x}px;top:{y}px" data-at="{at}" data-fx="stamp"{o}>{ico(icon, 54)}<span>{text}</span></div>'


def tile(x, y, at, icon, label):
    return f'<div class="tile" style="left:{x}px;top:{y}px" data-at="{at}" data-fx="pop">{ico(icon, 96)}<b>{label}</b></div>'


def progress(x, y, at, fill_at, dur, to=0.7, label=None):
    lab = f'<div class="lbl" style="position:absolute;left:{x}px;top:{y + 100}px" data-at="{fill_at}" data-fx="in">{label}</div>' if label else ""
    return (f'<div class="prog" style="left:{x}px;top:{y}px" data-at="{at}" data-fx="in"><i class="fill" data-progress="{fill_at},{dur}" '
            f'data-to="{to}"></i><i class="glint" data-glint="{fill_at}"></i></div>{lab}')


def orbit(items, at, dur, core_big, core_small):
    """Items (name, icon) orbit around a glowing core for dur seconds."""
    pos = [(0, -230), (200, 115), (-200, 115), (0, 230), (-200, -115), (200, -115)]
    ops = "".join(f'<div class="op" style="left:{pos[i][0]}px;top:{pos[i][1]}px">{ico(ic, 40)}<span>{n}</span></div>' for i, (n, ic) in enumerate(items))
    return (f'<div class="orbit" data-orbit="{at},{dur}">{ops}</div>'
            f'<div class="ocore" data-at="{at + 0.3}" data-fx="pop"><b>{core_big}</b><span>{core_small}</span></div>'
            f'<i class="oring" data-at="{at + 0.15}" data-fx="fade"></i>')


def warn(x, y, at, label):
    return (f'<div class="warn" style="left:{x}px;top:{y}px" data-at="{at}" data-fx="stamp">{ico("warn", 150)}</div>'
            f'<div class="lbl big r" style="position:absolute;left:{x - 50}px;top:{y + 200}px;width:340px;text-align:center" data-at="{at + 0.06}" data-fx="in">{label}</div>')


def globe(x, y, at, label=None):
    lab = f'<div class="lbl" style="position:absolute;left:{x}px;top:{y + 310}px;width:300px;text-align:center" data-at="{at + 0.5}" data-fx="in">{label}</div>' if label else ""
    return f'<div class="globe" style="left:{x}px;top:{y}px" data-at="{at}" data-fx="pop" data-pulse="{at}">{ico("globe", 260)}<i class="pr"></i><i class="pr"></i></div>{lab}'


def badge(x, y, at, text):
    return f'<div class="badge" style="left:{x}px;top:{y}px" data-at="{at}" data-fx="stamp">{text}</div>'


def floor(at):
    return f'<div class="floor" data-at="{at}" data-fx="fade"></div>'


def beam(x, y, at):
    return f'<div class="beam" style="left:{x}px;top:{y}px" data-at="{at}" data-fx="fade"></div>'


def shake(sid, at, dur=0.6):
    """Wrap scene content in a div with this id and shake it at `at` (pair with a 'down' cue, never a glitch)."""
    return f'data-shake="{at},{dur}" id="{sid}"'


ICONS = '''
<symbol id="i-rocket" viewBox="0 0 64 64"><path d="M32 5c9 7 13 18 11 32l-11 8-11-8C19 23 23 12 32 5z"/><circle cx="32" cy="24" r="5"/><path d="M21 37l-7 10 9-2M43 37l7 10-9-2M27 50l5 9 5-9"/></symbol>
<symbol id="i-hex" viewBox="0 0 64 64"><path d="M32 6 54 19v26L32 58 10 45V19z"/><circle cx="32" cy="32" r="9"/></symbol>
<symbol id="i-chip" viewBox="0 0 64 64"><rect x="16" y="16" width="32" height="32" rx="5"/><rect x="25" y="25" width="14" height="14" rx="2"/><path d="M24 8v8M32 8v8M40 8v8M24 48v8M32 48v8M40 48v8M8 24h8M8 32h8M8 40h8M48 24h8M48 32h8M48 40h8"/></symbol>
<symbol id="i-cloud" viewBox="0 0 64 64"><path d="M19 47h27a11 11 0 0 0 0-22 15 15 0 0 0-28-3A12 12 0 0 0 19 47z"/></symbol>
<symbol id="i-bank" viewBox="0 0 64 64"><path d="M8 24 32 10l24 14zM13 28v19M25 28v19M39 28v19M51 28v19M8 53h48"/></symbol>
<symbol id="i-bell" viewBox="0 0 64 64"><path d="M18 44V30a14 14 0 0 1 28 0v14l5 5H13zM27 53a5 5 0 0 0 10 0"/></symbol>
<symbol id="i-person" viewBox="0 0 64 64"><circle cx="32" cy="21" r="10"/><path d="M12 56c2-12 10-18 20-18s18 6 20 18"/></symbol>
<symbol id="i-up" viewBox="0 0 64 64"><path d="M8 48 24 32l10 9 22-22M42 19h14v14"/></symbol>
<symbol id="i-down" viewBox="0 0 64 64"><path d="M8 16 24 32l10-9 22 22M42 45h14V31"/></symbol>
<symbol id="i-drop" viewBox="0 0 64 64"><path d="M32 6c10 14 16 24 16 32a16 16 0 0 1-32 0c0-8 6-18 16-32z"/></symbol>
<symbol id="i-mic" viewBox="0 0 64 64"><rect x="24" y="6" width="16" height="30" rx="8"/><path d="M14 30a18 18 0 0 0 36 0M32 48v10M22 58h20"/></symbol>
<symbol id="i-chat" viewBox="0 0 64 64"><path d="M10 12h44v32H30L17 55V44h-7z"/><path d="M22 28h2M31 28h2M40 28h2"/></symbol>
<symbol id="i-search" viewBox="0 0 64 64"><circle cx="27" cy="27" r="16"/><path d="M39 39l16 16"/></symbol>
<symbol id="i-warn" viewBox="0 0 64 64"><path d="M32 7 59 55H5z"/><path d="M32 25v15M32 47v1"/></symbol>
<symbol id="i-globe" viewBox="0 0 64 64"><circle cx="32" cy="32" r="25"/><ellipse cx="32" cy="32" rx="11" ry="25"/><path d="M7 32h50M11 19h42M11 45h42"/></symbol>
<symbol id="i-coin" viewBox="0 0 64 64"><circle cx="32" cy="32" r="24"/><path d="M38 23c-2-3-12-4-12 2s12 4 12 10-10 6-13 2M32 16v6M32 42v6"/></symbol>
<symbol id="i-doc" viewBox="0 0 64 64"><path d="M16 6h22l12 12v40H16zM38 6v12h12M24 32h16M24 42h16"/></symbol>
<symbol id="i-cal" viewBox="0 0 64 64"><rect x="8" y="12" width="48" height="44" rx="6"/><path d="M8 24h48M20 6v12M44 6v12"/></symbol>
<symbol id="i-lock" viewBox="0 0 64 64"><rect x="14" y="28" width="36" height="28" rx="6"/><path d="M22 28v-8a10 10 0 0 1 20 0v8"/></symbol>
<symbol id="i-shield" viewBox="0 0 64 64"><path d="M32 6 54 14v18c0 14-10 22-22 26C20 54 10 46 10 32V14z"/></symbol>
<symbol id="i-cart" viewBox="0 0 64 64"><path d="M6 10h8l7 32h30l6-22H17"/><circle cx="25" cy="52" r="4"/><circle cx="47" cy="52" r="4"/></symbol>
<symbol id="i-wallet" viewBox="0 0 64 64"><rect x="8" y="16" width="48" height="36" rx="7"/><path d="M8 26h48"/><rect x="40" y="31" width="16" height="10" rx="4"/></symbol>
'''


def page(v):
    """Assemble index.html from a loaded video.py module."""
    total = v.TOTAL
    S = v.scenes()
    dust = "".join(f'<i style="left:{(i*211) % 1920}px;top:{(i*137) % 1080}px;width:{2 + (i % 3)}px;height:{2 + (i % 3)}px;'
                   f'opacity:{.10 + (i % 5) * .06:.2f}"></i>' for i in range(46))
    body = []
    for i, (a, b) in enumerate(v.SCENES):
        st = max(0, a - 0.05)
        body.append(f'<div id="s{i}" class="clip scene" data-start="{st:.2f}" data-duration="{min((b - a) + 0.45, total - st):.2f}" '
                    f'data-track-index="{1 + (i % 2)}" data-in="{a}" data-out="{b}"><div class="cam"><div class="push">{S.get(i, "")}</div></div></div>')
    vids = []
    for k, (a, b) in enumerate(v.FACES, 1):
        vids.append(f'<video id="fv{k}" class="clip face" src="assets/face{k}.mp4" muted playsinline data-start="{a - 0.3:.2f}" '
                    f'data-duration="{b - a + 0.6:.2f}" data-media-start="0" data-track-index="{10 + k}" data-a="{a}" data-b="{b}"></video>')
        vids.append(f'<div id="fo{k}" class="clip fover" data-start="{a - 0.3:.2f}" data-duration="{b - a + 0.6:.2f}" data-track-index="{20 + k}"></div>')
    html = open(os.path.join(ENGINE, "template.html"), encoding="utf-8").read()
    return (html.replace("%ICONS%", ICONS).replace("%DUST%", dust).replace("%SCENES%", "\n".join(body))
            .replace("%VIDS%", "\n".join(vids)).replace("%TOTAL%", str(total))
            .replace("%WORLDS%", json.dumps(v.WORLDS)).replace("%CAPS%", json.dumps(v.CAPS))
            .replace("%CUSTOM%", getattr(v, "CUSTOM_JS", "")))
