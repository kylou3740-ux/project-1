# Apple Inc. (AAPL) — FIN 43900 Project 1 Model

## Decision context
- Intended user: buy-side investment committee with no current position.
- Target: Apple Inc. (NASDAQ: AAPL), common equity.
- Thesis: **WATCH / DEFER** pending stronger evidence on sustainable growth, cash-flow conversion, and Greater China demand.
- Market reference: $326.57 close on September 10, 2026
- Currency / units: USD; model amounts are USD millions except per-share data.
- Horizon: five explicit forecast years, FY2026E–FY2030E.

## Files
- `model.py` — forecast engine, FCFF DCF, sensitivity, reverse DCF, checks.
- `app.py` — local Streamlit driver panel, forecast tables, valuation and validation.
- `docs/assumption-challenge.md` — driver basis, challenge questions and evidence needed.
- `docs/validation-and-ai-use.md` — validation record draft and mandatory human-authored changed-input record placeholder.

## Model architecture
1. FY2025 opening balances anchor the pro forma.
2. Revenue growth and Services mix drive revenue and blended gross margin.
3. The income statement calculates EBIT, interest, tax and net income.
4. Inventory and other working-capital proxy, PP&E, debt, equity and cash roll forward to the balance sheet.
5. The cash-flow statement links net income, D&A, working capital, capex, debt repayment and buybacks to ending cash.
6. FCFF is calculated from NOPAT + D&A − capex − change in working capital.
7. DCF discounts the five forecast FCFFs at WACC and adds a Gordon-growth terminal value. Enterprise value is bridged to equity using cash and marketable securities less debt, then divided by diluted shares.

## Controls
The interface exposes bounded revenue growth, Services mix step, segment margins, SG&A ratio, capex, WACC and terminal growth. The accounting engine and checks are not editable. The reset button restores base assumptions. WACC must exceed terminal growth.

### Comparable-company valuation methodology

The EV/EBITDA cross-check applies Microsoft and Alphabet peer multiples to Apple's trailing-twelve-month (TTM) EBITDA, rather than Apple's forecast FY2026 EBITDA. Apple's TTM EBITDA is calculated from reported financial statements for the twelve months ending June 27, 2026.

Apple's cash and marketable securities, debt, and diluted share-count inputs use the latest financial information available for the valuation analysis, with the diluted share count treated as a proxy rather than an exact point-in-time count.

The Microsoft and Alphabet EV/EBITDA multiples remain provisional until their valuation dates, trailing EBITDA definitions, and enterprise-value adjustments are verified. 

## Reproducibility and tests
Run `py -m unittest discover -s tests -v` to run the model tests. 

## Market-data references carried into the model
- Microsoft EV/EBITDA: https://finbox.com/NASDAQGS:MSFT/explorer/ev_to_ebitda_ltm/
- Alphabet EV/EBITDA: https://finbox.com/NASDAQGS:GOOG/explorer/ev_to_ebitda_ltm/.
