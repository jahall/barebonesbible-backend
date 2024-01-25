import unicodedata


def transliterate_greek(text):
    """
    Transliterate greek.
    """
    text = _strip_accents(text)
    for gr_char, tlit_char in _MAP.items():
        text = text.replace(gr_char, tlit_char)
    return text


def _strip_accents(text):
    text = unicodedata.normalize("NFD", text)
    return "".join(c for c in text if unicodedata.category(c) != 'Mn')


_MAP = {
    '\u0391': 'A',
    '\u0392': 'B',
    '\u0393': 'G',
    '\u0394': 'D',
    '\u0395': 'E',
    '\u0396': 'Z',
    '\u0397': 'Ai',  #?
    '\u0398': 'Th',
    '\u0399': 'I',
    '\u039A': 'K',
    '\u039B': 'L',
    '\u039C': 'M',
    '\u039D': 'N',
    '\u039E': 'X',
    '\u039F': 'O',
    '\u03A1': 'P',
    '\u03A2': 'R',
    '\u03A3': 'S',
    '\u03A4': 'T',
    '\u03A5': 'U',
    '\u03A6': 'Ph',
    '\u03A7': 'Ch',
    '\u03A8': 'Ps',
    '\u03A9': 'O',
    '\u03B1': 'a',
    '\u03B2': 'b',
    '\u03B3': 'g',
    '\u03B4': 'd',
    '\u03B5': 'e',
    '\u03B6': 'z',
    '\u03B7': 'ai',  #?
    '\u03B8': 'th',
    '\u03B9': 'i',
    '\u03BA': 'k',
    '\u03BB': 'l',
    '\u03BC': 'm',
    '\u03BD': 'n',
    '\u03BE': 'x',
    '\u03BF': 'o',
    '\u03C0': 'p',
    '\u03C1': 'r',
    '\u03C2': 's',
    '\u03C3': 's',
    '\u03C4': 't',
    '\u03C5': 'u',
    '\u03C6': 'ph',
    '\u03C7': 'ch',
    '\u03C8': 'ps',
    '\u03C9': 'o',
}
