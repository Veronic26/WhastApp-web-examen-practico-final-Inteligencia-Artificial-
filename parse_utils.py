import re
import pandas as pd

PATTERNS = [
    r'^(\d{1,2}/\d{1,2}/\d{4}), (\d{1,2}:\d{2}\s*[ap]\.\s*m\.) - (.*?): (.*)$',
    r'^(\d{1,2}/\d{1,2}/\d{4}) (\d{1,2}:\d{2}\s*[ap]\.\s*m\.) - (.*?): (.*)$',
    r'^(\d{1,2}/\d{1,2}/\d{4}), (\d{1,2}:\d{2}) - (.*?): (.*)$',
]

def _clean_time(t):
    return t.replace('\u202f', '').replace('\xa0', '').strip()

def parse_line(line):
    for pat in PATTERNS:
        m = re.match(pat, line, re.IGNORECASE)
        if m:
            date = m.group(1)
            time = _clean_time(m.group(2))
            author = m.group(3)
            message = m.group(4)
            return date, time, author, message
    return None, None, None, None

def _convert_time_to_24h(t):
    # t examples: '6:49 p. m.' or '18:49' or '6:49 p.m.'
    if not isinstance(t, str):
        return t
    s = t.replace(' ', '').lower()
    am = 'a.' in s
    pm = 'p.' in s
    m = re.match(r'(\d{1,2}):(\d{2})', s)
    if not m:
        return t
    hh = int(m.group(1))
    mm = int(m.group(2))
    if pm and hh != 12:
        hh = hh + 12
    if am and hh == 12:
        hh = 0
    return f'{hh:02d}:{mm:02d}'

def read_chat_from_path(path):
    data = []
    with open(path, encoding='utf-8') as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            d, t, a, m = parse_line(line)
            if d is not None:
                data.append([d, t, a, m])
            else:
                if data:
                    data[-1][3] += '\n' + line
    df = pd.DataFrame(data, columns=['Date', 'Time', 'Author', 'Message'])

    def make_datetime(row):
        date_str = row['Date']
        time_str = row['Time']
        try:
            t24 = _convert_time_to_24h(time_str)
            dt = pd.to_datetime(f'{date_str} {t24}', dayfirst=True, errors='coerce')
            if pd.isna(dt):
                dt = pd.to_datetime(f'{date_str} {time_str}', dayfirst=True, errors='coerce')
            return dt
        except Exception:
            return pd.NaT

    df['datetime'] = df.apply(make_datetime, axis=1)
    df['date_only'] = df['datetime'].dt.date
    df['year'] = df['datetime'].dt.year
    df['month'] = df['datetime'].dt.month_name()
    df['hour'] = df['datetime'].dt.hour
    df['weekday'] = df['datetime'].dt.day_name()

    def is_media(msg):
        if not isinstance(msg, str):
            return False
        msg_lower = msg.lower()
        if '<multimedia' in msg_lower or '<media' in msg_lower or 'omitted' in msg_lower or 'archivo adjunto' in msg_lower or 'image omitted' in msg_lower:
            return True
        return False

    df['is_media'] = df['Message'].apply(is_media)
    return df

# extract emojis using unicode ranges
EMOJI_PATTERN = re.compile(
    r'['
    r'\U0001F600-\U0001F64F'  # emoticons
    r'\U0001F300-\U0001F5FF'  # symbols & pictographs
    r'\U0001F680-\U0001F6FF'  # transport & map
    r'\U0001F1E0-\U0001F1FF'  # flags
    r'\U00002700-\U000027BF'  # dingbats
    r'\U0001F900-\U0001F9FF'  # supplemental symbols and pictographs
    r']+', flags=re.UNICODE
)

def extract_emojis_from_text(text):
    if not isinstance(text, str):
        return []
    return EMOJI_PATTERN.findall(text)

def get_emoji_counts(series):
    from collections import Counter
    c = Counter()
    for msg in series.dropna():
        emojis = extract_emojis_from_text(msg)
        for e in emojis:
            e_clean = re.sub('[\U0001F3FB-\U0001F3FF]', '', e)
            c[e_clean] += 1
    return c
