// Génère les .docx du dossier de candidature à partir des sources markdown.
const fs = require('fs');
const path = require('path');
const D = require('docx');
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  WidthType, BorderStyle, ShadingType, AlignmentType, HeadingLevel,
  Header, Footer, PageNumber, LevelFormat, convertMillimetersToTwip,
} = D;

const NAVY = '1F3864';
const GREY = '595959';
const RULE = 'BFBFBF';
const HEADSHADE = 'EDF0F7';

const PAGE_W = 11906, MARGIN = convertMillimetersToTwip(20);
const CONTENT_W = PAGE_W - 2 * MARGIN;

// ---------- markdown inline ----------
function inline(text, base = {}) {
  const runs = [];
  const re = /(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/g;
  let last = 0, m;
  const push = (t, extra) => { if (t) runs.push(new TextRun({ text: t, ...base, ...extra })); };
  while ((m = re.exec(text)) !== null) {
    push(text.slice(last, m.index));
    const tok = m[0];
    if (tok.startsWith('**')) push(tok.slice(2, -2), { bold: true });
    else if (tok.startsWith('`')) push(tok.slice(1, -1), { font: 'Consolas', size: (base.size || 21) - 2 });
    else push(tok.slice(1, -1), { italics: true });
    last = m.index + tok.length;
  }
  push(text.slice(last));
  return runs.length ? runs : [new TextRun({ text: '', ...base })];
}

const strip = s => s.replace(/\*\*|\*|`/g, '');

// ---------- tables ----------
function splitRow(line) {
  return line.trim().replace(/^\|/, '').replace(/\|$/, '').split('|').map(c => c.trim());
}

function buildTable(rows) {
  const header = rows[0];
  const body = rows.slice(1);
  const hasHeader = header.some(c => c !== '');
  const nCols = Math.max(...rows.map(r => r.length));
  const norm = rows.map(r => { const c = r.slice(); while (c.length < nCols) c.push(''); return c; });

  // largeurs adaptatives, plancher à 12 % de la largeur utile
  const weight = Array(nCols).fill(0);
  norm.forEach(r => r.forEach((c, i) => { weight[i] = Math.max(weight[i], Math.min(strip(c).length, 90)); }));
  const total = weight.reduce((a, b) => a + b, 0) || nCols;
  let widths = weight.map(w => Math.max(Math.round(CONTENT_W * w / total), Math.round(CONTENT_W * 0.12)));
  const drift = CONTENT_W - widths.reduce((a, b) => a + b, 0);
  widths[widths.length - 1] += drift;

  const cell = (txt, i, isHead) => new TableCell({
    width: { size: widths[i], type: WidthType.DXA },
    shading: isHead ? { type: ShadingType.CLEAR, fill: HEADSHADE, color: 'auto' } : undefined,
    margins: { top: 60, bottom: 60, left: 110, right: 110 },
    children: [new Paragraph({
      spacing: { after: 0, before: 0, line: 252 },
      children: inline(txt, { size: 19, bold: isHead || undefined, color: isHead ? NAVY : undefined }),
    })],
  });

  const trs = [];
  if (hasHeader) trs.push(new TableRow({ tableHeader: true, children: norm[0].map((c, i) => cell(c, i, true)) }));
  norm.slice(1).forEach(r => trs.push(new TableRow({ children: r.map((c, i) => cell(c, i, false)) })));

  const b = { style: BorderStyle.SINGLE, size: 2, color: RULE };
  return new Table({
    columnWidths: widths,
    width: { size: CONTENT_W, type: WidthType.DXA },
    borders: { top: b, bottom: b, left: b, right: b, insideHorizontal: b, insideVertical: b },
    rows: trs,
  });
}

// ---------- markdown -> éléments ----------
function render(md) {
  const lines = md.split('\n');
  const out = [];
  let i = 0, h1At = -1, subtitleDone = false, sectionStarted = false;

  const hr = () => new Paragraph({
    spacing: { before: 120, after: 160 }, children: [new TextRun('')],
    border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: RULE, space: 1 } },
  });

  while (i < lines.length) {
    const line = lines[i];
    const t = line.trim();

    if (t === '') { i++; continue; }

    if (t === '---' || t === '***') { out.push(hr()); i++; continue; }

    if (t.startsWith('```')) {                       // bloc de code
      i++;
      const buf = [];
      while (i < lines.length && !lines[i].trim().startsWith('```')) buf.push(lines[i++]);
      i++;
      buf.forEach(l => out.push(new Paragraph({
        spacing: { after: 0, line: 240 },
        shading: { type: ShadingType.CLEAR, fill: 'F5F6F8', color: 'auto' },
        children: [new TextRun({ text: l || ' ', font: 'Consolas', size: 17 })],
      })));
      out.push(new Paragraph({ spacing: { after: 120 }, children: [new TextRun('')] }));
      continue;
    }

    if (t.startsWith('|')) {                          // tableau
      const rows = [];
      while (i < lines.length && lines[i].trim().startsWith('|')) {
        const r = splitRow(lines[i]);
        if (!r.every(c => /^:?-{2,}:?$/.test(c))) rows.push(r);
        i++;
      }
      out.push(buildTable(rows));
      out.push(new Paragraph({ spacing: { after: 140 }, children: [new TextRun('')] }));
      continue;
    }

    if (t.startsWith('> ')) {                         // citation
      const buf = [];
      while (i < lines.length && lines[i].trim().startsWith('>')) { buf.push(lines[i].trim().replace(/^>\s?/, '')); i++; }
      out.push(new Paragraph({
        spacing: { before: 100, after: 160, line: 252 },
        indent: { left: 340 },
        border: { left: { style: BorderStyle.SINGLE, size: 12, color: NAVY, space: 10 } },
        children: inline(buf.join(' '), { size: 19, italics: true, color: GREY }),
      }));
      continue;
    }

    const h = t.match(/^(#{1,4})\s+(.*)$/);
    if (h) {
      const lvl = h[1].length, txt = h[2];
      if (lvl === 1) {
        h1At = out.length;
        out.push(new Paragraph({
          spacing: { before: 0, after: 60 }, alignment: AlignmentType.CENTER,
          children: inline(txt, { size: 30, bold: true, color: NAVY, font: 'Calibri' }),
        }));
      } else if (lvl === 2 && h1At === out.length - 1 && !subtitleDone) {
        subtitleDone = true;
        out.push(new Paragraph({
          spacing: { before: 0, after: 180 }, alignment: AlignmentType.CENTER,
          children: inline(txt, { size: 22, color: GREY, font: 'Calibri' }),
        }));
      } else if (lvl === 2) {
        subtitleDone = true; sectionStarted = true;
        out.push(new Paragraph({
          heading: HeadingLevel.HEADING_1, spacing: { before: 260, after: 120 },
          children: inline(txt, { size: 23, bold: true, color: NAVY, font: 'Calibri' }),
        }));
      } else {
        out.push(new Paragraph({
          heading: lvl === 3 ? HeadingLevel.HEADING_2 : HeadingLevel.HEADING_3,
          spacing: { before: 200, after: 100 },
          children: inline(txt, { size: 21, bold: true, color: NAVY, font: 'Calibri' }),
        }));
      }
      i++; continue;
    }

    const box = t.match(/^-\s+\[([ xX])\]\s+(.*)$/);
    if (box) {
      out.push(new Paragraph({
        spacing: { after: 70, line: 252 }, indent: { left: 240 },
        children: [new TextRun({ text: (box[1] === ' ' ? '☐' : '☑') + '  ', size: 21 }), ...inline(box[2])],
      }));
      i++; continue;
    }

    if (/^[-*]\s+/.test(t)) {                          // puce
      out.push(new Paragraph({
        numbering: { reference: 'puces', level: 0 },
        spacing: { after: 70, line: 252 },
        children: inline(t.replace(/^[-*]\s+/, '')),
      }));
      i++; continue;
    }

    // paragraphe : agréger les lignes contiguës (les sources sont enveloppées à 80 colonnes)
    const buf = [];
    while (i < lines.length) {
      const c = lines[i].trim();
      if (c === '' || c.startsWith('|') || c.startsWith('#') || c.startsWith('>') ||
          c === '---' || /^[-*]\s+/.test(c) || c.startsWith('```')) break;
      buf.push(c); i++;
    }
    const para = buf.join(' ');
    const isCoda = /^\*[^*].*\*$/.test(para);
    const isMeta = !sectionStarted;
    out.push(new Paragraph({
      spacing: { after: isMeta ? 180 : 140, line: 264 },
      alignment: isMeta ? AlignmentType.CENTER : AlignmentType.JUSTIFIED,
      children: inline(para, isMeta ? { size: 19 } : (isCoda ? { size: 19, color: GREY } : {})),
    }));
  }
  return out;
}

// ---------- document ----------
function build(mdPath, outPath, runningTitle) {
  const md = fs.readFileSync(mdPath, 'utf8');
  const doc = new Document({
    creator: 'Équipe SentinelleCoop',
    title: runningTitle,
    description: 'Dossier de candidature — Hackathon National d\'Innovation CIF, projet DigiCoop-WA+',
    styles: {
      default: {
        document: {
          run: { font: 'Cambria', size: 21, color: '1A1A1A' },
          paragraph: { spacing: { after: 140, line: 264 } },
        },
      },
    },
    numbering: {
      config: [{
        reference: 'puces',
        levels: [{
          level: 0, format: LevelFormat.BULLET, text: '•', alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 340, hanging: 200 } } },
        }],
      }],
    },
    sections: [{
      properties: {
        page: {
          size: { width: PAGE_W, height: 16838 },
          margin: { top: MARGIN, right: MARGIN, bottom: MARGIN, left: MARGIN, header: 620, footer: 560 },
        },
      },
      headers: {
        default: new Header({
          children: [new Paragraph({
            alignment: AlignmentType.RIGHT, spacing: { after: 0 },
            border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: RULE, space: 4 } },
            children: [new TextRun({ text: runningTitle, size: 16, color: GREY, font: 'Calibri' })],
          })],
        }),
      },
      footers: {
        default: new Footer({
          children: [new Paragraph({
            alignment: AlignmentType.CENTER, spacing: { before: 0, after: 0 },
            children: [
              new TextRun({ text: 'Équipe SentinelleCoop — Hackathon CIF DigiCoop-WA+  ·  ', size: 15, color: GREY, font: 'Calibri' }),
              new TextRun({ children: [PageNumber.CURRENT], size: 15, color: GREY, font: 'Calibri' }),
              new TextRun({ text: ' / ', size: 15, color: GREY, font: 'Calibri' }),
              new TextRun({ children: [PageNumber.TOTAL_PAGES], size: 15, color: GREY, font: 'Calibri' }),
            ],
          })],
        }),
      },
      children: render(md),
    }],
  });
  return Packer.toBuffer(doc).then(buf => { fs.writeFileSync(outPath, buf); console.log('écrit', outPath); });
}

const jobs = [
  ['00-SOMMAIRE.md', '00-SOMMAIRE.docx', 'Sommaire du dossier'],
  ['01-FICHE-PRESENTATION-EQUIPE.md', '01-FICHE-PRESENTATION-EQUIPE.docx', 'Fiche de présentation de l\'équipe'],
  ['02-NOTE-PRESENTATION-SOLUTION.md', '02-NOTE-PRESENTATION-SOLUTION.docx', 'Note de présentation de la solution'],
  ['03-PROFILS-SYNTHETIQUES-MEMBRES.md', '03-PROFILS-SYNTHETIQUES-MEMBRES.docx', 'Profils synthétiques des membres'],
];
(async () => { for (const [a, b, c] of jobs) await build(a, b, c); })();
