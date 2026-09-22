"""Local, visible-screen draft reading. No game process memory is accessed."""
import bootstrap
import asyncio
import io
import re
import unicodedata
from PIL import Image, ImageOps
from data import HEROES, MAPS
from hero_ids import IDS
from functools import lru_cache

@lru_cache(maxsize=1)
def templates():
    import cv2
    import numpy as np
    result = []
    for path in (bootstrap.ROOT / 'assets').glob('storm_ui_glues_draft_portrait_*.png'):
        hero = IDS.get(path.stem.replace('storm_ui_glues_draft_portrait_', ''))
        if not hero:
            continue
        portrait = Image.open(path).convert('RGB').crop((45, 30, 135, 120))
        for size in (27, 30, 31, 32, 33, 34, 35, 36, 39, 42, 45, 48):
            result.append((hero, cv2.cvtColor(np.array(portrait.resize((size, size))), cv2.COLOR_RGB2GRAY)))
    # Ban tiles can use the square hero-select artwork, which is not always
    # the same composition as the tall draft portrait (notably Johanna).
    # Keep both references and the existing confidence/margin requirements.
    for path in (bootstrap.ROOT / 'assets').glob('storm_ui_ingame_heroselect_btn_*.png'):
        hero = IDS.get(path.stem.replace('storm_ui_ingame_heroselect_btn_', ''))
        if not hero:
            continue
        portrait = Image.open(path).convert('RGB')
        for size in (30, 32, 33, 34, 35, 36, 37, 38, 39, 40, 42, 45, 48):
            result.append((hero, cv2.cvtColor(np.array(portrait.resize((size, size))), cv2.COLOR_RGB2GRAY)))
    return result

def read_bans(image):
    import cv2
    import numpy as np
    found = []
    for index, x in enumerate((250, 330, 410, image.width - 404, image.width - 324, image.width - 244)):
        patch = image.crop((x - 33, 12, x + 33, 75))
        gray = cv2.cvtColor(np.array(patch), cv2.COLOR_RGB2GRAY)
        scores = {}
        for hero, template in templates():
            score = float(cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED).max())
            scores[hero] = max(score, scores.get(hero, 0))
        best = sorted(scores.items(), key=lambda item: -item[1])
        if best and best[0][1] >= .78 and best[0][1] - best[1][1] >= .09:
            found.append({'index': index, 'hero': best[0][0], 'score': round(best[0][1], 3)})
    return found


def normal(text):
    return re.sub(r'[^a-z0-9]', '', unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode().lower())


async def ocr(image):
    from winrt.windows.media.ocr import OcrEngine
    from winrt.windows.globalization import Language
    from winrt.windows.graphics.imaging import BitmapDecoder
    from winrt.windows.storage.streams import InMemoryRandomAccessStream, DataWriter
    engine = OcrEngine.try_create_from_language(Language('en-US'))
    if engine is None:
        engine = OcrEngine.try_create_from_user_profile_languages()
    if engine is None:
        raise RuntimeError('Windows OCR language is missing. Install English language OCR in Windows Settings.')
    buf = io.BytesIO()
    image.convert('RGB').save(buf, format='PNG')
    stream = InMemoryRandomAccessStream()
    writer = DataWriter(stream)
    writer.write_bytes(buf.getvalue())
    await writer.store_async()
    writer.detach_stream()
    stream.seek(0)
    decoder = await BitmapDecoder.create_async(stream)
    bitmap = await decoder.get_software_bitmap_async()
    result = await engine.recognize_async(bitmap)
    text = '\n'.join(line.text for line in result.lines)
    bitmap.close()
    stream.close()
    return text


def match_name(text, choices):
    # Exact normalized line matches only: uncertain OCR is never guessed.
    lines = {normal(line) for line in text.splitlines()}
    matches = [name for name in choices if normal(name) in lines]
    return matches[0] if len(matches) == 1 else None


async def read_image_async(image):
    original = image.convert('RGB')
    scale = original.height / 857
    image = original
    width = round(image.width * 857 / image.height)
    image = image.resize((width, 857))
    title = await ocr(image.crop((width // 2 - 430, 0, width // 2 + 430, 38)).resize((1290, 57)))
    map_name = match_name(title, MAPS[1:])
    phase = 'draft'
    if not map_name:
        center = await ocr(image.crop((width // 2 - 250, 305, width // 2 + 250, 385)).resize((1000, 160)))
        if 'matchstarting' not in normal(center):
            return {'valid': False, 'message': 'Waiting for a draft or match-starting screen.'}
        phase = 'starting'
    slots = []
    for side in ('allies', 'enemies'):
        for index in range(5):
            y = 110 + index * 132
            x = 0 if index % 2 == 0 else 80
            box = (x, y, x + 175, y + 115) if side == 'allies' else (width - x - 175, y, width - x, y + 115)
            angle = 30 if side == 'allies' else -30
            crop = image.crop(box)
            native = original.crop(tuple(round(v * scale) for v in box))
            flat = native.rotate(angle, expand=True, resample=Image.Resampling.BICUBIC, fillcolor=(30,25,45))
            flat = flat.resize((flat.width * 2, flat.height * 2))
            text = await ocr(flat)
            hero = match_name(text, HEROES)
            if not hero:
                # A second rendering recovers anti-aliased short names without fuzzy hero guesses.
                alternate = await ocr(ImageOps.autocontrast(flat.convert('L')))
                hero = match_name(alternate, HEROES)
                if hero:
                    text = alternate
            if not hero:
                # Retain the old rendering as a final exact-name fallback for dark hovers.
                alternate = await ocr(crop.rotate(angle, expand=True, fillcolor=(30,25,45)).resize((440,400)))
                hero = match_name(alternate, HEROES)
                if hero:
                    text = alternate
            if not hero:
                # Isolate the straightened name ribbon when effects or nearby
                # player text confuse whole-card OCR. Still require an exact name.
                ribbon = flat.crop((0, round(flat.height*.38), flat.width, round(flat.height*.72)))
                alternate = await ocr(ImageOps.autocontrast(ribbon.convert('L')))
                hero = match_name(alternate, HEROES)
                if hero:
                    text = alternate + '\n' + text
            # White name ribbons indicate committed picks; dark ribbons are hovers.
            pixels = list(crop.getdata())
            white = sum(min(p) > 210 and max(p) - min(p) < 40 for p in pixels) / len(pixels)
            lines = text.splitlines()
            player = lines[-1] if hero and len(lines) > 1 and normal(lines[-1]) != normal(hero) else ''
            committed = phase == 'starting' or white > .14
            slots.append({'side': side, 'index': index, 'hero': hero, 'player': player,
                          'locked': bool(hero and committed), 'locked_hint': committed, 'text': text, 'white': round(white, 3)})
    if phase == 'starting' and sum(s['locked'] for s in slots) < 6:
        return {'valid': False, 'message': 'Final teams are not readable yet.'}
    return {'valid': True, 'map': map_name, 'phase': phase, 'slots': slots, 'bans': read_bans(image) if phase == 'draft' else [],
            'message': 'Draft read. Unreadable slots are left unchanged.'}


def read_image(image):
    return asyncio.run(read_image_async(image))
