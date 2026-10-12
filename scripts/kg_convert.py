#!/usr/bin/env python3
"""Convert archived pages of the old Centralized Database of Legal Information of Kyrgyzstan
(cbd.minjust.gov.kg/act/view/<lang>/<id>, taken from Common Crawl by kg_cc.py) to Markdown.

Only the Constitution, codes and laws (incl. constitutional laws) are kept; the type is inferred
from the page title (the old site does not expose a machine-readable act type on the page).
"""
import gzip, os, re, sys, html
from bs4 import BeautifulSoup, NavigableString

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..'))
RAW = os.path.abspath(os.path.join(REPO, '..', '_raw', 'kg'))
RETRIEVED = '2026-10-12'

LANG = {'ru-ru': 'ru', 'ky-kg': 'ky'}
DIRS = {
    'ru': {'constitution': 'konstitutsiya', 'code': 'kodeksy', 'constitutional_law': 'konstitutsionnye-zakony', 'law': 'zakony'},
    'ky': {'constitution': 'konstitutsiya', 'code': 'kodekster', 'constitutional_law': 'konstitutsiyalyk-myizamdar', 'law': 'myizamdar'},
}
KINDS = ['part', 'section', 'subsection', 'chapter', 'paragraph', 'article']
PAT = {
    'part': re.compile(r'^((общая|особенная)\s+часть|часть\s+[IVXLC\d]+\b|(жалпы|өзгөчө|атайын)\s+бөлүк|[IVXLC\d]+[-‑]?\s*бөлүк\b)', re.I),
    'section': re.compile(r'^(раздел\s|[IVXLC\d]+[-‑]?\s*бөлүм\b|[а-яөүң]+\s+бөлүм\b)', re.I),
    'subsection': re.compile(r'^(подраздел\s|[IVXLC\d]+[-‑]?\s*бөлүмчө\b)', re.I),
    'chapter': re.compile(r'^(глава\s|[IVXLC\d]+[-‑]?\s*(глава|бап)\b)', re.I),
    'paragraph': re.compile(r'^(параграф\s|§\s*\d|[IVXLC\d]+[-‑]?\s*параграф\b)', re.I),
    'article': re.compile(r'^(статья\s+\d|\d+(-\d+)?[-‑]?\s*берене\b)', re.I),
}
MONTHS = {'январ': 1, 'феврал': 2, 'март': 3, 'апрел': 4, 'мая': 5, 'май': 5, 'июн': 6, 'июл': 7, 'август': 8,
          'сентябр': 9, 'октябр': 10, 'ноябр': 11, 'декабр': 12}


def kind_of(t):
    for k in KINDS:
        if PAT[k].match(t):
            return k
    return None


def norm(t):
    t = t.replace('\xa0', ' ')
    return re.sub(r'\s+', ' ', t).strip()


def md_escape(t):
    t = re.sub(r'^(#+)', r'\\\1', t)
    t = re.sub(r'^(\d+)([.)]) ', r'\1\\\2 ', t)
    t = re.sub(r'^([-+*>]) ', r'\\\1 ', t)
    return t


def ptext(p):
    parts, cur = [], []
    for d in p.descendants:
        if isinstance(d, NavigableString):
            cur.append(str(d))
        elif d.name == 'br':
            parts.append(''.join(cur)); cur = []
    parts.append(''.join(cur))
    return [norm(x) for x in parts if norm(x)]


def table_md(tbl):
    rows = []
    for tr in tbl.find_all('tr'):
        cells = [' '.join(ptext(td)).replace('|', '\\|') for td in tr.find_all(['td', 'th'])]
        if any(cells):
            rows.append(cells)
    if not rows:
        return ''
    n = max(len(r) for r in rows)
    rows = [r + [''] * (n - len(r)) for r in rows]
    return '\n'.join(['| ' + ' | '.join(rows[0]) + ' |', '|' + ' --- |' * n] +
                     ['| ' + ' | '.join(r) + ' |' for r in rows[1:]])


def convert(content):
    blocks = []
    for el in content.find_all(['p', 'table', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li'], recursive=True):
        if el.name != 'table' and el.find_parent('table') is not None:
            continue
        if el.name == 'table':
            m = table_md(el)
            if m:
                blocks.append(['raw', m])
            continue
        lines = ptext(el)
        if not lines:
            continue
        one = ' '.join(lines)
        bold = norm(' '.join(x.get_text(' ') for x in el.find_all(['b', 'strong']))) == one or el.name.startswith('h')
        k = kind_of(one) if (bold or len(one) < 200) else None
        if k and (bold or k == 'article'):
            blocks.append(['h', k, one])
        elif bold and blocks and blocks[-1][0] == 'h' and blocks[-1][1] in KINDS and len(one) < 300:
            blocks[-1][2] += ' ' + one
        else:
            for ln in lines:
                blocks.append(['p', ln])
    return blocks


def render(blocks):
    present = [k for k in KINDS if any(b[0] == 'h' and b[1] == k for b in blocks)]
    level = {k: min(2 + i, 6) for i, k in enumerate(present)}
    out = []
    for b in blocks:
        if b[0] == 'h':
            out.append('#' * level[b[1]] + ' ' + b[2])
        elif b[0] == 'p':
            out.append(md_escape(b[1]))
        else:
            out.append(b[1])
    return '\n\n'.join(out) + '\n'


def classify(title, lang):
    t = title.lower()
    if re.search(r'комментари|түшүндүрм|научно-практическ', t):
        return None
    if lang == 'ru':
        t0 = t.lstrip('"«( ')
        if t0.startswith('конституционный закон'):
            return 'constitutional_law'
        if t0.startswith('закон'):
            return 'law'
        if t0.startswith('кодекс') and 'о внесении' not in t and 'о введении' not in t:
            return 'code'
        if re.search(r'постановлени|указ\b|указ |распоряжени|положени[ея]|решени[ея]|приказ|инструкци|правила|соглашени|договор|протокол|конвенци|меморандум|программ|концепци|стратеги', t[:120]):
            return None
        if t.lstrip('"«').startswith('конституция') and 'закон' not in t[:40]:
            return 'constitution'
        if 'конституционный закон' in t:
            return 'constitutional_law'
        if 'кодекс' in t and 'о внесении' not in t and 'о введении' not in t:
            return 'code'
        if 'закон' in t:
            return 'law'
        return None
    if re.search(r'мыйзамы\W*$', t) and not re.search(r'токтому|чечими|жарлыгы', t):
        return 'constitutional_law' if 'конституциялык мыйзам' in t else 'law'
    if re.search(r'өкмөт|министрлер кабинет|жарлы|токтом|жобо|буйру|тескеме|чечим|келишим|макулдашуу|протокол|конвенция|программ|концепци|стратегия', t):
        return None
    if 'конституциясы' in t and 'мыйзам' not in t:
        return 'constitution'
    if 'конституциялык мыйзам' in t:
        return 'constitutional_law'
    if 'кодекс' in t and 'өзгөртүү' not in t and 'колдонууга киргизүү' not in t:
        return 'code'
    if 'мыйзам' in t:
        return 'law'
    return None


def parse_date(t):
    m = re.search(r'(\d{1,2})\s+([а-я]+)\s+(\d{4})\s+год', t, re.I)
    if m:
        mon = m.group(2).lower()
        for k, v in MONTHS.items():
            if mon.startswith(k):
                return f'{m.group(3)}-{v:02d}-{int(m.group(1)):02d}'
    m = re.search(r'(\d{4})-жылдын\s+(\d{1,2})\s*-?\s*([а-яөүң]+)', t, re.I)
    if m:
        ky = {'январ': 1, 'феврал': 2, 'март': 3, 'апрел': 4, 'май': 5, 'июн': 6, 'июл': 7, 'август': 8,
              'сентябр': 9, 'октябр': 10, 'ноябр': 11, 'декабр': 12}
        for k, v in ky.items():
            if m.group(3).lower().startswith(k):
                return f'{m.group(1)}-{v:02d}-{int(m.group(2)):02d}'
    m = re.search(r'(\d{2})\.(\d{2})\.(\d{4})', t)
    if m:
        return f'{m.group(3)}-{m.group(2)}-{m.group(1)}'
    return None


def yq(s):
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'


def main():
    stats, skipped, repealed = {}, 0, 0
    for lcode in ('ru-ru', 'ky-kg'):
        d = os.path.join(RAW, 'html', lcode)
        if not os.path.isdir(d):
            continue
        lang = LANG[lcode]
        for fn in sorted(os.listdir(d)):
            if not fn.endswith('.html.gz'):
                continue
            docid = fn[:-8]
            raw = gzip.open(os.path.join(d, fn)).read()
            head, _, body = raw.partition(b'\n')
            _, cts, cfile, coff, clen = head.decode().split(':')
            soup = BeautifulSoup(body.decode('utf-8', 'replace'), 'lxml')
            t = soup.find('title')
            title = norm(html.unescape(t.get_text())) if t else docid
            typ = classify(title, lang)
            if typ is None:
                skipped += 1
                continue
            content = soup.select_one('.act-content')
            if content is None:
                continue
            for img in content.find_all('img'):
                img.decompose()
            head_txt = norm(content.get_text(' '))[:500].lower()
            if re.search(r'утратил[аио]?\s+силу|күчүн\s+жогот', head_txt):
                repealed += 1
                continue
            blocks = convert(content)
            if not blocks:
                continue
            ed = None
            m = re.search(r'Редакция:\s*</?[^>]*>?\s*([\d.]{10})', body.decode('utf-8', 'replace'))
            if not m:
                m = re.search(r'(?:Редакция|Редакциясы)[^0-9]{0,200}?(\d{2}\.\d{2}\.\d{4})', soup.get_text(' '))
            if m:
                dd = m.group(1).split('.')
                ed = f'{dd[2]}-{dd[1]}-{dd[0]}'
            date = parse_date(title)
            year = date[:4] if date else 'unknown'
            sub = DIRS[lang][typ]
            rel = os.path.join(lang, sub, year, f'{docid}.md') if typ == 'law' else os.path.join(lang, sub, f'{docid}.md')
            url = f'http://cbd.minjust.gov.kg/act/view/{lcode}/{docid}'
            fm = ['---', f'title: {yq(title)}', f'identifier: "cbd:{docid}"', f'type: {"act" if typ == "law" else typ}',
                  'jurisdiction: kg', f'language: {lang}']
            if date:
                fm.append(f'date: {date}')
            if ed:
                fm.append(f'last_amended: {ed}  # edition date shown by the database at capture time')
            fm += ['status: unknown', f'source: "{url}"',
                   f'archived_source: "https://data.commoncrawl.org/{cfile}"',
                   f'archive: "Common Crawl capture {cts[:4]}-{cts[4:6]}-{cts[6:8]}, WARC bytes {coff}+{clen}"',
                   f'retrieved: {RETRIEVED}', '---', '']
            md = '\n'.join(fm) + f'\n# {title}\n\n' + render(blocks)
            out = os.path.join(REPO, rel)
            os.makedirs(os.path.dirname(out), exist_ok=True)
            with open(out, 'w', encoding='utf-8', newline='\n') as f:
                f.write(md)
            stats[(lang, typ)] = stats.get((lang, typ), 0) + 1
    print(stats, 'skipped(other types)', skipped, 'repealed', repealed)


if __name__ == '__main__':
    main()
