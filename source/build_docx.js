// Génère la version Word (.docx) du carnet à partir de docx_model.json (export_docx_model.py).
// Usage : node build_docx.js   (le module npm "docx" doit être résolvable, ex. NODE_PATH=…/node_modules)
const fs = require("fs");
const path = require("path");
const D = require("docx");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType, BorderStyle, ShadingType,
  AlignmentType, HeadingLevel, PageBreak, TableOfContents, Header, Footer, PageNumber, LevelFormat,
  HeightRule, ImageRun, PositionalTab, PositionalTabAlignment, PositionalTabRelativeTo, PositionalTabLeader,
  VerticalAlign, TableLayoutType,
} = D;

const HERE = __dirname;
const model = JSON.parse(fs.readFileSync(path.join(HERE, "docx_model.json"), "utf8"));
const RED = "D6402B", INK = "1C2448", INK2 = "4A5275", FAINT = "8D93AB", RULE = "D9DCE6", SY = "AFBDE0";
const FONTS = { serif: "Sitka Text", disp: "Sitka Display", sans: "Bahnschrift", cond: "Bahnschrift SemiBold Condensed", mono: "Cascadia Mono" };
const W = 9700;

// ------------------------------------------------------------- runs
function run(r) {
  const o = { text: r.t, font: FONTS[r.f || "sans"], size: Math.round((r.s || 9.5) * 2), color: r.c || INK };
  if (r.b) o.bold = true;
  if (r.i) o.italics = true;
  if (r.hl) o.shading = { type: ShadingType.CLEAR, color: "auto", fill: "FFE36E" };
  if (r.u === "wave") o.underline = { type: D.UnderlineType.WAVE, color: INK2 };
  if (r.sp) o.characterSpacing = r.sp;
  if (r.border) o.border = { style: BorderStyle.DOUBLE, size: 6, color: r.border, space: 1 };
  return new TextRun(o);
}
const runs = (rs) => (rs || []).map(run);
const none = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
const line = (color, size = 4, style = BorderStyle.SINGLE) => ({ style, size, color });

function P(rs, o = {}) {
  const opt = { children: runs(rs), spacing: { before: o.before ?? 0, after: o.after ?? 80, line: o.line ?? 276 } };
  if (o.align) opt.alignment = o.align;
  if (o.keep) opt.keepNext = true;
  if (o.border) opt.border = o.border;
  if (o.indent) opt.indent = o.indent;
  if (o.heading) opt.heading = o.heading;
  if (o.shade) opt.shading = { type: ShadingType.CLEAR, color: "auto", fill: o.shade };
  return new Paragraph(opt);
}

// ------------------------------------------------------------- tables
function bordersFor(kind, ri, ci, nrows, ncols, c) {
  const b = { top: none, bottom: none, left: none, right: none };
  switch (kind) {
    case "grid": b.top = b.bottom = b.left = b.right = line(SY); if (ci === 0) b.left = none; break;
    case "rows": b.bottom = line(RULE); if (c.header && ri === 0) b.bottom = line(INK, 8); break;
    case "corr": b.bottom = line(SY); if (ci < ncols - 1) b.right = line("E2E7F4"); if (ri === 0) b.bottom = line(RED, 8); break;
    case "trio": b.top = line(RULE); b.bottom = line(RULE); if (ci > 0) b.left = line(RULE); break;
    case "ruler": b.top = line(c.top || INK, c.topw || 18); b.left = line(INK, 6); if (ci === ncols - 1) b.right = line(INK, 6); break;
    case "lines": b.bottom = line(SY); break;
    case "box": b.top = b.bottom = b.left = b.right = line(c.boxColor || INK, c.boxSize || 8, c.boxStyle || BorderStyle.SINGLE); break;
  }
  if (c.under) b.bottom = line(c.under, 6);
  return b;
}

function mkTable(widths, rows, kind, opts = {}) {
  const nrows = rows.length, ncols = widths.length;
  return new Table({
    width: { size: widths.reduce((a, b) => a + b, 0), type: WidthType.DXA },
    columnWidths: widths,
    layout: TableLayoutType.FIXED,
    rows: rows.map((row, ri) => {
      const h = Math.max(0, ...row.map((c) => c.h || 0));
      return new TableRow({
        cantSplit: true,
        tableHeader: !!(opts.header && ri === 0),
        height: h ? { value: h, rule: HeightRule.ATLEAST } : undefined,
        children: row.map((c, ci) => new TableCell({
          width: { size: widths[ci], type: WidthType.DXA },
          borders: bordersFor(kind, ri, ci, nrows, ncols, { ...c, header: opts.header, ...opts }),
          shading: c.shade || opts.fill ? { type: ShadingType.CLEAR, color: "auto", fill: c.shade || opts.fill } : undefined,
          margins: { top: opts.pad ?? 50, bottom: opts.pad ?? 50, left: 90, right: 90 },
          verticalAlign: VerticalAlign.TOP,
          children: c.children || (c.paras || [[]]).map((rs, k) => P(rs, {
            after: 20, align: c.align === "right" ? AlignmentType.RIGHT : c.align === "center" ? AlignmentType.CENTER : undefined,
          })),
        })),
      });
    }),
  });
}

function box(children, o = {}) {
  return mkTable([W], [[{ children }]], "box", { boxColor: o.color, boxSize: o.size, boxStyle: o.style, fill: o.fill, pad: o.pad ?? 110 });
}
const spacer = (after = 60) => new Paragraph({ children: [], spacing: { before: 0, after } });
const img = (file, wmm, hmm) => new Paragraph({
  spacing: { before: 120, after: 120 },
  children: [new ImageRun({ type: "png", data: fs.readFileSync(path.join(HERE, "docx_assets", file)),
    transformation: { width: Math.round(wmm * 3.78), height: Math.round(hmm * 3.78) } })],
});
const rightTab = () => new PositionalTab({ alignment: PositionalTabAlignment.RIGHT, relativeTo: PositionalTabRelativeTo.MARGIN, leader: PositionalTabLeader.NONE });

// ------------------------------------------------------------- blocks
const out = [];
const numberingRefs = [];
let pendingBreak = false;
function push(x) {
  if (pendingBreak && x instanceof Paragraph === false) { out.push(new Paragraph({ children: [new PageBreak()] })); pendingBreak = false; }
  out.push(x);
}
function pushPara(opt) {
  // vrai saut de page dans le premier paragraphe : respecté par Word, Google Docs et les aperçus
  if (pendingBreak) { opt.children = [new PageBreak(), ...(opt.children || [])]; pendingBreak = false; }
  out.push(new Paragraph(opt));
}
function para(rs, o = {}) {
  const opt = { children: runs(rs), spacing: { before: o.before ?? 0, after: o.after ?? 80, line: 276 } };
  // gros caractères : interligne minimal fixe, sinon certains lecteurs superposent les lignes
  const maxPt = Math.max(0, ...rs.map((r) => r.s || 9.5));
  if (maxPt >= 20) opt.spacing = { ...opt.spacing, line: Math.round(maxPt * 20 * 1.12), lineRule: D.LineRuleType.AT_LEAST };
  if (o.keep) opt.keepNext = true;
  if (o.align) opt.alignment = o.align;
  if (o.heading) opt.heading = o.heading;
  if (o.border) opt.border = o.border;
  if (o.indent) opt.indent = o.indent;
  if (o.numbering) opt.numbering = o.numbering;
  pushPara(opt);
}

for (const b of model.blocks) {
  switch (b.k) {
    case "pb": pendingBreak = true; break;
    case "p": {
      const rs = b.style === "lead" ? b.runs.map((r) => ({ f: "serif", s: 11.5, ...r })) : b.runs;
      para(rs, { before: b.before, after: b.after, keep: b.keep, border: b.rule ? { top: line(RULE, 4) } : undefined });
      break;
    }
    case "h1":
      para(b.runs.map((r) => ({ f: "disp", s: 22, ...r })), { heading: b.toc ? HeadingLevel.HEADING_1 : undefined, after: 160, keep: true });
      break;
    case "h2":
      para(b.runs.map((r) => ({ f: "disp", s: 18, ...r })), { heading: HeadingLevel.HEADING_2, after: 120, keep: true });
      break;
    case "h3":
      para(b.runs, { before: 200, after: 80, keep: true });
      break;
    case "toc":
      pushPara({ children: [] });
      out.push(new TableOfContents("Sommaire", { hyperlink: true, headingStyleRange: "1-1" }));
      break;
    case "bullets":
      for (const it of b.items) para(it.map((r) => ({ s: 9.5, ...r })), b.plain ? { after: 40, indent: { left: 200 } } : { after: 40, numbering: { reference: "bul", level: 0 } });
      break;
    case "numbered": {
      const ref = "num" + Math.random().toString(36).slice(2, 7);
      numberingRefs.push(ref);
      for (const it of b.items) para(it.map((r) => ({ s: 9.5, ...r })), { after: 40, numbering: { reference: ref, level: 0 } });
      break;
    }
    case "lines":
      push(mkTable([W], Array.from({ length: b.n }, () => [{ paras: [[{ t: " " }]], h: b.h || 450 }]), "lines", { pad: 0 }));
      break;
    case "table":
      push(mkTable(b.widths, b.rows, b.border || "rows", { header: b.header }));
      push(spacer(60));
      break;
    case "cover": {
      para([{ t: b.date, f: "cond", s: 10, c: RED }], { after: 400 });
      para([{ t: b.kick, f: "sans", s: 8.5, c: RED, b: true, sp: 60 }], { after: 300 });
      b.lines_.forEach((l, i) => para([{ t: l, f: "disp", s: 54, c: i === 2 ? RED : INK, i: i === 2 }], { after: 0 }));
      para([{ t: b.sub, f: "serif", s: 14, c: INK2 }], { before: 360, after: 200 });
      push(img("wave_cover.png", 165, 31));
      push(mkTable([2425, 2425, 2425, 2425], [b.stats.map(([n, l]) => ({ paras: [[{ t: n, f: "cond", s: 24, c: RED }], [{ t: l, f: "sans", s: 8.5, c: INK2 }]] }))], "trio"));
      para([{ t: b.foot, f: "serif", s: 10.5, c: INK }], { before: 600 });
      para([{ t: "Ce carnet appartient à : ", f: "sans", s: 9, c: INK2 }, { t: "                                                  ", hl: true }], { before: 200 });
      break;
    }
    case "phase":
      para([{ t: String(b.n).padStart(2, "0"), f: "cond", s: 96, c: "F2D4CC" }], { align: AlignmentType.RIGHT, after: 0 });
      para([{ t: b.kick, f: "sans", s: 8.5, c: RED, b: true, sp: 40 }], { after: 120 });
      para([{ t: `Phase ${b.n} — ${b.name}`, f: "disp", s: 30, c: INK }], { heading: HeadingLevel.HEADING_1, after: 160 });
      para([{ t: b.goal, f: "serif", s: 12.5, i: true, c: INK2 }], { after: 80 });
      push(img(`wave_phase${b.n}.png`, 165, 20));
      para([{ t: "TA VOIX GRANDIT · ", f: "sans", s: 8, c: INK2, b: true }, { t: b.meta, f: "sans", s: 8, c: INK2 }], { after: 160 });
      break;
    case "dayhead": {
      const stamps = (b.stamps || []).flatMap((s) => [{ t: "  " }, { t: ` ${s.toUpperCase()} `, f: "cond", s: 8, c: RED, b: true, border: RED }]);
      pushPara({
        children: [run({ t: b.date, f: "sans", s: 9, c: INK2 }), ...runs(stamps)],
        spacing: { after: 20 }, keepNext: true,
      });
      para([{ t: `${b.num}  `, f: "cond", s: 22, c: RED }, { t: b.title, f: "disp", s: 21, c: INK }], { heading: HeadingLevel.HEADING_2, after: 40, keep: true });
      para([{ t: b.meta.split(" — ")[0], f: "sans", s: 8.5, c: RED, b: true }, { t: " — " + b.meta.split(" — ").slice(1).join(" — "), f: "sans", s: 8.5, c: INK2 }], { after: 120, keep: true });
      break;
    }
    case "bubble":
      push(box([P([{ t: b.small, s: 8.5, c: INK2 }], { after: 40 }),
        P([{ t: b.q, f: "serif", s: b.qsmall ? 9.5 : 11.5, i: !b.qsmall, c: INK }], { after: 0 })], { color: INK, size: 8 }));
      push(spacer(80));
      break;
    case "text":
      para([{ t: b.label, f: "sans", s: 7.5, c: RED, b: true, sp: 40 }], { after: 40, keep: true });
      para([{ t: "« ", f: "disp", s: 16, c: RED }, ...b.runs.map((r) => ({ f: "serif", s: 10.5, ...r }))],
        { after: 100, border: { top: line(INK2, 4, BorderStyle.DOTTED), bottom: line(INK2, 4, BorderStyle.DOTTED) } });
      break;
    case "pron":
      push(mkTable([2600, 7100], [[
        { paras: [[{ t: "SON DU JOUR", f: "sans", s: 7, c: RED, b: true, sp: 40 }], [{ t: b.title, f: "disp", s: 12.5, c: INK }]] },
        { paras: [[{ t: b.expl, s: 8.5, c: INK }], b.ex] },
      ]], "none", { fill: "EDF0F8", pad: 100 }));
      push(spacer(80));
      break;
    case "rec": {
      const kids = [P([{ t: "● REC  ", c: RED, b: true, s: 8 }, { t: b.head.toUpperCase(), f: "sans", s: 8, b: true, c: INK, sp: 30 }], { after: 40 }), P(b.task, { after: 40 })];
      if (b.tools && b.tools.length) {
        kids.push(mkTable([3000, 3150, 3150], [b.tools.map(([h, a, c]) => ({ paras: [[{ t: h, f: "sans", s: 7, c: RED, b: true }], [{ t: a, f: "serif", s: 9.5, i: true }], [{ t: c, s: 8, c: INK2 }]] }))], "trio"));
        kids.push(P([], { after: 0 }));
      }
      push(box(kids, { color: INK, size: 12 }));
      push(spacer(80));
      break;
    }
    case "note":
      push(mkTable([W], [[{ paras: [[{ t: b.head, f: "serif", s: 10, i: true }], b.runs] }]], "none", { fill: "E8EEFA", pad: 100 }));
      push(spacer(80));
      break;
    case "prompt":
      push(box([
        new Paragraph({ spacing: { after: 60 }, children: [run({ t: "✂  ", s: 10, c: INK2 }), run({ t: b.head, f: "serif", s: 10.5 }),
          run({ t: "   ·   COPIER TEL QUEL", f: "sans", s: 7, c: RED, b: true, sp: 30 })] }),
        P([{ t: b.body, f: "mono", s: 7.5, c: INK }], { after: 0, line: 252 }),
      ], { color: INK2, size: 6, style: BorderStyle.DASHED, fill: "F3EFE6" }));
      push(spacer(80));
      break;
    default:
      throw new Error("bloc inconnu " + b.k);
  }
}

// ------------------------------------------------------------- document

const doc = new Document({
  creator: "Carnet de voix",
  title: model.title,
  description: "Programme quotidien de français oral et professionnel — 16 novembre 2026 → 30 avril 2027",
  features: { updateFields: true },
  styles: {
    default: { document: { run: { font: FONTS.sans, size: 19, color: INK } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONTS.disp, size: 44, color: INK }, paragraph: { spacing: { before: 0, after: 160 }, keepNext: true, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONTS.disp, size: 42, color: INK }, paragraph: { spacing: { before: 0, after: 40 }, keepNext: true, outlineLevel: 1 } },
    ],
  },
  numbering: {
    config: [
      { reference: "bul", levels: [{ level: 0, format: LevelFormat.BULLET, text: "▪", alignment: AlignmentType.LEFT,
        style: { run: { color: RED }, paragraph: { indent: { left: 360, hanging: 240 } } } }] },
      ...numberingRefs.map((ref) => ({ reference: ref, levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
        style: { run: { color: RED, bold: true }, paragraph: { indent: { left: 400, hanging: 300 } } } }] })),
    ],
  },
  sections: [{
    properties: {
      titlePage: true,
      page: { size: { width: 11906, height: 16838 }, margin: { top: 1000, bottom: 900, left: 1134, right: 1072, header: 450, footer: 420 } },
    },
    headers: {
      first: new Header({ children: [new Paragraph({ children: [] })] }),
      default: new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT,
        children: [run({ t: "Parler, expliquer, convaincre · carnet de voix", f: "sans", s: 7.5, c: FAINT, sp: 20 })] })] }),
    },
    footers: {
      first: new Footer({ children: [new Paragraph({ children: [] })] }),
      default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, border: { top: line(RULE, 4) },
        children: [new TextRun({ children: [PageNumber.CURRENT], font: FONTS.cond, size: 22, color: INK })] })] }),
    },
    children: out,
  }],
});

const dest = path.join(HERE, "..", "Programme-Francais-Oral-Soutenance-2026-2027.docx");
// On retire les entrées « dossier » du ZIP : certains services cloud refusent sinon d'ouvrir le fichier.
const JSZip = require("jszip");
Packer.toBuffer(doc)
  .then((buf) => JSZip.loadAsync(buf))
  .then(async (zip) => {
    // zip.remove(dossier) supprimerait aussi son contenu : on recopie seulement les fichiers.
    const clean = new JSZip();
    for (const name of Object.keys(zip.files)) {
      const f = zip.files[name];
      if (!f.dir) clean.file(name, await f.async("nodebuffer"), { createFolders: false });
    }
    return clean.generateAsync({ type: "nodebuffer", compression: "DEFLATE" });
  })
  .then((buf) => { fs.writeFileSync(dest, buf); console.log("DOCX :", dest, (buf.length / 1e6).toFixed(1), "Mo"); });
