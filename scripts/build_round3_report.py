"""Render the current Round 3 Markdown submission; never mutate demo assets."""

import argparse
import re
from html import escape
from pathlib import Path

from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs/ROUND3_SUBMISSION_CONTENT.md"
NAVY, SUN, MUTED = map(HexColor, ["#1E2640", "#DC9750", "#5B6374"])


def inline(text):
    text = escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"`([^`]+)`", r"<font face='Courier'>\1</font>", text)
    return re.sub(
        r"\[([^\]]+)\]\((https?://[^)]+)\)", r'<link href="\2" color="#315B83">\1</link>', text
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=ROOT / "output/pdf/BrandProof_Round_3_Final_Submission.pdf"
    )
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="BPTitle",
            fontName="Helvetica-Bold",
            fontSize=27,
            leading=32,
            textColor=NAVY,
            spaceAfter=15,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BPSub",
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=17,
            textColor=NAVY,
            spaceBefore=10,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BPBody",
            fontName="Helvetica",
            fontSize=10,
            leading=14.5,
            textColor=NAVY,
            spaceAfter=9,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BPCaption",
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=MUTED,
            spaceAfter=10,
        )
    )
    story = []
    # Explicit page separators keep the concise source and generated document aligned.
    for index, page in enumerate(SOURCE.read_text(encoding="utf-8").split("<!-- page -->")):
        if index:
            story.append(PageBreak())
        paragraphs = re.split(r"\n\s*\n", page.strip())
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            image = re.fullmatch(r"!\[([^\]]+)\]\(([^)]+)\)", paragraph)
            if image:
                path = (SOURCE.parent / image[2]).resolve()
                if not path.is_relative_to(ROOT) or not path.is_file():
                    raise ValueError("Submission screenshot is missing or outside this repository")
                picture = Image(str(path))
                factor = min(475 / picture.imageWidth, 285 / picture.imageHeight)
                picture.drawWidth = picture.imageWidth * factor
                picture.drawHeight = picture.imageHeight * factor
                story.extend(
                    [
                        Spacer(1, 7),
                        picture,
                        Spacer(1, 6),
                        Paragraph(inline(image[1]), styles["BPCaption"]),
                    ]
                )
            elif paragraph.startswith("# "):
                story.append(Paragraph(inline(paragraph[2:]), styles["BPTitle"]))
            elif paragraph.startswith("## "):
                story.append(Paragraph(inline(paragraph[3:]), styles["BPSub"]))
            else:
                story.append(Paragraph(inline(paragraph.replace("\n", " ")), styles["BPBody"]))

    def footer(canvas, doc):
        canvas.setFillColor(NAVY)
        canvas.rect(0, 0, A4[0], 35, fill=1, stroke=0)
        canvas.setFillColor(SUN)
        canvas.setFont("Helvetica-Bold", 8)
        canvas.drawString(48, 14, "BRANDPROOF  /  YOGI2KANWAR  /  ROUND 3")
        canvas.setFillColor(white)
        canvas.drawRightString(A4[0] - 48, 14, str(doc.page))

    SimpleDocTemplate(
        str(args.output),
        pagesize=A4,
        leftMargin=60,
        rightMargin=60,
        topMargin=45,
        bottomMargin=53,
        title="BrandProof - Round 3 final submission",
        author="YOGI2KANWAR",
    ).build(story, onFirstPage=footer, onLaterPages=footer)
    print(args.output)


if __name__ == "__main__":
    main()
