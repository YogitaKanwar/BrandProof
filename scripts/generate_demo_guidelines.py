"""Reproduce the tiny fictional public PDF fixture using the existing pypdf dependency."""

from pathlib import Path

from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

writer = PdfWriter()
page = writer.add_blank_page(width=612, height=792)
font = DictionaryObject(
    {
        NameObject("/Type"): NameObject("/Font"),
        NameObject("/Subtype"): NameObject("/Type1"),
        NameObject("/BaseFont"): NameObject("/Helvetica"),
    }
)
page[NameObject("/Resources")] = DictionaryObject(
    {NameObject("/Font"): DictionaryObject({NameObject("/F1"): writer._add_object(font)})}
)
stream = DecodedStreamObject()
stream.set_data(b"""q 0.043 0.16 0.176 rg 0 610 612 182 re f Q
BT /F1 15 Tf 1 1 1 rg 48 738 Td (BRANDPROOF / FICTIONAL GUIDELINES) Tj ET
BT /F1 30 Tf 1 1 1 rg 48 675 Td (Workshop Campaign) Tj ET
BT /F1 12 Tf 0.043 0.4 0.35 rg 48 560 Td (A fictional reference for the interactive demo.) Tj ET
BT /F1 12 Tf 0.15 0.23 0.23 rg 48 530 Td (Inspect the extracted rules and confirm them only after checking this page.) Tj ET
BT /F1 17 Tf 0.043 0.16 0.176 rg 48 460 Td (Campaign price: INR 899) Tj 0 -42 Td (Campaign date: 2026-11-12) Tj 0 -42 Td (Required text: Terms apply) Tj ET
BT /F1 11 Tf 0.3 0.38 0.36 rg 48 280 Td (The demo marketing caption and poster deliberately display INR 599.) Tj 0 -22 Td (Run the real review to compare content with confirmed references.) Tj 0 -22 Td (These guidelines do not approve marketing content or verify a real owner.) Tj ET
q 0.81 0.88 0.84 RG 48 100 m 564 100 l S Q
BT /F1 10 Tf 0.3 0.38 0.36 rg 48 76 Td (Fictional material only / No confidential information / Page 1 of 1) Tj ET
""")
page[NameObject("/Contents")] = writer._add_object(stream)
target = Path(__file__).resolve().parents[1] / "frontend/public/demo/workshop-guidelines.pdf"
target.parent.mkdir(parents=True, exist_ok=True)
writer.write(target)
