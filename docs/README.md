# docs/

`RoadMind_Technical_Report.docx` — the full technical specification & final project report (23 pages),
covering: problem statement, deviations from the original proposal, dataset & EDA, preprocessing/feature
engineering, provider-fingerprint removal, modeling methodology, real held-out evaluation results, SHAP
explainability, robustness checks, system architecture (backend + frontend), UI walkthrough, testing,
limitations, future work, and references. Every number in it is real, pulled from `reports/*` and the
live application — nothing is illustrative or fabricated.

`RoadMind_Technical_Report.pdf` — the same report, pre-rendered to PDF (handy if your faculty submission
portal wants a PDF instead of / alongside the .docx).

**Before submitting:** fill in the cover-page placeholders (`[Student Name]`, `[Roll Number / Course Code]`,
`[Faculty / Advisor Name]`, `[Institution Name]`, `[Submission Date]`), and refresh the Table of Contents
field (right-click it → Update Field, or Ctrl+A then F9) — Word shows it as a placeholder until opened
and refreshed once.

`assets/` — the real charts and screenshots embedded in the report (copied from `reports/eda/`,
`reports/eval/`, `reports/shap/`, and live screenshots of the running dashboard).

`build_report.js` — the docx-js script that generates the report. Regenerate after any change to the
underlying results with:
```bash
NODE_PATH=<path to a node_modules containing the `docx` package> node docs/build_report.js
```
