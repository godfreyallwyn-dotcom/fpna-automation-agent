# FP&A Agent - from raw ERP export to MIS deck with one command

An agentic finance-planning workflow. Drop in the month's input files, run one command, and it produces:

| Deliverable | What it is |
|---|---|
| `output/FPnA_Pack_*.xlsx` | 11-sheet Excel pack. Inputs are blue, everything derived is a **live formula** (flag thresholds and scenario shocks are editable) |
| `output/powerbi/` | Star-schema CSVs + DAX measures + setup guide. Connect Power BI once; every later run is just *Refresh* |
| `output/FPnA_MIS_Deck_*.pptx` | 9-slide MIS deck with native (editable) charts, EBITDA bridge, outlook and scenarios |
| `output/agent_trace.md` | Every tool call the agent made, why, and what came back |

```bash
pip install -r requirements.txt
python run.py                # sample data is generated automatically on first run
python run.py --input my_data/ --output out/      # your own files (same layout as data/input)
python run.py --no-llm       # force offline mode
python -m unittest discover -s tests
```

## The workflow (what a finance team does every month)

```
Raw inputs -> data-quality checks -> clean & map to P&L -> reconcile to ERP control totals
   -> driver-based budget -> variance vs budget & PY (materiality flags) -> root-cause drill-downs
   -> back-tested forecast -> scenarios -> commentary -> Excel + Power BI + deck
```

## Automation vs. generative AI vs. agentic (and where each is used here)

- **Automation** - fixed code: cleaning, budget maths, variances, forecasting. All numbers come from here.
- **Generative AI** - an LLM writes the commentary. It only receives a pre-computed fact sheet, and **every number in its text is verified against that sheet**; a sentence with an unknown number is rejected and replaced by a template.
- **Agentic** - a planner chooses which tool to call next from observations. Examples in this repo:
  - It picks the data-fix list from what the quality scan finds, and **retries with more fixes if reconciliation fails**.
  - It drills into **only the lines that breach materiality**.
  - If a drill-down shows a variance is a **one-off** (>=60% in a single month), it overrides the forecast method so the spike is not extrapolated.
  - Forecast method per line is **chosen by back-test**, not assumed.

Two interchangeable planners (`fpna_agent/planners.py`):
1. `RulePlanner` - deterministic policy that reacts to tool observations. Runs offline, no API key.
2. `LLMPlanner` - Claude chooses tools via tool-use (set `ANTHROPIC_API_KEY`, optional `FPNA_MODEL`). If the API fails mid-run, the agent falls back to the rule planner; if the LLM tries to finish early, a safety net completes the missing steps. Tool prerequisites are enforced in code, so the LLM cannot skip a control.

## Layout

```
run.py                     one-command entrypoint
fpna_agent/
  agent.py                 observe -> think -> act loop, safety net, trace
  planners.py              RulePlanner + LLMPlanner
  tools/                   ingest, budget, variance (+drill-down), forecast (+scenarios), commentary
  reports/                 excel_pack.py, deck.py, powerbi.py
  finance.py, sample_data.py, llm.py (stdlib-only API client)
tests/                     pipeline, guardrail, scripted-LLM and safety-net tests
```

## Input files (`data/input/`)

`gl_actuals.csv` (INR, deliberately messy), `chart_of_accounts.csv`, `control_totals.csv`, `budget_revenue_drivers.csv`,
`budget_headcount_plan.csv`, `budget_fixed_costs.csv`, `sales_volume_actuals.csv`, `headcount_actuals.csv`.
The sample GL contains duplicate journals, mixed period formats, comma-formatted text amounts, stray whitespace, a blank row
and an account missing from the chart of accounts - the agent finds and fixes all of them and proves the result ties to control totals.

## Honest notes

- All data is synthetic (a fictional consumer-goods company, Indian FY Apr-Mar, INR Lakhs).
- Power BI: Python cannot author a `.pbix`; it produces the model-ready data and DAX, you build the report once.
- Excel formulas calculate when opened in Excel. (The shipped sample file was recalculated with LibreOffice so previewers show values.)
- The LLM planner/commentary path is covered by tests using a scripted fake transport; it has not been exercised against the live API in this repo's CI.
- Forecasting is intentionally simple and explainable (seasonal-YoY, run-rate, moving average, median) rather than a black box.
- To adapt: change `fy_start_month`, thresholds and scenario shocks in `fpna_agent/config.py`; map your own accounts in `chart_of_accounts.csv`.
