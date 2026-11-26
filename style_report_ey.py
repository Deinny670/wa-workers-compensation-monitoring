"""Additional EY-inspired visual edition of the same independent work sample.

Reuses the existing report content, data and layout functions. This is not an
EY publication. No EY logo or proprietary typeface is embedded.
Run: python style_report_ey.py
"""
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from reportlab.graphics.shapes import Drawing, Rect, String, Line
from reportlab.lib.pagesizes import A4
import style_report as base

INK=colors.HexColor('#2E2E38')
YELLOW=colors.HexColor('#FFE600')
GREY=colors.HexColor('#747480')
PALE=colors.HexColor('#F1F1F2')
WHITE=colors.white
RULE=colors.HexColor('#D6D6DA')
base.INK=INK
base.TEAL=YELLOW
base.YELLOW=YELLOW
base.PALE=PALE
base.BODY=INK
base.MUTED=colors.HexColor('#5C5C68')
base.RULE=RULE
base.LINK_COLOR='#2E2E38'
for name,style in base.STYLES.items():
    style.textColor=base.MUTED if name=='small' else INK
base.STYLES['title'].fontName=base.BOLD
base.STYLES['title'].fontSize=23
base.STYLES['title'].leading=27
base.STYLES['metric'].textColor=WHITE
base.STYLES['metric'].fontName=base.BOLD
base.STYLES['label'].textColor=WHITE
base.STYLES['metric_note']=base.STYLES['small'].clone('metric_note',textColor=colors.HexColor('#E1E1E6'))


def frame(canvas,doc):
    canvas.saveState()
    canvas.setFillColor(INK)
    canvas.setFont(base.BOLD,8)
    canvas.drawString(44,A4[1]-35,'WA WORKERS COMPENSATION')
    canvas.setFont(base.REG,7.5)
    canvas.drawRightString(A4[0]-44,A4[1]-35,'INDEPENDENT PORTFOLIO CASE STUDY')
    canvas.setFillColor(INK)
    canvas.rect(44,A4[1]-47,base.W,1,fill=1,stroke=0)
    canvas.setFillColor(YELLOW)
    canvas.rect(44,A4[1]-49,73,4,fill=1,stroke=0)
    canvas.setStrokeColor(RULE)
    canvas.setLineWidth(.5)
    canvas.line(44,37,A4[0]-44,37)
    canvas.setFillColor(base.MUTED)
    canvas.setFont(base.REG,7)
    canvas.drawString(44,24,'Zule Yu | Prepared with AI assistance | 26 November 2026')
    canvas.drawRightString(A4[0]-44,24,f'{doc.page} / 2')
    canvas.restoreState()


def metrics(buckets):
    lost=[sum(v[i] for k,v in buckets.items() if k not in ['0 days','All claims']) for i in range(4)]
    series=[('Lost-time claims',lost),('No lost-time claims',buckets['0 days']),
            ('Total in-scope claims',buckets['All claims'])]
    cells=[]
    for label,values in series:
        a,b=values[-2:]
        cells.append([base.p(f'{100*(b/a-1):+.1f}%','metric'),base.p(label,'label'),
                      base.p(f'{a:,.0f} to {b:,.0f}<br/>{b-a:+,.0f} claims','metric_note')])
    gap=9;width=(base.W-2*gap)/3
    table=Table([[cells[0],'',cells[1],'',cells[2]]],colWidths=[width,gap,width,gap,width],hAlign='LEFT')
    table.setStyle(TableStyle([
        ('VALIGN',(0,0),(-1,-1),'TOP'),
        ('LEFTPADDING',(0,0),(-1,-1),12),('RIGHTPADDING',(0,0),(-1,-1),9),
        ('TOPPADDING',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),7),
        *[('BACKGROUND',(i,0),(i,0),INK) for i in [0,2,4]],
        *[('LINEABOVE',(i,0),(i,0),3,YELLOW) for i in [0,2,4]],
    ]))
    return table


def bars(rows,total=None):
    payment=total is not None
    h=232 if payment else 166
    d=Drawing(base.W,h)
    d.add(Rect(0,0,base.W,h,fillColor=PALE,strokeColor=None))
    left=196;span=base.W-left-78
    maxv=total if payment else max(v for _,v in rows)
    for i,(name,value) in enumerate(rows):
        y=h-31-i*27-(12 if payment and i else 0)
        is_total=payment and i==0
        highlight=(name=='Income payments') if payment else i==0
        font=base.BOLD if is_total or highlight else base.REG
        fill=INK if is_total else YELLOW if highlight else GREY
        d.add(String(13,y+3,name,fontName=font,fontSize=8.2,fillColor=INK))
        width=value/maxv*span
        d.add(Rect(left,y,width,12,fillColor=fill,strokeColor=None))
        label=f'${value:.1f}m' if payment else f'+{value:,.0f}'
        if name=='Income payments':label+=f' ({100*value/total:.1f}%)'
        d.add(String(left+width+6,y+2.5,label,fontName=font,fontSize=8,fillColor=INK))
    if payment:d.add(Line(13,h-41,base.W-13,h-41,strokeColor=RULE,strokeWidth=.65))
    return d


if __name__=='__main__':
    base.frame=frame
    base.metrics=metrics
    base.bars=bars
    base.main(base.ROOT/'outputs/WA_Workers_Compensation_Analysis_EY.pdf')
