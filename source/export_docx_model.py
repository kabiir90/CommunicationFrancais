# -*- coding: utf-8 -*-
"""Exporte le carnet sous forme de blocs neutres (JSON) pour la version Word (build_docx.js).
Mêmes données et mêmes rotations que build.py, pour que PDF et DOCX restent identiques sur le fond."""
import datetime as dt
import json
import re
from pathlib import Path

import build as B
from common import (START, END, PHASES, phase_of, PRON, RESCUE, CONNECT, REWRITE, CRITERIA, CRIT_DESC,
                    SUNDAY, MONTH_EVAL, LISTEN)

RED, INK, INK2 = "D6402B", "1C2448", "4A5275"
blocks = []


# ---------------------------------------------------------------- helpers
def R(t, **k):
    d = {"t": t}
    d.update(k)
    return d


def rich(txt, **k):
    """Texte -> runs ; {{champ}} devient du surligné jaune."""
    out = []
    for i, part in enumerate(re.split(r"\{\{(.+?)\}\}", txt)):
        if not part:
            continue
        if i % 2:
            out.append(R(part, i=True, hl=True, **{x: y for x, y in k.items() if x not in ("i",)}))
        else:
            out.append(R(part, **k))
    return out


def groups(txt, **k):
    """Phrase à imiter : chaque groupe de souffle souligné en vague, ‖ = pause rouge."""
    out = []
    for i, chunk in enumerate(txt.split(" // ")):
        if i:
            out.append(R("  ‖  ", c=RED, b=True, f="sans"))
        for j, g in enumerate(chunk.split(" / ")):
            if j:
                out.append(R("   ", **k))
            for r in rich(g, **k):
                r["u"] = "wave"
                out.append(r)
    return out


def alt(txt, **k):
    out = []
    for j, part in enumerate(txt.split(" / ")):
        if j:
            out.append(R("  ou  ", c=RED, f="sans", s=7.5, b=True))
        out += rich(part, **k)
    return out


def add(k, **kw):
    kw["k"] = k
    blocks.append(kw)


def pb():
    add("pb")


def kicker(t):
    add("p", runs=[R(t.upper(), c=RED, f="sans", s=8, b=True, sp=40)], after=40)


def title(t, level=1, toc=True):
    add("h1" if level == 1 else "h2", runs=[R(t)], toc=toc)


def para(runs, **kw):
    if isinstance(runs, str):
        runs = rich(runs)
    add("p", runs=runs, **kw)


def small(t, **kw):
    para([R(t, s=8.5, c=INK2)], **kw)


def label(t):
    add("p", runs=[R(t.upper(), c=RED, f="sans", s=7.5, b=True, sp=30)], before=120, after=40, keep=True)


def lines(n, h=450):
    add("lines", n=n, h=h)


def section(n, t, m=""):
    runs = [R(f"{n:02d}  ", c=RED, f="cond", s=14, b=True), R(t, f="serif", s=13, c=INK)]
    if m:
        runs.append(R(f"   {m}", f="sans", s=8, c=INK2))
    add("h3", runs=runs)


def table(widths, rows, **kw):
    add("table", widths=widths, rows=rows, **kw)


def cell(runs=None, paras=None, **kw):
    if isinstance(runs, str):
        runs = rich(runs)
    d = {"paras": paras if paras is not None else [runs or []]}
    d.update(kw)
    return d


def dots_runs():
    return [R("☐1 ☐2 ☐3 ☐4 ☐5", f="sans", s=8, c=INK2)]


W = 9700  # largeur utile (dxa)


def ruler(steps):
    tot = sum(m for _, m in steps)
    widths = [max(700, round(W * m / tot)) for _, m in steps]
    widths[-1] += W - sum(widths)
    row = []
    for n, m in steps:
        spk = n in B.SPEAKING
        row.append(cell(paras=[[R(n, f="sans", s=7.5, b=True, c=RED if spk else INK)], [R(f"{m} min", f="sans", s=7, c=INK2)]],
                        top=RED if spk else INK))
    table(widths, [row], border="ruler")


# ---------------------------------------------------------------- front matter
def cover():
    add("cover", date="16.11.2026 → 30.04.2027",
        kick="CARNET DE VOIX · FRANÇAIS ORAL & PROFESSIONNEL",
        lines_=["Parler,", "expliquer,", "convaincre."],
        sub="Un entraînement quotidien pour passer de « je cherche mes mots » à une soutenance d'ingénieur claire, calme et convaincante.",
        stats=[("166", "jours de pratique"), ("23", "tests oraux"), ("6", "phases"), ("4", "modes avec Claude")],
        foot="Cycle ingénieur · génie logiciel — Préparation à la soutenance, avril 2027")


def toc_page():
    kicker("Sommaire")
    title("Sommaire", toc=False)
    add("toc")
    small("Dans Word : clic droit sur le sommaire › « Mettre à jour les champs » pour afficher les numéros de page. "
          "Pour aller directement à un jour : Affichage › Volet de navigation, puis clique sur la date.")
    label("Mon engagement")
    para("Du 16 novembre 2026 au 30 avril 2027, je parle français chaque jour à voix haute — 60 minutes quand je peux, "
         "20 minutes quand la journée est chargée, jamais zéro. Je m'enregistre, je corrige trois points au maximum, "
         "et je mesure mes progrès chaque dimanche.", style="lead")
    table([3233, 3233, 3234], [[cell([R("Date de début", f="sans", s=8, c=RED, b=True)]), cell([R("Mon heure de séance", f="sans", s=8, c=RED, b=True)]),
                                cell([R("Signature", f="sans", s=8, c=RED, b=True)])],
                               [cell([R(" ")], h=600), cell([R(" ")]), cell([R(" ")])]], border="lines")
    pb()
    kicker("Calendrier des séances")
    title("Calendrier", toc=True)
    rows = [[cell([R("Date", b=True, f="sans", s=8)]), cell([R("Séance", b=True, f="sans", s=8)]), cell([R("✓", b=True, f="sans", s=8)])]]
    d = START
    days = {x["date"]: x for x in B.load_days()}
    sidx = 0
    while d <= END:
        if d.weekday() == 6:
            t = "Test oral : " + SUNDAY[sidx][0]
            sidx += 1
            sh = "FBF0D9"
        else:
            t = days[d]["t"]
            sh = None
        rows.append([cell([R(f"{B.JOURS[d.weekday()][:3]}. {d.day:02d}/{d.month:02d}", f="sans", s=8)], shade=sh),
                     cell([R(f"J{(d - START).days + 1:03d} · {t}", s=8.5)], shade=sh), cell([R("☐", s=8)], shade=sh)])
        d += dt.timedelta(days=1)
    table([1500, 7600, 600], rows, border="rows", header=True)


def usage():
    pb()
    kicker("Mode d'emploi")
    title("Ouvrir le carnet, suivre la séance, parler.")
    para("Ce carnet n'est pas un cours à lire : c'est un entraînement. Chaque matin, tu ouvres la page du jour, tu suis les sept étapes "
         "dans l'ordre et tu parles à voix haute. Le but n'est pas de mémoriser des phrases, mais de construire des réflexes.", style="lead")
    label("Une séance type (≈ 60 min)")
    steps = [("1 · Échauffement", "4′", "Penser en français, parler sans s'arrêter"), ("2 · Écoute", "10′", "Comprendre un texte entendu, répondre"),
             ("3 · Lecture et imitation", "10′", "Six lectures, six objectifs différents"), ("4 · Écriture", "12′", "Réécrire avec mes mots, produire un message"),
             ("5 · Dialogue", "14′", "Jeu de rôle, puis avec Claude"), ("6 · Parole sans lire", "5′", "Défi oral enregistré"),
             ("7 · Bilan", "5′", "3 corrections maximum, auto-évaluation")]
    table([3000, 900, 5800], [[cell([R(a, f="sans", s=9)]), cell([R(b, f="sans", s=9, b=True)]), cell([R(c, s=9)])] for a, b, c in steps], border="rows")
    label("Les jours chargés : version courte (20 min)")
    add("bullets", items=[rich("Échauffement : 2 min"), rich("Les 3 phrases à imiter : 4 min"),
                          rich("Dialogue du jour avec Claude (prompt prêt) : 10 min"), rich("Défi oral enregistré : 4 min")])
    label("Le rythme de la semaine")
    add("bullets", items=[rich("Lundi → vendredi : séances complètes"), rich("Samedi : séance plus légère + révision intelligente"),
                          rich("Dimanche : test oral + page de suivi"), rich("Fin de mois : évaluation mensuelle"),
                          rich("Mars–avril : quelques séances longues (65 à 90 min, mention « Séance longue ») pour les simulations")])
    label("Lire une page en 5 secondes")
    add("bullets", items=[[R("Rouge", c=RED, b=True), R(" : à toi de parler ou de corriger")],
                          [R("surligné", hl=True, i=True), R(" : à compléter avec les vraies informations de ton projet")],
                          [R("souligné en vague", u="wave"), R(" = un souffle · "), R("‖", c=RED, b=True), R(" = une pause")],
                          [R("● REC", c=RED, b=True), R(" : enregistre-toi · "), R("✂", b=True), R(" : prompt à copier dans Claude")]])
    label("Les quatre règles d'or")
    add("bullets", items=[rich("Parler avant d'être prêt : une phrase imparfaite dite à voix haute t'apprend plus qu'une phrase parfaite pensée en silence."),
                          rich("Trois corrections maximum : on corrige d'abord ce qui empêche de comprendre."),
                          rich("Chaque répétition a un but : prononciation, fluidité, intonation, mémoire ou spontanéité."),
                          rich("Ne pas inventer : ni au jury, ni dans ce carnet. On dit ce qu'on sait, on reconnaît ce qu'on ne sait pas.")])


def methods():
    pb()
    kicker("Méthodes")
    title("Lire, imiter, corriger : la méthode du carnet")
    label("La lecture intelligente — six passages, six objectifs")
    rows = [("1 · Silencieuse", "Lis une fois, sans bouger les lèvres.", "Comprendre le sens global"),
            ("2 · À voix haute, lentement", "Articule chaque syllabe.", "Prononciation"),
            ("3 · Rythme naturel", "Lis par groupes de sens.", "Fluidité"),
            ("4 · En imitant", "Écoute la lecture (Edge ou Claude), copie la mélodie.", "Intonation"),
            ("5 · Sans regarder", "Regarde une phrase, lève les yeux, dis-la.", "Mémorisation active"),
            ("6 · Résumé oral", "Ferme le carnet, résume en 3 phrases.", "Spontanéité")]
    table([2800, 4300, 2600], [[cell([R(a, f="sans", s=9, b=True)]), cell(b), cell([R(c, c=RED, s=9)])] for a, b, c in rows], border="rows")
    label("La correction bienveillante")
    para("Après chaque séance, choisis trois erreurs au maximum, dans cet ordre : 1. ce qui empêche de comprendre · 2. la grammaire · 3. le naturel. "
         "Pour chaque erreur : ma formulation → correction naturelle → explication simple → réutilisation à l'oral.")
    ex = [("Je suis d'accord avec ça que tu dis.", "Je suis d'accord avec ce que tu dis.", "Après « avec », on dit « ce que »."),
          ("J'ai fait un test pour voir si ça marche ou non.", "J'ai fait un test pour vérifier que ça marchait.", "Plus précis et plus naturel."),
          ("Le projet il est basé sur…", "Mon projet repose sur…", "On évite « le projet il » en contexte formel.")]
    table([3300, 3300, 3100], [[cell([R("Ma formulation", i=True, c=RED)]), cell([R("Correction naturelle", i=True, c=RED)]), cell([R("Explication", i=True, c=RED)])]] +
          [[cell(a), cell(b), cell(c)] for a, b, c in ex], border="rows", header=True)
    label("Penser directement en français")
    para("Chaque échauffement te demande de décrire ce que tu fais, vois, penses ou prévois, à voix haute, sans traduire. "
         "La durée augmente : 30 s en novembre, 1 min en décembre, 2 min en janvier, 3 min en février, 4 min en mars et avril "
         "(3 min les jours de séance légère). Si un mot manque, décris-le au lieu de t'arrêter.")
    label("Écouter de vrais Français")
    para("Le texte du jour s'écoute avec la lecture à voix haute (Edge, Word : Révision › Lire à voix haute) ou avec Claude en mode vocal. "
         "Chaque dimanche, ajoute une écoute authentique : RFI « Journal en français facile », TV5MONDE, InnerFrench, France Info, conférences tech en français.")


def toolkit():
    pb()
    kicker("Boîte à outils")
    title("Ne plus rester bloqué")
    table([4700, 5000], [[cell([R("Expression de secours", f="sans", s=8, b=True)]), cell([R("Quand l'utiliser", f="sans", s=8, b=True)])]] +
          [[cell([R(a, i=True)]), cell([R(b, s=9, c=INK2)])] for a, b in RESCUE], border="rows", header=True)
    label("Trois registres, une même idée")
    reg = [("J'ai pas capté.", "Je n'ai pas bien compris.", "Pourriez-vous préciser ce point ?"),
           ("Ça bugue grave.", "Il y a un gros bug.", "Nous avons identifié une anomalie bloquante."),
           ("C'est galère.", "C'est compliqué.", "Cette partie a présenté une difficulté technique."),
           ("Je te dis ça vite fait.", "Je te réponds rapidement.", "Je reviens vers vous dans les plus brefs délais.")]
    table([2700, 3000, 4000], [[cell([R("Familier", f="sans", s=8, b=True)]), cell([R("Naturel", f="sans", s=8, b=True)]), cell([R("Professionnel", f="sans", s=8, b=True)])]] +
          [[cell(a), cell(b), cell(c)] for a, b, c in reg], border="rows", header=True)
    pb()
    kicker("Boîte à outils")
    title("Relier ses idées")
    small("Inutile d'apprendre cette liste par cœur : chaque séance te donne un connecteur à placer dans ton défi oral.")
    table([2700, 1900, 5100], [[cell([R("Connecteur", f="sans", s=8, b=True)]), cell([R("Pour…", f="sans", s=8, b=True)]), cell([R("Exemple naturel", f="sans", s=8, b=True)])]] +
          [[cell([R(a, b=True)]), cell([R(b, s=9, c=INK2)]), cell(c)] for a, b, c in CONNECT], border="rows", header=True)
    label("Mes connecteurs préférés")
    lines(4)


def claude_modes():
    pb()
    kicker("Entraînement avec Claude")
    title("Un partenaire qui te fait parler — pas qui parle à ta place")
    para("Chaque séance se termine par un prompt complet, prêt à copier. Utilise si possible le mode vocal de l'application Claude.")
    modes = [("Mode dialogue", "Tu es mon partenaire d'entraînement oral en français (niveau B1, je vise B2). MODE DIALOGUE. Tu joues [rôle] ; je joue [mon rôle]. Situation : [situation]. Parle naturellement, ajoute un imprévu, 8 à 10 échanges, une seule réplique à la fois. Attends toujours ma réponse. Ne réponds jamais à ma place. À la fin : 3 corrections maximum (ma phrase → version naturelle → explication simple), puis fais-moi redire seulement ces phrases."),
             ("Mode compréhension", "MODE COMPRÉHENSION. Dis-moi (ou écris) un message naturel d'environ 120 mots sur [thème]. Pose-moi 3 questions, une à la fois. Puis demande-moi de reformuler avec « Si j'ai bien compris… ». Corrige seulement à la fin, 3 points maximum."),
             ("Mode présentation", "MODE PRÉSENTATION. Je vais présenter [sujet] pendant [durée] sans lire. Ne m'interromps pas. Ensuite, pose 2 questions de relance, une à la fois. Termine par un point fort réel, 3 corrections maximum, et la phrase que je dois redire. N'invente rien sur mon projet."),
             ("Mode simulation de jury", "MODE JURY. Tu es membre d'un jury de soutenance d'ingénieur, poli mais exigeant. Mon projet : [résumé que je fournis]. Pose 5 questions, une à la fois : 1 facile, 2 techniques, 1 critique, 1 imprévue. Si je bloque, propose une expression de secours et attends. N'invente aucun détail sur mon projet.")]
    for n, t in modes:
        label(n)
        add("prompt", head=f"Prompt de base — {n}", body=t)
    label("Honnêteté sur la prononciation")
    para("Quand Claude ne reçoit qu'une transcription texte de ta voix, il ne peut pas entendre ton accent. Les prompts lui demandent de ne pas juger ta prononciation dans ce cas. "
         "Pour la prononciation, ton meilleur outil reste l'enregistrement.")


def stress():
    pb()
    kicker("Gestion du stress")
    title("Le corps parle avant les mots")
    items = [("Respiration 4-4-6", "Inspire 4 s, garde 4 s, expire 6 s. Trois cycles avant chaque séance, cinq avant une simulation."),
             ("Posture", "Pieds à largeur d'épaules, épaules basses, mains visibles à hauteur de la taille."),
             ("Regard", "Regarde chaque membre du jury 3 à 5 secondes, à tour de rôle."),
             ("Voix et débit", "Environ 130 mots par minute. La voix descend à la fin des affirmations."),
             ("Pauses", "Une ou deux secondes avant une idée importante ou après une question : c'est naturel pour le public."),
             ("Après un oubli", "Respire, regarde ta diapositive, dis : « Je reprends : l'idée principale ici, c'est… »")]
    table([2600, 7100], [[cell([R(a, f="serif", s=11)]), cell(b)] for a, b in items], border="rows")
    label("Ma routine personnelle des 10 minutes avant de parler")
    lines(8)


def project_pages():
    groups_ = [("Fiche projet (1/3) — l'essentiel", [("Titre du projet", "Le nom exact, tel qu'il apparaît sur ton rapport.", 1),
                                                     ("Organisme d'accueil / encadrants", "Entreprise, laboratoire ou école ; encadrants.", 2),
                                                     ("Mon sujet en une phrase", "« Mon projet consiste à … pour … afin de … »", 2),
                                                     ("Contexte", "Où, pour qui, quelle situation de départ ?", 4),
                                                     ("Problématique", "Quel problème précis ? Pourquoi est-il important ?", 4),
                                                     ("Objectifs", "3 objectifs maximum, si possible mesurables.", 4)]),
               ("Fiche projet (2/3) — besoins et conception", [("Utilisateurs / acteurs", "Qui utilise le système ? Avec quels rôles ?", 2),
                                                               ("Besoins fonctionnels principaux", "Ce que le système doit faire (5 à 7 points).", 5),
                                                               ("Besoins non fonctionnels", "Performance, sécurité, disponibilité, ergonomie…", 3),
                                                               ("Contraintes et cahier des charges", "Délais, budget, technologies imposées, données.", 3),
                                                               ("Méthode de travail", "Scrum, sprints, outils, planning.", 2),
                                                               ("Conception", "Diagrammes réalisés.", 3)]),
               ("Fiche projet (3/3) — réalisation et résultats", [("Architecture", "Couches, composants, communication, déploiement.", 4),
                                                                 ("Technologies et justification", "Pour chaque technologie : pourquoi elle, et pas une autre ?", 4),
                                                                 ("Réalisations principales", "Ce que je montrerai en démonstration.", 3),
                                                                 ("Tests et qualité", "Types de tests, outils, résultats.", 3),
                                                                 ("Résultats", "Chiffres, retours, objectifs atteints ou non.", 3),
                                                                 ("Limites et perspectives", "Ce qui manque honnêtement ; les améliorations.", 3)])]
    for i, (t, fields) in enumerate(groups_):
        pb()
        kicker("Mon projet de fin d'études")
        title(t, toc=(i == 0))
        small("À remplir avec les informations réelles de ton projet. Les séances de février à avril s'appuient sur ces pages : rien n'est inventé à ta place.")
        for a, b, k in fields:
            label(a)
            para([R(b, i=True, s=9, c=INK2)], after=40)
            lines(k)
    pb()
    kicker("Mon projet de fin d'études")
    title("Mes pitchs", toc=False)
    for a, b, k in [("Pitch de 30 secondes (≈ 70 mots)", "Qui je suis · le problème · ma solution · le résultat.", 5),
                    ("Pitch de 2 minutes (≈ 260 mots) — plan", "Contexte → problématique → objectifs → solution → technologies → résultats → perspectives.", 11),
                    ("Mes 5 mots-clés techniques (et comment je les prononce)", "", 4), ("Les 3 messages que le jury doit retenir", "", 3)]:
        label(a)
        if b:
            para([R(b, i=True, s=9, c=INK2)], after=40)
        lines(k)


def initial_test():
    pb()
    kicker("Test initial · 16 novembre 2026")
    title("Mon point de départ")
    para([R("Le 16 novembre, fais ce test en premier (≈ 12 min), puis la séance du jour 001 en version courte (20 min). ", b=True),
          R("Ce test n'est pas un examen : c'est une photographie. Enregistre chaque épreuve et garde les fichiers. Le 30 avril, tu les réécouteras.")])
    rows = [("1 · Me présenter", "Nom, études, ville, ce que j'aime dans l'informatique.", "1 min"), ("2 · Raconter", "Raconte ta journée d'hier.", "1 min"),
            ("3 · Expliquer", "Explique un projet scolaire : but, outils, difficulté.", "2 min"),
            ("4 · Donner un avis", "« Le télétravail, bonne ou mauvaise idée pour un développeur ? »", "1 min"),
            ("5 · Répondre", "Claude te pose 3 questions surprises (prompt ci-dessous).", "3 min"),
            ("6 · Comprendre", "Écoute 3 min de RFI « Journal en français facile », puis résume.", "4 min")]
    table([2300, 5300, 1000, 1100], [[cell([R(x, f="sans", s=8, b=True)]) for x in ("Épreuve", "Consigne", "Durée", "Réelle")]] +
          [[cell([R(a, f="sans", s=9)]), cell(b), cell([R(c, f="sans", s=9)]), cell([R(" ")])] for a, b, c in rows], border="rows", header=True)
    crit_table("Note de départ", first="")
    label("Ce qui me bloque le plus quand je parle")
    lines(3)
    label("Nombre de pauses longues (> 3 s) — épreuve 2")
    lines(1)
    label("Mon objectif personnel pour avril 2027")
    lines(2)
    add("prompt", head="Prompt pour Claude — test initial",
        body="Tu es examinateur bienveillant de français oral. Je suis développeur en génie logiciel, niveau B1 environ. Pose-moi 3 questions surprises sur ma vie quotidienne, mes études et mon avenir professionnel, une seule à la fois, en attendant ma réponse. Ne m'aide pas pendant que je réponds. À la fin, décris mon niveau en 4 lignes (fluidité, construction des phrases, vocabulaire, clarté) et donne mes 3 erreurs les plus importantes, avec une correction naturelle et une explication simple. Ne juge pas ma prononciation si tu ne reçois que du texte.")


def crit_table(col, first="Mois préc."):
    rows = [[cell([R("Critère et repères", f="sans", s=8, b=True)]), cell([R(col, f="sans", s=8, b=True)])] +
            ([cell([R(first, f="sans", s=8, b=True)])] if first else [])]
    for c in CRITERIA:
        r = [cell(paras=[[R(c, b=True, f="sans", s=9)], [R(f"1 : {CRIT_DESC[c][0]} · 3 : {CRIT_DESC[c][1]} · 5 : {CRIT_DESC[c][2]}", s=8, c=INK2)]]),
             cell(dots_runs())]
        if first:
            r.append(cell([R(" ")]))
        rows.append(r)
    table([6100, 2200, 1400] if first else [7300, 2400], rows, border="rows", header=True)


def progress_grid():
    pb()
    kicker("Tableau de progression global")
    title("23 semaines, 8 critères")
    small("Chaque dimanche, reporte ta note (1 à 5) pour chaque critère, et colorie la case : plus la note est haute, plus la couleur est foncée.")
    abbr = ["Flu.", "Comp.", "Pron.", "Phr.", "Voc.", "Clar.", "Conf.", "Rép."]
    head = [cell([R("Semaine", f="sans", s=7.5, b=True)])] + [cell([R(a, f="sans", s=7.5, b=True)]) for a in abbr] + [cell([R("Remarque", f="sans", s=7.5, b=True)])]
    sundays = [START + dt.timedelta(i) for i in range(166) if (START + dt.timedelta(i)).weekday() == 6]
    rows = [head] + [[cell([R(f"S{i + 1} · {d.day:02d}/{d.month:02d}", f="sans", s=8)], h=380)] + [cell([R(" ")]) for _ in range(9)] for i, d in enumerate(sundays)]
    rows.append([cell([R("Final · 30/04", f="sans", s=8, b=True)], h=380)] + [cell([R(" ")]) for _ in range(9)])
    table([1500] + [650] * 8 + [3000], rows, border="grid", header=True)
    small("Légende : Flu. fluidité · Comp. compréhension · Pron. prononciation · Phr. construction des phrases · Voc. vocabulaire professionnel · "
          "Clar. clarté des explications · Conf. confiance · Rép. réponse aux questions.")


def phase_page(p):
    pb()
    add("phase", n=p["n"], kick=f"PHASE {p['n']} SUR 6 · {B.fdate(p['start'], False).upper()} → {B.fdate(p['end'], False).upper()}",
        name=p["name"], goal=p["goal"],
        meta=f"Niveau visé {p['level']} · échauffement : {p['warm'] if p['n'] < 6 else '4 minutes'} de parole continue")
    label("Ce que je vais travailler")
    add("bullets", items=[rich(x) for x in p["skills"]])
    label("À la fin de la phase, je sais…")
    para(p["final"], style="lead")
    label("Mes intentions pour cette phase")
    lines(4)
    label("Ce que je veux pouvoir dire à l'oral à la fin de la phase")
    lines(5)


# ---------------------------------------------------------------- day
def day_page(day, idx, all_days, num, week_no):
    d = day["date"]
    p = phase_of(d)
    light = day["light"]
    parole = B.speak_minutes(day, light)
    long_session = parole > 5
    steps = [(n, parole if n == "Parole" else m) for n, m in (B.STEPS_LIGHT if light else B.STEPS_NORMAL)]
    total = sum(m for _, m in steps)
    warm_txt = "3 minutes" if light and p["n"] >= 4 else p["warm"]
    dur_label = f"{parole} min" if long_session else B.speak_dur(p)
    pron = PRON[(idx * 5) % len(PRON)] if idx % 2 == 0 else PRON[(idx * 3 + 7) % len(PRON)]
    rescue = RESCUE[idx % len(RESCUE)]
    rescue_old = RESCUE[(idx - 4) % len(RESCUE)]
    conn = CONNECT[(idx * 3) % len(CONNECT)]
    rew = REWRITE[idx % len(REWRITE)]
    mode, prompt = B.claude_prompt(day, p)
    sm = lambda x: f"{x} min"
    L = lambda a, b: a if not light else b

    pb()
    stamps = [x for x in [day["tag"], "Séance légère" if light else None, f"Séance longue · {total} min" if long_session else None] if x]
    add("dayhead", num=f"{num:03d}", date=B.fdate(d).capitalize(), title=day["t"],
        meta=f"Phase {p['n']} — {p['name']} · {total} minutes · {B.MODE_NAMES[mode]}", stamps=stamps,
        anchor=f"d{d.isoformat()}")
    table([3000, 3000, 3700], [[cell(paras=[[R("J'apprends…", i=True, f="serif", s=10)], rich(day["learn"], s=9)]),
                                cell(paras=[[R("Pourquoi ?", i=True, f="serif", s=10)], rich(day["why"], s=9)]),
                                cell(paras=[[R("✓ Objectif du jour", i=True, f="serif", s=10, c=RED)], rich(day["obj"], s=9)])]], border="trio")
    ruler(steps)
    para([R("Rouge = tu parles. ", c=RED, f="sans", s=7.5, b=True),
          R("Jour chargé ? Version 20 min : échauffement 2′ · phrases à imiter 4′ · dialogue avec Claude 10′ · défi oral 4′.", f="sans", s=7.5, c=INK2)])

    section(1, "Échauffement — penser directement en français", sm(L(4, 3)))
    add("bubble", small=f"Parle {warm_txt} sans t'arrêter, sans traduire. Bloqué ? Dis « {rescue[0]} » et continue.", q=day["warm"])

    section(2, "Écoute et compréhension", sm(L(10, 6)))
    small("1. Écoute le texte sans le regarder (lecture à voix haute de Word/Edge, ou Claude). 2. Réponds aux questions à l'oral. 3. Réécoute en lisant et vérifie.")
    add("text", label="TEXTE DU JOUR", runs=rich(day["text"]))
    for i, q in enumerate(day["q"]):
        para([R(f"Q{i + 1}  ", c=RED, f="cond", b=True)] + rich(q, s=9.5), after=20)

    section(3, "Lecture intelligente et imitation", sm(L(10, 6)))
    table([1616] * 5 + [1620], [[cell(paras=[[R(a, f="sans", s=7.5, b=True)], [R(b, f="sans", s=7, c=INK2)]], top=RED if i >= 4 else INK, topw=4 + i * 4)
                                 for i, (a, b) in enumerate([("1 · Silence", "comprendre le sens"), ("2 · Lentement", "articuler chaque son"),
                                                             ("3 · Naturel", "gagner en fluidité"), ("4 · Imiter", "copier l'intonation"),
                                                             ("5 · Sans texte", "retenir l'essentiel"), ("6 · Résumé", "dire avec mes mots")])]], border="ruler")
    small("Phrases à imiter : lentement, puis à vitesse normale, puis dans une réponse à Claude. Soulignement en vague = un souffle · ‖ = une pause.")
    for s in day["imit"]:
        para(groups(s, f="serif", s=11), after=60)
    label("Mes notes de lecture — mots nouveaux, sons difficiles, phrase que je veux garder")
    lines(3)

    # page 2
    pb()
    add("pron", title=pron[0], expl=pron[1], ex=groups(pron[2], f="serif", s=10.5))
    if day["reg"]:
        f_, n_, p_ = day["reg"]
        para([R("Registre — du plus familier au plus professionnel  →", f="sans", s=7.5, c=INK2)], before=120, after=40)
        table([3233, 3233, 3234], [[cell(paras=[[R("FAMILIER · entre amis", f="sans", s=7, b=True, c="8D93AB")], rich(f_, f="serif", s=9.5)], top="C9CCD8"),
                                    cell(paras=[[R("NATUREL · collègues", f="sans", s=7, b=True, c=INK2)], rich(n_, f="serif", s=9.5)], top="7C84A6"),
                                    cell(paras=[[R("PROFESSIONNEL · jury, client", f="sans", s=7, b=True, c=INK)], rich(p_, f="serif", s=9.5)], top=INK)]], border="ruler")
    section(4, "Atelier d'écriture et de réécriture", sm(L(12, 8)))
    table([4850, 4850], [[cell(paras=[[R("A  ", c=RED, f="disp", s=14, i=True), R("Réécriture", i=True, f="serif", s=10)], rich(rew, s=9)]),
                          cell(paras=[[R("B  ", c=RED, f="disp", s=14, i=True), R("Production", i=True, f="serif", s=10)], rich(day["write"], s=9)])]], border="none")
    small("Méthode : écris sans regarder le texte → compare avec l'original → corrige 3 points maximum → relis ta version à voix haute.")
    label("A · Ma réécriture, avec mes mots")
    lines(4)
    label("B · Ma production")
    lines(5)

    section(5, "Dialogue réaliste", sm(L(14, 10)))
    para([R("SCÈNE  ", c=RED, f="sans", s=7.5, b=True)] + rich(day["ctx"], i=True, c=INK2, s=9.5), after=60)
    rows = []
    for ln in day["lines"]:
        who, txt = ln.split(":", 1)
        who, txt = who.strip(), txt.strip()
        name = (day["a"] if who == "A" else day["b"]).split(",")[0].split("(")[0].strip()
        if txt.startswith("?"):
            rows.append([cell([R(name.upper(), f="sans", s=7.5, b=True, c=RED)], ),
                         cell(paras=[[R("✎ À TOI, SANS MODÈLE · ", f="sans", s=7.5, b=True, c=RED)] + rich(txt[1:].strip(), i=True, c=RED, s=10), [R(" ")]], under=RED)])
        else:
            rows.append([cell([R(name.upper(), f="sans", s=7.5, b=True, c=INK if who == "B" else INK2)], ),
                         cell([R("— ", c="8D93AB")] + rich(txt, f="serif", s=10))])
    table([1900, 7800], rows, border="none")
    para([R("≈ AUTRES FAÇONS DE DIRE LA MÊME CHOSE", c=RED, f="sans", s=7.5, b=True)], before=120, after=40, rule=True)
    for v in day["var"]:
        para([R("≈  ", c=RED, b=True)] + alt(v, f="serif", s=9.5), after=20)
    small("Comment pratiquer : lis d'abord les deux rôles à voix haute · puis cache la colonne « Moi » et réponds de mémoire · enfin joue la scène avec Claude, qui changera les répliques.")

    # page 3
    pb()
    section(6, "Prise de parole sans lire", sm(parole))
    add("rec", head=f"Défi oral · {dur_label} · enregistre-toi", task=rich(day["speak"], f="serif", s=11.5),
        tools=[("SI JE BLOQUE", rescue[0], rescue[1]),
               ("CONNECTEUR À PLACER", f"{conn[0]} — {conn[1]}", conn[2]),
               ("RAPPEL (VU AVANT)" if idx >= 4 else "À DÉCOUVRIR AUSSI", rescue_old[0], "À replacer naturellement." if idx >= 4 else rescue_old[1])])
    if d.weekday() == 5:
        wk = [x for x in all_days if (d - x["date"]).days in range(1, 6)]
        ex = " · ".join(f"« {RESCUE[all_days.index(x) % len(RESCUE)][0]} »" for x in wk[:5])
        ph = " · ".join(f"« {x['imit'][0].replace(' // ', ' ').replace(' / ', ' ')} »" for x in wk[:3])
        add("note", head="Révision intelligente de la semaine",
            runs=rich(f"Expressions de secours vues : {ex}. Phrases à réutiliser : {ph}. Défi : place au moins 3 de ces éléments dans le dialogue d'aujourd'hui, sans les lire.", s=9))
    else:
        rd = [all_days[j] for j in (idx - 2, idx - 6) if j >= 0]
        if rd:
            add("note", head="Réutilise aujourd'hui, dans un autre contexte",
                runs=[r for x in rd for r in rich(f"« {x['imit'][1].replace(' // ', ' ').replace(' / ', ' ')} » (jour {(x['date'] - START).days + 1:03d})   ", s=9)])
    add("prompt", head=f"Prompt pour Claude — {B.MODE_NAMES[mode]}", body=prompt)
    section(7, "Bilan et corrections", sm(L(5, 3)))
    corr_table(3)
    small("3 corrections maximum : d'abord ce qui gêne la compréhension, puis la grammaire, puis le naturel. Redis chaque correction 2 fois, puis dans une phrase nouvelle.")
    table([5700, 4000], [[cell([R(c, f="sans", s=9)]), cell(dots_runs())] for c in [CRITERIA[(idx + k * 3) % 8] for k in range(3)]] +
          [[cell([R("☐ Séance complète   ☐ Version courte   ☐ Objectif atteint", f="sans", s=9)]), cell([R(" ")])]], border="rows")
    label("Expressions utiles notées aujourd'hui")
    lines(3)
    label("Ce que je sais faire maintenant · ce que je reprends demain")
    lines(3)


def corr_table(n, heads=("Ma formulation", "Correction naturelle", "Pourquoi (simple)", "Redit")):
    w = [3000, 3000, 2900, 800] if len(heads) == 4 else [3600, 3300, 2800]
    rows = [[cell([R(h, i=True, f="serif", s=9, c=RED)]) for h in heads]]
    rows += [[cell([R(" ")], h=500) for _ in heads[:-1]] + [cell([R("☐" if heads[-1] == "Redit" else " ", c="8D93AB")], align="center")] for _ in range(n)]
    table(w, rows, border="corr", header=True)


def sunday_page(d, week_no, sidx, week_days, num):
    p = phase_of(d)
    t, t1, t2, t3 = SUNDAY[sidx]
    pb()
    add("dayhead", num=f"{num:03d}", date=B.fdate(d).capitalize(), title=t,
        meta=f"Semaine {week_no} — test oral hebdomadaire · 45 minutes", stamps=["Test oral"], anchor=f"d{d.isoformat()}")
    table([3000, 3000, 3700], [[cell(paras=[[R("Je vérifie…", i=True, f="serif", s=10)], rich("Ce que j'ai vraiment retenu cette semaine, sans relire mes notes.", s=9)]),
                                cell(paras=[[R("Pourquoi ?", i=True, f="serif", s=10)], rich("Parler sans préparation, c'est la situation réelle d'une soutenance.", s=9)]),
                                cell(paras=[[R("✓ Règle du test", i=True, f="serif", s=10, c=RED)], rich("Tu t'enregistres. Tu ne t'arrêtes pas pour te corriger. Tu écoutes après.", s=9)])]], border="trio")
    section(1, "Préparation", "5 min")
    add("bubble", small="Respiration 4-4-6 (inspire 4 s, garde 4 s, expire 6 s) × 3. Relis seulement les titres de la semaine :",
        q=" · ".join(f"{x['date'].day:02d}/{x['date'].month:02d} {x['t']}" for x in week_days), qsmall=True)
    for n_, lab, task, m in [(2, "Épreuve 1", t1, "6 min"), (3, "Épreuve 2", t2, "7 min"), (4, "Épreuve 3", t3, "7 min")]:
        section(n_, lab, m)
        add("rec", head="enregistre-toi", task=rich(task, f="serif", s=11), tools=[])
    nxt = d + dt.timedelta(days=7)
    if nxt.month != d.month or nxt > END:
        para([R("Fin du mois → ", c=RED, b=True, f="sans", s=8.5), R("après ce test, remplis la page « Évaluation mensuelle » qui suit et compare avec le mois précédent.", f="sans", s=8.5, c=INK2)])
    section(5, "Écoute authentique de la semaine", "10 min")
    small(f"{LISTEN[sidx % len(LISTEN)]}. Écoute une fois sans pause, note 3 idées, puis résume à voix haute en 1 minute avec « Si j'ai bien compris… ».")
    lines(2)
    section(6, "Après l'écoute de mon enregistrement", "10 min")
    label("Ce qui est déjà mieux que la semaine dernière")
    lines(2)
    label("Ce que je veux améliorer en priorité")
    lines(2)
    prompt = (f"Tu es mon examinateur bienveillant pour un test oral de français (niveau {p['level']}). "
              f"Thème de la semaine : « {t} ». Fais-moi passer 3 épreuves, une par une, et attends ma réponse à chaque fois : "
              f"1) {t1} 2) {t2} 3) {t3} Ne m'interromps pas. À la fin : une note de 1 à 5 pour fluidité, construction des phrases, "
              "clarté et confiance, avec une phrase de justification chacune ; puis les 3 corrections les plus utiles "
              "(ma phrase → version naturelle → explication) et fais-moi redire ces 3 phrases. "
              "Ne juge pas ma prononciation si tu ne reçois que du texte. N'invente rien sur mon projet.")
    add("prompt", head="Prompt pour Claude — test oral", body=prompt)

    # suivi hebdomadaire
    pb()
    kicker(f"Suivi hebdomadaire · semaine {week_no}")
    title("Ma semaine en un coup d'œil", toc=False)
    table([2600, 4400, 900, 900, 900], [[cell([R(x, f="sans", s=8, b=True)]) for x in ("Date", "Thème", "Complète", "Courte", "Remarque")]] +
          [[cell([R(B.fdate(x["date"]), f="sans", s=8.5)]), cell([R(x["t"], s=9)]), cell([R("☐")], align="center"), cell([R("☐")], align="center"), cell([R(" ")])] for x in week_days],
          border="rows", header=True)
    label("Auto-évaluation (1 = difficile · 5 = à l'aise)")
    table([4200, 3000, 2500], [[cell([R(x, f="sans", s=8, b=True)]) for x in ("Critère", "Note", "Évolution")]] +
          [[cell([R(c, f="sans", s=9)]), cell(dots_runs()), cell([R(" ")])] for c in CRITERIA], border="rows", header=True)
    label("Expressions que j'ai réellement utilisées à l'oral")
    lines(3)
    label("Mon objectif pour la semaine prochaine (mesurable)")
    lines(2)
    label("Mes 3 erreurs les plus fréquentes — et leur correction")
    corr_table(3, heads=("Ma formulation", "Correction naturelle", "Réutilisée à l'oral dans…"))
    table([3233, 3233, 3234], [[cell(paras=[[R("Temps de parole", f="serif", s=11)], [R("Mon plus long passage sans lire :", s=8.5, c=INK2)], [R(" ")]], under=INK2),
                                cell(paras=[[R("Pauses longues", f="serif", s=11)], [R("Silences de plus de 3 s (épreuve 1) :", s=8.5, c=INK2)], [R(" ")]], under=INK2),
                                cell(paras=[[R("Confiance", f="serif", s=11)], [R("Un moment où je me suis senti à l'aise :", s=8.5, c=INK2)], [R(" ")]], under=INK2)]], border="none")


def month_eval(month):
    name, tasks, measure = MONTH_EVAL[month]
    pb()
    kicker(f"Évaluation mensuelle · {name}")
    title(f"Où en suis-je à la fin de {name.lower()} ?", toc=True)
    table([4850, 4850], [[cell(paras=[[R("Épreuves (enregistrées)", f="serif", s=11)], rich(tasks, s=9)]),
                          cell(paras=[[R("Mesure objective", f="serif", s=11)], rich(measure, s=9)])]], border="trio")
    crit_table("Note ce mois", first="Test initial" if month == 11 else "Mois préc.")
    label("Mes trois progrès réels du mois")
    lines(4)
    label("Mes trois priorités pour le mois prochain")
    lines(4)
    label("La phrase que je dis maintenant sans effort (et que je ne savais pas dire avant)")
    lines(2)


def final_and_annexes():
    pb()
    kicker("Simulation finale · 30 avril 2027")
    title("La répétition générale")
    small("Conditions réelles : debout, tenue de soutenance, diapositives projetées, au moins une personne dans le rôle du jury (ou Claude en mode vocal), chronomètre visible. Enregistre tout.")
    table([5500, 3000, 1200], [[cell([R(x, f="sans", s=8, b=True)]) for x in ("Étape", "Durée", "Réalisé")]] +
          [[cell(a), cell(b), cell([R("☐")], align="center")] for a, b in [("Routine anti-stress", "5 min"), ("Présentation complète", "selon règlement (≈ 20 min)"),
                                                                            ("Questions du jury", "15 min"), ("Réécoute et grille ci-dessous", "20 min")]],
          border="rows", header=True)
    crit = ["Structure claire et respect du temps", "Clarté du contexte et de la problématique", "Explication de l'architecture et des choix",
            "Démonstration commentée", "Résultats, limites, perspectives", "Fluidité et prononciation", "Posture, regard, voix", "Qualité des réponses aux questions"]
    table([5000, 2400, 2300], [[cell([R(x, f="sans", s=8, b=True)]) for x in ("Grille du jury", "Note", "Commentaire")]] +
          [[cell(c), cell(dots_runs()), cell([R(" ")])] for c in crit], border="rows", header=True)
    label("Comparaison avec le test initial (16 novembre)")
    lines(3)
    label("Mes 3 derniers ajustements avant le jour J")
    lines(3)
    label("Journal des questions du jury — et la qualité de ma réponse")
    corr_table(6, heads=("Question posée", "Ce que j'ai répondu (idée clé)", "Note /5"))

    Q = [("Questions faciles", ["Pouvez-vous résumer votre projet en une minute ?", "Pourquoi avez-vous choisi ce sujet ?", "Quel a été votre rôle exact dans l'équipe ?", "Qu'est-ce qui vous a le plus plu dans ce projet ?", "Combien de temps a duré le projet ?", "Qui sont les utilisateurs de votre application ?"]),
         ("Questions techniques", ["Pourquoi avoir choisi cette architecture ?", "Comment les composants communiquent-ils entre eux ?", "Comment avez-vous conçu votre base de données ?", "Comment gérez-vous l'authentification et les droits ?", "Comment votre application se comporte-t-elle avec beaucoup d'utilisateurs ?", "Comment avez-vous déployé la solution ?", "Comment gérez-vous les erreurs ?", "Quels tests avez-vous écrits, et avec quels outils ?"]),
         ("Questions critiques", ["Pourquoi pas une autre technologie, par exemple [X] ?", "Votre solution existe déjà sur le marché : quelle est votre valeur ajoutée ?", "Vos résultats sont-ils vraiment mesurés ?", "Ce choix n'est-il pas trop complexe pour ce besoin ?", "Si c'était à refaire, que changeriez-vous ?", "Votre couverture de tests est-elle suffisante ?"]),
         ("Questions imprévues", ["Quel est le lien entre votre projet et votre formation ?", "Comment expliqueriez-vous votre projet à un enfant ?", "Quelle compétence non technique avez-vous développée ?", "Où vous voyez-vous dans trois ans ?", "Quel serait le coût de votre solution en production ?", "Que feriez-vous si le client changeait d'avis demain ?"]),
         ("Questions difficiles", ["Votre problématique est-elle vraiment résolue ?", "Quelle est la principale faiblesse de votre travail ?", "Pouvez-vous expliquer précisément ce bout de code ?", "Comment garantissez-vous la sécurité des données personnelles ?", "Pourquoi ce délai par rapport au planning initial ?"])]
    pb()
    kicker("Annexe A")
    title("Annexe A — Banque de questions du jury")
    small("Méthode RAPIDE : Reformuler (si besoin) · Affirmer l'idée principale · Prouver par un fait · Illustrer par un exemple · Dire la limite · Enchaîner ou s'arrêter.")
    for h, qs in Q:
        label(h)
        add("numbered", items=[rich(q) for q in qs])

    pb()
    kicker("Annexe B")
    title("Annexe B — Plan de ma soutenance (base 20 minutes)")
    plan = [("Ouverture et présentation personnelle", "1 min"), ("Contexte et organisme", "1 min 30"), ("Problématique et objectifs", "1 min 30"),
            ("Analyse des besoins", "2 min"), ("Conception et architecture", "3 min"), ("Technologies et justification", "1 min 30"),
            ("Réalisation et démonstration", "5 min"), ("Tests et résultats", "2 min"), ("Limites et perspectives", "1 min"), ("Conclusion et remerciements", "1 min 30")]
    table([500, 3700, 1100, 1700, 2700], [[cell([R(x, f="sans", s=8, b=True)]) for x in ("#", "Partie", "Durée", "Diapositives", "Transition")]] +
          [[cell(str(i + 1)), cell(a), cell(b), cell([R(" ")]), cell([R(" ")])] for i, (a, b) in enumerate(plan)], border="rows", header=True)
    small("Total : 20 minutes. Durées indicatives, à adapter au règlement de ton école.")
    label("Ma première phrase (à savoir parfaitement)")
    lines(3)
    label("Ma dernière phrase")
    lines(3)
    label("Version courte de secours (10 minutes) — ce que je garde, ce que je coupe")
    lines(4)

    pb()
    kicker("Annexe C")
    title("Annexe C — Check-list du jour J")
    label("La veille")
    add("bullets", items=[rich("☐ " + x) for x in ["Présentation exportée en PDF + version originale", "Copie sur clé USB et dans le cloud", "Démo testée de bout en bout ; vidéo de secours enregistrée", "Adaptateurs (HDMI, USB-C), chargeur", "Tenue préparée", "Trajet et horaire vérifiés, arrivée 30 min avant", "Une dernière répétition légère, puis repos", "Coucher à heure normale"]], plain=True)
    label("Le jour même")
    add("bullets", items=[rich("☐ " + x) for x in ["Petit-déjeuner léger, eau", "Échauffement vocal 5 min", "Respiration 4-4-6 × 5", "Vérification du matériel dans la salle", "Première phrase répétée deux fois", "Téléphone en silencieux", "Sourire au jury en entrant", "Pendant les questions : écouter jusqu'au bout"]], plain=True)
    label("Mes phrases d'ancrage")
    para("« Je connais mon projet mieux que personne. » · « Une pause n'est pas une erreur. » · « Si je ne sais pas, je le dis, et j'explique ce que je sais. »", style="lead")
    label("Après la soutenance : ce que je retiens")
    lines(5)

    for i in range(3):
        pb()
        kicker("Annexe D")
        title(f"Annexe D — Carnet d'expressions {i + 1}/3", toc=(i == 0))
        small("Note ici les expressions entendues dans de vraies conversations. Colonne 3 : la situation où tu l'as réutilisée.")
        corr_table(22, heads=("Expression entendue", "Sens / registre", "Je l'ai réutilisée quand ?", "✓"))


# ---------------------------------------------------------------- assemble
def main():
    days = B.load_days()
    by_date = {x["date"]: x for x in days}
    cover()
    pb()
    toc_page()
    usage(); methods(); toolkit(); claude_modes(); stress(); project_pages(); initial_test(); progress_grid()
    seq = [START + dt.timedelta(i) for i in range((END - START).days + 1)]
    sundays = [x for x in seq if x.weekday() == 6]
    cur = None
    for i, d in enumerate(seq):
        p = phase_of(d)
        if p is not cur:
            phase_page(p)
            cur = p
        week_no = (d - START).days // 7 + 1
        if d.weekday() == 6:
            sidx = sundays.index(d)
            wd = [by_date[x] for x in seq if 0 < (d - x).days <= 6 and x in by_date]
            sunday_page(d, week_no, sidx, wd, i + 1)
            nxt = d + dt.timedelta(days=7)
            if nxt.month != d.month or nxt > END:
                month_eval(d.month)
        else:
            day_page(by_date[d], days.index(by_date[d]), days, i + 1, week_no)
    final_and_annexes()
    out = Path(__file__).parent / "docx_model.json"
    out.write_text(json.dumps({"title": B.TITLE, "blocks": blocks}, ensure_ascii=False), encoding="utf-8")
    print(len(blocks), "blocs ->", out)


if __name__ == "__main__":
    main()
