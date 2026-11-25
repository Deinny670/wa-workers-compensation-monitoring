"""Create an additional styled PDF; leave the original analysis and PDF unchanged.

Uses the existing findings and CSVs. Run analyse.py first if they do not exist.
Arial is used when available on Windows, otherwise PDF-standard Helvetica.
"""
import re
from pathlib import Path

from reportlab.graphics.shapes import Drawing, Rect, String, Line
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
    KeepTogether,
)

from analyse import ROOT, URL, load

INK = colors.HexColor('#004346')
TEAL = colors.HexColor('#12A791')
YELLOW = colors.HexColor('#FECD00')
PALE = colors.HexColor('#F3F6F7')
BODY = colors.HexColor('#344649')
MUTED = colors.HexColor('#56696C')
RULE = colors.HexColor('#D9E3E3')
W = A4[0] - 88
REG, BOLD = 'Helvetica', 'Helvetica-Bold'
font_dir = Path('C:/Windows/Fonts')
if all((font_dir / f).is_file() for f in ['arial.ttf', 'arialbd.ttf']):
    pdfmetrics.registerFont(TTFont('ReportArial', str(font_dir/'arial.ttf')))
    pdfmetrics.registerFont(TTFont('ReportArial-Bold', str(font_dir/'arialbd.ttf')))
    pdfmetrics.registerFontFamily('ReportArial', normal='ReportArial', bold='ReportArial-Bold')
    REG, BOLD = 'ReportArial', 'ReportArial-Bold'

STYLES = {
    'title': ParagraphStyle('title', fontName=REG, fontSize=24, leading=28,
                            textColor=INK, spaceAfter=8),
    'deck': ParagraphStyle('deck', fontName=REG, fontSize=10.2, leading=14,
                           textColor=BODY, spaceAfter=13),
    'h2': ParagraphStyle('h2', fontName=BOLD, fontSize=12.5, leading=16,
                         textColor=INK, spaceBefore=11, spaceAfter=7),
    'body': ParagraphStyle('body', fontName=REG, fontSize=9, leading=12.5,
                           textColor=BODY, spaceAfter=7),
    'small': ParagraphStyle('small', fontName=REG, fontSize=7.4, leading=10.2,
                            textColor=MUTED, spaceAfter=5),
    'metric': ParagraphStyle('metric', fontName=REG, fontSize=25, leading=29,
                             textColor=INK, spaceAfter=3),
    'label': ParagraphStyle('label', fontName=BOLD, fontSize=9.2, leading=12,
                            textColor=INK, spaceAfter=5),
}


def p(text, style='body'):
    return Paragraph(text, STYLES[style])


def section(markdown, name):
    text = markdown.split('## '+name+'\n\n', 1)[1].split('\n\n## ', 1)[0]
    return [x.strip() for x in text.split('\n\n') if x.strip()]


def frame(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(INK)
    canvas.setFont(BOLD, 8)
    canvas.drawString(44, A4[1]-35, 'WA WORKERS COMPENSATION')
    canvas.setFillColor(MUTED)
    canvas.setFont(REG, 7.5)
    canvas.drawRightString(A4[0]-44, A4[1]-35, 'INDEPENDENT PORTFOLIO CASE STUDY')
    canvas.setStrokeColor(YELLOW)
    canvas.setLineWidth(2)
    canvas.line(44, A4[1]-46, A4[0]-44, A4[1]-46)
    canvas.setStrokeColor(RULE)
    canvas.setLineWidth(.5)
    canvas.line(44, 37, A4[0]-44, 37)
    canvas.setFont(REG, 7)
    canvas.setFillColor(MUTED)
    canvas.drawString(44, 24, 'Zule Yu | Prepared with AI assistance | 25 November 2026')
    canvas.drawRightString(A4[0]-44, 24, f'{doc.page} / 2')
    canvas.restoreState()


def metrics(buckets):
    lost = [sum(v[i] for k,v in buckets.items() if k not in ['0 days','All claims']) for i in range(4)]
    series = [('Lost-time claims', lost), ('No lost-time claims', buckets['0 days']),
              ('Total in-scope claims', buckets['All claims'])]
    cells=[]
    for label, values in series:
        a,b=values[-2:]
        cells.append([
            p(f'{100*(b/a-1):+.1f}%', 'metric'), p(label,'label'),
            p(f'{a:,.0f} to {b:,.0f}<br/>{b-a:+,.0f} claims', 'small'),
        ])
    gap=9
    width=(W-2*gap)/3
    table=Table([[cells[0],'',cells[1],'',cells[2]]],
                colWidths=[width,gap,width,gap,width], hAlign='LEFT')
    table.setStyle(TableStyle([
        ('VALIGN',(0,0),(-1,-1),'TOP'),
        ('LEFTPADDING',(0,0),(-1,-1),12),('RIGHTPADDING',(0,0),(-1,-1),9),
        ('TOPPADDING',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),7),
        *[('BACKGROUND',(i,0),(i,0),PALE) for i in [0,2,4]],
        *[('LINEABOVE',(i,0),(i,0),2,TEAL) for i in [0,2,4]],
    ]))
    return table


def bars(rows, total=None):
    """Shared linear scale; separate total from its components without double counting."""
    payment = total is not None
    h=232 if payment else 166
    d=Drawing(W,h)
    d.add(Rect(0,0,W,h,rx=8,ry=8,fillColor=PALE,strokeColor=None))
    left=196
    span=W-left-78
    maxv=total if payment else max(v for _,v in rows)
    for i,(name,value) in enumerate(rows):
        y=h-31-i*27-(12 if payment and i else 0)
        is_total=payment and i==0
        font=BOLD if is_total or name=='Income payments' else REG
        d.add(String(13,y+3,name,fontName=font,fontSize=8.2,fillColor=INK if is_total else BODY))
        width=value/maxv*span
        d.add(Rect(left,y,width,12,fillColor=INK if is_total else TEAL,strokeColor=None))
        label=f'${value:.1f}m' if payment else f'+{value:,.0f}'
        if name=='Income payments':label+=f' ({100*value/total:.1f}%)'
        d.add(String(left+width+6,y+2.5,label,fontName=font,fontSize=8,fillColor=INK))
    if payment:
        d.add(Line(13,h-41,W-13,h-41,strokeColor=RULE,strokeWidth=.65))
    return d


def note_panel(items):
    content=[]
    for text in items:content.append(p(text))
    table=Table([[content]],colWidths=[W],hAlign='LEFT')
    table.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1),PALE),
        ('BOX',(0,0),(-1,-1),.4,RULE),
        ('LEFTPADDING',(0,0),(-1,-1),12),('RIGHTPADDING',(0,0),(-1,-1),12),
        ('TOPPADDING',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),5),
    ]))
    return table


def main():
    markdown=(ROOT/'outputs/FINDINGS.md').read_text(encoding='utf-8')
    checks=section(markdown,'Data checks')
    scope=section(markdown,'Scope and limitations')
    follow=section(markdown,'Recommended follow-up')
    buckets=load('claim_buckets.csv')
    industries=load('industry_claims.csv')
    pay=load('payments_real_aud_m.csv')
    ranked=sorted(((k,v[-1]-v[-2]) for k,v in industries.items()),key=lambda x:x[1],reverse=True)
    categories=['Income payments','Lump sums','Medical & hospital','Allied health*',
                'Workplace rehabilitation','Legal & miscellaneous']
    payments=sorted(((k,pay[k][-1]-pay[k][-2]) for k in categories),key=lambda x:x[1],reverse=True)
    a,b=pay['Total claim payments'][-2:]
    story=[
        p('Claims activity and payment trends','title'),
        p('Where should a portfolio analyst investigate changes in claims activity and payments?', 'deck'),
        metrics(buckets), Spacer(1,7),
        p('Change from 2023/24 to 2024/25p. Source: WorkCover WA Annual Statistical Report 2024/25, p10. The latest year is provisional.','small'),
        Spacer(1,3),
        p('<b>Industry concentration.</b> Health care, mining and transport contributed 54.3% of the net increase in lost-time claims. Counts do not measure risk relative to hours worked or other insured activity.'),
        p('<b>Payment pressure.</b> Inflation-adjusted payments rose 16.7%; income payments contributed 61.7% of the increase. The payment totals and breakdown are shown on page 2.'),
        p('Largest contributions to annual lost-time claim growth','h2'),
        bars(ranked[:5]), Spacer(1,6),
        p('Change from 2023/24 to 2024/25p; claim counts, not frequency rates.<br/>Source: WorkCover WA Annual Statistical Report 2024/25, p23.','small'),
        p('The report does not provide an industry breakdown of the decline in no-lost-time claims.','small'),
        p('Checks against the source report','h2'),
        p('The checks below refer to WorkCover WA\'s Annual Statistical Report 2024/25.','small'),
    ]
    for text in checks:story.append(p(text))
    story.extend([
        PageBreak(), p('Payments and analytical judgement','title'),
        p('Income payments accounted for 61.7% of the annual payment increase.','deck'),
        p('Annual payment increase and its components','h2'),
        p(f'Inflation-adjusted AUD. Total payments: ${a:,.1f}m to ${b:,.1f}m (+{100*(b/a-1):.1f}%).','small'),
        bars([('Total increase',b-a),*payments],total=b-a),Spacer(1,7),
        p('* Includes other treatment services.<br/>Source: WorkCover WA Annual Statistical Report 2024/25, p12.','small'),
        p('Recommended follow-up','h2'),
    ])
    for text in follow:
        title,body=text.split('. ',1)
        story.append(p(f'<b>{title}.</b> {body}'))
    story.append(p('Scope and limitations','h2'))
    story.append(note_panel(scope))
    story.extend([
        Spacer(1,9),
        p('Source: WorkCover WA, Annual Statistical Report 2024/25, pp 2, 4, 10, 12, 23 and glossary pp 40-42. Derived analysis is independent and is not attributable to WorkCover WA.','small'),
        p(f'<link href="{URL}" color="#004346">Open the original WorkCover WA Annual Statistical Report 2024/25</link>','small'),
    ])
    target=ROOT/'outputs/WA_Workers_Compensation_Analysis_Styled.pdf'
    SimpleDocTemplate(str(target),pagesize=A4,leftMargin=44,rightMargin=44,
                      topMargin=63,bottomMargin=49,
                      title='WA Workers Compensation Monitoring - Styled Edition',
                      author='Zule Yu',subject='Independent AI-assisted portfolio case study').build(
                          story,onFirstPage=frame,onLaterPages=frame)
    print(target)


if __name__=='__main__':
    main()
