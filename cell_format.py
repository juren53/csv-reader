"""Display XLSX cell values the way Excel shows them, and parse edited text back.

format_cell(value, number_format) -> str
    Renders a cell value using its Excel number format: currency, thousands
    separators, fixed decimals, percentages, dates and times. Formats that are
    not understood fall back to a plain rendering, never an error.

parse_cell_text(text, number_format, kind) -> value or None
    The reverse for edited text: "$1,250.00" -> 1250.0, "12%" -> 0.12,
    "9/4/2026" with an m/d/yyyy format -> datetime. Returns None when the text
    does not parse, so the caller can keep it as text.
"""
import datetime
import re

GENERAL = 'General'

# Builtin format 14 is "locale short date"; openpyxl reports it as mm-dd-yy,
# but Excel (US) shows m/d/yyyy. Same for 22 (short date + time).
_LOCALE_FORMATS = {
    'mm-dd-yy': 'm/d/yyyy',
    'm/d/yy h:mm': 'm/d/yyyy h:mm',
}

_BRACKET_RE = re.compile(r'\[[^\]]*\]')
_DATE_TOKEN_RE = re.compile(
    r'"[^"]*"|\\.|yyyy|yy|mmmmm|mmmm|mmm|mm|m|dddd|ddd|dd|d|hh|h|ss|s|'
    r'AM/PM|am/pm|A/P|a/p|\.0+|.', re.IGNORECASE)


# ----------------------------------------------------------------- general

def _general(value):
    if isinstance(value, bool):
        return 'TRUE' if value else 'FALSE'
    if isinstance(value, float):
        if value.is_integer() and abs(value) < 1e15:
            return str(int(value))
        return f"{value:.15g}"
    if isinstance(value, datetime.datetime):
        if value.time() == datetime.time(0):
            return value.date().isoformat()
        return value.isoformat(sep=' ', timespec='seconds')
    if isinstance(value, (datetime.date, datetime.time)):
        return value.isoformat()
    return str(value)


def _split_sections(fmt):
    """Split on ';' outside quotes / escapes"""
    sections, current, i, quoted = [], [], 0, False
    while i < len(fmt):
        ch = fmt[i]
        if ch == '"':
            quoted = not quoted
        elif ch == '\\' and not quoted and i + 1 < len(fmt):
            current.append(fmt[i:i + 2])
            i += 2
            continue
        elif ch == ';' and not quoted:
            sections.append(''.join(current))
            current = []
            i += 1
            continue
        current.append(ch)
        i += 1
    sections.append(''.join(current))
    return sections


def _strip_brackets(section):
    """Drop [Red], [<=100], [$-409]; keep the symbol of [$€-407]"""
    def keep_currency(match):
        body = match.group(0)[1:-1]
        if body.startswith('$'):
            return body[1:].split('-')[0]
        return ''
    return _BRACKET_RE.sub(keep_currency, section)


# ----------------------------------------------------------------- numbers

def _tokenize_number(section):
    """List of ('lit', text) / ('ph', char) tokens, or None if unsupported"""
    tokens, i = [], 0
    while i < len(section):
        ch = section[i]
        if ch == '"':
            end = section.find('"', i + 1)
            end = len(section) if end == -1 else end
            tokens.append(('lit', section[i + 1:end]))
            i = end + 1
            continue
        if ch == '\\' and i + 1 < len(section):
            tokens.append(('lit', section[i + 1]))
            i += 2
            continue
        if ch == '_' and i + 1 < len(section):   # space the width of next char
            tokens.append(('lit', ' '))
            i += 2
            continue
        if ch == '*' and i + 1 < len(section):   # repeat-fill: ignore
            i += 2
            continue
        if ch in '0#?.,':
            tokens.append(('ph', ch))
        elif ch in 'eE/':                        # handled by caller / fractions
            return None
        elif ch == '@':
            pass
        else:
            tokens.append(('lit', ch))
        i += 1
    return tokens


def _format_scientific(value, section, negative):
    mantissa = re.sub(r'"[^"]*"|\\.', '', section).upper().split('E')[0]
    decimals = len(mantissa.partition('.')[2].replace(',', ''))
    return f"{'-' if negative else ''}{abs(value):.{decimals}E}"


def _format_number(value, section, negative):
    section = _strip_brackets(section)
    if re.search(r'[eE][+-]', re.sub(r'"[^"]*"|\\.', '', section)):
        return _format_scientific(value, section, negative)
    tokens = _tokenize_number(section)
    if tokens is None:
        return None
    ph_idx = [i for i, (kind, _) in enumerate(tokens) if kind == 'ph']
    if not ph_idx:  # all-literal section, e.g. "-" for zero
        return ''.join(text for _, text in tokens)
    first, last = ph_idx[0], ph_idx[-1]
    if any(kind == 'lit' for kind, _ in tokens[first:last + 1]):
        return None  # literals inside the digits (phone/ID masks): not supported
    prefix = ''.join(text for _, text in tokens[:first])
    suffix = ''.join(text for _, text in tokens[last + 1:])
    block = ''.join(text for _, text in tokens[first:last + 1])

    if '%' in prefix + suffix:
        value *= 100
    int_part, _, frac_part = block.partition('.')
    while int_part.endswith(','):             # trailing commas scale by 1000
        value /= 1000
        int_part = int_part[:-1]
    thousands = ',' in int_part
    int_digits = int_part.replace(',', '')
    max_dec = len(frac_part.replace(',', ''))
    min_dec = len(frac_part.rstrip('#?').replace(',', ''))

    text = f"{abs(value):,.{max_dec}f}" if thousands else f"{abs(value):.{max_dec}f}"
    whole, _, frac = text.partition('.')
    if max_dec > min_dec:
        frac = frac[:min_dec] + frac[min_dec:].rstrip('0')
    min_int = int_digits.count('0')
    if whole.replace(',', '') == '0' and min_int == 0:
        whole = ''
    elif min_int > len(whole.replace(',', '')):
        whole = whole.zfill(min_int)
    result = whole + '.' + frac if frac else whole  # '#' / '?' show nothing for zero
    return f"{'-' if negative else ''}{prefix}{result}{suffix}"


def _number_text(value, fmt):
    sections = _split_sections(fmt)
    if value < 0 and len(sections) >= 2 and sections[1]:
        return _format_number(-value, sections[1], negative=False)
    if value == 0 and len(sections) >= 3:
        return _format_number(value, sections[2], negative=False)
    return _format_number(value, sections[0], negative=value < 0)


# ------------------------------------------------------------------- dates

def _date_tokens(section):
    """Tokens with 'm' resolved to month or minute"""
    raw = [t for t in _DATE_TOKEN_RE.findall(_strip_brackets(section))]
    kinds = []
    for t in raw:
        low = t.lower()
        if t.startswith('"'):
            kinds.append(('lit', t[1:-1]))
        elif t.startswith('\\'):
            kinds.append(('lit', t[1:]))
        elif low in ('yyyy', 'yy', 'mmmmm', 'mmmm', 'mmm', 'mm', 'm', 'dddd', 'ddd', 'dd', 'd',
                     'hh', 'h', 'ss', 's'):
            kinds.append(('tok', low))
        elif low in ('am/pm', 'a/p'):
            kinds.append(('tok', low))
        elif low.startswith('.0'):
            kinds.append(('tok', low))
        else:
            kinds.append(('lit', t))
    # m / mm after an hour or before seconds means minutes
    toks = [i for i, (k, _) in enumerate(kinds) if k == 'tok']
    for pos, i in enumerate(toks):
        if kinds[i][1] in ('m', 'mm'):
            prev = kinds[toks[pos - 1]][1] if pos > 0 else ''
            nxt = kinds[toks[pos + 1]][1] if pos + 1 < len(toks) else ''
            if prev in ('h', 'hh') or nxt in ('s', 'ss'):
                kinds[i] = ('tok', 'min' + kinds[i][1])
    return kinds


def _date_text(value, fmt):
    section = _split_sections(fmt)[0]
    tokens = _date_tokens(section)
    twelve_hour = any(k == 'tok' and v in ('am/pm', 'a/p') for k, v in tokens)
    if isinstance(value, datetime.time):
        value = datetime.datetime.combine(datetime.date(1899, 12, 30), value)
    elif not isinstance(value, datetime.datetime):
        value = datetime.datetime.combine(value, datetime.time(0))
    hour = value.hour % 12 or 12 if twelve_hour else value.hour
    out = []
    for kind, tok in tokens:
        if kind == 'lit':
            out.append(tok)
        elif tok == 'yyyy':
            out.append(f"{value.year:04d}")
        elif tok == 'yy':
            out.append(f"{value.year % 100:02d}")
        elif tok == 'mmmmm':
            out.append(value.strftime('%B')[0])
        elif tok == 'mmmm':
            out.append(value.strftime('%B'))
        elif tok == 'mmm':
            out.append(value.strftime('%b'))
        elif tok == 'mm':
            out.append(f"{value.month:02d}")
        elif tok == 'm':
            out.append(str(value.month))
        elif tok == 'dddd':
            out.append(value.strftime('%A'))
        elif tok == 'ddd':
            out.append(value.strftime('%a'))
        elif tok == 'dd':
            out.append(f"{value.day:02d}")
        elif tok == 'd':
            out.append(str(value.day))
        elif tok == 'hh':
            out.append(f"{hour:02d}")
        elif tok == 'h':
            out.append(str(hour))
        elif tok == 'minmm':
            out.append(f"{value.minute:02d}")
        elif tok == 'minm':
            out.append(str(value.minute))
        elif tok == 'ss':
            out.append(f"{value.second:02d}")
        elif tok == 's':
            out.append(str(value.second))
        elif tok == 'am/pm':
            out.append('AM' if value.hour < 12 else 'PM')
        elif tok == 'a/p':
            out.append('A' if value.hour < 12 else 'P')
        elif tok.startswith('.0'):
            digits = len(tok) - 1
            out.append('.' + f"{value.microsecond:06d}"[:digits])
    return ''.join(out)


def _date_parse_pattern(fmt):
    """strptime pattern for a date format, or None"""
    tokens = _date_tokens(_split_sections(fmt)[0])
    twelve_hour = any(k == 'tok' and v in ('am/pm', 'a/p') for k, v in tokens)
    mapping = {'yyyy': '%Y', 'yy': '%y', 'mmmm': '%B', 'mmm': '%b', 'mm': '%m', 'm': '%m',
               'dddd': '%A', 'ddd': '%a', 'dd': '%d', 'd': '%d',
               'hh': '%I' if twelve_hour else '%H', 'h': '%I' if twelve_hour else '%H',
               'minmm': '%M', 'minm': '%M', 'ss': '%S', 's': '%S', 'am/pm': '%p'}
    out = []
    for kind, tok in tokens:
        if kind == 'lit':
            out.append(tok.replace('%', '%%'))
        elif tok in mapping:
            out.append(mapping[tok])
        else:
            return None  # a/p, mmmmm, fractions: not parseable
    return ''.join(out)


# ------------------------------------------------------------------ public

def is_date_format(fmt):
    if not fmt or fmt == GENERAL:
        return False
    fmt = _LOCALE_FORMATS.get(fmt, fmt)
    section = re.sub(r'"[^"]*"|\\.', '', _strip_brackets(_split_sections(fmt)[0]))
    return bool(re.search(r'[ymdhs]', section, re.IGNORECASE))


def is_number_format(fmt):
    return bool(fmt) and fmt not in (GENERAL, '@') and not is_date_format(fmt)


def format_cell(value, number_format=GENERAL):
    """Text for a cell value as Excel would display it"""
    if value is None:
        return ''
    if type(value) is str:  # fast path: most cells are plain text
        return value
    if type(value) is int and (number_format is None or number_format == GENERAL):
        return str(value)
    fmt = _LOCALE_FORMATS.get(number_format or GENERAL, number_format or GENERAL)
    try:
        if isinstance(value, (datetime.datetime, datetime.date, datetime.time)):
            if is_date_format(fmt):
                return _date_text(value, fmt)
        elif isinstance(value, (int, float)) and not isinstance(value, bool):
            if is_number_format(fmt):
                text = _number_text(value, fmt)
                if text is not None:
                    return text.strip()  # drop alignment padding from _) etc.
    except (ValueError, OverflowError, IndexError):
        pass
    return _general(value)


_NUMBER_STRIP_RE = re.compile(r'[\s,$€£¥]')


def parse_number(text):
    """'$1,250.00' -> 1250.0, '(5)' -> -5, '12%' -> 0.12; None if not a number"""
    t = text.strip()
    negative = False
    if t.startswith('(') and t.endswith(')'):
        negative, t = True, t[1:-1]
    percent = t.endswith('%')
    if percent:
        t = t[:-1]
    t = _NUMBER_STRIP_RE.sub('', t)
    if t.startswith('-'):
        negative, t = not negative, t[1:]
    if not re.fullmatch(r'(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?', t):
        return None
    if '.' in t or 'e' in t.lower() or percent:
        value = float(t) / (100 if percent else 1)
    else:
        value = int(t)
    return -value if negative else value


def parse_date(text, number_format=GENERAL):
    """Parse edited text using the cell's date format, then ISO; None if neither"""
    t = text.strip()
    fmt = _LOCALE_FORMATS.get(number_format or GENERAL, number_format or GENERAL)
    pattern = _date_parse_pattern(fmt) if is_date_format(fmt) else None
    if pattern:
        try:
            return datetime.datetime.strptime(t, pattern)
        except ValueError:
            pass
    try:
        return datetime.datetime.fromisoformat(t)
    except ValueError:
        return None
