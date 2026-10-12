# Kyrgyzstan — legislation as Markdown (LawCodex)

Legislation of the Kyrgyz Republic (Кыргыз Республикасы) as Markdown, in Kyrgyz (`ky/`, state
language) and Russian (`ru/`, official language). Part of [LawCodex](https://github.com/LawCodex).

Retrieved: **2026-10-12**.

> **Important — texts are archived versions from 2021–2023, not current consolidated texts.**
> See [Why archives](#why-archives) below. Check `last_amended` (edition date shown by the
> database) and `archive` (capture date) in each file's front matter.

## Coverage

__COUNTS__

* **Constitution** of 5 May 2021 (in the database edition captured by the archive).
* **Codes**, **constitutional laws** and **laws** whose page in the old Centralized Database of Legal
  Information was captured by Common Crawl between 2021 and early 2024, and whose text was *not*
  marked "УТРАТИЛ СИЛУ / КҮЧҮН ЖОГОТТУ" (repealed) at capture time. Because the database may have
  repealed or amended an act after the capture, `status` is `unknown` for every file.
* The act type is inferred from the database title of each page (the old site has no
  machine-readable type on the document page); government/presidential decrees, regulations,
  treaties and commentaries are skipped.

## Why archives

The official source is the **Centralized Database of Legal Information** of the Ministry of Justice
(Централизованный банк данных правовой информации, https://cbd.minjust.gov.kg). It offers consolidated
texts and even an OpenData API (`/api/v1/OpenData/…`), but from outside Kyrgyzstan every request —
including `robots.txt` and the API — is answered **HTTP 403 Forbidden** (a firewall/geo block, not a
bot challenge; it does not depend on the User-Agent). The current site is moreover a JavaScript
single-page application whose archived copies contain no text.

The texts were therefore taken from **Common Crawl** (https://commoncrawl.org) captures of the
*previous*, server-rendered version of the database (`http://cbd.minjust.gov.kg/act/view/{ru-ru,ky-kg}/<id>`),
which was replaced at the end of 2023. The zipnum index of the crawls CC-MAIN-2021-25 …
CC-MAIN-2024-18 is scanned for `cbd.minjust.gov.kg/act/view/`, and each page is read with an HTTP
range request from the WARC file recorded in `archived_source` / `archive`. For each document the
newest capture of the plain (current-edition) URL is used.

To build a complete, current corpus one would need access to cbd.minjust.gov.kg (e.g. the Ministry
allow-listing a LawCodex crawler, or publishing the OpenData dump openly).

## Not covered / gaps

* Acts never captured by Common Crawl (the old database held tens of thousands of acts; only a few
  thousand pages were crawled), all acts adopted or amended after 2023, and current consolidated
  versions.
* Secondary legislation (decrees of the President, resolutions of the Cabinet of Ministers,
  ministerial acts) — deliberately skipped.

## Licence

Under art. 8 of the Law of the Kyrgyz Republic "On Copyright and Related Rights", official documents
(laws, court decisions and other texts of a legislative, administrative and judicial nature) and
their official translations are not objects of copyright.

## Structure

```
ru/konstitutsiya/<id>.md                 Constitution
ru/kodeksy/<id>.md                       codes
ru/konstitutsionnye-zakony/<id>.md       constitutional laws
ru/zakony/<year>/<id>.md                 laws, by year of adoption
ky/konstitutsiya/ ky/kodekster/ ky/konstitutsiyalyk-myizamdar/ ky/myizamdar/<year>/   same, Kyrgyz
scripts/                                 fetch + convert code
```

`<id>` is the document code of the Centralized Database (e.g. `112213` = Constitution 2021,
`112309` = Criminal Code 2021). Headings follow the act structure (раздел / глава / параграф /
статья — бөлүм / глава / берене).

## Regenerate

```
python3 -m pip install -r scripts/requirements.txt
python3 scripts/kg_cc.py index CC-MAIN-2024-18 CC-MAIN-2024-10 CC-MAIN-2023-50 ... CC-MAIN-2021-25
python3 scripts/kg_cc.py fetch          # -> ../_raw/kg/html/
python3 scripts/kg_convert.py
```
