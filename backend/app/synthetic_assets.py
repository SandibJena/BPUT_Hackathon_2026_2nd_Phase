"""Generate plainly labeled fictional reports and schematic image fixtures."""
import json
from pathlib import Path
import textwrap

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from app.core.config import DISCLAIMER

REPORTS = [
    {'slug': 'cbc', 'title': 'CBC', 'date': '2026-09-21', 'blurry': False,
     'values': [{'test': 'Hemoglobin', 'value': 11.0, 'unit': 'g/dL', 'reference_range': '12.0-16.0'},
                {'test': 'White cell count', 'value': 12000, 'unit': 'cells/uL', 'reference_range': '4000-11000'}]},
    {'slug': 'sugar', 'title': 'Fasting sugar', 'date': '2026-09-21', 'blurry': False,
     'values': [{'test': 'Fasting glucose', 'value': 135, 'unit': 'mg/dL', 'reference_range': '70-100'}]},
    {'slug': 'lipid', 'title': 'Lipid panel', 'date': '2026-09-20', 'blurry': False,
     'values': [{'test': 'Total cholesterol', 'value': 215, 'unit': 'mg/dL', 'reference_range': '0-200'}]},
    {'slug': 'lft', 'title': 'LFT', 'date': '2026-09-20', 'blurry': False,
     'values': [{'test': 'ALT', 'value': 48, 'unit': 'U/L', 'reference_range': '7-40'}]},
    {'slug': 'urine_blurry', 'title': 'Urine report', 'date': '2026-09-21', 'blurry': True,
     'values': [{'test': 'pH', 'value': 6.0, 'unit': None, 'reference_range': '4.5-8.0'}]},
]


def footer(draw: ImageDraw.ImageDraw, y: int, width: int = 86) -> None:
    font = ImageFont.load_default(size=18)
    for line in textwrap.wrap(DISCLAIMER, width):
        draw.text((40, y), line, fill='#172b38', font=font)
        y += 25


def generate_assets(destination: Path) -> None:
    report_dir, image_dir = destination / 'reports', destination / 'images'
    report_dir.mkdir(parents=True, exist_ok=True)
    image_dir.mkdir(parents=True, exist_ok=True)
    for index, report in enumerate(REPORTS, start=1):
        image = Image.new('RGB', (1100, 780), 'white')
        draw = ImageDraw.Draw(image)
        font = ImageFont.load_default(size=25)
        lines = ['SYNTHETIC SAMPLE - NOT A REAL PATIENT REPORT',
                 f"{report['title']} | DEMO-{index:03d} | {report['date']}",
                 'Illustrative reference ranges; not for clinical use.', '']
        for value in report['values']:
            lines.append(f"{value['test']}: {value['value']} {value['unit'] or ''}")
            lines.append(f"Reference range printed on this fictional report: {value['reference_range']}")
        y = 40
        for line in lines:
            draw.text((40, y), line, fill='#172b38', font=font)
            y += 45
        if report['blurry']:
            image = image.filter(ImageFilter.GaussianBlur(radius=3))
        # Keep disclaimer readable even on the low-quality OCR fixture.
        footer(ImageDraw.Draw(image), 615)
        image.save(report_dir / f"{report['slug']}.png")
        image.save(report_dir / f"{report['slug']}.pdf", 'PDF', resolution=150)
    (report_dir / 'expected_values.json').write_text(json.dumps(REPORTS, indent=2), encoding='utf-8')

    for kind in ('schematic_skin', 'schematic_wound', 'blank_control'):
        image = Image.new('RGB', (1100, 780), '#f6eee5')
        draw = ImageDraw.Draw(image)
        draw.text((40, 35), 'SYNTHETIC SCHEMATIC - NOT A CLINICAL PHOTO',
                  fill='#172b38', font=ImageFont.load_default(size=26))
        if kind == 'schematic_skin':
            for x, y in ((320, 240), (460, 280), (520, 400), (350, 420)):
                draw.ellipse((x, y, x + 60, y + 40), fill='#c66d72')
        elif kind == 'schematic_wound':
            draw.line((300, 310, 700, 350), fill='#985f65', width=14)
        draw.text((40, 550), 'No scale, diagnostic meaning, or severity label.',
                  fill='#172b38', font=ImageFont.load_default(size=23))
        footer(draw, 615)
        image.save(image_dir / f'{kind}.png')
