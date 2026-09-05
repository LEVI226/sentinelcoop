#!/usr/bin/env python3
"""Génère le .docx depuis le .md, puis resserre marges et corps de texte."""
import re, sys, shutil, subprocess, zipfile, os, tempfile

SZ = "21"        # 10.5 pt (demi-points)
MARGIN = "1000"  # ~1,76 cm (twips)

def build(md, docx):
    subprocess.run(["pandoc", md, "-o", docx], check=True)
    tmp = tempfile.mkdtemp()
    with zipfile.ZipFile(docx) as z:
        names = z.namelist()
        z.extractall(tmp)

    p = os.path.join(tmp, "word/styles.xml")
    s = open(p, encoding="utf-8").read()
    s = re.sub(r'<w:sz w:val="24"\s*/>', f'<w:sz w:val="{SZ}"/>', s)
    s = re.sub(r'<w:szCs w:val="24"\s*/>', f'<w:szCs w:val="{SZ}"/>', s)
    s = re.sub(r'<w:spacing w:after="200"\s*/>', '<w:spacing w:after="110"/>', s)
    open(p, "w", encoding="utf-8").write(s)

    p = os.path.join(tmp, "word/document.xml")
    d = open(p, encoding="utf-8").read()
    pgmar = (f'<w:pgMar w:top="{MARGIN}" w:right="{MARGIN}" w:bottom="{MARGIN}" '
             f'w:left="{MARGIN}" w:header="480" w:footer="480" w:gutter="0"/>')
    if "<w:pgMar" in d:
        d = re.sub(r'<w:pgMar[^>]*/>', pgmar, d)
    else:
        d = d.replace("</w:sectPr>", pgmar + "</w:sectPr>")
    open(p, "w", encoding="utf-8").write(d)

    with zipfile.ZipFile(docx, "w", zipfile.ZIP_DEFLATED) as z:
        for n in names:
            z.write(os.path.join(tmp, n), n)
    shutil.rmtree(tmp)

def pages(docx):
    out = tempfile.mkdtemp()
    subprocess.run(["soffice", "--headless", "--convert-to", "pdf", docx,
                    "--outdir", out], check=True, capture_output=True)
    pdf = os.path.join(out, os.path.basename(docx).replace(".docx", ".pdf"))
    n = len(re.findall(rb"/Type\s*/Page[^s]", open(pdf, "rb").read()))
    shutil.rmtree(out)
    return n

if __name__ == "__main__":
    for md in sys.argv[1:]:
        docx = md.replace(".md", ".docx")
        build(md, docx)
        print(f"{docx}: {pages(docx)} pages")
