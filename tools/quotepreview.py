"""Render quote images locally, without a bot token or a Discord connection.

    python tools/quotepreview.py                     # the built-in sample set
    python tools/quotepreview.py --text "**hi** *there*"
    python tools/quotepreview.py --only styles --out /tmp/q

Exists so markdown rendering (italics, bold, strikethrough, code, spoilers)
can be eyeballed after a change to quoteimage.py.
"""
import argparse
import asyncio
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image, ImageDraw

import quoteimage

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# A markdown torture test: every delimiter, the shapes that used to clip
# (leading italic glyphs, descenders under a rule or a code box), the parser's
# edge cases, and enough text to exercise the auto-shrink and the word splitter.
SAMPLES = {
    "styles": "*italic* **bold** ***both*** ~~strike~~ __underline__ `code` ||spoiler||",
    "italic": "*fluffy jiggly pyjamas, glowing quietly*",
    "descenders": "__ggyypqj__ ~~ggyypqj~~ `ggyypqj`",
    "edges": "un**bel**ievable snake_case_name **unmatched *a*",
    "intraword": "un**bel**ievable ~~super~~cali*fragilistic*expiali`docious`",
    "multiline": "first line\nsecond line\n\nafter a blank line\n\n\n\nand a **capped** run of them",
    "codeblock": "look at this:\n```python\nprint('hello')\n```",
    "spoiler": "the twist is ||he was the killer|| all along",
    "long": "**this is a much longer quote** that should *shrink the font* down a fair bit and also wrap across ~~several~~ many lines while keeping every `styled` run inside the text column",
    "wrap": "*aaaaaaaa bbbbbbbb cccccccc dddddddd eeeeeeee ffffffff gggggggg*",
    "longword": "**MEMEMEMEMEMEMEMEMEMEMEMEMEMEMEMEMEMEMEMEMEMEMEMEMEMEMEMEMEMEMEME**",
    "mixed": "*hello* **こんにちは** ~~привет~~",
}

def placeholderAvatar(size=300):
    """Repo icon if it's there, otherwise a flat disc - only the pixels matter."""
    icon = os.path.join(REPO_ROOT, "siteresources", "icon.png")
    if os.path.exists(icon):
        return open(icon, "rb").read()
    img = Image.new("RGB", (size, size), (60, 60, 70))
    ImageDraw.Draw(img).ellipse([20, 20, size - 20, size - 20], fill=(120, 120, 140))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

async def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--text", help="render this one string instead of the sample set")
    ap.add_argument("--only", action="append", help="render only these samples (repeatable); default is all of them")
    ap.add_argument("--out", default="quotepreview", help="output directory (default: ./quotepreview)")
    ap.add_argument("--font", default=None, help="body font path (default: whatever quoteimage resolves for this OS)")
    ap.add_argument("--avatar", default=None, help="avatar image path; the spotlight is tinted with its main color")
    ap.add_argument("--name", default="Test User")
    ap.add_argument("--username", default="testuser")
    ap.add_argument("--max-chars", type=int, default=400, help="truncation limit; the bot itself uses 200")
    args = ap.parse_args()

    font_path = args.font or quoteimage.resolveFontPath()
    if not os.path.exists(font_path):
        print(f"warning: {font_path} does not exist; text will fall back and may look wrong", file=sys.stderr)

    samples = {"custom": args.text} if args.text else SAMPLES
    if args.only:
        missing = [k for k in args.only if k not in samples]
        if missing:
            ap.error(f"unknown sample(s): {', '.join(missing)}; available: {', '.join(samples)}")
        samples = {k: samples[k] for k in args.only}

    os.makedirs(args.out, exist_ok=True)
    avatar_bytes = open(args.avatar, "rb").read() if args.avatar else placeholderAvatar()
    print(f"font: {font_path}")
    print(f"spotlight: {quoteimage.dominantColor(Image.open(io.BytesIO(avatar_bytes)))}")
    for name, text in samples.items():
        png_bytes, had_spoiler = await quoteimage.renderQuoteImage(
            content_text=text,
            author_display_name=args.name,
            author_username=args.username,
            avatar_bytes=avatar_bytes,
            font_path=font_path,
            max_chars=args.max_chars,
        )
        path = os.path.join(args.out, f"{name}.png")
        with open(path, "wb") as f:
            f.write(png_bytes)
        print(f"  {path}  ({len(png_bytes)} bytes, spoiler={had_spoiler})")

if __name__ == "__main__":
    asyncio.run(main())
