"""
Quote image generator.

No discord.py dependency on purpose: takes plain strings/bytes in, hands a
PNG back out. Callers (cogs/quote.py) do the discord-specific work of
resolving mentions/avatars before calling in here.
"""
import os
import re
import io
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import emoji as emojilib
from fontTools.ttLib import TTFont, TTLibFileIsCollectionError

CUSTOM_EMOJI_RE = re.compile(r"<(a?):(\w+):(\d+)>")

MARKDOWN_DELIMS = [
    ("```", frozenset({"code"})),
    ("***", frozenset({"bold", "italic"})),
    ("~~", frozenset({"strike"})),
    ("**", frozenset({"bold"})),
    ("__", frozenset({"underline"})),
    ("||", frozenset({"spoiler"})),
    ("`", frozenset({"code"})),
    ("*", frozenset({"italic"})),
    ("_", frozenset({"italic"})),
]
CODE_FENCE_LANG_RE = re.compile(r"[A-Za-z0-9_+-]*\n")

FALLBACK_FONT_PATHS = [
    r"C:\Windows\Fonts\seguisym.ttf",  # Segoe UI Symbol: broad symbol/script coverage
    "/System/Library/Fonts/Apple Symbols.ttf",  # macOS equivalent: broad symbol/script coverage
    r"C:\Windows\Fonts\msyh.ttc",      # Microsoft YaHei: Chinese
    "/System/Library/Fonts/STHeiti Medium.ttc",  # macOS equivalent: Chinese
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",  # Linux equivalent (WenQuanYi Zen Hei): CJK
    r"C:\Windows\Fonts\malgun.ttf",    # Malgun Gothic: Korean
    "/System/Library/Fonts/AppleSDGothicNeo.ttc",  # macOS equivalent: Korean
    r"C:\Windows\Fonts\meiryo.ttc",    # Meiryo: Japanese
    "/System/Library/Fonts/ヒラギノ角ゴシック W4.ttc",  # macOS equivalent (Hiragino Kaku Gothic): Japanese
    r"C:\Windows\Fonts\arial.ttf",     # Arial: broad Latin/Cyrillic/Greek fallback
    "/System/Library/Fonts/Supplemental/Arial.ttf",  # macOS equivalent: broad Latin/Cyrillic/Greek fallback
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",  # Linux equivalent (metric-compatible with Arial)
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux: very broad Latin/Cyrillic/Greek/symbol coverage
    "/usr/share/fonts/truetype/freefont/FreeSans.ttf",  # Linux: last-ditch, ships with most distros
]

# Body font for the quote itself. Same ordering idea as above: the first one
# actually installed wins, so one code path renders on Windows, macOS and Linux
# instead of silently collapsing to PIL's tiny bitmap default.
PRIMARY_FONT_PATHS = [
    r"C:\Windows\Fonts\arial.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
]

# How families name their bold/italic/bold-italic faces relative to the regular
# one. Tried in order against the regular font's own directory: "arial.ttf" ->
# "arialbd.ttf", "DejaVuSans.ttf" -> "DejaVuSans-Bold.ttf", "FreeSans.ttf" ->
# "FreeSansOblique.ttf", and so on.
FONT_STYLE_SUFFIXES = {
    (True, False): ["bd", "b", "-Bold", "Bold", " Bold"],
    (False, True): ["i", "-Italic", "-Oblique", "Italic", "Oblique", " Italic", " Oblique"],
    (True, True): ["bi", "z", "-BoldItalic", "-BoldOblique", "BoldItalic", "BoldOblique", " Bold Italic", " Bold Oblique"],
}
# Families that spell the regular face out ("LiberationSans-Regular.ttf") swap
# that token instead of appending to it.
FONT_REGULAR_TOKENS = ["-Regular", " Regular", "Regular"]
FONT_STYLE_REPLACEMENTS = {
    (True, False): ["-Bold", " Bold", "Bold"],
    (False, True): ["-Italic", "-Oblique", " Italic", " Oblique", "Italic", "Oblique"],
    (True, True): ["-BoldItalic", "-BoldOblique", " Bold Italic", " Bold Oblique", "BoldItalic", "BoldOblique"],
}

_cmap_cache = {}
_font_obj_cache = {}
_emoji_img_cache = {}
_style_path_cache = {}

def resolveFontPath():
    """First body font actually installed on this machine.

    Falls back to the Windows path so the failure mode stays the old one
    (fallback chain, then tofu) rather than a crash on a bare container.
    """
    return next((p for p in PRIMARY_FONT_PATHS if os.path.exists(p)), PRIMARY_FONT_PATHS[0])

def fontHasGlyph(path, ch):
    if ch.isspace():
        return os.path.exists(path)  # trust space is in-cmap for any font that actually loads; avoids stranding it on a dead primary_path
    if path not in _cmap_cache:
        try:
            try:
                ttf = TTFont(path, lazy=True)
            except TTLibFileIsCollectionError:
                # .ttc collections need an explicit face index or fontTools refuses
                # to open them; index 0 is the one ImageFont.truetype loads too.
                # Every CJK fallback below is a .ttc, so without this they all
                # report "no glyph" and Chinese/Japanese renders as tofu.
                ttf = TTFont(path, lazy=True, fontNumber=0)
            cmap = ttf.getBestCmap() or {}
            ttf.close()
            _cmap_cache[path] = cmap
        except Exception:
            return False  # don't cache the failure; retry next time in case it was transient
    return ord(ch) in _cmap_cache[path]

def choosePathForChar(ch, primary_path):
    if fontHasGlyph(primary_path, ch):
        return primary_path
    for fp in FALLBACK_FONT_PATHS:
        if os.path.exists(fp) and fontHasGlyph(fp, ch):
            return fp
    return primary_path  # last resort: may render as tofu, better than crashing

def getFontObj(path, size):
    key = (path, size)
    if key not in _font_obj_cache:
        try:
            _font_obj_cache[key] = ImageFont.truetype(path, size)
        except Exception:
            # don't cache the failure; retry next time in case it was transient.
            # ask load_default for the size so we get a scalable face with real
            # metrics - the bare bitmap default has no .size/.getmetrics(), which
            # the styled-run drawing below relies on.
            try:
                return ImageFont.load_default(size)
            except Exception:
                return ImageFont.load_default()
    return _font_obj_cache[key]

def styledFontPath(regular_path, style):
    """Path to the real bold/italic face beside regular_path, or None.

    Faking bold with an outline stroke and italic with a shear is a last resort;
    nearly every family ships the real faces next to the regular one under a
    predictable name, and the real ones look far better.
    """
    want = ("bold" in style, "italic" in style)
    if not any(want):
        return None
    key = (regular_path, want)
    if key not in _style_path_cache:
        stem, ext = os.path.splitext(regular_path)
        candidates = [stem + suffix + ext for suffix in FONT_STYLE_SUFFIXES[want]]
        for token in FONT_REGULAR_TOKENS:
            if stem.endswith(token):
                base = stem[: -len(token)]
                candidates = [base + rep + ext for rep in FONT_STYLE_REPLACEMENTS[want]] + candidates
                break
        _style_path_cache[key] = next((c for c in candidates if os.path.exists(c)), None)
    return _style_path_cache[key]

def fontMetrics(font):
    # (ascent, descent) below/above the line top. font.size is the nominal em and
    # is smaller than ascent+descent for most faces, so decorations placed off it
    # land inside the glyphs instead of around them.
    try:
        return font.getmetrics()
    except Exception:
        size = getattr(font, "size", 16)
        return int(size * 0.8), int(size * 0.2)

def buildRuns(word, size, primary_path, style=frozenset()):
    # split a word into (text, font, style) runs so mixed-script words each render
    # with a font that has the glyphs. A run that resolved to a real bold/italic
    # face drops those flags, so drawStyledRun doesn't fake them on top of a face
    # that already has them.
    runs = []
    cur_key, cur_text = None, ""
    for ch in word:
        base = choosePathForChar(ch, primary_path)
        styled = styledFontPath(base, style)
        key = (styled, style - {"bold", "italic"}) if styled and fontHasGlyph(styled, ch) else (base, style)
        if key == cur_key:
            cur_text += ch
        else:
            if cur_text:
                runs.append((cur_text, getFontObj(cur_key[0], size), cur_key[1]))
            cur_key, cur_text = key, ch
    if cur_text:
        runs.append((cur_text, getFontObj(cur_key[0], size), cur_key[1]))
    return runs

def buildSegmentRuns(segments, size, primary_path):
    # a word's (text, style) pieces flattened into one list of drawable runs
    return [run for text, style in segments for run in buildRuns(text, size, primary_path, style)]

def parseDiscordMarkdown(text):
    """Strip Discord markdown delimiters, returning (plain_text, style_ranges).

    style_ranges is a list of (start, end, frozenset_of_styles) covering
    plain_text contiguously. A delimiter only opens a run if its matching
    close exists later in the string; otherwise it's kept as a literal
    character, same fallback Discord itself uses for malformed markdown.
    """
    n = len(text)
    i = 0
    pos = 0
    plain = []
    ranges = []
    stack = []  # (delim, style)
    cur_buf = []

    def active_style():
        style = frozenset()
        for _, st in stack:
            style |= st
        return style

    def flush_buf():
        nonlocal pos
        if cur_buf:
            piece = "".join(cur_buf)
            plain.append(piece)
            ranges.append((pos, pos + len(piece), active_style()))
            pos += len(piece)
            cur_buf.clear()

    while i < n:
        if stack and stack[-1][0] in ("`", "```"):
            # inside a code span/fence: markdown is not parsed here, only the
            # matching close is recognized (mirrors Discord's own behavior)
            delim = stack[-1][0]
            if text.startswith(delim, i):
                flush_buf()
                stack.pop()
                i += len(delim)
            else:
                cur_buf.append(text[i])
                i += 1
            continue

        matched = None
        for delim, style in MARKDOWN_DELIMS:
            if text.startswith(delim, i):
                matched = (delim, style)
                break
        if matched is None:
            cur_buf.append(text[i])
            i += 1
            continue
        delim, style = matched
        if all(c == "_" for c in delim):
            # underscores don't open/close emphasis mid-word (snake_case,
            # custom emoji names like <:some_emoji:123>), unlike "*"
            before = text[i - 1] if i > 0 else ""
            after = text[i + len(delim)] if i + len(delim) < n else ""
            is_word_char = lambda c: c.isalnum() or c == "_"
            if is_word_char(before) and is_word_char(after):
                cur_buf.append(text[i])
                i += 1
                continue
        if stack and stack[-1][0] == delim:
            flush_buf()
            stack.pop()
            i += len(delim)
            continue
        if text.find(delim, i + len(delim)) == -1:
            cur_buf.append(text[i])
            i += 1
            continue
        flush_buf()
        stack.append((delim, style))
        i += len(delim)
        if delim == "```":
            m = CODE_FENCE_LANG_RE.match(text, i)
            if m:
                i = m.end()
    flush_buf()
    return "".join(plain), ranges

def styleFor(style_ranges, span_start, span_end):
    # for spans that can only carry one style (an emoji): whichever style covers
    # most of it, rather than just the first character's
    best_style, best_overlap = frozenset(), 0
    for start, end, style in style_ranges:
        overlap = min(end, span_end) - max(start, span_start)
        if overlap > best_overlap:
            best_overlap, best_style = overlap, style
    return best_style

def styleSegments(style_ranges, span_start, span_end):
    """Cut [span_start, span_end) into (start, end, style) pieces.

    Markdown can open and close inside a word when it touches text with no
    surrounding space ("un**bel**ievable"), so a word is not one style - it is
    a sequence of them. style_ranges covers the text contiguously, so the
    pieces come out ordered and gapless; neighbours sharing a style are merged
    to keep the run count down.
    """
    pieces = []
    for start, end, style in style_ranges:
        lo, hi = max(start, span_start), min(end, span_end)
        if lo >= hi:
            continue
        if pieces and pieces[-1][2] == style and pieces[-1][1] == lo:
            pieces[-1] = (pieces[-1][0], hi, style)
        else:
            pieces.append((lo, hi, style))
    return pieces or [(span_start, span_end, frozenset())]

def findEmojiSpans(text):
    spans = [(m.start(), m.end(), "custom", {"animated": bool(m.group(1)), "name": m.group(2), "id": m.group(3)}) for m in CUSTOM_EMOJI_RE.finditer(text)]
    spans += [(e["match_start"], e["match_end"], "unicode", {"char": e["emoji"]}) for e in emojilib.emoji_list(text)]
    spans.sort(key=lambda s: s[0])
    filtered, last_end = [], 0
    for s in spans:
        if s[0] >= last_end:
            filtered.append(s)
            last_end = s[1]
    return filtered

def safeTruncate(text, max_chars):
    if len(text) <= max_chars:
        return text, 0
    cut = max_chars
    for start, end, _, _ in findEmojiSpans(text):
        if start < cut < end:
            cut = start
    return text[:cut], len(text) - cut

def tokenizeContent(text):
    plain_text, style_ranges = parseDiscordMarkdown(text)
    spans = findEmojiSpans(plain_text)
    tokens, pos = [], 0
    for start, end, kind, data in spans:
        if start > pos:
            tokens.append(("text", plain_text[pos:start], pos, start))
        tokens.append((kind, data, start, end))
        pos = end
    if pos < len(plain_text):
        tokens.append(("text", plain_text[pos:], pos, len(plain_text)))
    atoms = []
    for kind, data, start_pos, end_pos in tokens:
        if kind == "text":
            # "\n" first so newlines survive as their own atoms; \S+ can't span
            # one anyway, it just used to get dropped along with the other
            # whitespace, running every paragraph together into one blob
            for m in re.finditer(r"\n|\S+", data):
                if m.group(0) == "\n":
                    atoms.append(("break", None, frozenset()))
                    continue
                lo, hi = start_pos + m.start(), start_pos + m.end()
                segments = [(plain_text[a:b], st) for a, b, st in styleSegments(style_ranges, lo, hi)]
                union = frozenset().union(*(st for _, st in segments))
                atoms.append(("word", segments, union))
        else:
            atoms.append((kind, data, styleFor(style_ranges, start_pos, end_pos)))
    return trimBreaks(atoms)

def trimBreaks(atoms, max_run=2):
    """Drop leading/trailing blank lines and cap runs of them.

    A message padded with newlines would otherwise shrink the card's font to the
    floor to make room for empty lines. max_run=2 leaves at most one blank line
    between paragraphs, which is what the spacing is for.
    """
    trimmed, run = [], 0
    for atom in atoms:
        if atom[0] == "break":
            run += 1
            if run > max_run or not trimmed:
                continue  # over the cap, or still before any content
        else:
            run = 0
        trimmed.append(atom)
    while trimmed and trimmed[-1][0] == "break":
        trimmed.pop()
    return trimmed

BOLD_STROKE = 1
ITALIC_SHEAR = 0.22
SHEAR_PAD = 2  # slack on the scratch layer for ink straying past the metric box
CODE_BG = (40, 40, 40)
CODE_FG = (255, 200, 120)
SPOILER_BG = (28, 28, 33)
SPOILER_FG = (145, 145, 155)

def italicShift(font):
    # Horizontal room the fake italic needs on top of the upright width. Keyed to
    # the font rather than the text so runWidth and drawStyledRun always agree -
    # if they disagree, runs overlap and lines overflow the text column.
    ascent, descent = fontMetrics(font)
    return int((ascent + descent) * ITALIC_SHEAR)

def runWidth(draw, text, font, style):
    stroke_w = BOLD_STROKE if "bold" in style else 0
    w = draw.textbbox((0, 0), text, font=font, stroke_width=stroke_w)[2] + stroke_w
    if "italic" in style:
        w += italicShift(font)
    return w

def drawStyledRun(img, draw, x, y, text, font, color, style):
    """Draw one (text, font) run with Discord-style emphasis, return width consumed.

    "bold"/"italic" only reach here when the family had no real face for them
    (buildRuns strips the flags when it found one). Bold is then faked with an
    outline stroke, italic by shearing the glyphs on a scratch RGBA layer, since
    PIL has no native oblique transform.

    Underline/strike/backgrounds are placed off the font's real ascent and
    descent, not font.size: font.size is the nominal em, which is smaller than
    the glyph box for most faces, so a rule at y + font.size cuts through the
    descenders instead of clearing them.
    """
    ascent, descent = fontMetrics(font)
    stroke_w = BOLD_STROKE if "bold" in style else 0
    fill = CODE_FG if "code" in style else (SPOILER_FG if "spoiler" in style else color)
    bbox = draw.textbbox((0, 0), text, font=font, stroke_width=stroke_w)
    plain_w = bbox[2] + stroke_w  # the stroke also bleeds left of x, so draw it shifted in by stroke_w
    shift = italicShift(font) if "italic" in style else 0
    consumed_w = plain_w + shift

    bg = CODE_BG if "code" in style else (SPOILER_BG if "spoiler" in style else None)
    if bg is not None:
        draw.rectangle([x - 4, y - 2, x + consumed_w + 4, y + ascent + descent + 2], fill=bg)

    if shift:
        tmp_w, tmp_h = plain_w + shift + 2 * SHEAR_PAD, ascent + descent + 2 * SHEAR_PAD
        tmp = Image.new("RGBA", (tmp_w, tmp_h), (0, 0, 0, 0))
        ImageDraw.Draw(tmp).text((SHEAR_PAD + stroke_w, SHEAR_PAD), text, font=font, fill=fill, stroke_width=stroke_w, stroke_fill=fill)
        # The -shift translation is what keeps the glyphs whole. transform() reads
        # output (x, y) from input (x + ITALIC_SHEAR*y + c): with c = 0 the lower
        # rows sample from x < 0 and the bottom-left of the run is shaved clean
        # off, while the extra `shift` columns on the right stay empty. c = -shift
        # slides the whole lean right by one full step, so the baseline row lands
        # back on x = 0 and the tops occupy the added columns.
        sheared = tmp.transform((tmp_w, tmp_h), Image.AFFINE, (1, ITALIC_SHEAR, -shift, 0, 1, 0), resample=Image.BICUBIC)
        img.paste(sheared, (x - SHEAR_PAD, y - SHEAR_PAD), sheared)
    else:
        draw.text((x + stroke_w, y), text, font=font, fill=fill, stroke_width=stroke_w, stroke_fill=fill)

    line_w = max(1, (ascent + descent) // 20)
    # rules span the upright extent: a sheared run's top overhangs to the right,
    # but its baseline - where the rules live - does not
    rule_w = plain_w
    if "underline" in style:
        # below the descender line, not through it: descenders reach exactly
        # ascent + descent, so anything shorter bisects every g/y/p/q/j. The
        # line box (see lineMetrics) always leaves room for this.
        ly = y + ascent + descent + line_w
        draw.line([(x, ly), (x + rule_w, ly)], fill=fill, width=line_w)
    if "strike" in style:
        _, x_top, _, x_bottom = font.getbbox("x")
        # middle of the x-height, however tall this face runs it; a font with no
        # "x" at all (symbol/CJK-only) reports an empty box, so estimate instead
        ly = y + ((x_top + x_bottom) // 2 if x_bottom > x_top else int(ascent * 0.7))
        draw.line([(x, ly), (x + rule_w, ly)], fill=fill, width=line_w)
    return consumed_w

SPOTLIGHT_SAMPLE = 96      # avatar is downsampled to this before quantizing
SPOTLIGHT_PALETTE = 16     # representative colors median-cut reduces it to
SPOTLIGHT_MIN_CHROMA = 0.10  # below this the avatar is effectively greyscale
SPOTLIGHT_MIN_VALUE = 180  # lift dark colors so the spotlight still reads on black
SPOTLIGHT_FALLBACK = (255, 255, 255)  # for avatars with no color worth picking

def dominantColor(img, fallback=SPOTLIGHT_FALLBACK):
    """The avatar's main color, for the spotlight behind it.

    Averaging the pixels gives mud, and the most *populous* color is usually a
    flat background (white, black, grey), so the image is median-cut down to a
    handful of representative colors and those are scored by pixel count
    weighted by chroma - a small vivid area beats a large drab one. Only the
    circular crop the card actually shows is sampled.

    Chroma (hi - lo) rather than HSV saturation ((hi - lo) / hi), because
    saturation is meaningless down near black: pure black with one channel a
    single step up scores a perfect 1.0 and would win on any dark avatar.

    Near-greyscale avatars score nothing and return the fallback - plain white,
    which the gradient's own falloff carries fine. The winner is
    scaled up to SPOTLIGHT_MIN_VALUE if it's dark; scaling RGB uniformly moves
    only the brightness, leaving hue and saturation intact.
    """
    try:
        small = img.convert("RGBA").resize((SPOTLIGHT_SAMPLE, SPOTLIGHT_SAMPLE), Image.LANCZOS)
        px = small.load()
        radius = SPOTLIGHT_SAMPLE / 2
        pixels = []
        for y in range(SPOTLIGHT_SAMPLE):
            for x in range(SPOTLIGHT_SAMPLE):
                if (x - radius + 0.5) ** 2 + (y - radius + 0.5) ** 2 > radius ** 2:
                    continue  # outside the circular mask, never visible on the card
                r, g, b, a = px[x, y]
                if a > 128:
                    pixels.append((r, g, b))
        if not pixels:
            return fallback

        flat = Image.new("RGB", (len(pixels), 1))
        flat.putdata(pixels)
        quantized = flat.quantize(colors=SPOTLIGHT_PALETTE, method=Image.MEDIANCUT)
        palette = quantized.getpalette()

        best, best_score = fallback, 0.0
        for count, index in quantized.getcolors(SPOTLIGHT_PALETTE) or []:
            color = tuple(palette[index * 3: index * 3 + 3])
            chroma = (max(color) - min(color)) / 255
            score = count * chroma
            if chroma >= SPOTLIGHT_MIN_CHROMA and score > best_score:
                best, best_score = color, score
        if best_score == 0.0:
            return fallback

        hi = max(best)
        if hi < SPOTLIGHT_MIN_VALUE:
            best = tuple(min(255, round(c * SPOTLIGHT_MIN_VALUE / hi)) for c in best)
        return best
    except Exception:
        return fallback  # a spotlight in the wrong color beats no card at all

async def fetchEmojiImage(session, kind, data, size):
    cache_key = (kind, data.get("id") or data.get("char"))
    if cache_key not in _emoji_img_cache:
        raw_img = None
        try:
            if kind == "custom":
                ext = "gif" if data["animated"] else "png"
                async with session.get(f"https://cdn.discordapp.com/emojis/{data['id']}.{ext}") as resp:
                    if resp.status == 200:
                        raw_img = Image.open(io.BytesIO(await resp.read()))
                        raw_img.seek(0)  # first frame if animated
                        raw_img = raw_img.convert("RGBA")
            else:
                codepoints_variants = {
                    "-".join(f"{ord(c):x}" for c in data["char"] if ord(c) != 0xFE0F),
                    "-".join(f"{ord(c):x}" for c in data["char"]),
                }
                for cps in codepoints_variants:
                    async with session.get(f"https://cdn.jsdelivr.net/gh/jdecked/twemoji@latest/assets/72x72/{cps}.png") as resp:
                        if resp.status == 200:
                            raw_img = Image.open(io.BytesIO(await resp.read())).convert("RGBA")
                            break
        except Exception:
            raw_img = None
        _emoji_img_cache[cache_key] = raw_img
    raw_img = _emoji_img_cache[cache_key]
    return raw_img.resize((size, size), Image.LANCZOS) if raw_img else None

async def renderQuoteImage(
    content_text,
    author_display_name,
    author_username,
    avatar_bytes,
    font_path,
    max_chars=200,
    watermark_text="etanbot // coded by etangaming123",
    emoji_session=None,
):
    """Render a quote card, returning (png_bytes, had_spoiler).

    The spotlight behind the avatar is tinted with the avatar's own main color.

    had_spoiler says whether any of the text that actually made it onto the
    card was marked ||spoiler||, so the caller can flag the attachment as a
    spoiler too - the image shows the text dimmed rather than hiding it.

    All inputs are plain Python types (strings/bytes), no discord.py objects,
    so this can be called from a bare asyncio script for testing.
    """
    W, H = 1200, 630

    avatar_img = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")

    # Black background
    img = Image.new('RGB', (W, H), (0, 0, 0))

    # Radial spotlight gradient, tinted with the avatar's own main color
    spotlight_color = dominantColor(avatar_img)
    y_coords, x_coords = np.mgrid[0:H, 0:W]
    cx, cy = W // 4, H // 2
    max_r = H * 0.78
    dist = np.sqrt((x_coords - cx) ** 2 + (y_coords - cy) ** 2)
    brightness = np.clip(1.0 - dist / max_r, 0, 1) ** 0.55
    brightness = (brightness * 255).astype(np.uint8)

    brightness_f = brightness.astype(np.float32)
    r = (brightness_f * spotlight_color[0] / 255).astype(np.uint8)
    g = (brightness_f * spotlight_color[1] / 255).astype(np.uint8)
    b = (brightness_f * spotlight_color[2] / 255).astype(np.uint8)
    gradient = Image.fromarray(np.stack([r, g, b], axis=2), 'RGB')
    img.paste(gradient, (0, 0), Image.fromarray(brightness))

    # Circular avatar
    av_size = 300
    avatar_img = avatar_img.resize((av_size, av_size), Image.LANCZOS)
    mask = Image.new('L', (av_size, av_size), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, av_size - 1, av_size - 1], fill=255)
    ax, ay = cx - av_size // 2, cy - av_size // 2
    img.paste(avatar_img.convert('RGB'), (ax, ay), mask)

    draw = ImageDraw.Draw(img)

    # Fixed sizes for name/username/watermark, kept independent of whether font_path
    # itself loads. drawCenteredRuns() below resolves these through buildRuns(), which
    # (like the quote body) falls back through FALLBACK_FONT_PATHS at the requested size
    # if font_path is bad - rather than silently collapsing to PIL's tiny bitmap
    # load_default() the way a bare ImageFont.truetype(font_path, size) would.
    NAME_SIZE, USERNAME_SIZE, WM_SIZE = 38, 28, 20
    font_wm = getFontObj(choosePathForChar("e", font_path), WM_SIZE)

    # Text area: right half
    tx, ty_pad = W // 2 + 30, 40
    text_w = W - tx - ty_pad

    quote_text, trimmed_chars = safeTruncate(content_text, max_chars)
    if trimmed_chars:
        quote_text += f"... [{trimmed_chars} more characters]"

    atoms = tokenizeContent(quote_text)

    # Prefetch emoji images (unicode + custom Discord emoji) once at a large size, resized per font-size trial
    emoji_images = {}
    async def prefetch(session):
        for kind, data, style in atoms:
            if kind in ("custom", "unicode"):
                key = (kind, data.get("id") or data.get("char"))
                if key not in emoji_images:
                    emoji_images[key] = await fetchEmojiImage(session, kind, data, 128)

    if emoji_session is not None:
        await prefetch(emoji_session)
    else:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            await prefetch(session)

    def elementWidth(el):
        if el[0] == "emoji":
            return el[2]
        return sum(runWidth(draw, t, f, run_style) for t, f, run_style in el[1])

    def splitLongWord(segments, font_size):
        # break an unbroken run (e.g. "MEMEMEME...") into chunks that each fit
        # text_w, so it wraps instead of overflowing past the text area. Chunks
        # are themselves (text, style) segment lists, since the styles can
        # change partway through the word being split
        chunks, cur, cur_w = [], [], 0
        for text, style in segments:
            for ch in text:
                ch_w = elementWidth(("text", buildRuns(ch, font_size, font_path, style)))
                if cur and cur_w + ch_w > text_w:
                    chunks.append(cur)
                    cur, cur_w = [], 0
                if cur and cur[-1][1] == style:
                    cur[-1] = (cur[-1][0] + ch, style)
                else:
                    cur.append((ch, style))
                cur_w += ch_w
        if cur:
            chunks.append(cur)
        return chunks

    def atomElements(kind, data, style, font_size):
        # returns [(element, needs_space_before), ...]; chunks split out of
        # one long word are glued together (no space between them)
        if kind == "word":
            el = ("text", buildSegmentRuns(data, font_size, font_path))
            if elementWidth(el) <= text_w:
                return [(el, True)]
            chunks = splitLongWord(data, font_size)
            return [(("text", buildSegmentRuns(c, font_size, font_path)), i == 0)
                    for i, c in enumerate(chunks)]
        img128 = emoji_images.get((kind, data.get("id") or data.get("char")))
        if img128 is None:
            # custom emoji has no "char" fallback glyph (deleted/CDN failure);
            # show its name instead of silently dropping the atom
            fallback_text = data.get("char") or f":{data.get('name', 'emoji')}:"
            el = ("text", buildRuns(fallback_text, font_size, font_path, style))
        else:
            el = ("emoji", img128.resize((font_size, font_size), Image.LANCZOS), font_size)
        return [(el, True)]

    def lineMetrics(font_size):
        # line box from the font's real metrics; the old font_size * 1.25 guess
        # is shorter than ascent + descent on plenty of faces, which left the
        # last line's descenders and underline running into the author name
        f = getFontObj(choosePathForChar("A", font_path), font_size)
        ascent, descent = fontMetrics(f)
        return ascent, descent, ascent + descent + max(2, font_size // 8)

    def wrapAtoms(font_size):
        space_w = draw.textbbox((0, 0), " ", font=getFontObj(choosePathForChar(" ", font_path), font_size))[2]
        lines, cur, cur_w = [], [], 0
        for kind, data, style in atoms:
            if kind == "break":
                lines.append(cur)  # may be empty: that's a deliberate blank line
                cur, cur_w = [], 0
                continue
            for el, spacer in atomElements(kind, data, style, font_size):
                w = elementWidth(el)
                add_w = w if not cur else (space_w if spacer else 0) + w
                if cur and cur_w + add_w > text_w:
                    lines.append(cur)
                    cur, cur_w = [(el, spacer)], w
                else:
                    cur.append((el, spacer))
                    cur_w += add_w
        if cur:
            lines.append(cur)
        return lines, space_w

    # Dynamically shrink font until the wrapped content fits vertically
    max_text_h = H - 80 - (NAME_SIZE + 8) - USERNAME_SIZE - 20
    font_size = 62
    while True:
        quote_lines, space_w = wrapAtoms(font_size)
        ascent, descent, lh = lineMetrics(font_size)
        if len(quote_lines) * lh <= max_text_h or font_size <= 16:
            break  # exit with quote_lines/lh from the same size, never a mix of two
        font_size -= 2

    total_q_h = len(quote_lines) * lh
    name_h = NAME_SIZE + 8
    uname_h = USERNAME_SIZE
    total_h = total_q_h + name_h + uname_h + 20
    start_y = (H - total_h) // 2

    # Quote lines (centered in text area)
    for i, line in enumerate(quote_lines):
        line_w = sum(elementWidth(el) for el, _ in line) + space_w * sum(
            1 for j, (_, spacer) in enumerate(line) if j > 0 and spacer
        )
        x = tx + (text_w - line_w) // 2
        yy = start_y + i * lh
        for j, (el, spacer) in enumerate(line):
            if j > 0 and spacer:
                x += space_w
            if el[0] == "emoji":
                emoji_img = el[1]
                img.paste(emoji_img, (x, yy + ascent - el[2]), emoji_img)  # bottom on the baseline, not floating at the line top
                x += el[2]
            else:
                for t, f, run_style in el[1]:
                    x += drawStyledRun(img, draw, x, yy, t, f, (255, 255, 255), run_style)

    y = start_y + total_q_h + 10

    def drawCenteredRuns(text, size, y_top, color):
        runs = buildRuns(text, size, font_path)
        w = sum(draw.textbbox((0, 0), t, font=f)[2] for t, f, _ in runs)
        x = tx + (text_w - w) // 2
        for t, f, _ in runs:
            draw.text((x, y_top), t, fill=color, font=f)
            x += draw.textbbox((0, 0), t, font=f)[2]

    # "- DisplayName"
    drawCenteredRuns(f"- {author_display_name}", NAME_SIZE, y, (255, 255, 255))
    y += name_h

    # "@username"
    drawCenteredRuns(f"@{author_username}", USERNAME_SIZE, y, (160, 160, 160))

    # Watermark bottom-right
    draw.text((W - 12, H - 12), watermark_text, fill=(90, 90, 90), font=font_wm, anchor="rb")

    had_spoiler = any("spoiler" in style for _, _, style in atoms)

    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    buffered.seek(0)
    return buffered.read(), had_spoiler
