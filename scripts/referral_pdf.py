"""One-page partner referral sheet for land agents to give landowner clients (approved by Ben 19 Nov 2026)."""
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from reportlab.platypus import Paragraph, Frame
from reportlab.lib.styles import ParagraphStyle

F = '/usr/share/fonts/truetype/dejavu/'
pdfmetrics.registerFont(TTFont('S', F + 'DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('SB', F + 'DejaVuSans-Bold.ttf'))
from reportlab.pdfbase.pdfmetrics import registerFontFamily
registerFontFamily('S', normal='S', bold='SB', italic='S', boldItalic='SB')
INK, MUTED, ACCENT, LINE, PANEL = HexColor('#0f1b2d'), HexColor('#5a6475'), HexColor('#0a7f96'), HexColor('#d6dbe3'), HexColor('#f2f5f8')
W, H = A4
M = 46

body = ParagraphStyle('b', fontName='S', fontSize=11, leading=16.5, textColor=INK, spaceAfter=6)
small = ParagraphStyle('s', parent=body, fontSize=8.5, leading=12, textColor=MUTED)
h1 = ParagraphStyle('h1', fontName='SB', fontSize=23, leading=28, textColor=INK, spaceAfter=10)
h2 = ParagraphStyle('h2', fontName='SB', fontSize=14, leading=18, textColor=ACCENT, spaceBefore=14, spaceAfter=4)
bul = ParagraphStyle('li', parent=body, leftIndent=12, bulletIndent=0, spaceAfter=2)

c = canvas.Canvas('/home/claude/work/Benzene partner referral sheet.pdf', pagesize=A4)
c.setTitle('Has a developer asked about your land? Check the grid first.')
c.setAuthor('Benzene')

# header: partner logo space on the left, Benzene on the right
c.setStrokeColor(LINE); c.setDash(3, 3); c.setLineWidth(0.8)
c.roundRect(M, H - M - 58, 190, 58, 6)
c.setDash()
c.setFillColor(MUTED); c.setFont('S', 8.5)
c.drawCentredString(M + 95, H - M - 25, 'Partner logo')
c.drawCentredString(M + 95, H - M - 37, '[Partner firm name]')
c.drawImage('/home/claude/benzene-data-repo/brand/benzene-logo.png', W - M - 130, H - M - 46, width=130, height=130 * 425 / 1200, mask='auto')
c.setStrokeColor(LINE); c.line(M, H - M - 74, W - M, H - M - 74)

story = [
    Paragraph('Has a developer asked about your land? Check the grid first.', h1),
    Paragraph('&nbsp;', ParagraphStyle('sp', parent=body, fontSize=4, leading=4)),
    Paragraph('[Partner firm name] works with Benzene, a GB grid connection research service. Before you agree an option, it is worth knowing how crowded the grid is near your land. A project cannot earn anyone money until it connects, and some connection dates are now years away.', body),
    Paragraph('Free substation check', h2),
    Paragraph('Name a substation, a site or a postcode. Within one business day we reply with:', body),
    Paragraph('how much capacity is already queued there', bul, bulletText='•'),
    Paragraph('which Gate those projects hold under connections reform', bul, bulletText='•'),
    Paragraph('their contracted connection dates', bul, bulletText='•'),
    Paragraph('No charge and no obligation.', body),
    Paragraph('Landowner grid note: £495, three working days', h2),
    Paragraph('A two-page note on your land, written for you and your agent:', body),
    Paragraph('how crowded the grid is nearby, at transmission and, where data allows, on the local network', bul, bulletText='•'),
    Paragraph('who else is queuing at the same substations, and when they are due to connect', bul, bulletText='•'),
    Paragraph('the questions to put to the developer before you sign', bul, bulletText='•'),
    Paragraph('See a sample, for a made-up field next to Creyke Beck substation in the East Riding: <font color="#0a7f96">www.benzene-group.com/sample-landowner-note.html</font>', body),
    Paragraph('How to ask', h2),
    Paragraph('Email <b>info@benzene-group.com</b> or use the form at <b>www.benzene-group.com</b>. Mention [Partner firm name] so we know who referred you.', body),
]
fr = Frame(M, 150, W - 2 * M, H - M - 84 - 150, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0, showBoundary=0)
left = fr.addFromList(story, c)
assert not left, 'content did not fit'

# "what the note is not" panel
c.setFillColor(PANEL); c.setStrokeColor(LINE)
c.roundRect(M, 62, W - 2 * M, 76, 6, fill=1, stroke=1)
fr2 = Frame(M + 14, 66, W - 2 * M - 28, 68, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
fr2.addFromList([
    Paragraph('<b>What the note is not</b>', ParagraphStyle('x', parent=body, spaceAfter=3)),
    Paragraph('It is a desk review of public registers. It is not a valuation, legal advice, advice on option terms or an engineering study. For those, talk to your agent, solicitor or a grid engineer.', small),
], c)
c.setFillColor(MUTED); c.setFont('S', 8)
c.drawString(M, 42, 'Coverage: Great Britain. Northern Ireland is not covered.')
c.drawRightString(W - M, 42, 'www.benzene-group.com')
c.showPage(); c.save()
print('ok')
