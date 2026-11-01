"""Name/markup helpers (pick_first, italicize_name ported from biota/app/jinja_func.py)."""
import re


def pick_first(string, seperator='', lang='zh'):
    a = string.split(seperator)
    if len(a) > 1:
        if lang == 'zh':
            other = '、'.join(a[1:])
            return f'{a[0]}（{other}）'
        return a[0]
    elif len(a) == 1:
        return a[0]


UPRIGHT_NAME_PARTS = {
    'var.', 'subvar.', 'subsp.', 'ssp.', 'f.', 'fo.', 'forma', 'subf.',
    'nothovar.', 'nothosubsp.', 'sect.', 'subsect.', 'ser.', 'cv.',
    'sp.', 'spp.', 'aff.', 'cf.', 'x', '×',
}


def italicize_name(name):
    """"Camphora officinarum var. nominale" -> "<i>Camphora officinarum</i> var. <i>nominale</i>"."""
    if not name:
        return ''
    out, italic = [], []

    def flush():
        if italic:
            out.append(f"<i>{' '.join(italic)}</i>")
            italic.clear()

    for word in name.split():
        if word.lower() in UPRIGHT_NAME_PARTS:
            flush()
            out.append(word)
        else:
            italic.append(word)
    flush()
    return ' '.join(out)


TAG_RE = re.compile(r'<[^>]+>')


def strip_tags(text: str | None) -> str:
    return re.sub(r'\s+', ' ', TAG_RE.sub('', text or '')).strip()


def name_from_usage(usage: str | None) -> str:
    """Plain scientific name (no author) from a TaiCOL usage string.

    "<i>Berberis alpicola</i> C.K.Schneid."            -> "Berberis alpicola"
    "<i>Camphora officinarum</i> var. <i>nominale</i> (Hayata) ..." -> "Camphora officinarum var. nominale"
    Everything after the LAST </i> is authorship / citation.
    """
    if not usage:
        return ''
    head, sep, _ = usage.rpartition('</i>')
    return strip_tags(head + sep if sep else usage)
