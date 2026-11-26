# WA workers compensation monitoring

An independent, AI-assisted case study of public WA workers compensation data, prepared to practise portfolio performance analysis. It is not commissioned by Suncorp or EY and uses no Suncorp customer data.

Start with [the final two-page analysis](outputs/WA_Workers_Compensation_Analysis_Styled.pdf), [computed findings](outputs/FINDINGS.md) and [metrics](outputs/metrics.json). The [original report layout](outputs/WA_Workers_Compensation_Analysis.pdf) is retained for reference. The final edition uses the same data and findings with a clearer visual hierarchy.

An additional [EY-inspired visual edition](outputs/WA_Workers_Compensation_Analysis_EY.pdf) presents the same analysis using charcoal, yellow and square panels. It is an independent work sample, not an EY publication. Both existing report layouts remain available.

## Question

Which changes in claims activity and payments warrant further investigation, and what can the published aggregates actually establish?

## Reproduce

Use Python 3.10 or later:

```sh
python -m pip install -r requirements.txt
python analyse.py
python style_report.py
python style_report_ey.py
```

To extract the source tables again, download the original PDF and run:

```sh
python analyse.py --source-pdf /path/to/WorkCover-WA-Annual-Statistical-Report-2024-25-BISstatrep.pdf
```

`style_report.py` generates the final styled edition after the analysis outputs are available. It uses Arial on Windows when installed, with a Helvetica fallback elsewhere. Both versions remain two-page reports with selectable text.

`style_report_ey.py` generates the additional charcoal-and-yellow edition without overwriting either existing PDF. It reuses the content and layout functions in `style_report.py`. The palette and typography hierarchy are informed by [EY Australia's designed Transparency Report 2026](https://www.ey.com/content/dam/ey-unified-site/ey-com/en-au/pdfs/ey-au-transparency-report-fy26.pdf). Arial is used as an available substitute for the report's EY Interstate typeface; no EY logo or proprietary font is embedded.

No credentials, API keys or live AI service are needed. Checked-in CSVs support offline reproduction. Extraction fails if table row counts change. Reconciliation checks verify the latest industry totals against the days-lost table. For the six payment categories, the annual reconciliation allows a maximum AUD 0.1m difference from the published total: the only observed difference is -AUD 0.1m in 2022/23, consistent with rounding of displayed values. The latest annual component increases must sum to the total increase, with only floating-point precision allowed. Yearly differences and the tolerance are recorded in `outputs/metrics.json`. SVG charts, metrics and PDF are generated deterministically from these CSVs.

## Data and definitions

Source: [WorkCover WA Annual Statistical Report 2024/25](https://www.workcover.wa.gov.au/wp-content/uploads/2025/12/WorkCover-WA-Annual-Statistical-Report-2024-25-BISstatrep.pdf). Published November 2025; data extracted by WorkCover WA on 17 September 2025. Acknowledgment: WorkCover WA, Government of Western Australia. The publication permits copying with acknowledgment; third-party source material is not relicensed by this repository. The source PDF is not bundled.

CSV provenance: `claim_buckets.csv` p10; `payments_real_aud_m.csv` p12; `industry_claims.csv` p23. `industry_growth.csv` is derived. Original file hash is recorded in `data/provenance.json`.

- Lost-time claims involve at least one day or shift off work. Counts use lodgement year.
- Payments are transaction-year cash flows, including older claims, and are inflation-adjusted in the source table used here.
- The latest year is provisional as at the source's 17 September 2025 data snapshot; later claim information may change the figures. This static report does not update automatically. The Workers Compensation and Injury Management Act 2023 commenced 1 July 2024; this analysis does not isolate its effects.
- This is a historical snapshot, not the most recent available scheme update.
- Counts are not exposure-adjusted frequency. Cash payments divided by newly lodged claims are not cohort severity. No loss ratio or profitability estimate is made.

## Analytical workflow

1. Read definitions and source tables, including narrative/table discrepancies.
2. Extract typed values with page provenance.
3. Reconcile totals and retain exceptions explicitly.
4. Calculate annual movements and contribution to net growth.
5. Generate charts and a short management interpretation.
6. Specify the additional data needed to test explanations.

## Authorship and AI use

Prepared by Zule Yu with substantial assistance from an AI coding agent for extraction code, calculations, charting and drafting. The repository makes the method and checks visible. The project is an educational work sample, not evidence of independent production engineering or paid portfolio-analysis experience. Review and understanding of the outputs remain necessary before using it in an application discussion.
