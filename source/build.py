# -*- coding: utf-8 -*-
"""Génère le programme quotidien (HTML A4 à pages fixes) puis le PDF via Edge/Playwright."""
import datetime as dt
import html
import re
import sys
from pathlib import Path

from common import (START, END, PHASES, phase_of, PRON, RESCUE, CONNECT, REWRITE, CRITERIA,
                    CRIT_DESC, SUNDAY, MONTH_EVAL, LISTEN)
import data_nov, data_dec, data_jan, data_feb, data_mar, data_apr

HERE = Path(__file__).parent
OUT_DIR = HERE.parent
TITLE = "Parler, expliquer, convaincre"
SUB = "Programme quotidien de français oral et professionnel — vers ma soutenance d'ingénieur"

JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
MOIS = ["", "janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
        "septembre", "octobre", "novembre", "décembre"]


def fdate(d, weekday=True):
    s = f"{d.day if d.day > 1 else '1er'} {MOIS[d.month]} {d.year}"
    return f"{JOURS[d.weekday()]} {s}" if weekday else s


def esc(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"\{\{(.+?)\}\}", r'<span class="fill">\1</span>', s)
    s = s.replace("« ", "« ").replace(" »", " »")
    s = re.sub(r" ([?!:;])", " \\1", s)
    return s


def esc_groups(s):
    s = esc(s).replace(" // ", ' <span class="sep2">//</span> ').replace(" / ", ' <span class="sep">/</span> ')
    return s


# ------------------------------------------------------------------ CSS
CSS = r"""
@page { size: A4; margin: 0; }
:root{--ink:#1c2333;--muted:#5d6678;--faint:#8a92a3;--accent:#b8502a;--accent-soft:#fbefe9;
--teal:#1d6a73;--teal-soft:#eaf4f5;--gold:#a87b22;--gold-soft:#faf3e3;--plum:#5b4a8b;--plum-soft:#f1eef8;
--line:#dfe3ea;--soft:#f5f6f8;}
*{box-sizing:border-box}
html,body{margin:0;padding:0;background:#fff;color:var(--ink);
 font-family:"Segoe UI","Calibri",sans-serif;font-size:9.4pt;line-height:1.42;-webkit-print-color-adjust:exact;print-color-adjust:exact}
.page{width:210mm;height:297mm;position:relative;overflow:hidden;page-break-after:always;break-after:page;background:#fff}
.ph{position:absolute;top:8mm;left:17mm;right:17mm;display:flex;justify-content:space-between;
 font-size:7.2pt;letter-spacing:.06em;text-transform:uppercase;color:var(--faint);border-bottom:.6pt solid var(--line);padding-bottom:1.6mm}
.ph b{color:var(--accent);font-weight:600}
.pf{position:absolute;bottom:7.5mm;left:17mm;right:17mm;display:flex;justify-content:space-between;align-items:center;
 font-size:7.2pt;color:var(--faint)}
.pf .num{font-family:Georgia,serif;font-size:9pt;color:var(--ink)}
.content{position:absolute;top:17mm;bottom:14mm;left:17mm;right:17mm;overflow:hidden}
h1,h2,h3,.serif{font-family:Georgia,"Cambria",serif;font-weight:normal;margin:0}
h2.sec{font-size:17pt;color:var(--ink);margin:0 0 3mm}
p{margin:0 0 2mm}
.fill{display:inline-block;min-width:24mm;border-bottom:1pt dashed var(--accent);color:var(--accent);
 font-style:italic;padding:0 1mm;background:var(--accent-soft);border-radius:1mm 1mm 0 0}
.sep{color:var(--accent);font-weight:700;margin:0 .4mm}
.sep2{color:var(--accent);font-weight:700}
.muted{color:var(--muted)}
.small{font-size:8.2pt}
.kicker{font-size:7.4pt;letter-spacing:.14em;text-transform:uppercase;color:var(--accent);font-weight:600}

/* --- day header --- */
.dayhead{display:flex;align-items:flex-end;gap:5mm;margin-bottom:1.5mm}
.dnum{font-family:Georgia,serif;font-size:30pt;line-height:.9;color:var(--accent)}
.dnum small{display:block;font-family:"Segoe UI",sans-serif;font-size:6.8pt;letter-spacing:.16em;color:var(--faint);text-transform:uppercase;margin-bottom:1mm}
.dmeta{flex:1}
.ddate{font-size:9pt;color:var(--muted);text-transform:capitalize}
.dtitle{font-family:Georgia,serif;font-size:17pt;line-height:1.15;color:var(--ink)}
.chips{display:flex;flex-wrap:wrap;gap:1.5mm;justify-content:flex-end;max-width:52mm}
.chip{font-size:7pt;padding:.6mm 2mm;border-radius:5mm;background:var(--soft);color:var(--muted);white-space:nowrap}
.chip.a{background:var(--accent);color:#fff}
.chip.l{background:var(--gold-soft);color:var(--gold);font-weight:600}
.trio{display:grid;grid-template-columns:1fr 1fr 1.25fr;gap:3mm;margin:2.5mm 0 2.5mm;padding:2.2mm 0;border-top:.6pt solid var(--line);border-bottom:.6pt solid var(--line)}
.trio div{font-size:8.4pt;line-height:1.35}
.trio b{display:block;font-size:6.8pt;letter-spacing:.12em;text-transform:uppercase;color:var(--teal);margin-bottom:.6mm}
.trio .goal b{color:var(--accent)}
.timeline{display:flex;height:6.2mm;border-radius:1.2mm;overflow:hidden;margin-bottom:1mm}
.timeline div{display:flex;align-items:center;justify-content:center;font-size:6.6pt;color:#fff;white-space:nowrap;overflow:hidden;border-right:1.2pt solid #fff}
.tlnote{font-size:7.4pt;color:var(--muted);margin-bottom:2.6mm}
.tlnote b{color:var(--ink)}

/* --- sections --- */
.sh{display:flex;align-items:center;gap:2.2mm;margin:2.6mm 0 1.4mm}
.sh .n{width:5.6mm;height:5.6mm;border-radius:50%;background:var(--ink);color:#fff;font-size:7.6pt;display:flex;align-items:center;justify-content:center;font-weight:600;flex:none}
.sh .t{font-family:Georgia,serif;font-size:11.6pt}
.sh .m{margin-left:auto;font-size:7.2pt;color:var(--muted);border:.6pt solid var(--line);border-radius:4mm;padding:.3mm 2mm}
.instr{font-size:8.3pt;color:var(--muted);margin-bottom:1.4mm}
.instr b{color:var(--ink);font-weight:600}
.warm{background:var(--soft);border-radius:1.6mm;padding:2mm 3mm;font-size:9pt}
.warm .q{font-family:Georgia,serif;font-size:10.4pt;font-style:italic}
.text{font-family:Georgia,serif;font-size:10.1pt;line-height:1.55;padding:2.6mm 3.6mm;border-left:2.4pt solid var(--teal);background:var(--teal-soft);border-radius:0 1.6mm 1.6mm 0;margin-bottom:1.6mm}
.text .lbl{font-family:"Segoe UI",sans-serif;font-size:6.8pt;letter-spacing:.14em;text-transform:uppercase;color:var(--teal);font-weight:600;display:block;margin-bottom:.8mm}
ol.qs{margin:0;padding-left:5mm;font-size:8.9pt}
ol.qs li{margin-bottom:.4mm}
.steps{display:grid;grid-template-columns:repeat(6,1fr);gap:1.2mm;margin-bottom:1.8mm}
.steps div{background:var(--soft);border-radius:1.2mm;padding:1mm 1.4mm;font-size:6.9pt;line-height:1.25;color:var(--muted)}
.steps b{display:block;color:var(--ink);font-size:7.2pt}
.imit{margin:0 0 1.6mm;padding:0;list-style:none}
.imit li{font-size:9.6pt;padding:1.1mm 0 1.1mm 6mm;border-bottom:.5pt dotted var(--line);position:relative}
.imit li:before{content:"›";position:absolute;left:1mm;color:var(--accent);font-weight:700}
.pron{display:grid;grid-template-columns:34mm 1fr;gap:3mm;background:var(--plum-soft);border-radius:1.6mm;padding:2mm 3mm;font-size:8.3pt}
.pron .pt{font-family:Georgia,serif;color:var(--plum);font-size:10pt;line-height:1.2}
.pron .pt small{display:block;font-family:"Segoe UI",sans-serif;font-size:6.6pt;letter-spacing:.12em;text-transform:uppercase;margin-bottom:.6mm}
.pron .ph2{font-family:Georgia,serif;font-size:9.4pt;margin-top:1mm;color:var(--ink)}
.reg{display:grid;grid-template-columns:repeat(3,1fr);gap:1.5mm;margin-top:1.6mm}
.reg div{border:.6pt solid var(--line);border-radius:1.4mm;padding:1.2mm 2mm;font-size:8.2pt}
.reg b{display:block;font-size:6.6pt;letter-spacing:.12em;text-transform:uppercase;color:var(--faint)}

/* dialogue */
.dlg{border-radius:1.8mm;background:#fff;border:.7pt solid var(--line);padding:2.2mm 3mm}
.dlg .ctx{font-size:8.2pt;color:var(--muted);margin-bottom:1.4mm}
.dlg .ctx b{color:var(--ink)}
.ln{display:grid;grid-template-columns:23mm 1fr;gap:2mm;padding:.7mm 0;font-size:9.1pt}
.ln .who{font-size:7.3pt;font-weight:600;letter-spacing:.04em;color:var(--teal);text-align:right;padding-top:.5mm}
.ln.b .who{color:var(--accent)}
.ln.me .say{border:1pt dashed var(--accent);border-radius:1.4mm;padding:1mm 2mm;background:var(--accent-soft);color:var(--accent);font-size:8.4pt}
.ln.me .say b{font-weight:600}
.var{margin-top:1.6mm;background:var(--gold-soft);border-radius:1.6mm;padding:1.8mm 3mm;font-size:8.3pt}
.var b.h{font-size:6.8pt;letter-spacing:.12em;text-transform:uppercase;color:var(--gold);display:block;margin-bottom:.6mm}
.var div{margin-bottom:.5mm}

/* writing */
.flexcol{display:flex;flex-direction:column;height:100%}
.grow{flex:1 1 auto;min-height:12mm}
.growcol{display:flex;flex-direction:column}
.lines{background-image:repeating-linear-gradient(to bottom,transparent 0,transparent 7.2mm,#c9ced8 7.2mm,#c9ced8 7.45mm);border-radius:1mm}
.lines.sm{background-image:repeating-linear-gradient(to bottom,transparent 0,transparent 6.4mm,#c9ced8 6.4mm,#c9ced8 6.65mm)}
.wtask{display:grid;grid-template-columns:1fr 1fr;gap:3mm;margin-bottom:1.4mm}
.wtask div{font-size:8.5pt;border-left:2pt solid var(--accent);padding-left:2.4mm}
.wtask b{display:block;font-size:6.8pt;letter-spacing:.12em;text-transform:uppercase;color:var(--accent)}
.wflow{font-size:7.6pt;color:var(--muted);margin-bottom:1mm}

.speak{border:1.2pt solid var(--ink);border-radius:1.8mm;padding:2.2mm 3mm;font-size:9pt}
.speak .ttl{font-size:6.8pt;letter-spacing:.14em;text-transform:uppercase;color:var(--accent);font-weight:700}
.speak .tk{font-family:Georgia,serif;font-size:10.4pt;margin:.6mm 0 1mm}
.tools{display:grid;grid-template-columns:1fr 1fr 1fr;gap:2.4mm;margin-top:2.2mm}
.tools div{background:var(--soft);border-radius:1.4mm;padding:1.6mm 2.4mm;font-size:8pt;line-height:1.35}
.tools b{display:block;font-size:6.6pt;letter-spacing:.12em;text-transform:uppercase;color:var(--teal);margin-bottom:.4mm}
.tools i{font-family:Georgia,serif;font-size:8.8pt;color:var(--ink)}

/* bilan */
.bilan{display:grid;grid-template-columns:1.75fr 1fr;gap:3.5mm;margin-top:1.6mm}
table.corr{width:100%;border-collapse:collapse;font-size:7.4pt}
table.corr th{text-align:left;font-weight:600;color:var(--muted);border-bottom:.8pt solid var(--ink);padding:.6mm 1mm}
table.corr td{height:8.4mm;border-bottom:.6pt solid var(--line);border-right:.6pt solid var(--line)}
table.corr td:last-child{border-right:none;width:8mm;text-align:center;color:var(--faint)}
.selfev{font-size:8pt}
.selfev .row{display:flex;justify-content:space-between;align-items:center;padding:.9mm 0;border-bottom:.5pt dotted var(--line)}
.dots span{display:inline-block;width:3.4mm;height:3.4mm;border:.8pt solid var(--faint);border-radius:50%;margin-left:1mm;font-size:5.5pt;text-align:center;line-height:3.2mm;color:var(--faint)}
.check{display:flex;align-items:center;gap:1.6mm;margin-top:1.4mm;font-size:8pt}
.box{display:inline-block;width:3.6mm;height:3.6mm;border:1pt solid var(--ink);border-radius:.6mm;flex:none}

/* claude */
.claude{margin-top:2.4mm;border-radius:1.8mm;background:#1f2533;color:#e9ecf2;padding:2.4mm 3.4mm;font-size:7.75pt;line-height:1.42}
.claude .hd{display:flex;justify-content:space-between;font-size:6.8pt;letter-spacing:.14em;text-transform:uppercase;color:#f0a37f;margin-bottom:1mm;font-weight:600}
.claude .hd span{color:#9aa3b5}
.claude .body{font-family:"Consolas","Cascadia Mono",monospace;font-size:7.5pt;color:#f3f5f9}
.recall{background:var(--teal-soft);border-radius:1.6mm;padding:1.8mm 3mm;font-size:8.2pt;margin-top:2mm}
.recall b.h{font-size:6.8pt;letter-spacing:.12em;text-transform:uppercase;color:var(--teal);display:block;margin-bottom:.4mm}
.short{font-size:7.6pt;color:var(--muted);margin-top:1.2mm;border-top:.6pt solid var(--line);padding-top:1.2mm}
.short b{color:var(--gold)}

/* generic blocks */
.card{border:.7pt solid var(--line);border-radius:2mm;padding:3mm 4mm;margin-bottom:3mm}
.card h3{font-size:12pt;margin-bottom:1.4mm}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:4mm}
.grid3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:3.5mm}
.lead{font-family:Georgia,serif;font-size:11.5pt;line-height:1.55;color:var(--ink)}
ul.clean{margin:0;padding-left:4.5mm}
ul.clean li{margin-bottom:1mm}
table.t{width:100%;border-collapse:collapse;font-size:8.3pt}
table.t th{text-align:left;font-size:7pt;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);border-bottom:1pt solid var(--ink);padding:1.2mm 1.5mm}
table.t td{border-bottom:.6pt solid var(--line);padding:1.3mm 1.5mm;vertical-align:top}
.field{border-bottom:.8pt solid #c9ced8;height:7.4mm}
.fieldlbl{font-size:7.2pt;letter-spacing:.1em;text-transform:uppercase;color:var(--accent);font-weight:600;margin-top:2.2mm}
.fieldhelp{font-size:7.8pt;color:var(--muted)}
a{color:inherit;text-decoration:none}
"""


# ------------------------------------------------------------------ page shell
class Book:
    def __init__(self):
        self.pages = []      # html strings
        self.anchors = {}    # key -> page number (1-based)

    def add(self, body, left="", right="", foot_left="", anchor=None, bare=False):
        n = len(self.pages) + 1
        if anchor:
            self.anchors[anchor] = n
        aid = f' id="{anchor}"' if anchor else ""
        if bare:
            self.pages.append(f'<section class="page"{aid}>{body}</section>')
        else:
            self.pages.append(
                f'<section class="page"{aid}><div class="ph"><span>{left}</span><span>{right}</span></div>'
                f'<div class="content">{body}</div>'
                f'<div class="pf"><span>{foot_left}</span><span class="num">{n}</span></div></section>')
        return n


def dots(n=5):
    return '<span class="dots">' + "".join(f"<span>{i}</span>" for i in range(1, n + 1)) + "</span>"


def lines(h_mm, cls="lines"):
    return f'<div class="{cls}" style="height:{h_mm}mm"></div>'


# ------------------------------------------------------------------ claude prompt
RULES = ("Règles : pose une seule question à la fois et attends ma réponse. Ne réponds jamais à ma place. "
         "Laisse-moi finir mes idées avant de corriger. À la fin seulement : 3 corrections maximum "
         "(ma phrase → version naturelle → explication simple), puis fais-moi répéter uniquement ces phrases. "
         "Ne commente pas ma prononciation si tu ne reçois que du texte. Mon projet : n'invente rien, utilise seulement ce que je te dis.")

MODE_NAMES = {"dialogue": "Mode dialogue", "comprehension": "Mode compréhension",
              "presentation": "Mode présentation", "jury": "Mode simulation de jury"}

# mode par jour de semaine (lun..sam) et par phase
MODE_TABLE = {
    1: ["dialogue", "comprehension", "dialogue", "comprehension", "dialogue", "dialogue"],
    2: ["dialogue", "comprehension", "dialogue", "presentation", "dialogue", "dialogue"],
    3: ["dialogue", "comprehension", "presentation", "dialogue", "presentation", "dialogue"],
    4: ["presentation", "dialogue", "jury", "presentation", "comprehension", "jury"],
    5: ["presentation", "jury", "comprehension", "presentation", "jury", "jury"],
    6: ["jury", "presentation", "jury", "comprehension", "jury", "jury"],
}


def speak_dur(p):
    return {1: "1 minute", 2: "1 à 2 minutes", 3: "2 minutes", 4: "3 minutes", 5: "3 à 5 minutes", 6: "5 minutes ou plus"}[p["n"]]


def claude_prompt(day, p):
    mode = day["mode"] or MODE_TABLE[p["n"]][day["date"].weekday()]
    head = (f"Tu es mon partenaire d'entraînement oral en français. Mon niveau : {p['level']}. "
            f"Je prépare ma soutenance d'ingénieur en génie logiciel (avril 2027). "
            f"Séance du {fdate(day['date'], False)}, thème : « {day['t']} ».")
    if mode == "dialogue":
        me = "mon propre rôle" if day['b'].strip().lower() == "moi" else day['b']
        m = (f"MODE DIALOGUE. Tu joues : {day['a']}. Je joue {me}. Situation : {day['ctx']} "
             "Parle comme une personne réelle (phrases naturelles, un peu d'implicite), ajoute un petit imprévu au milieu, 8 à 10 échanges. "
             "Ensuite, rejoue la même scène avec une variante pour que je réponde autrement.")
    elif mode == "comprehension":
        m = ("MODE COMPRÉHENSION. Écris (ou dis, en mode vocal) un message naturel d'environ 120 mots sur le thème du jour, "
             "comme quelqu'un qui parle vraiment. Pose-moi ensuite 3 questions, une par une. "
             "Puis demande-moi de reformuler le message en commençant par « Si j'ai bien compris… ». "
             f"Termine par un mini-dialogue où tu joues : {day['a']}.")
    elif mode == "presentation":
        m = (f"MODE PRÉSENTATION. Je vais parler {speak_dur(p)} sans lire sur : {day['speak']} "
             "Ne m'interromps pas. Ensuite, pose-moi 2 questions de relance, une par une. "
             "Termine par un point fort réel, 3 corrections maximum et la phrase que je dois redire.")
    else:
        m = (f"MODE JURY. Tu es membre d'un jury de soutenance d'ingénieur, poli mais exigeant. Sujet : {day['speak']} "
             "Pose 5 questions, une à la fois : 1 facile, 2 techniques, 1 critique, 1 imprévue. "
             "Si je bloque, ne donne pas la réponse : propose-moi une expression de secours et attends.")
    tail = f"Commence par cette question d'échauffement : « {day['warm']} »"
    return mode, " ".join([head, m, RULES, tail])


# ------------------------------------------------------------------ day pages
COLORS = ["#8a92a3", "#1d6a73", "#5b4a8b", "#b8502a", "#a87b22", "#1c2333", "#5d6678"]
STEPS_NORMAL = [("Échauffement", 4), ("Écoute", 10), ("Lecture", 10), ("Écriture", 12),
                ("Dialogue", 14), ("Parole", 5), ("Bilan", 5)]
STEPS_LIGHT = [("Échauf.", 3), ("Écoute", 6), ("Lecture", 6), ("Écriture", 8),
               ("Dialogue", 10), ("Parole", 4), ("Bilan", 3)]


def timeline(light):
    steps = STEPS_LIGHT if light else STEPS_NORMAL
    total = sum(m for _, m in steps)
    segs = "".join(f'<div style="flex:{m};background:{COLORS[i]}">{n} {m}′</div>' for i, (n, m) in enumerate(steps))
    return total, f'<div class="timeline">{segs}</div>'


def sh(n, t, m=""):
    mm = f'<span class="m">{m}</span>' if m else ""
    return f'<div class="sh"><span class="n">{n}</span><span class="t">{t}</span>{mm}</div>'


def render_dialogue(day):
    rows = []
    for ln in day["lines"]:
        who, txt = ln.split(":", 1)
        who, txt = who.strip(), txt.strip()
        name = day["a"] if who == "A" else day["b"]
        short = name.split(",")[0].split("(")[0].strip()
        if txt.startswith("?"):
            rows.append(f'<div class="ln b me"><span class="who">{esc(short)}</span>'
                        f'<span class="say"><b>À toi, sans modèle —</b> {esc(txt[1:].strip())}</span></div>')
        else:
            cls = "a" if who == "A" else "b"
            rows.append(f'<div class="ln {cls}"><span class="who">{esc(short)}</span><span class="say">{esc(txt)}</span></div>')
    return "".join(rows)


def add_day(book, day, idx, all_days, week_no, num=None):
    d = day["date"]
    num = num or idx + 1
    p = phase_of(d)
    light = day["light"]
    total, tl = timeline(light)
    pron = PRON[(idx * 5) % len(PRON)] if idx % 2 == 0 else PRON[(idx * 3 + 7) % len(PRON)]
    rescue = RESCUE[idx % len(RESCUE)]
    rescue_old = RESCUE[(idx - 4) % len(RESCUE)]
    conn = CONNECT[(idx * 3) % len(CONNECT)]
    rew = REWRITE[idx % len(REWRITE)]
    mode, prompt = claude_prompt(day, p)
    left = f"{TITLE} · <b>Phase {p['n']}</b> · {p['name']}"
    right = f"Semaine {week_no} · {MOIS[d.month]} {d.year}"
    foot = f"Jour {num:03d} / 166 · {fdate(d)}"
    chips = [f'<span class="chip a">Phase {p["n"]}</span>', f'<span class="chip">{total} min</span>',
             f'<span class="chip">{MODE_NAMES[mode]}</span>']
    if light:
        chips.insert(1, '<span class="chip l">Séance légère</span>')
    if day["tag"]:
        chips.insert(1, f'<span class="chip l">{esc(day["tag"])}</span>')

    reg = ""
    if day["reg"]:
        f_, n_, p_ = day["reg"]
        reg = (f'<div class="reg"><div><b>Familier</b>{esc(f_)}</div><div><b>Naturel</b>{esc(n_)}</div>'
               f'<div><b>Professionnel</b>{esc(p_)}</div></div>')

    imit = "".join(f"<li>{esc_groups(s)}</li>" for s in day["imit"])
    qs = "".join(f"<li>{esc(q)}</li>" for q in day["q"])

    page1 = f"""
<div class="dayhead">
  <div class="dnum"><small>Jour</small>{num:03d}</div>
  <div class="dmeta"><div class="ddate">{fdate(d)}</div><div class="dtitle">{esc(day['t'])}</div></div>
  <div class="chips">{''.join(chips)}</div>
</div>
<div class="trio">
  <div><b>Ce que j'apprends</b>{esc(day['learn'])}</div>
  <div><b>Pourquoi c'est utile</b>{esc(day['why'])}</div>
  <div class="goal"><b>Objectif mesurable</b>{esc(day['obj'])}</div>
</div>
{tl}
<div class="tlnote"><b>Version courte (20 min) :</b> échauffement 2′ · phrases à imiter 4′ · dialogue avec Claude 10′ · défi oral 4′.</div>

{sh(1, "Échauffement — penser directement en français", ("3" if light else "4") + " min")}
<div class="warm"><span class="muted small">Parle {p['warm']} sans t'arrêter, sans traduire. Si tu bloques, dis « {esc(rescue[0])} » et continue.</span><br>
<span class="q">{esc(day['warm'])}</span></div>

{sh(2, "Écoute et compréhension", ("6" if light else "10") + " min")}
<div class="instr"><b>1.</b> Écoute le texte sans le regarder (Edge : clic droit › « Lire à voix haute », ou demande à Claude de te le lire). <b>2.</b> Réponds aux questions à l'oral. <b>3.</b> Réécoute en lisant et vérifie.</div>
<div class="text"><span class="lbl">Texte du jour</span>{esc(day['text'])}</div>
<ol class="qs">{qs}</ol>

{sh(3, "Lecture intelligente et imitation", ("6" if light else "10") + " min")}
<div class="steps">
<div><b>1 · Silence</b>comprendre le sens</div><div><b>2 · Lentement</b>articuler chaque son</div>
<div><b>3 · Naturel</b>gagner en fluidité</div><div><b>4 · Imiter</b>copier l'intonation</div>
<div><b>5 · Sans texte</b>retenir l'essentiel</div><div><b>6 · Résumé</b>dire avec mes mots</div></div>
<div class="instr">Phrases à imiter : <b>lentement</b>, puis <b>à vitesse normale</b>, puis <b>dans une réponse à Claude</b>. Les barres <span class="sep">/</span> marquent les groupes de souffle.</div>
<ul class="imit">{imit}</ul>
<div class="pron"><div class="pt"><small>Prononciation</small>{esc(pron[0])}</div>
<div>{esc(pron[1])}<div class="ph2">{esc_groups(pron[2])}</div></div></div>
{reg}
"""
    book.add(page1, left, right, foot, anchor=f"d{d.isoformat()}")

    # ---- page 2
    write_h = 40 if not light else 30
    sat_review = ""
    if d.weekday() == 5:
        wk = [x for x in all_days if (d - x["date"]).days in range(1, 6)]
        ph = " · ".join(f"« {esc(x['imit'][0].replace(' / ', ' ').replace(' // ', ' '))} »" for x in wk[:3])
        ex = " · ".join(f"« {esc(RESCUE[all_days.index(x) % len(RESCUE)][0])} »" for x in wk[:5])
        sat_review = (f'<div class="recall"><b class="h">Révision intelligente de la semaine</b>'
                      f'Expressions de secours vues : {ex}.<br>Phrases à réutiliser dans un nouveau contexte : {ph}.<br>'
                      f'<b>Défi :</b> place au moins 3 de ces éléments dans le dialogue d\'aujourd\'hui, sans les lire.</div>')
        write_h = 22
    recall_days = [all_days[j] for j in (idx - 2, idx - 6) if j >= 0]
    recall = ""
    if recall_days and not sat_review:
        items = " ".join(f"<div>« {esc(x['imit'][1].replace(' // ', ' ').replace(' / ', ' '))} » <span class='muted'>(jour {(x['date'] - START).days + 1:03d})</span></div>" for x in recall_days)
        recall = f'<div class="recall"><b class="h">Réutilise aujourd\'hui, dans un autre contexte</b>{items}</div>'

    var = "".join(f"<div>{esc(v)}</div>" for v in day["var"])
    page2 = f"""<div class="flexcol">
{sh(4, "Atelier d'écriture et de réécriture", ("8" if light else "12") + " min")}
<div class="wtask"><div><b>A · Réécriture</b>{esc(rew)}</div><div><b>B · Production</b>{esc(day['write'])}</div></div>
<div class="wflow">Méthode : écris <b>sans regarder</b> le texte → compare avec l'original → corrige 3 points maximum → relis ta version <b>à voix haute</b>.</div>
<div class="fieldlbl">A · Ma réécriture, avec mes mots</div>{lines(36)}
<div class="fieldlbl">B · Ma production</div><div class="lines grow"></div>

{sh(5, "Dialogue réaliste", ("10" if light else "14") + " min")}
<div class="dlg"><div class="ctx"><b>Situation :</b> {esc(day['ctx'])}</div>{render_dialogue(day)}
<div class="var"><b class="h">Ne dépends pas d'une seule phrase — autres façons de dire</b>{var}</div></div>
<div class="instr" style="margin-top:1.4mm"><b>Comment pratiquer :</b> lis d'abord les deux rôles à voix haute · puis cache la colonne « Moi » et réponds de mémoire · enfin joue la scène avec Claude (prompt en page suivante), qui changera les répliques.</div>
</div>"""
    book.add(page2, left, right, foot)

    page3 = f"""<div class="flexcol">
{sh(6, "Prise de parole sans lire", ("4" if light else "5") + " min")}
<div class="speak"><div class="ttl">Défi oral · {speak_dur(p)} · enregistre-toi</div>
<div class="tk">{esc(day['speak'])}</div>
<div class="tools"><div><b>Expression de secours</b><i>{esc(rescue[0])}</i><br><span class="muted">{esc(rescue[1])}</span></div>
<div><b>Connecteur à placer</b><i>{esc(conn[0])}</i> — {esc(conn[1])}<br><span class="muted">{esc(conn[2])}</span></div>
<div><b>Rappel (vu avant)</b><i>{esc(rescue_old[0])}</i><br><span class="muted">À replacer naturellement.</span></div></div></div>
{sat_review}{recall}

<div class="claude"><div class="hd">À copier dans Claude · {MODE_NAMES[mode]}<span>une question à la fois</span></div>
<div class="body">{esc(prompt)}</div></div>

{sh(7, "Bilan et corrections", ("3" if light else "5") + " min")}
<div class="bilan"><div>
<table class="corr"><tr><th style="width:31%">Ma formulation</th><th style="width:31%">Correction naturelle</th><th>Pourquoi (simple)</th><th>Redit</th></tr>
<tr><td></td><td></td><td></td><td>☐</td></tr><tr><td></td><td></td><td></td><td>☐</td></tr><tr><td></td><td></td><td></td><td>☐</td></tr></table>
<div class="small muted" style="margin-top:.8mm">3 corrections maximum : d'abord ce qui gêne la compréhension, puis la grammaire, puis le naturel. Redis chaque correction 2 fois, puis dans une phrase nouvelle.</div>
</div><div class="selfev">
{''.join(f'<div class="row"><span>{c}</span>{dots()}</div>' for c in [CRITERIA[(idx + k * 3) % 8] for k in range(3)])}
<div class="check"><span class="box"></span> Séance complète <span class="box" style="margin-left:2mm"></span> Version courte</div>
<div class="check"><span class="box"></span> Objectif mesurable atteint</div>
</div></div>
<div class="grid2 grow" style="margin-top:2.4mm"><div class="growcol"><div class="fieldlbl">Expressions utiles notées aujourd'hui</div><div class="lines sm grow"></div></div>
<div class="growcol"><div class="fieldlbl">Ce que je sais faire maintenant · ce que je reprends demain</div><div class="lines sm grow"></div></div></div>
</div>"""
    book.add(page3, left, right, foot)


# ------------------------------------------------------------------ Sunday pages
def add_sunday(book, d, week_no, sidx, week_days, idx):
    p = phase_of(d)
    t, t1, t2, t3 = SUNDAY[sidx]
    left = f"{TITLE} · <b>Phase {p['n']}</b> · {p['name']}"
    right = f"Semaine {week_no} · test oral du dimanche"
    foot = f"Jour {idx + 1:03d} / 166 · {fdate(d)}"
    listen = LISTEN[sidx % len(LISTEN)]
    themes = "".join(f"<li><b>{x['date'].day:02d}/{x['date'].month:02d}</b> — {esc(x['t'])}</li>" for x in week_days)
    prompt = (f"Tu es mon examinateur bienveillant pour un test oral de français (niveau {p['level']}). "
              f"Thème de la semaine : « {t} ». Fais-moi passer 3 épreuves, une par une, et attends ma réponse à chaque fois : "
              f"1) {t1} 2) {t2} 3) {t3} Ne m'interromps pas. À la fin : une note de 1 à 5 pour fluidité, construction des phrases, "
              "clarté et confiance, avec une phrase de justification chacune ; puis les 3 corrections les plus utiles "
              "(ma phrase → version naturelle → explication) et fais-moi redire ces 3 phrases. "
              "Ne juge pas ma prononciation si tu ne reçois que du texte. N'invente rien sur mon projet.")
    body = f"""
<div class="dayhead"><div class="dnum"><small>Jour</small>{idx + 1:03d}</div>
<div class="dmeta"><div class="ddate">{fdate(d)} · Test oral hebdomadaire</div><div class="dtitle">{esc(t)}</div></div>
<div class="chips"><span class="chip a">Semaine {week_no}</span><span class="chip">45 min</span><span class="chip l">Test du dimanche</span></div></div>
<div class="trio"><div><b>Ce que je vérifie</b>Ce que j'ai vraiment retenu cette semaine, sans relire mes notes.</div>
<div><b>Pourquoi c'est utile</b>Parler sans préparation, c'est la situation réelle d'une soutenance.</div>
<div class="goal"><b>Règle du test</b>Tu t'enregistres. Tu ne t'arrêtes pas pour te corriger. Tu écoutes après.</div></div>

{sh(1, "Préparation", "5 min")}
<div class="warm">Respiration 4-4-6 (inspire 4 s, garde 4 s, expire 6 s) × 3. Relis seulement les titres de la semaine :<ul class="clean small" style="margin-top:1mm">{themes}</ul></div>

{sh(2, "Épreuve 1", "")}<div class="speak"><div class="tk">{esc(t1)}</div></div>
{sh(3, "Épreuve 2", "")}<div class="speak"><div class="tk">{esc(t2)}</div></div>
{sh(4, "Épreuve 3", "")}<div class="speak"><div class="tk">{esc(t3)}</div></div>

{sh(5, "Écoute authentique de la semaine", "10 min")}
<div class="instr">{esc(listen)}. Écoute une fois sans pause, note 3 idées, puis résume à voix haute en 1 minute avec « Si j'ai bien compris… ».</div>
{lines(15, "lines sm")}

{sh(6, "Après l'écoute de mon enregistrement", "10 min")}
<div class="grid2"><div><div class="fieldlbl">Ce qui est déjà mieux que la semaine dernière</div>{lines(20, "lines sm")}</div>
<div><div class="fieldlbl">Ce que je veux améliorer en priorité</div>{lines(20, "lines sm")}</div></div>

<div class="claude"><div class="hd">À copier dans Claude · Test oral<span>une épreuve à la fois</span></div><div class="body">{esc(prompt)}</div></div>
"""
    book.add(body, left, right, foot, anchor=f"d{d.isoformat()}")

    # weekly tracking page
    rows = "".join(
        f"<tr><td>{fdate(x['date'])}</td><td>{esc(x['t'])}</td><td style='text-align:center'>☐</td><td style='text-align:center'>☐</td><td></td></tr>"
        for x in week_days)
    crit = "".join(f"<tr><td>{c}</td><td>{dots()}</td><td></td></tr>" for c in CRITERIA)
    body2 = f"""
<div class="kicker">Suivi hebdomadaire · semaine {week_no}</div>
<h2 class="sec" style="margin-top:1mm">Ma semaine en un coup d'œil</h2>
<table class="t"><tr><th style="width:26%">Date</th><th>Thème</th><th>Complète</th><th>Courte</th><th style="width:18%">Remarque</th></tr>{rows}</table>
<div class="grid2" style="margin-top:4mm"><div>
<div class="fieldlbl">Auto-évaluation (1 = difficile · 5 = à l'aise)</div>
<table class="t"><tr><th>Critère</th><th>Note</th><th>Évolution</th></tr>{crit}</table></div>
<div><div class="fieldlbl">Expressions que j'ai réellement utilisées à l'oral</div>{lines(36, "lines sm")}
<div class="fieldlbl">Mon objectif pour la semaine prochaine (mesurable)</div>{lines(20, "lines sm")}</div></div>
<div class="fieldlbl" style="margin-top:3mm">Mes 3 erreurs les plus fréquentes — et leur correction</div>
<table class="corr"><tr><th style="width:27%">Ma formulation</th><th style="width:27%">Correction naturelle</th><th style="width:28%">Explication simple</th><th>Réutilisée à l'oral dans…</th></tr>
<tr><td style="height:11mm"></td><td></td><td></td><td></td></tr><tr><td style="height:11mm"></td><td></td><td></td><td></td></tr><tr><td style="height:11mm"></td><td></td><td></td><td></td></tr></table>
<div class="grid3" style="margin-top:4mm"><div class="card"><h3>Temps de parole</h3><div class="small muted">Durée de mon plus long passage sans lire :</div><div class="field"></div></div>
<div class="card"><h3>Pauses longues</h3><div class="small muted">Nombre de silences de plus de 3 s (épreuve 1) :</div><div class="field"></div></div>
<div class="card"><h3>Confiance</h3><div class="small muted">Un moment où je me suis senti à l'aise :</div><div class="field"></div></div></div>
"""
    book.add(body2, left, f"Semaine {week_no} · suivi", foot)


def add_month_eval(book, month, p):
    name, tasks, measure = MONTH_EVAL[month]
    rows = "".join(f"<tr><td><b>{c}</b><div class='small muted'>1 : {CRIT_DESC[c][0]} · 3 : {CRIT_DESC[c][1]} · 5 : {CRIT_DESC[c][2]}</div></td>"
                   f"<td>{dots()}</td><td style='width:18mm'></td></tr>" for c in CRITERIA)
    body = f"""
<div class="kicker">Évaluation mensuelle · {name}</div>
<h2 class="sec" style="margin-top:1mm">Où en suis-je à la fin de {name.lower()} ?</h2>
<div class="grid2"><div class="card"><h3>Épreuves (enregistrées)</h3><p>{esc(tasks)}</p></div>
<div class="card"><h3>Mesure objective</h3><p>{esc(measure)}</p></div></div>
<table class="t"><tr><th>Critère et repères</th><th style="width:30mm">Note ce mois</th><th>Mois préc.</th></tr>{rows}</table>
<div class="grid2" style="margin-top:3mm"><div><div class="fieldlbl">Mes trois progrès réels du mois</div>{lines(26, "lines sm")}</div>
<div><div class="fieldlbl">Mes trois priorités pour le mois prochain</div>{lines(26, "lines sm")}</div></div>
"""
    book.add(body, f"{TITLE} · <b>Évaluation</b>", f"Phase {p['n']} · {p['name']}", f"Évaluation mensuelle · {name}",
             anchor=f"eval{month}")


# ------------------------------------------------------------------ front matter
def cover(book):
    body = f"""
<div style="position:absolute;inset:0;background:#1c2333"></div>
<div style="position:absolute;left:0;top:0;bottom:0;width:9mm;background:#b8502a"></div>
<div style="position:absolute;left:26mm;right:22mm;top:34mm;color:#fff">
 <div style="font-size:8pt;letter-spacing:.3em;text-transform:uppercase;color:#f0a37f">Programme quotidien · 16 novembre 2026 → 30 avril 2027</div>
 <div style="font-family:Georgia,serif;font-size:44pt;line-height:1.05;margin-top:12mm">Parler,<br>expliquer,<br><span style="color:#f0a37f">convaincre.</span></div>
 <div style="font-family:Georgia,serif;font-size:14pt;line-height:1.45;margin-top:10mm;color:#d7dbe4;max-width:140mm">
 166 séances de français oral, écrit et professionnel pour présenter mon projet de fin d'études avec assurance, clarté et naturel.</div>
 <div style="display:flex;gap:7mm;margin-top:16mm;font-size:8.5pt;color:#c4cad6">
  {''.join(f'<div style="border-top:1.4pt solid #f0a37f;padding-top:2mm;width:22mm"><div style="color:#fff;font-family:Georgia,serif;font-size:12pt">{x}</div>{y}</div>' for x, y in [("166","séances"),("23","tests oraux"),("6","phases"),("4","modes avec Claude")])}
 </div>
</div>
<div style="position:absolute;left:26mm;right:22mm;bottom:30mm;color:#c4cad6;font-size:9pt;border-top:.6pt solid #3a4357;padding-top:5mm;display:flex;justify-content:space-between">
 <div>Cycle ingénieur · Génie logiciel<br><span style="color:#fff">Préparation à la soutenance — avril 2027</span></div>
 <div style="text-align:right">Ce carnet appartient à<br><span style="display:inline-block;width:62mm;border-bottom:.8pt solid #f0a37f;height:6mm"></span></div>
</div>"""
    book.add(body, bare=True)


def usage(book):
    body = f"""
<div class="kicker">Mode d'emploi</div>
<h2 class="sec" style="margin-top:1mm">Ouvrir le carnet, suivre la séance, parler.</h2>
<p class="lead">Ce carnet n'est pas un cours à lire : c'est un entraînement. Chaque matin, tu ouvres la page du jour, tu suis les sept étapes dans l'ordre et tu parles à voix haute. Le but n'est pas de mémoriser des phrases, mais de construire des réflexes.</p>
<div class="grid2" style="margin-top:4mm">
<div class="card"><h3>Une séance type (≈ 60 min)</h3><table class="t">
<tr><td>1 · Échauffement</td><td>4′</td><td>Penser en français, parler sans s'arrêter</td></tr>
<tr><td>2 · Écoute</td><td>10′</td><td>Comprendre un texte entendu, répondre</td></tr>
<tr><td>3 · Lecture et imitation</td><td>10′</td><td>Six lectures, six objectifs différents</td></tr>
<tr><td>4 · Écriture</td><td>12′</td><td>Réécrire avec mes mots, produire un message</td></tr>
<tr><td>5 · Dialogue</td><td>14′</td><td>Jeu de rôle, puis avec Claude</td></tr>
<tr><td>6 · Parole sans lire</td><td>5′</td><td>Défi oral enregistré</td></tr>
<tr><td>7 · Bilan</td><td>5′</td><td>3 corrections maximum, auto-évaluation</td></tr></table></div>
<div class="card"><h3>Les jours chargés : version courte (20 min)</h3>
<ul class="clean"><li>Échauffement : 2 min</li><li>Les 3 phrases à imiter : 4 min</li><li>Dialogue du jour avec Claude (prompt prêt) : 10 min</li><li>Défi oral enregistré : 4 min</li></ul>
<p class="small muted" style="margin-top:2mm">Coche « Version courte » dans le bilan. Une séance courte vaut mieux qu'une séance oubliée.</p>
<h3 style="margin-top:3mm">Le rythme de la semaine</h3>
<ul class="clean"><li><b>Lundi → vendredi :</b> séances complètes</li><li><b>Samedi :</b> séance plus légère + révision intelligente</li><li><b>Dimanche :</b> test oral + page de suivi</li><li><b>Fin de mois :</b> évaluation mensuelle</li></ul></div></div>
<div class="grid3">
<div class="card"><h3>Repères visuels</h3><p class="small"><span style="color:var(--teal)">■</span> Texte et écoute · <span style="color:var(--plum)">■</span> Prononciation · <span style="color:var(--gold)">■</span> Variantes · <span style="color:var(--accent)">■</span> Ton tour de parler · <span style="color:var(--ink)">■</span> Prompt Claude</p></div>
<div class="card"><h3>Les champs à compléter</h3><p class="small">Quand tu vois <span class="fill">nom du projet</span>, remplace par l'information réelle de ton projet. Rien n'est inventé à ta place.</p></div>
<div class="card"><h3>Matériel</h3><p class="small">Ce carnet (imprimé ou PDF), un stylo, ton téléphone pour t'enregistrer, Claude (texte ou vocal), un chronomètre.</p></div></div>
<div class="card" style="border-color:var(--accent)"><h3>Les quatre règles d'or</h3>
<div class="grid2 small"><div><b>1. Parler avant d'être prêt.</b> Une phrase imparfaite dite à voix haute t'apprend plus qu'une phrase parfaite pensée en silence.<br><b>2. Trois corrections maximum.</b> On corrige d'abord ce qui empêche de comprendre.</div>
<div><b>3. Chaque répétition a un but.</b> Prononciation, fluidité, intonation, mémoire ou spontanéité — jamais répéter pour répéter.<br><b>4. Ne pas inventer.</b> Ni au jury, ni dans ce carnet : on dit ce qu'on sait, on reconnaît ce qu'on ne sait pas.</div></div></div>
"""
    book.add(body, f"{TITLE}", "Mode d'emploi", "Mode d'emploi", anchor="usage")


def methods(book):
    body = f"""
<div class="kicker">Méthodes</div>
<h2 class="sec" style="margin-top:1mm">Lire, imiter, corriger : la méthode du carnet</h2>
<div class="card"><h3>La lecture intelligente — six passages, six objectifs</h3>
<table class="t"><tr><th>Passage</th><th>Comment</th><th>Objectif</th></tr>
<tr><td>1 · Silencieuse</td><td>Lis une fois, sans bouger les lèvres. Souligne un mot inconnu au maximum.</td><td>Comprendre le sens global</td></tr>
<tr><td>2 · À voix haute, lentement</td><td>Articule chaque syllabe, exagère un peu les voyelles.</td><td>Prononciation</td></tr>
<tr><td>3 · Rythme naturel</td><td>Lis par groupes de sens, sans t'arrêter sur chaque mot.</td><td>Fluidité</td></tr>
<tr><td>4 · En imitant</td><td>Écoute la lecture à voix haute (Edge ou Claude), puis copie la mélodie.</td><td>Intonation</td></tr>
<tr><td>5 · Sans regarder</td><td>Regarde une phrase, lève les yeux, dis-la. Comme devant un jury.</td><td>Mémorisation active</td></tr>
<tr><td>6 · Résumé oral</td><td>Ferme le carnet, résume en 3 phrases avec tes mots.</td><td>Spontanéité</td></tr></table></div>
<div class="card"><h3>La correction bienveillante</h3>
<p>Après chaque séance, choisis <b>trois erreurs au maximum</b>, dans cet ordre de priorité :</p>
<div class="grid3 small"><div><b style="color:var(--accent)">1. Compréhension</b><br>L'erreur change le sens ou empêche de comprendre.</div>
<div><b style="color:var(--teal)">2. Grammaire</b><br>Accord, temps, construction de la phrase.</div>
<div><b style="color:var(--gold)">3. Naturel</b><br>Correct mais pas comme un Français le dirait.</div></div>
<p style="margin-top:3mm">Pour chaque erreur, remplis les quatre colonnes :</p>
<table class="t"><tr><th>Ma formulation</th><th>Correction naturelle</th><th>Explication simple</th><th>Réutilisation orale</th></tr>
<tr><td>Je suis d'accord avec ça que tu dis.</td><td>Je suis d'accord avec ce que tu dis.</td><td>Après « avec », on dit « ce que », pas « ça que ».</td><td>Redis-la 2 fois, puis place-la dans le dialogue.</td></tr>
<tr><td>J'ai fait un test pour voir si ça marche ou non.</td><td>J'ai fait un test pour vérifier que ça marchait.</td><td>Plus précis et plus naturel à l'oral pro.</td><td>Utilise « vérifier que » au daily de demain.</td></tr>
<tr><td>Le projet il est basé sur…</td><td>Le projet repose sur… / Mon projet est basé sur…</td><td>Évite de répéter le sujet (« le projet il ») en contexte formel.</td><td>À redire dans ton pitch de 1 minute.</td></tr></table>
<p class="small muted" style="margin-top:2mm">Corrige-toi toi-même d'abord : réécoute ton enregistrement, entoure ce qui te gêne, propose ta correction, puis vérifie avec Claude.</p></div>
<div class="grid2"><div class="card"><h3>Penser directement en français</h3><p class="small">Chaque échauffement te demande de décrire ce que tu fais, vois, penses ou prévois — à voix haute, sans traduire. La durée augmente : <b>30 s</b> en novembre, <b>1 min</b> en décembre, <b>2 min</b> en janvier, <b>3 min</b> en février, <b>4 à 5 min</b> en mars et avril. Si un mot manque, décris-le au lieu de t'arrêter.</p></div>
<div class="card"><h3>Écouter de vrais Français</h3><p class="small">Le texte du jour s'écoute avec la lecture à voix haute d'Edge (voix naturelles) ou avec Claude en mode vocal. Chaque dimanche, ajoute une écoute authentique : RFI « Journal en français facile », TV5MONDE, InnerFrench, France Info, conférences tech en français.</p></div></div>
"""
    book.add(body, TITLE, "Méthodes", "Méthodes", anchor="methods")


def toolkit(book):
    resc = "".join(f"<tr><td><i class='serif'>{esc(a)}</i></td><td class='muted'>{esc(b)}</td></tr>" for a, b in RESCUE)
    conn = "".join(f"<tr><td><b>{esc(a)}</b></td><td class='muted'>{esc(b)}</td><td>{esc(c)}</td></tr>" for a, b, c in CONNECT)
    body1 = f"""
<div class="kicker">Boîte à outils</div>
<h2 class="sec" style="margin-top:1mm">Ne plus rester bloqué</h2>
<p class="lead" style="margin-bottom:3mm">Ces expressions te donnent du temps et gardent la conversation vivante. Tu les rencontreras une par une dans les séances, puis elles reviendront quelques jours plus tard dans un autre contexte.</p>
<table class="t"><tr><th style="width:46%">Expression de secours</th><th>Quand l'utiliser</th></tr>{resc}</table>
<div class="card" style="margin-top:4mm"><h3>Trois registres, une même idée</h3>
<table class="t"><tr><th>Familier (entre amis)</th><th>Naturel (collègues)</th><th>Professionnel (jury, client)</th></tr>
<tr><td>J'ai pas capté.</td><td>Je n'ai pas bien compris.</td><td>Pourriez-vous préciser ce point ?</td></tr>
<tr><td>Ça bugue grave.</td><td>Il y a un gros bug.</td><td>Nous avons identifié une anomalie bloquante.</td></tr>
<tr><td>C'est galère.</td><td>C'est compliqué.</td><td>Cette partie a présenté une difficulté technique.</td></tr>
<tr><td>Je te dis ça vite fait.</td><td>Je te réponds rapidement.</td><td>Je reviens vers vous dans les plus brefs délais.</td></tr></table></div>
"""
    book.add(body1, TITLE, "Boîte à outils", "Boîte à outils", anchor="toolkit")
    body2 = f"""
<div class="kicker">Boîte à outils</div>
<h2 class="sec" style="margin-top:1mm">Relier ses idées</h2>
<p class="lead" style="margin-bottom:3mm">Inutile d'apprendre cette liste par cœur. Chaque séance te donne <b>un</b> connecteur à placer dans ton défi oral. À force de l'utiliser dans de vraies phrases, il deviendra automatique.</p>
<table class="t"><tr><th style="width:27%">Connecteur</th><th style="width:20%">Pour…</th><th>Exemple naturel</th></tr>{conn}</table>
<div class="card" style="margin-top:4mm"><h3>Mes connecteurs préférés (ceux qui me viennent naturellement)</h3>{lines(30, "lines sm")}</div>
"""
    book.add(body2, TITLE, "Boîte à outils", "Boîte à outils")


def claude_pages(book):
    modes = [
        ("Mode dialogue", "Claude joue un interlocuteur réel (collègue, client, responsable, ami). Il ajoute un imprévu et rejoue la scène avec une variante, pour que tu ne dépendes pas d'une seule phrase.",
         "Tu es mon partenaire d'entraînement oral en français (niveau B1, je vise B2). MODE DIALOGUE. Tu joues [rôle] ; je joue [mon rôle]. Situation : [situation]. Parle naturellement, ajoute un imprévu, 8 à 10 échanges, une seule réplique à la fois. Attends toujours ma réponse. Ne réponds jamais à ma place. À la fin : 3 corrections maximum (ma phrase → version naturelle → explication simple), puis fais-moi redire seulement ces phrases."),
        ("Mode compréhension", "Claude produit un message naturel, pose des questions une par une, puis te demande de reformuler. Idéal en mode vocal pour l'écoute.",
         "MODE COMPRÉHENSION. Dis-moi (ou écris) un message naturel d'environ 120 mots sur [thème], comme un Français qui parle vraiment. Pose-moi 3 questions, une à la fois, en attendant ma réponse. Puis demande-moi de reformuler avec « Si j'ai bien compris… ». Corrige seulement à la fin, 3 points maximum."),
        ("Mode présentation", "Tu parles sans être interrompu, Claude relance avec deux questions, puis donne un retour court et honnête.",
         "MODE PRÉSENTATION. Je vais présenter [sujet] pendant [durée] sans lire. Ne m'interromps pas. Ensuite, pose 2 questions de relance, une à la fois. Termine par un point fort réel, 3 corrections maximum, et la phrase que je dois redire. N'invente rien sur mon projet."),
        ("Mode simulation de jury", "Claude devient membre du jury : questions faciles, techniques, critiques et imprévues. Si tu bloques, il propose une expression de secours, pas la réponse.",
         "MODE JURY. Tu es membre d'un jury de soutenance d'ingénieur, poli mais exigeant. Mon projet : [résumé que je fournis]. Pose 5 questions, une à la fois : 1 facile, 2 techniques, 1 critique, 1 imprévue. Attends ma réponse. Si je bloque, propose une expression de secours et attends. N'invente aucun détail sur mon projet. À la fin : retour sur clarté, concision, calme, et 3 corrections maximum."),
    ]
    cards = "".join(f'<div class="card"><h3>{a}</h3><p class="small">{esc(b)}</p><div class="claude" style="margin-top:1.5mm"><div class="hd">Prompt de base<span>à adapter</span></div><div class="body">{esc(c)}</div></div></div>' for a, b, c in modes)
    body = f"""
<div class="kicker">Entraînement avec Claude</div>
<h2 class="sec" style="margin-top:1mm">Un partenaire qui te fait parler — pas qui parle à ta place</h2>
<p class="small">Chaque page du jour se termine par un prompt complet, prêt à copier. Il contient le thème, la situation, le mode et les règles. Utilise si possible le <b>mode vocal</b> de l'application Claude : tu parles, tu écoutes, comme dans la vraie vie.</p>
<div class="grid2">{cards}</div>
<div class="card" style="border-color:var(--plum)"><h3>Honnêteté sur la prononciation</h3><p class="small">Quand Claude ne reçoit qu'une transcription texte de ta voix, il ne peut pas entendre ton accent, ton rythme ou tes liaisons. Les prompts lui demandent de ne pas juger ta prononciation dans ce cas. Pour la prononciation, ton meilleur outil reste <b>l'enregistrement</b> : écoute-toi, compare avec la lecture à voix haute du texte, et note ce que tu entends.</p></div>
"""
    book.add(body, TITLE, "Entraînement avec Claude", "Entraînement avec Claude", anchor="claude")


def stress(book):
    body = f"""
<div class="kicker">Gestion du stress</div>
<h2 class="sec" style="margin-top:1mm">Le corps parle avant les mots</h2>
<p class="lead">Le stress ne disparaît pas : on apprend à le diriger. Ces routines reviennent dans les séances de mars et d'avril ; pratique-les dès maintenant, quelques minutes par jour.</p>
<div class="grid2" style="margin-top:4mm">
<div class="card"><h3>Respiration 4-4-6</h3><p class="small">Inspire par le nez 4 secondes, garde l'air 4 secondes, expire lentement par la bouche 6 secondes. Trois cycles avant chaque séance, cinq avant une simulation. L'expiration longue calme le rythme cardiaque.</p></div>
<div class="card"><h3>Posture</h3><p class="small">Pieds à largeur d'épaules, poids réparti, épaules basses. Mains visibles, à hauteur de la taille. Bouge pour montrer l'écran, puis reviens à ta position stable.</p></div>
<div class="card"><h3>Regard</h3><p class="small">Regarde chaque membre du jury 3 à 5 secondes, à tour de rôle. Pendant une question, regarde celui qui la pose ; en répondant, inclus aussi les autres.</p></div>
<div class="card"><h3>Voix et débit</h3><p class="small">Vise environ 130 mots par minute. Termine tes affirmations en descendant la voix. Respire à chaque point, pas au milieu d'un groupe de mots.</p></div>
<div class="card"><h3>Pauses</h3><p class="small">Une pause d'une ou deux secondes avant une idée importante ou après une question du jury montre que tu réfléchis. Le silence te semble long ; pour le public, il est naturel.</p></div>
<div class="card"><h3>Après un oubli</h3><p class="small">1. Respire. 2. Regarde ta diapositive. 3. Dis : « Je reprends : l'idée principale ici, c'est… ». 4. Si tu as sauté un point : « J'y reviendrai dans la partie suivante. » Personne ne connaît ton texte : seul toi sais qu'il manque quelque chose.</p></div></div>
<div class="card" style="border-color:var(--accent)"><h3>Ma routine personnelle des 10 minutes avant de parler</h3>{lines(36, "lines sm")}</div>
"""
    book.add(body, TITLE, "Gestion du stress", "Gestion du stress", anchor="stress")


def project_pages(book):
    groups = [
        ("Fiche projet (1/3) — l'essentiel", [
            ("Titre du projet", "Le nom exact, tel qu'il apparaît sur ton rapport.", 1),
            ("Organisme d'accueil / encadrants", "Entreprise, laboratoire ou école ; encadrant académique et professionnel.", 2),
            ("Mon sujet en une phrase", "« Mon projet consiste à … pour … afin de … »", 2),
            ("Contexte", "Où, pour qui, quelle situation de départ ?", 4),
            ("Problématique", "Quel problème précis ? Pourquoi est-il important ? Une question claire.", 4),
            ("Objectifs", "3 objectifs maximum, si possible mesurables.", 4)]),
        ("Fiche projet (2/3) — besoins et conception", [
            ("Utilisateurs / acteurs", "Qui utilise le système ? Avec quels rôles ?", 2),
            ("Besoins fonctionnels principaux", "Ce que le système doit faire (5 à 7 points).", 5),
            ("Besoins non fonctionnels", "Performance, sécurité, disponibilité, ergonomie…", 3),
            ("Contraintes et cahier des charges", "Délais, budget, technologies imposées, données.", 3),
            ("Méthode de travail", "Scrum, sprints, outils de gestion, planning.", 2),
            ("Conception", "Diagrammes réalisés (cas d'utilisation, classes, séquence…).", 3)]),
        ("Fiche projet (3/3) — réalisation et résultats", [
            ("Architecture", "Couches, composants, communication, déploiement.", 4),
            ("Technologies et justification", "Pour chaque technologie : pourquoi elle, et pas une autre ?", 4),
            ("Réalisations principales", "Les fonctionnalités que je montrerai en démonstration.", 3),
            ("Tests et qualité", "Types de tests, outils, couverture, résultats.", 3),
            ("Résultats", "Chiffres, retours utilisateurs, objectifs atteints ou non.", 3),
            ("Limites et perspectives", "Ce qui manque honnêtement ; les améliorations prévues.", 3)]),
    ]
    first = True
    for title, fields in groups:
        inner = "".join(f'<div class="fieldlbl">{a}</div><div class="fieldhelp">{b}</div>{lines(7.45 * k + 1)}' for a, b, k in fields)
        body = f"""<div class="kicker">Mon projet de fin d'études</div><h2 class="sec" style="margin-top:1mm">{title}</h2>
<p class="small muted">À remplir avec les informations réelles de ton projet, puis à mettre à jour. Les séances de février à avril s'appuient sur ces pages : rien n'est inventé à ta place.</p>{inner}"""
        book.add(body, TITLE, "Mon projet", "Fiche projet", anchor="projet" if first else None)
        first = False
    body = f"""<div class="kicker">Mon projet de fin d'études</div><h2 class="sec" style="margin-top:1mm">Mes pitchs</h2>
<div class="fieldlbl">Pitch de 30 secondes (≈ 70 mots)</div><div class="fieldhelp">Qui je suis · le problème · ma solution · le résultat.</div>{lines(37)}
<div class="fieldlbl">Pitch de 2 minutes (≈ 260 mots) — plan</div><div class="fieldhelp">Contexte → problématique → objectifs → solution → technologies → résultats → perspectives.</div>{lines(82)}
<div class="fieldlbl">Mes 5 mots-clés techniques (et comment je les prononce)</div>{lines(30)}
<div class="fieldlbl">Les 3 messages que le jury doit retenir</div>{lines(23)}"""
    book.add(body, TITLE, "Mon projet", "Fiche projet")


def initial_test(book):
    rows = "".join(f"<tr><td><b>{c}</b><div class='small muted'>1 : {CRIT_DESC[c][0]} · 5 : {CRIT_DESC[c][2]}</div></td><td>{dots()}</td></tr>" for c in CRITERIA)
    body = f"""
<div class="kicker">Test initial · 16 novembre 2026</div>
<h2 class="sec" style="margin-top:1mm">Mon point de départ</h2>
<p class="small">Ce test n'est pas un examen : c'est une photographie. Enregistre chaque épreuve sur ton téléphone et garde les fichiers. Le 30 avril, tu les réécouteras.</p>
<table class="t"><tr><th>Épreuve</th><th>Consigne</th><th>Durée</th><th>Durée réelle</th></tr>
<tr><td>1 · Me présenter</td><td>Nom, études, ville, ce que j'aime dans l'informatique.</td><td>1 min</td><td></td></tr>
<tr><td>2 · Raconter</td><td>Raconte ta journée d'hier, du matin au soir.</td><td>1 min</td><td></td></tr>
<tr><td>3 · Expliquer</td><td>Explique un projet scolaire que tu as réalisé : but, outils, difficulté.</td><td>2 min</td><td></td></tr>
<tr><td>4 · Donner un avis</td><td>« Le télétravail, bonne ou mauvaise idée pour un développeur ? »</td><td>1 min</td><td></td></tr>
<tr><td>5 · Répondre</td><td>Claude te pose 3 questions surprises (prompt ci-dessous).</td><td>3 min</td><td></td></tr>
<tr><td>6 · Comprendre</td><td>Écoute 3 min de RFI « Journal en français facile », puis résume.</td><td>4 min</td><td></td></tr></table>
<div class="grid2" style="margin-top:3mm"><div><table class="t"><tr><th>Critère</th><th>Note de départ</th></tr>{rows}</table></div>
<div><div class="fieldlbl">Ce qui me bloque le plus quand je parle</div>{lines(30, "lines sm")}
<div class="fieldlbl">Nombre de pauses longues (> 3 s) — épreuve 2</div><div class="field"></div>
<div class="fieldlbl">Mon objectif personnel pour avril 2027</div>{lines(23, "lines sm")}</div></div>
<div class="claude"><div class="hd">À copier dans Claude · Test initial<span>une question à la fois</span></div><div class="body">Tu es examinateur bienveillant de français oral. Je suis développeur en génie logiciel, niveau B1 environ. Pose-moi 3 questions surprises sur ma vie quotidienne, mes études et mon avenir professionnel, une seule à la fois, en attendant ma réponse. Ne m'aide pas pendant que je réponds. À la fin, décris mon niveau en 4 lignes (fluidité, construction des phrases, vocabulaire, clarté) et donne mes 3 erreurs les plus importantes, avec une correction naturelle et une explication simple. Ne juge pas ma prononciation si tu ne reçois que du texte.</div></div>
"""
    book.add(body, f"{TITLE} · <b>Évaluation</b>", "Test initial", "Test initial", anchor="test0")


def grid_progress(book, sundays):
    head = "".join(f"<th style='writing-mode:vertical-rl;transform:rotate(180deg);font-size:6.4pt;height:30mm;padding:1mm .5mm'>{c}</th>" for c in CRITERIA)
    rows = "".join(f"<tr><td style='white-space:nowrap'>S{i + 1} · {s.day:02d}/{s.month:02d}</td>" + "".join("<td></td>" for _ in CRITERIA) + "<td></td></tr>" for i, s in enumerate(sundays))
    body = f"""
<div class="kicker">Tableau de progression global</div>
<h2 class="sec" style="margin-top:1mm">23 semaines, 8 critères</h2>
<p class="small muted">Chaque dimanche, reporte ta note (1 à 5) pour chaque critère. Colorie la case : plus la note est haute, plus la couleur est foncée. En un regard, tu vois tes forces et tes priorités.</p>
<table class="t" style="font-size:7.6pt"><tr><th>Semaine</th>{head}<th style="width:40mm">Remarque</th></tr>{rows}
<tr><td><b>Final</b> 30/04</td>{''.join('<td></td>' for _ in CRITERIA)}<td></td></tr></table>
"""
    book.add(body, f"{TITLE} · <b>Suivi</b>", "Progression globale", "Progression globale", anchor="progress")


def phase_page(book, p):
    sk = "".join(f"<li>{esc(s)}</li>" for s in p["skills"])
    body = f"""
<div style="position:absolute;left:0;right:0;top:0;height:92mm;background:#1c2333"></div>
<div style="position:absolute;left:17mm;right:17mm;top:20mm;color:#fff">
<div style="font-size:8pt;letter-spacing:.3em;text-transform:uppercase;color:#f0a37f">Phase {p['n']} · {fdate(p['start'], False)} → {fdate(p['end'], False)}</div>
<div style="font-family:Georgia,serif;font-size:34pt;line-height:1.1;margin-top:6mm">{esc(p['name'])}</div>
<div style="font-family:Georgia,serif;font-size:12.5pt;color:#d7dbe4;margin-top:5mm;max-width:150mm">{esc(p['goal'])}</div></div>
<div style="position:absolute;left:17mm;right:17mm;top:104mm">
<div class="grid2"><div class="card"><h3>Ce que je vais travailler</h3><ul class="clean">{sk}</ul></div>
<div class="card"><h3>À la fin de cette phase, je suis capable de…</h3><p class="lead" style="font-size:10.5pt">{esc(p['final'])}</p>
<p class="small muted">Niveau visé : <b>{p['level']}</b> · Échauffement : <b>{p['warm']}</b> de parole continue.</p></div></div>
<div class="card"><h3>Mes intentions pour cette phase</h3>{lines(30, "lines sm")}</div>
<div class="card"><h3>Ce que je veux pouvoir dire, à l'oral, à la fin de la phase</h3>{lines(45, "lines sm")}</div></div>
"""
    book.add(body, bare=True, anchor=f"phase{p['n']}")


def appendices(book):
    Q = [
        ("Questions faciles (pour démarrer)", ["Pouvez-vous résumer votre projet en une minute ?", "Pourquoi avez-vous choisi ce sujet ?", "Quel a été votre rôle exact dans l'équipe ?", "Qu'est-ce qui vous a le plus plu dans ce projet ?", "Combien de temps a duré le projet ?", "Qui sont les utilisateurs de votre application ?"]),
        ("Questions techniques", ["Pourquoi avoir choisi cette architecture ?", "Comment les composants communiquent-ils entre eux ?", "Comment avez-vous conçu votre base de données ?", "Comment gérez-vous l'authentification et les droits ?", "Comment votre application se comporte-t-elle avec beaucoup d'utilisateurs ?", "Comment avez-vous déployé la solution ?", "Comment gérez-vous les erreurs ?", "Quels tests avez-vous écrits, et avec quels outils ?"]),
        ("Questions critiques", ["Pourquoi pas une autre technologie, par exemple [X] ?", "Votre solution existe déjà sur le marché : quelle est votre valeur ajoutée ?", "Vos résultats sont-ils vraiment mesurés ?", "Ce choix n'est-il pas trop complexe pour ce besoin ?", "Si c'était à refaire, que changeriez-vous ?", "Votre couverture de tests est-elle suffisante ?"]),
        ("Questions imprévues", ["Quel est le lien entre votre projet et votre formation ?", "Comment expliqueriez-vous votre projet à un enfant ?", "Quelle compétence non technique avez-vous développée ?", "Où vous voyez-vous dans trois ans ?", "Quel serait le coût de votre solution en production ?", "Que feriez-vous si le client changeait d'avis demain ?"]),
        ("Questions difficiles", ["Votre problématique est-elle vraiment résolue ?", "Quelle est la principale faiblesse de votre travail ?", "Pouvez-vous expliquer précisément ce bout de code ?", "Comment garantissez-vous la sécurité des données personnelles ?", "Pourquoi ce délai par rapport au planning initial ?"]),
    ]
    blocks = "".join(f'<div class="card"><h3>{a}</h3><ol class="qs">{"".join(f"<li>{esc(x)}</li>" for x in b)}</ol></div>' for a, b in Q)
    body = f"""<div class="kicker">Annexe A</div><h2 class="sec" style="margin-top:1mm">Banque de questions du jury</h2>
<p class="small muted">Pour chaque question : <b>1.</b> reformule si besoin <b>2.</b> réponds en une phrase claire <b>3.</b> justifie avec un fait ou un exemple de ton projet <b>4.</b> arrête-toi. Une bonne réponse dure souvent moins d'une minute.</p>
<div class="grid2"><div>{blocks.split('</div><div class="card">')[0]}</div></div>"""
    # simpler: two columns manual
    cards = [f'<div class="card"><h3>{a}</h3><ol class="qs">{"".join(f"<li>{esc(x)}</li>" for x in b)}</ol></div>' for a, b in Q]
    body = f"""<div class="kicker">Annexe A</div><h2 class="sec" style="margin-top:1mm">Banque de questions du jury</h2>
<p class="small muted">Pour chaque question : <b>1.</b> reformule si besoin · <b>2.</b> réponds en une phrase claire · <b>3.</b> justifie avec un fait de ton projet · <b>4.</b> arrête-toi. Une bonne réponse dure souvent moins d'une minute.</p>
<div class="grid2"><div>{cards[0]}{cards[2]}{cards[4]}</div><div>{cards[1]}{cards[3]}
<div class="card" style="border-color:var(--accent)"><h3>La structure RAPIDE d'une réponse</h3><p class="small"><b>Reformuler</b> (si besoin) · <b>Affirmer</b> l'idée principale · <b>Prouver</b> par un fait · <b>Illustrer</b> par un exemple · <b>Dire</b> la limite s'il y en a une · <b>Enchaîner</b> ou s'arrêter.</p></div></div></div>"""
    book.add(body, f"{TITLE} · <b>Annexes</b>", "Questions du jury", "Annexe A", anchor="annexA")

    plan = [("Ouverture et présentation personnelle", "1 min"), ("Contexte et organisme", "1 min 30"), ("Problématique et objectifs", "1 min 30"),
            ("Analyse des besoins", "2 min"), ("Conception et architecture", "3 min"), ("Technologies et justification", "1 min 30"),
            ("Réalisation et démonstration", "5 min"), ("Tests et résultats", "2 min"), ("Limites et perspectives", "1 min"),
            ("Conclusion et remerciements", "1 min 30")]
    rows = "".join(f"<tr><td>{i + 1}</td><td>{a}</td><td>{b}</td><td></td><td></td></tr>" for i, (a, b) in enumerate(plan))
    body = f"""<div class="kicker">Annexe B</div><h2 class="sec" style="margin-top:1mm">Plan de ma soutenance (base 20 minutes)</h2>
<p class="small muted">Durées indicatives, à adapter au règlement de ton école. Note tes diapositives et ta phrase de transition vers la partie suivante.</p>
<table class="t"><tr><th>#</th><th>Partie</th><th>Durée</th><th style="width:22%">Diapositives</th><th style="width:34%">Phrase de transition</th></tr>{rows}</table>
<div class="grid2" style="margin-top:4mm"><div class="card"><h3>Ma première phrase (à savoir parfaitement)</h3>{lines(22, "lines sm")}</div>
<div class="card"><h3>Ma dernière phrase</h3>{lines(22, "lines sm")}</div></div>
<div class="card"><h3>Transitions naturelles</h3><p class="small">« Maintenant que le contexte est posé, voyons la problématique. » · « Pour répondre à ce besoin, nous avons conçu… » · « Passons à présent à la réalisation. » · « Je vais maintenant vous montrer l'application en fonctionnement. » · « Pour terminer, j'aimerais évoquer les limites et les perspectives. »</p></div>
<div class="card"><h3>Version courte de secours (10 minutes) — ce que je garde, ce que je coupe</h3>{lines(30, "lines sm")}</div>"""
    book.add(body, f"{TITLE} · <b>Annexes</b>", "Plan de soutenance", "Annexe B", anchor="annexB")

    body = f"""<div class="kicker">Annexe C</div><h2 class="sec" style="margin-top:1mm">Check-list du jour J</h2>
<div class="grid2"><div class="card"><h3>La veille</h3>{''.join(f'<div class="check"><span class="box"></span>{x}</div>' for x in ["Présentation exportée en PDF + version originale", "Copie sur clé USB et dans le cloud", "Démo testée de bout en bout ; vidéo de secours enregistrée", "Adaptateurs (HDMI, USB-C), chargeur", "Tenue préparée", "Trajet et horaire vérifiés, arrivée 30 min avant", "Une dernière répétition légère, puis repos", "Coucher à heure normale"])}</div>
<div class="card"><h3>Le jour même</h3>{''.join(f'<div class="check"><span class="box"></span>{x}</div>' for x in ["Petit-déjeuner léger, eau", "Échauffement vocal 5 min (lecture à voix haute)", "Respiration 4-4-6 × 5", "Vérification du matériel dans la salle", "Première phrase répétée deux fois", "Téléphone en silencieux", "Sourire au jury en entrant", "Pendant les questions : écouter jusqu'au bout"])}</div></div>
<div class="card"><h3>Mes phrases d'ancrage (calme et confiance)</h3><p class="lead" style="font-size:10.5pt">« Je connais mon projet mieux que personne. » · « Une pause n'est pas une erreur. » · « Si je ne sais pas, je le dis, et j'explique ce que je sais. »</p>{lines(22, "lines sm")}</div>
<div class="card"><h3>Après la soutenance : ce que je retiens</h3>{lines(45, "lines sm")}</div>"""
    book.add(body, f"{TITLE} · <b>Annexes</b>", "Jour J", "Annexe C", anchor="annexC")

    for i in range(3):
        body = f"""<div class="kicker">Annexe D</div><h2 class="sec" style="margin-top:1mm">Carnet d'expressions {i + 1}/3</h2>
<p class="small muted">Note ici les expressions entendues dans de vraies conversations (podcasts, collègues, Claude). Colonne 3 : la situation où tu l'as réutilisée.</p>
<table class="corr"><tr><th style="width:38%">Expression entendue</th><th style="width:30%">Sens / registre</th><th>Je l'ai réutilisée quand ?</th><th>✓</th></tr>
{''.join('<tr><td style="height:9.4mm"></td><td></td><td></td><td>☐</td></tr>' for _ in range(24))}</table>"""
        book.add(body, f"{TITLE} · <b>Annexes</b>", "Carnet d'expressions", "Annexe D", anchor="annexD" if i == 0 else None)


def final_sim(book):
    crit = ["Structure claire et respect du temps", "Clarté du contexte et de la problématique", "Explication de l'architecture et des choix",
            "Démonstration commentée", "Résultats, limites, perspectives", "Fluidité et prononciation", "Posture, regard, voix", "Qualité des réponses aux questions"]
    rows = "".join(f"<tr><td>{c}</td><td>{dots()}</td><td></td></tr>" for c in crit)
    body = f"""<div class="kicker">Simulation finale · 30 avril 2027</div>
<h2 class="sec" style="margin-top:1mm">La répétition générale</h2>
<p class="small">Conditions réelles : debout, tenue de soutenance, diapositives projetées, au moins une personne dans le rôle du jury (ou Claude en mode vocal), chronomètre visible. Enregistre tout.</p>
<table class="t"><tr><th>Étape</th><th>Durée</th><th>Réalisé</th></tr>
<tr><td>Routine anti-stress</td><td>5 min</td><td>☐</td></tr><tr><td>Présentation complète</td><td>selon règlement (≈ 20 min)</td><td>☐</td></tr>
<tr><td>Questions du jury (faciles, techniques, critiques, imprévues)</td><td>15 min</td><td>☐</td></tr><tr><td>Réécoute et grille ci-dessous</td><td>20 min</td><td>☐</td></tr></table>
<div class="grid2" style="margin-top:3mm"><div><table class="t"><tr><th>Grille du jury</th><th>Note</th><th>Commentaire</th></tr>{rows}</table></div>
<div><div class="fieldlbl">Comparaison avec le test initial (16 novembre)</div>{lines(36, "lines sm")}
<div class="fieldlbl">Mes 3 derniers ajustements avant le jour J</div>{lines(30, "lines sm")}</div></div>"""
    book.add(body, f"{TITLE} · <b>Évaluation</b>", "Simulation finale", "Simulation finale", anchor="final")


def toc_pages(book, all_entries):
    """all_entries: list of (date, title, kind) — builds sommaire + calendrier with links."""
    a = book.anchors
    main = [("Mode d'emploi", "usage"), ("Méthodes : lecture, correction, pensée directe", "methods"),
            ("Boîte à outils : secours, connecteurs, registres", "toolkit"), ("Entraînement avec Claude : les 4 modes", "claude"),
            ("Gestion du stress", "stress"), ("Fiche « Mon projet » et pitchs", "projet"), ("Test initial", "test0"),
            ("Tableau de progression global", "progress")]
    main += [(f"Phase {p['n']} — {p['name']}", f"phase{p['n']}") for p in PHASES]
    main += [(f"Évaluation mensuelle — {MONTH_EVAL[m][0]}", f"eval{m}") for m in [11, 12, 1, 2, 3, 4]]
    main += [("Simulation finale complète", "final"), ("Annexe A — Banque de questions du jury", "annexA"),
             ("Annexe B — Plan de soutenance", "annexB"), ("Annexe C — Check-list du jour J", "annexC"),
             ("Annexe D — Carnet d'expressions", "annexD")]
    rows = "".join(f'<tr><td><a href="#{k}">{esc(t)}</a></td><td style="text-align:right;font-family:Georgia,serif"><a href="#{k}">{a.get(k, "")}</a></td></tr>' for t, k in main)
    cal = "".join(
        f'<div style="border-left:2pt solid var(--accent);padding:1mm 3mm;margin-bottom:1.6mm"><b class="serif" style="font-size:10pt">{p["name"]}</b>'
        f'<div class="small muted">{fdate(p["start"], False)} → {fdate(p["end"], False)} · niveau visé {p["level"]}</div></div>' for p in PHASES)
    body = f"""<div class="kicker">Sommaire</div><h2 class="sec" style="margin-top:1mm">Sommaire</h2>
<div class="grid2" style="grid-template-columns:1.35fr 1fr;gap:7mm"><table class="t">{rows}</table>
<div><div class="fieldlbl" style="margin-top:0">Calendrier de progression</div>{cal}
<p class="small muted" style="margin-top:2mm">Le calendrier détaillé des 166 séances, avec un lien vers chaque page, suit ce sommaire. Dans le PDF, clique sur une date pour y aller directement.</p></div></div>"""
    pages = [(body, "Sommaire")]
    months = [(2026, 11), (2026, 12), (2027, 1), (2027, 2), (2027, 3), (2027, 4)]
    for k in range(0, 6, 2):
        cols = ""
        for (y, m) in months[k:k + 2]:
            r = ""
            for d, t, kind in all_entries:
                if d.year == y and d.month == m:
                    key = f"d{d.isoformat()}"
                    cls = ' style="background:var(--gold-soft)"' if kind == "sun" else ""
                    r += (f'<tr{cls}><td style="white-space:nowrap;width:15mm"><a href="#{key}">{JOURS[d.weekday()][:3]}. {d.day:02d}</a></td>'
                          f'<td><a href="#{key}">{esc(t)}</a></td><td style="text-align:right;width:8mm"><a href="#{key}">{a[key]}</a></td><td style="width:5mm">☐</td></tr>')
            cols += f'<div><div class="fieldlbl" style="margin-top:0">{MOIS[m].capitalize()} {y}</div><table class="t" style="font-size:7.3pt">{r}</table></div>'
        pages.append((f'<div class="kicker">Calendrier des séances</div><div class="grid2" style="margin-top:2mm">{cols}</div>', "Calendrier"))
    return pages


# ------------------------------------------------------------------ assemble
def load_days():
    days = data_nov.DAYS + data_dec.DAYS + data_jan.DAYS + data_feb.DAYS + data_mar.DAYS + data_apr.DAYS
    days.sort(key=lambda x: x["date"])
    return days


def check(days):
    errs = []
    expected = []
    d = START
    while d <= END:
        if d.weekday() != 6:
            expected.append(d)
        d += dt.timedelta(days=1)
    got = [x["date"] for x in days]
    for e in expected:
        if e not in got:
            errs.append(f"Séance manquante : {e}")
    for g in got:
        if g.weekday() == 6:
            errs.append(f"Séance un dimanche : {g}")
        if got.count(g) > 1:
            errs.append(f"Doublon : {g}")
    titles = [x["t"] for x in days]
    for t in set(titles):
        if titles.count(t) > 1:
            errs.append(f"Titre répété : {t}")
    for x in days:
        n = len(x["text"].split())
        if not 70 <= n <= 160:
            errs.append(f"{x['date']} texte {n} mots")
        if len(x["imit"]) != 3 or len(x["q"]) != 3:
            errs.append(f"{x['date']} imit/q")
        if not any(l.split(":", 1)[1].strip().startswith("?") for l in x["lines"]):
            errs.append(f"{x['date']} pas de réplique sans modèle")
    return errs


def build():
    days = load_days()
    errs = check(days)
    if errs:
        print("\n".join(errs))
        if "--force" not in sys.argv:
            sys.exit(1)
    book = Book()
    cover(book)
    toc_slot = len(book.pages)
    n_toc = 4
    for _ in range(n_toc):
        book.pages.append(None)
    usage(book); methods(book); toolkit(book); claude_pages(book); stress(book)
    project_pages(book); initial_test(book)
    sundays = []
    d = START
    while d <= END:
        if d.weekday() == 6:
            sundays.append(d)
        d += dt.timedelta(days=1)
    grid_progress(book, sundays)

    # chronological program
    by_date = {x["date"]: x for x in days}
    entries, seq = [], []
    d = START
    while d <= END:
        seq.append(d)
        d += dt.timedelta(days=1)
    day_list = [by_date[x] for x in seq if x in by_date]
    cur_phase = None
    for i, d in enumerate(seq):
        p = phase_of(d)
        if p is not cur_phase:
            phase_page(book, p)
            cur_phase = p
        week_no = (d - START).days // 7 + 1
        if d.weekday() == 6:
            if d > max(by_date):
                continue
            sidx = sundays.index(d)
            wdays = [by_date[x] for x in seq if 0 < (d - x).days <= 6 and x in by_date]
            add_sunday(book, d, week_no, sidx, wdays, i)
            entries.append((d, "Test oral : " + SUNDAY[sidx][0], "sun"))
            nxt = d + dt.timedelta(days=7)
            if nxt.month != d.month or nxt > END:
                add_month_eval(book, d.month, p)
        elif d in by_date:
            add_day(book, by_date[d], day_list.index(by_date[d]), day_list, week_no, num=i + 1)
            entries.append((d, by_date[d]["t"], "day"))
    final_sim(book)
    appendices(book)

    # TOC (placeholders shift nothing since slots were reserved)
    toc = toc_pages(book, entries)
    assert len(toc) == n_toc
    for k, (body, right) in enumerate(toc):
        n = toc_slot + k + 1
        anchor = ' id="toc"' if k == 0 else ""
        book.pages[toc_slot + k] = (f'<section class="page"{anchor}><div class="ph"><span>{TITLE}</span><span>{right}</span></div>'
                                    f'<div class="content">{body}</div><div class="pf"><span>{right}</span><span class="num">{n}</span></div></section>')
    doc = (f'<!doctype html><html lang="fr"><head><meta charset="utf-8"><title>{TITLE}</title><style>{CSS}</style></head>'
           f'<body>{"".join(book.pages)}</body></html>')
    out_html = HERE / "programme.html"
    out_html.write_text(doc, encoding="utf-8")
    print(f"{len(book.pages)} pages HTML")
    return out_html, len(book.pages)


def to_pdf(out_html, n_pages):
    from playwright.sync_api import sync_playwright
    pdf = OUT_DIR / "Programme-Francais-Oral-Soutenance-2026-2027.pdf"
    with sync_playwright() as pw:
        b = pw.chromium.launch(channel="msedge")
        pg = b.new_page()
        pg.goto(out_html.as_uri(), wait_until="load")
        over = pg.evaluate("""() => [...document.querySelectorAll('.page')].map((p,i)=>{
            const c=p.querySelector('.content'); if(!c) return null;
            return c.scrollHeight>c.clientHeight+1 ? (i+1)+':'+(c.scrollHeight-c.clientHeight) : null}).filter(Boolean)""")
        if over:
            print("DÉBORDEMENTS :", over)
        pg.pdf(path=str(pdf), format="A4", print_background=True, prefer_css_page_size=True,
               margin=dict(top="0", bottom="0", left="0", right="0"), tagged=True, outline=True)
        b.close()
    print("PDF :", pdf)
    return over


if __name__ == "__main__":
    h, n = build()
    if "--nopdf" not in sys.argv:
        to_pdf(h, n)
