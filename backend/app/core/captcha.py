import base64
import io
import random
import re
import secrets
import uuid

from PIL import Image, ImageDraw, ImageFont

from app.core.redis import redis_manager


PHONE_REGEX = re.compile(r"^1[3-9]\d{9}$")

CAPTCHA_CHARS = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789"


def validate_phone(phone: str) -> bool:
    return bool(PHONE_REGEX.fullmatch(phone))


def _random_color(start: int = 0, end: int = 128) -> tuple[int, int, int]:
    return (
        secrets.randbelow(end - start) + start,
        secrets.randbelow(end - start) + start,
        secrets.randbelow(end - start) + start,
    )


async def generate_captcha() -> tuple[str, str, str]:
    width, height = 120, 50
    image = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(image)

    for _ in range(secrets.randbelow(50) + 30):
        x = secrets.randbelow(width)
        y = secrets.randbelow(height)
        draw.point((x, y), fill=_random_color(128, 256))

    for _ in range(secrets.randbelow(2) + 2):
        x1 = secrets.randbelow(width)
        y1 = secrets.randbelow(height)
        x2 = secrets.randbelow(width)
        y2 = secrets.randbelow(height)
        draw.line((x1, y1, x2, y2), fill=_random_color(64, 192), width=1)

    answer = "".join(secrets.choice(CAPTCHA_CHARS) for _ in range(4))

    try:
        font = ImageFont.truetype("arial.ttf", 28)
    except OSError:
        font = ImageFont.load_default()

    for i, char in enumerate(answer):
        x = 15 + i * 22 + secrets.randbelow(8)
        y = 5 + secrets.randbelow(8)
        color = _random_color(0, 128)
        char_image = Image.new("RGBA", (28, 35), (0, 0, 0, 0))
        char_draw = ImageDraw.Draw(char_image)
        char_draw.text((0, 0), char, font=font, fill=color)
        angle = secrets.randbelow(50) - 25
        rotated = char_image.rotate(angle, expand=True, fillcolor=(0, 0, 0, 0))
        image.paste(rotated, (x, y), rotated)

    captcha_id = uuid.uuid4().hex[:16]

    await redis_manager.set(f"captcha:{captcha_id}", answer, ex=300)

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    base64_image = "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("utf-8")

    return captcha_id, answer, base64_image


async def verify_captcha(captcha_id: str, code: str) -> bool:
    key = f"captcha:{captcha_id}"
    stored = await redis_manager.get(key)
    if stored is None:
        return False
    valid = stored.lower() == code.lower()
    await redis_manager.delete(key)
    return valid