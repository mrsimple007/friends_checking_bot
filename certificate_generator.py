"""
certificate_generator.py
Generates friendship certificate images by downloading a language-specific
template from Supabase and drawing dynamic text onto it with Pillow.
"""

import os
import io
import logging
import requests
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Template URLs – set these env vars or hard-code after uploading to Supabase
# ──────────────────────────────────────────────
CERT_TEMPLATE_EN = os.environ.get("CERT_TEMPLATE_EN", "")
CERT_TEMPLATE_RU = os.environ.get("CERT_TEMPLATE_RU", "")
CERT_TEMPLATE_UZ = os.environ.get("CERT_TEMPLATE_UZ", "")

TEMPLATE_URLS = {
    "en": CERT_TEMPLATE_EN,
    "ru": CERT_TEMPLATE_RU,
    "uz": CERT_TEMPLATE_UZ,
}

# ──────────────────────────────────────────────
# Friendship-level phrases (shown below the golden line, above score)
# ──────────────────────────────────────────────
FRIENDSHIP_PHRASES = {
    "uz": {
        (0,  39):  "Siz endigina tanishib kelmoqdasiz — bu do'stlikning boshlanishi! 🌱",
        (40, 59):  "Yaxshi do'stlik rivojlanmoqda. Davom eting! 🤝",
        (60, 79):  "Siz yaxshi do'stlarsiz! Bir-biringizni yaxshi bilasiz. 💛",
        (80, 94):  "Ajoyib do'stlik! Siz bir-biringizni juda yaxshi bilasiz. 🌟",
        (95, 100): "Siz haqiqiy eng yaqin do'stlarsiz! Bunday do'stlik bebaho! 💎",
    },
    "ru": {
        (0,  39):  "Вы только начинаете знакомиться — это начало дружбы! 🌱",
        (40, 59):  "Хорошая дружба развивается. Продолжайте! 🤝",
        (60, 79):  "Вы хорошие друзья! Вы хорошо знаете друг друга. 💛",
        (80, 94):  "Отличная дружба! Вы очень хорошо знаете друг друга. 🌟",
        (95, 100): "Вы настоящие лучшие друзья! Такая дружба бесценна! 💎",
    },
    "en": {
        (0,  39):  "You're just getting to know each other — friendship is beginning! 🌱",
        (40, 59):  "A good friendship is growing. Keep it up! 🤝",
        (60, 79):  "You are good friends! You know each other well. 💛",
        (80, 94):  "Amazing friendship! You know each other very well. 🌟",
        (95, 100): "You are true best friends! Such friendship is priceless! 💎",
    },
}


BOT_USERNAME = "@friend_checking_bot"


def _get_friendship_phrase(score: int, lang: str) -> str:
    phrases = FRIENDSHIP_PHRASES.get(lang, FRIENDSHIP_PHRASES["en"])
    for (lo, hi), phrase in phrases.items():
        if lo <= score <= hi:
            return phrase
    return ""


def _load_font(size: int, bold: bool = False):
    """Try to load a Unicode-capable font; fall back to Pillow default."""
    font_paths = [
        # Linux common paths
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf" if bold else
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        # macOS
        "/System/Library/Fonts/Helvetica.ttc",
        # Windows
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _download_template(url: str) -> Image.Image | None:
    """Download template image from URL and return PIL Image."""
    if not url:
        return None
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        return Image.open(io.BytesIO(resp.content)).convert("RGBA")
    except Exception as e:
        logger.error(f"Failed to download certificate template from {url}: {e}")
        return None


def _wrap_text(text: str, font, max_width: int, draw: ImageDraw.Draw) -> list[str]:
    """Wrap text to fit within max_width pixels."""
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = (current + " " + word).strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines

def generate_certificate_image(
    taker_name: str,
    owner_name: str,
    score: int,
    lang: str = "en",
) -> bytes | None:
    """
    Generate a certificate PNG in memory and return raw bytes.

    Template layout (2000×1414 px, percentages of height):
      57%        — gold divider line
      58–68%     — NAMES ZONE  (taker / & / owner, all centered)
      68–71%     — "Natija/daraja" italic label + gold underline  (pre-printed)
      72–77%     — SCORE VALUE
      79–82%     — "Quiz egasi" italic label  (pre-printed)
      82–85%     — gold underlines
      83–86%     — OWNER VALUE  (overlaps thin gold lines — intentional)
      86–88%     — "Bot" italic label  (pre-printed)
      89%        — gold underline
      90%+       — BOT VALUE
    """
    lang = lang if lang in TEMPLATE_URLS else "en"

    # ── 1. Load template ──────────────────────────────────────────────────
    img = _download_template(TEMPLATE_URLS[lang])
    if img is None:
        img = Image.new("RGBA", (2000, 1414), (255, 255, 255, 255))
        logger.warning("No certificate template found; using blank canvas.")

    W, H = img.size
    draw = ImageDraw.Draw(img)

    # ── 2. Fonts ───────────────────────────────────────────────────────────
    font_taker       = _load_font(52, bold=True)   # taker name  (centered)
    font_amp         = _load_font(30)              # "&"          (centered)
    font_owner_title = _load_font(38, bold=True)   # owner name  (centered, "Taqdim" section)
    font_score       = _load_font(60, bold=True)   # score value (left column)
    font_owner_val   = _load_font(34, bold=True)   # owner value (left column)
    font_bot         = _load_font(36, bold=True)   # bot value   (left column)
    font_phrase      = _load_font(23)              # friendship phrase (right side)

    # ── 3. Colours ────────────────────────────────────────────────────────
    COLOR_DARK   = (40,  25,   5, 255)
    COLOR_GOLD   = (170, 120,  20, 255)
    COLOR_PHRASE = (80,  60,  20, 255)

    # ── 4. Helpers ────────────────────────────────────────────────────────
    def draw_centered(text, font, y, color=COLOR_DARK):
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        draw.text(((W - tw) // 2, y), text, font=font, fill=color)

    def wrap_text(text, font, max_width):
        words = text.split()
        lines, cur = [], ""
        for w in words:
            test = (cur + " " + w).strip()
            if draw.textbbox((0, 0), test, font=font)[2] <= max_width:
                cur = test
            else:
                if cur:
                    lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        return lines

    def truncate(text, font, max_width):
        """Truncate text with '…' to fit within max_width pixels."""
        if draw.textbbox((0, 0), text, font=font)[2] <= max_width:
            return text
        while len(text) > 4:
            text = text[:-4] + "..."
            if draw.textbbox((0, 0), text, font=font)[2] <= max_width:
                break
        return text

    # ── 5. NAMES SECTION (58–68%) ─────────────────────────────────────────
    # Gold divider is at y ≈ 57% (y=805 on 2000×1414).
    # "Natija/daraja" italic starts at y ≈ 68% (y=965).
    # Fit: taker (50 px) + gap + "&" (28 px) + gap + owner (36 px) ≈ 130 px < 160 px available.

    GOLD_LINE_Y = int(H * 0.570)           # ~57% — measured gold divider top

    th_taker = draw.textbbox((0, 0), "Ay", font=font_taker)[3]        # ≈ 50 px
    th_amp   = draw.textbbox((0, 0), "&",  font=font_amp)[3]           # ≈ 28 px

    GAP = 8
    y_taker  = GOLD_LINE_Y + 20
    y_amp    = y_taker + th_taker + GAP
    y_own_t  = y_amp   + th_amp   + GAP

    draw_centered(taker_name, font_taker, y_taker, COLOR_DARK)
    draw_centered("&",        font_amp,   y_amp,   COLOR_GOLD)
    draw_centered(
        truncate(owner_name, font_owner_title, int(W * 0.82)),
        font_owner_title, y_own_t, COLOR_DARK
    )

    # ── 6. FRIENDSHIP PHRASE (right side, same height as left labels) ─────
    # Left labels span x = 10–62%.  Phrase lives in x = 63–92% zone.
    phrase     = _get_friendship_phrase(score, lang)
    phrase_cx  = int(W * 0.762)            # horizontal centre of right zone
    phrase_max = int(W * 0.30)
    y_phrase   = int(H * 0.690)            # aligns with "Natija/daraja" label row

    if phrase:
        for i, line in enumerate(wrap_text(phrase, font_phrase, phrase_max)):
            bbox = draw.textbbox((0, 0), line, font=font_phrase)
            tw   = bbox[2] - bbox[0]
            draw.text((phrase_cx - tw // 2, y_phrase + i * 30),
                      line, font=font_phrase, fill=COLOR_PHRASE)

    # ── 7. LEFT COLUMN VALUES (no labels — pre-printed on template) ───────
    lx = int(W * 0.095)   # 9.5 % from left

    # Score — blank zone between Natija/daraja gold line (71%) and Quiz egasi (79%)
    y_score = int(H * 0.724)
    draw.text((lx, y_score), f"{score}%", font=font_score, fill=COLOR_DARK)

    # Owner — below "Quiz egasi" italic (82%), overlapping thin gold lines (intentional)
    y_own_v = int(H * 0.836)
    draw.text(
        (lx, y_own_v),
        truncate(owner_name, font_owner_val, int(W * 0.44)),
        font=font_owner_val, fill=COLOR_DARK
    )

    # Bot — after bot gold underline (89%)
    y_bot = int(H * 0.904)
    draw.text((lx, y_bot), BOT_USERNAME, font=font_bot, fill=COLOR_GOLD)

    # ── 8. Serialise ──────────────────────────────────────────────────────
    out = io.BytesIO()
    img.convert("RGB").save(out, format="PNG", optimize=True)
    return out.getvalue()