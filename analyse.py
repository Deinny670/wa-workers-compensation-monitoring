"""Reproduce a small WA workers compensation monitoring case study.

AI-assisted portfolio project. Data are public scheme aggregates, not Suncorp data.
Run: python analyse.py [--source-pdf path/to/report.pdf]
Without a PDF, uses the checked-in extracted CSVs. No web/API access required.
"""
import argparse
import csv
import hashlib
import json
import re
from pathlib import Path

from reportlab.graphics.shapes import Drawing, Rect, String, Line
from reportlab.graphics import renderSVG
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.pagesizes import A4

ROOT = Path(__file__).resolve().parent
URL = 'https://www.workcover.wa.gov.au/wp-content/uploads/2025/12/WorkCover-WA-Annual-Statistical-Report-2024-25-BISstatrep.pdf'
YEARS = ['2021/22', '2022/23', '2023/24', '2024/25p']

def write_csv(name, rows):
    with (ROOT / 'data' / name).open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerows(rows)

def extract(pdf):
    from pypdf import PdfReader
    r = PdfReader(pdf)
    pages = [p.extract_text() or '' for p in r.pages]
    # Anchored table rows, with comma thousands separators and explicit page provenance.
    industries = []
    for line in pages[22].splitlines():
        m = re.fullmatch(r'(.+?)\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)\s*', line)
        if m and m[1].strip() != 'Lost-time claims':
            industries.append([m[1].strip(), *[int(m[i].replace(',', '')) for i in range(2, 6)]])
    if len(industries) != 19:
        raise ValueError(f'Expected 19 industries, extracted {len(industries)}')
    write_csv('industry_claims.csv', [['industry', *YEARS], *industries])
    payment_rows = []
    for line in pages[11].splitlines():
        m = re.fullmatch(r'(.+?)\s+\$([\d,.]+)m\s+\$([\d,.]+)m\s+\$([\d,.]+)m\s+\$([\d,.]+)m\s*', line)
        if m:
            payment_rows.append([m[1].strip(), *[float(m[i].replace(',', '')) for i in range(2, 6)]])
    if len(payment_rows) != 9:
        raise ValueError(f'Expected 9 payment rows, extracted {len(payment_rows)}')
    write_csv('payments_real_aud_m.csv', [['payment_group', *YEARS], *payment_rows])
    # Page 10 totals: validate the complete seven-row days-lost table, not narrative percentages.
    buckets = []
    for line in pages[9].splitlines():
        m = re.fullmatch(r'(0 days|1 - 4 days|5 - 19 days|20 - 59 days|60 - 119 days|120 - 179 days|180\+ days|All claims)\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)', line)
        if m:
            buckets.append([m[1], *[int(m[i].replace(',', '')) for i in range(2, 6)]])
    if len(buckets) != 8:
        raise ValueError('Days-lost table extraction failed')
    write_csv('claim_buckets.csv', [['days_lost', *YEARS], *buckets])
    (ROOT / 'data' / 'provenance.json').write_text(json.dumps({
        'source_url': URL, 'publication': 'November 2025',
        'data_extract': '2025-09-17', 'analysed': '2026-11-25',
        'source_sha256': hashlib.sha256(Path(pdf).read_bytes()).hexdigest(),
        'pages': {'industry_claims.csv': 23, 'payments_real_aud_m.csv': 12, 'claim_buckets.csv': 10},
        'scope': 'WA scheme; latest year provisional; not Suncorp portfolio data'
    }, indent=2), encoding='utf-8')

def load(name):
    with (ROOT / 'data' / name).open(encoding='utf-8') as f:
        rows = list(csv.reader(f))
    return {r[0]: [float(v) for v in r[1:]] for r in rows[1:]}

def chart(title, labels, values, fmt, signed=False, foot=''):
    # Horizontal bars retain long industry names and explicit units.
    height = 48 + len(labels) * 27 + 25
    d = Drawing(490, height)
    d.add(String(0, height-15, title, fontName='Helvetica-Bold', fontSize=10))
    maxv = max(abs(v) for v in values) or 1
    start = 205
    for i, (label, v) in enumerate(zip(labels, values)):
        y = height - 47 - i*27
        d.add(String(0, y+3, label, fontName='Helvetica', fontSize=8))
        width = abs(v)/maxv*205
        d.add(Rect(start, y, width, 13, fillColor=colors.HexColor('#24556b' if v>=0 else '#ad593d'), strokeColor=None))
        d.add(String(start+width+5, y+3, fmt(v), fontName='Helvetica', fontSize=8))
    for j,line in enumerate(reversed(foot.splitlines())):
        d.add(String(0, 5+j*10, line, fontName='Helvetica', fontSize=7, fillColor=colors.HexColor('#555555')))
    return d

def payment_chart(ranked_payments, total, increase):
    d=Drawing(490,325)
    d.add(String(0,310,'Annual payment increase and its components (inflation-adjusted AUD)',fontName='Helvetica-Bold',fontSize=10))
    d.add(String(0,293,f'Total payments: ${total[-2]:,.1f}m to ${total[-1]:,.1f}m (+{100*increase/total[-2]:.1f}%).',fontName='Helvetica',fontSize=8))
    rows=[('Total increase',increase),*ranked_payments]
    for i,(name,value) in enumerate(rows):
        y=260-i*27-(15 if i else 0)
        width=value/increase*205
        font='Helvetica-Bold' if i==0 else 'Helvetica'
        d.add(String(0,y+3,name,fontName=font,fontSize=8))
        d.add(Rect(205,y,width,13,fillColor=colors.HexColor('#253e49' if i==0 else '#24556b'),strokeColor=None))
        label=f'${value:.1f}m'
        if name=='Income payments':label+=f' ({100*value/increase:.1f}%)'
        d.add(String(210+width,y+3,label,fontName=font,fontSize=8))
    d.add(Line(0,249,490,249,strokeColor=colors.HexColor('#d9d9d9'),strokeWidth=.5))
    notes=[
      '* Includes other treatment services.',
      'Source: WorkCover WA Annual Statistical Report 2024/25, p12.'
    ]
    for j,line in enumerate(notes):
        d.add(String(0,40-j*10,line,fontName='Helvetica',fontSize=7,fillColor=colors.HexColor('#555555')))
    return d

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--source-pdf'); args=ap.parse_args()
    (ROOT/'data').mkdir(exist_ok=True); (ROOT/'outputs').mkdir(exist_ok=True)
    if args.source_pdf: extract(args.source_pdf)
    ind=load('industry_claims.csv'); pay=load('payments_real_aud_m.csv'); buckets=load('claim_buckets.csv')
    sums=[sum(v[i] for v in ind.values()) for i in range(4)]
    lost=[sum(v[i] for k,v in buckets.items() if k not in ['0 days','All claims']) for i in range(4)]
    allclaims=buckets['All claims']
    assert all(allclaims[i] == lost[i]+buckets['0 days'][i] for i in range(4))
    assert sums[2:] == lost[2:], 'Industry totals must reconcile for latest two years'
    assert lost == [14902,15518,16735,18014]
    total=pay['Total claim payments']; growth=total[-1]-total[-2]
    categories=['Income payments','Lump sums','Medical & hospital','Allied health*','Workplace rehabilitation','Legal & miscellaneous']
    increments=[pay[k][-1]-pay[k][-2] for k in categories]
    # Audit the displayed one-decimal figures; allow at most AUD 0.1m per year.
    payment_sum_differences=[round(sum(pay[k][i] for k in categories)-total[i],1) for i in range(4)]
    assert all(abs(d)<=0.1+1e-8 for d in payment_sum_differences), 'Annual payment reconciliation exceeds AUD 0.1m'
    assert abs(sum(increments)-growth)<1e-8, 'Latest annual payment increments must reconcile'
    ranked=sorted(((k,v[-1]-v[-2]) for k,v in ind.items()),key=lambda x:x[1],reverse=True)
    delta=lost[-1]-lost[-2]
    metrics={'lost_time_yoy_pct':100*delta/lost[-2], 'lost_time_increase':delta,
      'total_in_scope_claims_yoy_pct':100*(allclaims[-1]/allclaims[-2]-1),
      'total_payments_yoy_pct':100*growth/total[-2], 'income_payment_growth_contribution_pct':100*increments[0]/growth,
      'top_three_industry_growth_share_pct':100*sum(v for _,v in ranked[:3])/delta,
      'industry_sum_2022_23':sums[1], 'overall_lost_time_2022_23':lost[1],
      'payment_categories_minus_total_aud_m_by_year':dict(zip(['2021/22','2022/23','2023/24','2024/25p'],payment_sum_differences)),
      'annual_payment_reconciliation_tolerance_aud_m':0.1}
    out=ROOT/'outputs'
    (out/'metrics.json').write_text(json.dumps(metrics,indent=2),encoding='utf-8')
    write_csv('industry_growth.csv',[['industry','change_2023_24_to_2024_25p','share_of_net_increase_pct'],*[ [k,int(v),round(100*v/delta,4)] for k,v in ranked]])
    comparison=[['Claim category','2023/24','2024/25p','Change','Change %']]
    for label, values in [('Lost-time',lost),('No lost-time',buckets['0 days']),('Total in-scope',allclaims)]:
        a,b=values[-2:]
        comparison.append([label,f'{a:,.0f}',f'{b:,.0f}',f'{b-a:+,.0f}',f'{100*(b/a-1):+.1f}%'])
    write_csv('claim_category_comparison.csv',comparison)
    findings=[
      f'Lost-time claims rose {metrics["lost_time_yoy_pct"]:.1f}% year on year, while in-scope total claims fell {(1-allclaims[-1]/allclaims[-2])*100:.1f}%. These populations must be distinguished.',
      f'Health care, mining and transport contributed {metrics["top_three_industry_growth_share_pct"]:.1f}% of the net increase in lost-time claims. Counts do not measure exposure-adjusted risk.',
      f'Inflation-adjusted payments rose {metrics["total_payments_yoy_pct"]:.1f}%. Income replacement contributed {metrics["income_payment_growth_contribution_pct"]:.1f}% of that increase. Payment-year flows are not lodgement-cohort severity.'
    ]
    checks=[
      'On page 10, the source describes lost-time claims rising from 14,902 in 2021/22 to 18,014 in 2024/25p as a 9.3% increase. Those counts imply 20.9%. This analysis uses the table counts; the latest annual increase remains 7.6%.',
      'For 2022/23 lost-time claims, the industry table on page 23 reports 15,517, while the days-lost table on page 10 implies 15,518. The reason for this one-claim difference is unknown. Both tables agree for 2023/24 and 2024/25p, the years used for the industry-growth chart.',
      'On page 12, the six payment categories for 2022/23 sum to $1,314.0m, versus the published total of $1,314.1m. This $0.1m difference is consistent with rounding; the checks allow up to $0.1m per year. The latest annual component increases sum to $235.8m, matching the total increase.'
    ]
    ranked_payments=sorted(zip(categories,increments),key=lambda item:item[1],reverse=True)
    charts=[chart('Largest contributions to annual lost-time claim growth',[k for k,_ in ranked[:5]],[v for _,v in ranked[:5]],lambda x:f'+{x:,.0f}',foot='Change from 2023/24 to 2024/25p; counts, not frequency rates.\nSource: WorkCover WA Annual Statistical Report 2024/25, p23.'),
      payment_chart(ranked_payments,total,growth)]
    for i,d in enumerate(charts,1): renderSVG.drawToFile(d,str(out/f'chart_{i}.svg'))
    ss=getSampleStyleSheet(); ss.add(ParagraphStyle(name='SmallText',fontName='Helvetica',fontSize=8,leading=11,spaceAfter=6))
    ss['Title'].fontSize=20; ss['Title'].leading=23; ss['Title'].alignment=TA_LEFT
    ss['BodyText'].fontSize=9;ss['BodyText'].leading=12;ss['BodyText'].spaceAfter=8
    story=[Paragraph('WA workers compensation monitoring',ss['Title']),Paragraph('Independent portfolio case study | 25 November 2026 | Zule Yu with AI assistance',ss['SmallText']),Paragraph('Where should a portfolio analyst investigate changes in claims activity and payments?',ss['Heading2'])]
    for f in findings:story.append(Paragraph(f,ss['BodyText']))
    comparison_table=Table(comparison,colWidths=[155,80,85,80,90],hAlign='LEFT')
    comparison_table.setStyle(TableStyle([
      ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTNAME',(0,1),(-1,-1),'Helvetica'),
      ('FONTSIZE',(0,0),(-1,-1),8),('LEADING',(0,0),(-1,-1),11),
      ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e9eef1')),
      ('GRID',(0,0),(-1,-1),.4,colors.HexColor('#d9d9d9')),
      ('ALIGN',(1,1),(-1,-1),'RIGHT'),('VALIGN',(0,0),(-1,-1),'MIDDLE'),
      ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
    story.extend([comparison_table,Spacer(1,5),Paragraph('Source: WorkCover WA Annual Statistical Report 2024/25, p10. Total = lost-time + no lost-time. Latest year provisional. Payment totals supporting the 16.7% increase are shown on page 2 of this analysis.',ss['SmallText'])])
    payment_comparison=[['Payments (real AUD m)','2023/24','2024/25p','Increase','Change %']]
    for label,key in [('Total payments','Total claim payments'),('Income payments','Income payments')]:
        a,b=pay[key][-2:]
        payment_comparison.append([label,f'{a:,.1f}',f'{b:,.1f}',f'{b-a:,.1f}',f'+{100*(b/a-1):.1f}%'])
    write_csv('payment_comparison.csv',payment_comparison)
    payment_table=Table(payment_comparison,colWidths=[155,80,85,80,90],hAlign='LEFT')
    payment_table.setStyle(TableStyle([
      ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTNAME',(0,1),(-1,-1),'Helvetica'),
      ('FONTSIZE',(0,0),(-1,-1),8),('LEADING',(0,0),(-1,-1),11),
      ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e9eef1')),
      ('GRID',(0,0),(-1,-1),.4,colors.HexColor('#d9d9d9')),
      ('ALIGN',(1,1),(-1,-1),'RIGHT'),('VALIGN',(0,0),(-1,-1),'MIDDLE'),
      ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
    story.extend([Spacer(1,10),charts[0],Spacer(1,4),Paragraph('The report does not provide an industry breakdown of the decline in no-lost-time claims.',ss['SmallText'])])
    story.append(Paragraph('Checks against the source report',ss['Heading2']))
    story.append(Paragraph('The following checks refer to WorkCover WA\'s Annual Statistical Report 2024/25.',ss['SmallText']))
    for c in checks:story.append(Paragraph(c,ss['BodyText']))
    story.extend([PageBreak(),Paragraph('Payments and analytical judgement',ss['Title']),charts[1],Spacer(1,8)])
    story.append(Paragraph('Recommended follow-up',ss['Heading2']))
    follow_up=[
      '<b>Explain the shift in claim mix.</b> Why did lost-time claims rise while no-lost-time and total claims fell? Check injury types, hours worked by industry, reporting changes and whether provisional claims later change category.',
      '<b>Explain the income-payment increase.</b> Separate the number of workers receiving payments, weeks paid and average weekly amounts. Check which factors account for the additional $145.5m.',
      '<b>Test the connection.</b> Track the same groups of claims over time to see whether more lost-time claims or longer absences contributed to higher income payments. Separate new from older claims; annual totals alone cannot establish this link.'
    ]
    for text in follow_up:story.append(Paragraph(text,ss['BodyText']))
    story.append(Paragraph('Scope and limitations',ss['Heading2']))
    scope=[
      'These are public WA workers compensation scheme figures, not Suncorp portfolio results. The source uses data as at 17 September 2025. Its 2024/25 figures are provisional: later information about claims may change them. This is a historical snapshot, not evidence of conditions in November 2026.',
      'Claims are grouped by the financial year they were lodged. Payments are grouped by the financial year the money was paid, including payments on older claims, and are adjusted for inflation. Dividing annual payments by newly lodged claims would therefore mix different groups of claims and would not measure their average claim cost.',
      'This analysis includes neither premiums nor measures of insured activity, such as wages or hours worked. It cannot establish claims costs relative to premiums, profitability, or claims per unit of insured activity. WA\'s Workers Compensation and Injury Management Act 2023 took effect on 1 July 2024; this analysis does not isolate any effect of that change.'
    ]
    for text in scope:story.append(Paragraph(text,ss['BodyText']))
    story.append(Paragraph('Source: WorkCover WA, Annual Statistical Report 2024/25, pp 2, 4, 10, 12, 23 and glossary pp 40-42. Derived analysis is independent and is not attributable to WorkCover WA.',ss['SmallText']))
    story.append(Paragraph(f'<link href="{URL}" color="#24556b">Open the original WorkCover WA Annual Statistical Report 2024/25</link>',ss['SmallText']))
    SimpleDocTemplate(str(out/'WA_Workers_Compensation_Analysis.pdf'),pagesize=A4,rightMargin=48,leftMargin=48,topMargin=38,bottomMargin=38).build(story)
    md_table='\n'.join(['| '+' | '.join(row)+' |' for row in [comparison[0],['---']*5,*comparison[1:]]])
    payment_md='\n'.join(['| '+' | '.join(row)+' |' for row in [payment_comparison[0],['---']*5,*payment_comparison[1:]]])
    report='# Findings\n\n'+'\n\n'.join(findings)+'\n\n## Claim category comparison\n\n'+md_table+'\n\nSource: original report p10.\n\n## Payment comparison\n\n'+payment_md+'\n\nSource: original report p12; real AUD millions. Income payments contributed 145.5 / 235.8 = 61.7% of the total increase.\n\n## Recommended follow-up\n\n'+'\n\n'.join(re.sub('<[^>]+>','',t) for t in follow_up)+'\n\n## Data checks\n\n'+'\n\n'.join(checks)
    report+='\n\n## Scope and limitations\n\n'+'\n\n'.join(scope)
    (out/'FINDINGS.md').write_text(report,encoding='utf-8')
    print(json.dumps(metrics,indent=2));print('Reconciliation checks passed; source exceptions recorded.')

if __name__=='__main__':main()
