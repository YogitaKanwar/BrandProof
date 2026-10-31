from pathlib import Path

from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output/pdf"
OUT.mkdir(parents=True, exist_ok=True)
for name, file in [("Noto", "NotoSans-Regular.ttf"), ("NotoBold", "NotoSans-Bold.ttf")]:
    pdfmetrics.registerFont(TTFont(name, "/usr/share/fonts/noto/" + file))
pdfmetrics.registerFontFamily(
    "Noto", normal="Noto", bold="NotoBold", italic="Noto", boldItalic="NotoBold"
)
navy = HexColor("#1E2640")
sun = HexColor("#DC9750")
cream = HexColor("#FCF7EF")
muted = HexColor("#5B6374")
styles = getSampleStyleSheet()
styles.add(
    ParagraphStyle(
        name="BodyBP", fontName="Noto", fontSize=10, leading=15, textColor=navy, spaceAfter=10
    )
)
styles.add(
    ParagraphStyle(name="SmallBP", parent=styles["BodyBP"], fontSize=8, leading=12, textColor=muted)
)
styles.add(
    ParagraphStyle(
        name="HeadBP", fontName="NotoBold", fontSize=23, leading=29, textColor=navy, spaceAfter=18
    )
)
styles.add(
    ParagraphStyle(
        name="SubBP",
        fontName="NotoBold",
        fontSize=12,
        leading=17,
        textColor=navy,
        spaceBefore=12,
        spaceAfter=8,
    )
)
styles.add(
    ParagraphStyle(name="CoverBP", parent=styles["HeadBP"], fontSize=38, leading=45, spaceAfter=20)
)
story = []


def p(text, style="BodyBP"):
    return Paragraph(text, styles[style])


def add(text, style="BodyBP"):
    story.append(p(text, style))


def head(kicker, title):
    add(kicker.upper(), "SmallBP")
    add(title, "HeadBP")


def block(title, body):
    story.append(KeepTogether([p(title, "SubBP"), p(body)]))


def table(rows, widths):
    values = [[p(str(v), "SmallBP") for v in row] for row in rows]
    t = Table(values, colWidths=widths, hAlign="LEFT")
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), cream),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LINEBELOW", (0, 0), (-1, 0), 1, sun),
                ("LINEBELOW", (0, 1), (-1, -1), 0.3, HexColor("#E1E3E8")),
                ("LEFTPADDING", (0, 0), (-1, -1), 9),
                ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    story.append(t)


def footer(c, doc):
    c.saveState()
    w, h = A4
    c.setFillColor(navy)
    c.rect(0, h - 12, w, 12, fill=1, stroke=0)
    c.setFillColor(sun)
    c.rect(45, 35, 24, 3, fill=1, stroke=0)
    c.setFont("Noto", 7)
    c.setFillColor(muted)
    c.drawString(78, 34, "BrandProof | YOGI2KANWAR | Local release candidate | 31 Oct 2026")
    c.drawRightString(w - 45, 34, str(doc.page))
    c.restoreState()


head("Codex 48 / Round 3", "BrandProof")
add("Evidence before<br/>publication.", "CoverBP")
add("Team YOGI2KANWAR", "SubBP")
add(
    "A campaign review workspace that checks content against owner-confirmed brand rules, exposes its evidence and leaves publication decisions with people."
)
story.append(Spacer(1, 12))
table(
    [
        ["INPUT", "CHECK", "DECIDE"],
        [
            "PDF guidelines, caption and private poster",
            "Versioned rules, real OCR, bounded claims and measured visual samples",
            "Inspect evidence, record reasons and approve the current snapshot",
        ],
    ],
    [155, 155, 155],
)
story.append(Spacer(1, 18))
block(
    "Release status",
    "This report describes the local Round 3 candidate. It includes the three promised improvements and a bounded India advertising-risk extension. Local test results are reported on page 5. Public deployment, manual UI acceptance and PostgreSQL/container acceptance remain separate release gates.",
)
add(
    'Project: <link href="https://brand-proof-tau.vercel.app">brand-proof-tau.vercel.app</link><br/>Source: <link href="https://github.com/YogitaKanwar/BrandProof">github.com/YogitaKanwar/BrandProof</link><br/>Working branch: feat/brandproof-improvements-20261028',
    "SmallBP",
)
add(
    "The repository homepage returned HTTP 200 during inspection. Its API health endpoint returned HTTP 429; that observation is not a successful public workflow acceptance. The user requested a local release only.",
    "SmallBP",
)
story.append(PageBreak())
head("Promises 1 and 2", "Guidelines with evidence.<br/>Measurements with limits.")
block(
    "1 / PDF guideline import",
    "Owners import a PDF text layer. Supported directives become pending candidates with exact page quotations, offsets, filename and document digest. Explicit owner confirmation creates a new source version. A rule edit preserves history and cannot inherit a quotation that no longer supports it.",
)
add(
    "The extractor is bounded: 5 MiB, 30 pages, 8,000 characters per page, 60,000 total and a 15-second isolated worker. Scanned/blank pages are visibly unavailable; mixed documents can be partial. Narrative content outside the supported grammar produces no invented rule."
)
block(
    "What a judge can try",
    "Download the fictional sample PDF from the import panel, upload it, inspect its quotations and confirm a candidate. The fixture includes price, date, wording, background colour, contrast and alt-text requirements. Repeated imports can create pending duplicates; conflicting confirmed facts require clarification.",
)
block(
    "2 / Measured visual consistency and accessibility",
    "Supported flat backgrounds are compared with confirmed brand colours using CIE76 distance. Reliable OCR word samples report foreground/background colours, measured contrast and the configured ratio. Missing descriptions and supported literal price/date omissions produce alt-text findings.",
)
add(
    "The ordinary antialiased-text defect has been repaired using a solid ink core, colour-blend and glyph-boundary checks. Black/white samples measure 21:1. Low-contrast grey produces a measured finding. Small text with insufficient solid ink, gradients, mixed colours and uncertain OCR can abstain."
)
add(
    "These are bounded sample checks. Alt-text presence does not establish semantic quality. Raster dimensions do not establish WCAG large-text status, and sampled contrast does not certify full accessibility.",
    "SmallBP",
)
story.append(PageBreak())
head("Promise 3", "Governance Insights")
add(
    "Owners can see recurring finding categories across campaigns and inspect the exact source versions, findings and reasons behind reviewer decisions."
)
table(
    [
        ["MEASURE", "POLICY"],
        [
            "Category recurrence",
            "Count observations and distinct campaigns. This is not a count of proven truth violations.",
        ],
        [
            "Source-version grouping",
            "Keep each immutable guideline version separate. Similar wording in different campaigns does not imply one shared source.",
        ],
        [
            "Decision rate",
            "Latest dismissals plus exceptions divided by all reviewed observations, including reopen. Require at least five distinct reviewed campaign/content revisions.",
        ],
        [
            "Identical reruns",
            "Keep the latest completed/partial run per content/source/pack snapshot. Previous-run decisions are not carried forward.",
        ],
        [
            "Limits",
            "At most 500 runs and 5,000 decisions; disclose truncation. Evidence drilldowns link exact saved runs and reasons.",
        ],
    ],
    [132, 333],
)
block(
    "A signal to investigate",
    "A high rate can reveal unclear rules or review friction. Owners must inspect reasons before clarifying a guideline. Small samples show no rate. Regulatory dispositions are identified separately and never recommend weakening regulation.",
)
block(
    "Demonstration integrity",
    "Use clearly labelled fictional campaigns and scripted QA decisions for demonstrations. The implementation does not claim real customer analytics, independent identities or measured model accuracy. Workspace isolation and deleted-campaign visibility remain enforced.",
)
story.append(PageBreak())
head("Additional differentiator", "Cited advertising-risk review")
add(
    "An owner selects the target jurisdiction, sector and language. The campaign publication date is part of the saved review. Initial scope is selected English outcome, time-bound and absolute-performance signals for India."
)
block(
    "Verified reference",
    'The frozen pack uses the CCPA 2022 advertising guidelines, clause 12(a), Gazette PDF page 10. A brief verified quotation is: "shall be capable of substantiation". Each cited finding includes the official URL, source digest, clause/page, retrieval date and pack version.',
)
block(
    "Example",
    '"Guaranteed results in 30 days" creates one claim-risk prompt with supporting regulation evidence. The reviewer is asked for the outcome definition, evidence reference, audience, conditions and time period. A generic "T&amp;Cs apply" does not automatically resolve the concern.',
)
add(
    'Negation and ordinary refund controls include "No results are guaranteed" and "30-day money-back guarantee". A metaphor such as "Red Bull gives you wings" is outside the bounded truth analysis. A detected pattern does not establish falsity or a legal breach.'
)
block(
    "Changes invalidate earlier reliance",
    "Profile versions are immutable and advance the source revision. Reviews pin their profile and pack content. A profile change, installed-pack update or overdue source review can stale earlier approvals while preserving their historical evidence. Incomplete coverage requires explicit reviewer notes, and unresolved findings still block approval.",
)
add(
    "Pack: in-advertising-risk / 2026-10-31.1<br/>Retrieved: 31 Oct 2026 | source review due: 1 Dec 2026<br/>Source digest: d97e8ab663ebdab8b3e2139465013da14f65dead4fa3e3aa8023df8617fe32f1",
    "SmallBP",
)
add(
    "Sector-specific regulation, other jurisdictions/languages and complete consumer-law evaluation are outside coverage. The coaching pack remains disabled because the final official instrument could not be retrieved; no guessed clause was activated. Human review records are not legal certification.",
    "SmallBP",
)
add(
    '<link href="https://consumeraffairs.gov.in/public/upload/files/CCPA_Notification_1732707665.pdf">Official CCPA Gazette source</link> | <link href="https://consumeraffairs.gov.in/pages/consumer-protection-acts">Department of Consumer Affairs Acts index</link>',
    "SmallBP",
)
story.append(PageBreak())
head("Implementation and checks", "A complete local workflow")
table(
    [
        ["LAYER", "IMPLEMENTATION"],
        [
            "Frontend",
            "React 19, TypeScript and Vite; Dark Blue / Desert Sun workspace, caption/poster editing, source evidence, decisions and history.",
        ],
        [
            "API and storage",
            "Python, FastAPI, Pydantic, SQLAlchemy; six additive migrations and PostgreSQL-compatible models. Local acceptance uses isolated SQLite.",
        ],
        [
            "Documents and images",
            "pypdf in a bounded worker; Pillow normalization; real local Tesseract text, confidence, coordinates and offsets.",
        ],
        [
            "Checks",
            "Deterministic structured rules, bounded English claim patterns, visual sample measurements and a frozen legal reference pack.",
        ],
        [
            "Safety of evidence",
            "Immutable snapshots, expected-revision guards, owner confirmation, author/requester self-approval restrictions, stale receipts and same-browser session recovery.",
        ],
    ],
    [108, 357],
)
block(
    "Validation",
    "574 backend tests and 56 frontend tests pass locally; frontend lint/build, Ruff and whitespace checks pass. The latest automated results are recorded in docs/ROUND3_LOCAL_ACCEPTANCE_2026-10-31.md. Tests exercise malformed uploads, PDF provenance and partial pages, contrast uncertainty, profile permissions and isolation, legal citations, approval guards, Insights sample limits and restart persistence.",
)
add(
    "Optional Groq/OpenRouter contextual AI requires server configuration and per-review consent. It is not needed for the deterministic path and is not accepted here as a working live provider. Local claim matching is not general semantic truth verification."
)
block(
    "Changes since Round 2",
    "Completed the promised PDF, measured visual and Governance Insights flows locally; repaired contrast sampling; added cited advertising-risk review and profile/pack approval staleness. Existing immutable history, OCR highlighting, explicit corrections and human decisions remain central.",
)
add(
    "No production team authentication, broad legal advice, general logo/typography certification or all-input accessibility claim is made. Free hosting cold starts and database retention require operational acceptance.",
    "SmallBP",
)
story.append(PageBreak())
head("Handoff and release", "Ready to verify, then submit")
block(
    "Local acceptance gates",
    "Use the dated test report for exact command results and known limitations. Manual desktop/mobile browser acceptance is outstanding because the browser tool rejected access. Docker/PostgreSQL execution was unavailable because Docker socket access was denied. No security permissions were changed to bypass these limits.",
)
block(
    "Yogita deployment handoff",
    "Deploy the reviewed branch through the team-owned hosting accounts after an additive-migration backup/preflight. Verify the exact frontend/API build pair, health, fresh anonymous session, PDF import, contrast/alt text, cited risk, reviewer decisions, approval staleness, Insights links and persistence after restart. Record results before calling features publicly complete.",
)
block(
    "Submission package",
    "Working project link, source repository, this updated project report, completed-improvements list, implementation details, testing notes and member contributions. The team leader submits the official form. The supplied deadline is 3 Nov 2026, 23:59 IST; check the official final instructions.",
)
block(
    "Contributions",
    "Role mapping supplied by the team: Rushab Ramhari Patil owns backend, OCR, AI and database work; Yogita Kanwar owns frontend and integration. This local slice was developed with coding-assistant support. Confirm the final member contribution statement against actual commits and team records; no hours or percentages are inferred.",
)
add("References and verification record", "SubBP")
add(
    '<link href="https://wecodecoders.in/events/codex-48">Official Codex 48 event page</link><br/>docs/ROUND3_SCOPE.md - actual submitted promises<br/>docs/ROUND3_LOCAL_ACCEPTANCE_2026-10-31.md - dated testing evidence<br/>docs/ADVERTISING_RISK.md - pack scope and maintenance<br/>docs/ROUND3_RELEASE_HANDOFF.md - deployment and integration checklist',
    "SmallBP",
)
add(
    "This is a local release candidate, not proof of a healthy public deployment. Keep the final document aligned with the actual released build and verified results.",
    "SmallBP",
)
doc = SimpleDocTemplate(
    str(OUT / "BrandProof_Round_3_Release_Candidate.pdf"),
    pagesize=A4,
    rightMargin=65,
    leftMargin=65,
    topMargin=45,
    bottomMargin=60,
    title="BrandProof - Round 3 release candidate",
    author="YOGI2KANWAR",
)
doc.build(story, onFirstPage=footer, onLaterPages=footer)
# Deliberately simple one-page text fixture: supported directives are exact lines.
fixture = ROOT / "frontend/public/fictional-guidelines.pdf"
c = canvas.Canvas(str(fixture), pagesize=A4)
c.setTitle("Fictional workshop guidelines - BrandProof sample")
c.setAuthor("YOGI2KANWAR")
c.setFillColor(navy)
c.rect(0, A4[1] - 150, A4[0], 150, fill=1, stroke=0)
c.setFillColor(sun)
c.setFont("NotoBold", 11)
c.drawString(50, A4[1] - 52, "BRANDPROOF / FICTIONAL EXAMPLE")
c.setFillColor(white)
c.setFont("NotoBold", 23)
c.drawString(50, A4[1] - 92, "Workshop campaign guidelines")
c.setFillColor(navy)
c.setFont("Noto", 12)
lines = [
    "Campaign price: INR 499",
    "Campaign date: 2026-11-12",
    "Required text: Terms apply",
    'Use "affordable" instead of "cheap"',
    "Background colour: #FFFFFF",
    "Minimum contrast: 4.5",
    "Alt text: required",
]
y = A4[1] - 205
for line in lines:
    c.drawString(50, y, line)
    y -= 40
c.setFont("Noto", 9)
c.setFillColor(muted)
c.drawString(50, 120, "Fictional fixture only. Candidates remain pending until owner confirmation.")
c.drawString(50, 102, "These directives are brand rules, not legal sources or approval of content.")
c.drawString(
    50, 84, "Check quotations after import. Unsupported narrative text is not interpreted."
)
c.showPage()
c.save()
print(OUT / "BrandProof_Round_3_Release_Candidate.pdf")
print(fixture)
