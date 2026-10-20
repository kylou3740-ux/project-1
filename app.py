import streamlit as st
import pandas as pd
import model

st.set_page_config(page_title="Apple Valuation Workbench", layout="wide")
st.title("Apple Inc. (AAPL) — Valuation Workbench")
st.caption("FIN 43900 Project 1")
st.info("Decision context: the current research thesis is WATCH / DEFER. The tool presents a model-based range and tests assumptions; it does not make the investment decision automatically.")

if "overrides" not in st.session_state:
    st.session_state.overrides = {}
if st.sidebar.button("Reset to base assumptions"):
    st.session_state.overrides = {}

a = model.BASE
st.sidebar.header("Bounded driver panel")
with st.sidebar.form("drivers"):
    rg = st.slider("Annual revenue growth (%)", 0.0, 6.0, float(st.session_state.overrides.get("revenue_growth", a["revenue_growth"]))*100, 0.25, format="%.2f")
    mix = st.slider("Annual Services-mix increase (percentage points)", 0.0, 1.6, float(st.session_state.overrides.get("services_mix_step", a["services_mix_step"]))*100, 0.1, format="%.1f")
    pgm = st.slider("Product gross margin (%)", 34.0, 39.0, float(st.session_state.overrides.get("product_gross_margin", a["product_gross_margin"]))*100, 0.5, format="%.1f")
    sgm = st.slider("Services gross margin (%)", 70.0, 80.0, float(st.session_state.overrides.get("services_gross_margin", a["services_gross_margin"]))*100, 1.0, format="%.0f")
    sga = st.slider("SG&A / gross profit (%)", 13.0, 16.0, float(st.session_state.overrides.get("sga_to_gross_profit", a["sga_to_gross_profit"]))*100, 0.25, format="%.2f")
    capex = st.slider("Annual capital spending ($ millions)", 9000, 14000, int(st.session_state.overrides.get("capital_spending", a["capital_spending"])), 500)
    wacc = st.slider("WACC (%)", 8.0, 12.0, float(st.session_state.overrides.get("wacc", a["wacc"]))*100, 0.25, format="%.2f")
    tg = st.slider("Terminal growth (%)", 1.5, 3.5, float(st.session_state.overrides.get("terminal_growth", a["terminal_growth"]))*100, 0.25, format="%.2f")
    submitted = st.form_submit_button("Apply drivers")
if submitted:
    st.session_state.overrides = {"revenue_growth": rg/100, "services_mix_step": mix/100,
        "product_gross_margin": pgm/100, "services_gross_margin": sgm/100,
        "sga_to_gross_profit": sga/100, "capital_spending": float(capex),
        "wacc": wacc/100, "terminal_growth": tg/100}

try:
    report = model.run_report(st.session_state.overrides)
except ValueError as e:
    st.error(f"Input combination rejected: {e}")
    st.stop()
a, rows, dcf = report["assumptions"], report["forecast"], report["dcf"]
base_report = model.run_report()
base_value = base_report["dcf"]["value_per_share"]
lo = min(model.dcf_value(rows, a, wacc=x, terminal_growth=a["terminal_growth"])["value_per_share"] for x in [0.08, 0.09, a["wacc"], 0.11, 0.12] if x > a["terminal_growth"])
hi = max(model.dcf_value(rows, a, wacc=x, terminal_growth=a["terminal_growth"])["value_per_share"] for x in [0.08, 0.09, a["wacc"], 0.11, 0.12] if x > a["terminal_growth"])
col1, col2, col3, col4 = st.columns(4)
col1.metric("Base / selected DCF", f"${dcf['value_per_share']:.2f}", f"{dcf['value_per_share']-base_value:+.2f} vs base")
col2.metric("PV terminal value / EV", f"{dcf['terminal_value_share']:.1%}")
col3.metric("Reference market price", f"${a['market_price']:.2f}", a["market_price_date"])
col4.metric("Sensitivity span (WACC grid)", f"${lo:.0f}–${hi:.0f}")

st.subheader("Five-year forecast")
forecast_fields = [
 ("Income statement", "revenue", "Revenue"), ("Income statement", "gross_profit", "Gross profit"),
 ("Income statement", "operating_income", "Operating income / EBIT"), ("Income statement", "net_income", "Net income"),
 ("Cash flow", "cfo", "Cash from operations"), ("Cash flow", "cfi", "Cash from investing"),
 ("Cash flow", "cff", "Cash from financing"), ("Cash flow", "net_change_cash", "Net change in cash"),
 ("Cash flow", "fcff", "Free cash flow to firm"), ("Balance sheet", "cash", "Cash"),
 ("Balance sheet", "total_assets", "Total assets"), ("Balance sheet", "total_liabilities", "Total liabilities"),
 ("Balance sheet", "equity", "Shareholders' equity"), ("Checks", "balance_gap", "Assets − liabilities − equity"),
]
tab = pd.DataFrame({label: [rows[y][key] for y in model.YEARS] for _, key, label in forecast_fields}, index=[f"FY{y}E" for y in model.YEARS]).T
st.dataframe(tab.style.format("{:,.1f}"), width="stretch")

st.subheader("Valuation methods")
left, right = st.columns(2)
with left:
    st.markdown("**FCFF DCF**")
    st.write(f"Enterprise value: ${dcf['enterprise_value']:,.0f} million")
    st.write(f"Equity value: ${dcf['equity_value']:,.0f} million")
    st.write(f"Value per diluted share: ${dcf['value_per_share']:.2f}")
    st.write(f"Terminal value at FY2030: ${dcf['terminal_value']:,.0f} million")
with right:
    st.markdown("**Equity P/E reference cross-check**")
    comps = report["comps"]
    st.write(f"Low reference ({comps['low_pe']:.2f}×): ${comps['low_value']:.2f}/share")
    st.write(f"High reference ({comps['high_pe']:.2f}×): ${comps['high_value']:.2f}/share")
    st.markdown("**Enterprise-value multiple cross-check (EV/EBITDA)**")
    st.write(f"Microsoft {comps['low_ev_ebitda']:.2f}× → ${comps['ev_ebitda_low_value']:.2f}/share")
    st.write(f"Alphabet {comps['high_ev_ebitda']:.2f}× → ${comps['ev_ebitda_high_value']:.2f}/share")
    st.caption(comps["ev_ebitda_method"])

st.subheader("WACC × terminal-growth sensitivity")
sens = pd.DataFrame(report["sensitivity"])
pivot = sens.pivot(index="wacc", columns="terminal_growth", values="value_per_share")
pivot.index = [f"{x:.2%}" for x in pivot.index]
pivot.columns = [f"{x:.2%}" for x in pivot.columns]
st.dataframe(pivot.style.format("${:,.2f}"), width="stretch")

st.subheader("Reverse DCF")
rev = report["reverse_dcf"]
if rev["solved"]:
    st.write(f"To match ${rev['target_price']:.2f}, the model requires a uniform {rev['fcff_growth_shift']:+.2%} shift to the annual FCFF growth path, under fixed WACC, terminal growth, net cash and diluted shares.")
    st.write("Implied FCFF growth rates: " + ", ".join(f"{x:.1%}" for x in rev["implied_fcff_growth_rates"]))
else:
    st.write(rev["message"])
    st.write(f"Value at lower bound: ${rev['lower_value']:.2f}; at upper bound: ${rev['upper_value']:.2f}.")

st.subheader("Validation checks")
for name, passed in report["checks"].items():
    (st.success if passed else st.error)(f"{'PASS' if passed else 'FAIL'} — {name.replace('_', ' ')}")
if not all(report["checks"].values()):
    st.error("At least one validation check failed. Do not rely on the valuation until the failure is understood.")

st.subheader("Assumption audit")
st.markdown("Each assumption is a judgment with a basis and a challenge condition. Update this record with the exact filing/page/table references you personally verify before submission.")
st.dataframe(pd.DataFrame([
 {"Driver":"Revenue growth", "Base":f"{a['revenue_growth']:.1%}", "Basis":"FY2023–FY2025 reported revenue CAGR used in Lab 10", "Challenge / evidence to change":"A refreshed multi-year filing history or material evidence of a structural growth change"},
 {"Driver":"Services mix step", "Base":f"{a['services_mix_step']:.1%} pp/year", "Basis":"Lab 10 assumption; Services share of FY2025 revenue", "Challenge / evidence to change":"Services growth/mix data or regulation/pricing evidence contradicts continued mix gains"},
 {"Driver":"Gross margins", "Base":f"Product {a['product_gross_margin']:.1%}; Services {a['services_gross_margin']:.1%}", "Basis":"Historical segment margin judgment from Lab 10", "Challenge / evidence to change":"Segment margins, product mix, pricing, component costs or services economics shift"},
 {"Driver":"Capital spending", "Base":f"${a['capital_spending']:,.0f}m", "Basis":"Approximate three-year capex level used in prior coursework", "Challenge / evidence to change":"New 10-K/10-Q capex trend or capacity investment plans"},
 {"Driver":"WACC / terminal growth", "Base":f"{a['wacc']:.2%} / {a['terminal_growth']:.2%}", "Basis":"WACC from prior DCF reconstruction; terminal growth is a long-run judgment", "Challenge / evidence to change":"Updated Treasury yield, equity risk premium, beta, capital structure or long-run growth evidence"},
]), width="stretch")
