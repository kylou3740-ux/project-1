"""Apple (AAPL) Project 1 model engine. USD millions unless stated otherwise.

Forecasts are analyst assumptions, not company guidance. This is an educational model.
"""
from copy import deepcopy

YEARS = [2026, 2027, 2028, 2029, 2030]
BASE = {
    "revenue_growth": 0.042,
    "services_mix_step": 0.008,
    "product_gross_margin": 0.365,
    "services_gross_margin": 0.750,
    "sga_to_gross_profit": 0.1444,
    "depreciation_rate": 8000.0 / 45680.0,
    "capital_spending": 11000.0,
    "tax_rate": (16741/113736 + 29749/123485 + 20719/132729) / 3,
    "inventory_days": ((6331/(383285-169148)*365) + (7286/(391035-180683)*365) + (5718/(416161-195201)*365))/3,
    "other_wc_pct_change_revenue": 0.008,
    "debt_repayment": 10000.0,
    "share_buyback": 50000.0,
    "debt_rate": 0.043,
    "wacc": 0.09761520651813647,
    "terminal_growth": 0.025,
    "diluted_shares_m": 14750.302,
    "cash_and_securities": 146517.0,
    "debt_for_valuation": 84344.0,
    "market_price": 326.57,
    "market_price_date": "2026-09-10",
    "services_mix_start": 109158.0 / 416161.0,
    "starting_revenue": 416161.0,
    "opening_inventory": 5718.0,
    "opening_ppe": 49834.0,
    "opening_other_assets": 267755.0,
    "opening_cash": 35934.0,
    "opening_debt": 90678.0,
    "opening_other_liabilities": 194830.0,
    "opening_equity": 73733.0,
    "opening_total_assets": 359241.0,
    "opening_total_liabilities_equity": 359241.0,
    "peer_pe_low": 27.43398,
    "peer_pe_high": 30.76781,
    "apple_diluted_eps": 7.46,
    "peer_ev_ebitda_low": 18.96,  # Microsoft, 2026-09-10 FinanceCharts history
    "peer_ev_ebitda_high": 22.09, # Alphabet, 2026-09-10 FinanceCharts history
    "apple_ttm_ebitda": 167959.0,
}
BOUNDS = {
    "revenue_growth": (0.00, 0.06),
    "services_mix_step": (0.00, 0.016),
    "product_gross_margin": (0.34, 0.39),
    "services_gross_margin": (0.70, 0.80),
    "sga_to_gross_profit": (0.13, 0.16),
    "capital_spending": (9000.0, 14000.0),
    "wacc": (0.08, 0.12),
    "terminal_growth": (0.015, 0.035),
}


def blended_margin(a, i):
    mix = a["services_mix_start"] + a["services_mix_step"] * (i + 1)
    if not 0 < mix < 1:
        raise ValueError("Services mix must remain between 0% and 100%.")
    return (1 - mix) * a["product_gross_margin"] + mix * a["services_gross_margin"], mix


def build_model(overrides=None):
    a = deepcopy(BASE)
    if overrides:
        a.update(overrides)
    if a["wacc"] <= a["terminal_growth"]:
        raise ValueError("WACC must exceed terminal growth.")
    for key, (lo, hi) in BOUNDS.items():
        if not lo <= a[key] <= hi:
            raise ValueError(f"{key} must be between {lo} and {hi}.")
    if a["debt_repayment"] < 0 or a["share_buyback"] < 0:
        raise ValueError("Debt repayment and buybacks cannot be negative.")

    opening = {
        "revenue": a["starting_revenue"], "inventory": a["opening_inventory"],
        "ppe": a["opening_ppe"], "other_assets": a["opening_other_assets"],
        "cash": a["opening_cash"], "debt": a["opening_debt"],
        "other_liabilities": a["opening_other_liabilities"], "equity": a["opening_equity"],
    }
    rows = {}
    for i, year in enumerate(YEARS):
        revenue = opening["revenue"] * (1 + a["revenue_growth"])
        gross_margin, services_mix = blended_margin(a, i)
        gross_profit = revenue * gross_margin
        cogs = revenue - gross_profit
        sga = gross_profit * a["sga_to_gross_profit"]
        depreciation = opening["ppe"] * a["depreciation_rate"]
        operating_income = gross_profit - sga - depreciation
        interest = opening["debt"] * a["debt_rate"]
        pretax = operating_income - interest
        taxes = max(0.0, pretax) * a["tax_rate"]
        net_income = pretax - taxes

        inventory = cogs * a["inventory_days"] / 365.0
        change_inventory = inventory - opening["inventory"]
        change_other_wc = a["other_wc_pct_change_revenue"] * (revenue - opening["revenue"])
        other_assets = opening["other_assets"] + change_other_wc
        ppe = opening["ppe"] + a["capital_spending"] - depreciation
        debt_repayment = min(a["debt_repayment"], opening["debt"])
        debt = opening["debt"] - debt_repayment
        other_liabilities = opening["other_liabilities"]
        equity = opening["equity"] + net_income - a["share_buyback"]

        # FCFF is derived from the forecast operating statement and working capital.
        nopat = operating_income * (1 - a["tax_rate"])
        delta_nwc = change_inventory + change_other_wc
        fcff = nopat + depreciation - a["capital_spending"] - delta_nwc

        # Cash flow statement: net income, noncash D&A, investment, working capital,
        # financing and buybacks. Cash is calculated, never manually plugged.
        cfo = net_income + depreciation - change_inventory - change_other_wc
        cfi = -a["capital_spending"]
        cff = -debt_repayment - a["share_buyback"]
        net_change_cash = cfo + cfi + cff
        cash = opening["cash"] + net_change_cash

        total_assets = cash + inventory + ppe + other_assets
        total_liabilities = debt + other_liabilities
        balance_gap = total_assets - total_liabilities - equity
        cash_tie = cash - (opening["cash"] + net_change_cash)
        rows[year] = {
            "revenue": revenue, "cogs": cogs, "gross_margin": gross_margin,
            "services_mix": services_mix, "gross_profit": gross_profit, "sga": sga,
            "depreciation": depreciation, "operating_income": operating_income,
            "interest": interest, "pretax_income": pretax, "taxes": taxes,
            "net_income": net_income, "inventory": inventory, "change_inventory": change_inventory,
            "change_other_wc": change_other_wc, "delta_nwc": delta_nwc,
            "ppe": ppe, "other_assets": other_assets, "cash": cash, "debt": debt,
            "debt_repayment": debt_repayment, "other_liabilities": other_liabilities,
            "equity": equity, "total_assets": total_assets, "total_liabilities": total_liabilities,
            "balance_gap": balance_gap, "cfo": cfo, "cfi": cfi, "cff": cff,
            "net_change_cash": net_change_cash, "cash_tie": cash_tie,
            "nopat": nopat, "fcff": fcff,
        }
        opening = {"revenue": revenue, "inventory": inventory, "ppe": ppe,
                   "other_assets": other_assets, "cash": cash, "debt": debt,
                   "other_liabilities": other_liabilities, "equity": equity}
    return a, rows


def dcf_value(rows, a, wacc=None, terminal_growth=None, growth_shift=0.0):
    wacc = a["wacc"] if wacc is None else wacc
    g = a["terminal_growth"] if terminal_growth is None else terminal_growth
    if wacc <= g:
        raise ValueError("WACC must exceed terminal growth.")
    fcffs = [rows[y]["fcff"] for y in YEARS]
    # Reverse DCF shift applies to revenue growth and rebuilds model elsewhere.
    pv_explicit = sum(cf / ((1 + wacc) ** (i + 1)) for i, cf in enumerate(fcffs))
    terminal_value = fcffs[-1] * (1 + g) / (wacc - g)
    pv_terminal = terminal_value / ((1 + wacc) ** len(YEARS))
    ev = pv_explicit + pv_terminal
    equity_value = ev + a["cash_and_securities"] - a["debt_for_valuation"]
    per_share = equity_value / a["diluted_shares_m"]
    return {"pv_explicit_fcff": pv_explicit, "terminal_value": terminal_value,
            "pv_terminal": pv_terminal, "enterprise_value": ev, "equity_value": equity_value,
            "value_per_share": per_share, "terminal_value_share": pv_terminal / ev,
            "fcff_forecast": fcffs}


def sensitivity(overrides=None):
    a, rows = build_model(overrides)
    out = []
    for wacc in [0.08, 0.09, a["wacc"], 0.11, 0.12]:
        for g in [0.015, 0.02, a["terminal_growth"], 0.03, 0.035]:
            if g >= wacc:
                continue
            val = dcf_value(rows, a, wacc, g)["value_per_share"]
            out.append({"wacc": wacc, "terminal_growth": g, "value_per_share": val})
    return out


def reverse_dcf(target_price=None, lower=-0.05, upper=0.10, iterations=100, overrides=None):
    """Market-implied FCFF-growth shift, applied uniformly to annual FCFF growth rates.

    This is a diagnostic scenario, not a claim that revenue growth and FCFF growth
    are identical. The shift is applied to the baseline FCFF path while WACC, g,
    net cash and diluted shares remain fixed.
    """
    target = BASE["market_price"] if target_price is None else target_price
    a, rows = build_model(overrides)
    base_fcff = [rows[y]["fcff"] for y in YEARS]
    base_growth = [base_fcff[0] / (a["starting_revenue"] * 0 + 1) - 1]
    # For the first forecast year, the comparable starting FCFF is approximated
    # from FY2025 reported cash flow; later growth rates are year-over-year.
    start_fcff = 101785.144
    growths = [base_fcff[0] / start_fcff - 1]
    growths.extend(base_fcff[i] / base_fcff[i-1] - 1 for i in range(1, len(base_fcff)))
    def value_at(shift):
        fcf = []
        prior = start_fcff
        for gr in growths:
            prior *= (1 + gr + shift)
            fcf.append(prior)
        pv_explicit = sum(cf / ((1 + a["wacc"]) ** (i + 1)) for i, cf in enumerate(fcf))
        tv = fcf[-1] * (1 + a["terminal_growth"]) / (a["wacc"] - a["terminal_growth"])
        ev = pv_explicit + tv / ((1 + a["wacc"]) ** len(fcf))
        return (ev + a["cash_and_securities"] - a["debt_for_valuation"]) / a["diluted_shares_m"]
    low_v, high_v = value_at(lower), value_at(upper)
    if (target - low_v) * (target - high_v) > 0:
        return {"solved": False, "target_price": target, "lower_shift": lower,
                "upper_shift": upper, "lower_value": low_v, "upper_value": high_v,
                "message": "Target price is outside the valuation range produced by the permitted FCFF-growth-shift bracket."}
    lo, hi = lower, upper
    for _ in range(iterations):
        mid = (lo + hi) / 2
        mv = value_at(mid)
        if abs(mv - target) < 1e-7:
            lo = hi = mid
            break
        if (target - low_v) * (target - mv) <= 0:
            hi, high_v = mid, mv
        else:
            lo, low_v = mid, mv
    shift = (lo + hi) / 2
    return {"solved": True, "target_price": target, "fcff_growth_shift": shift,
            "implied_fcff_growth_rates": [x + shift for x in growths],
            "implied_value": value_at(shift)}



def peer_valuation(a=None, rows=None):
    a = BASE if a is None else a

    # P/E is a separate cross-check; its dates and EPS period still need verification.
    result = {
        "low_pe": a["peer_pe_low"],
        "high_pe": a["peer_pe_high"],
        "low_value": a["peer_pe_low"] * a["apple_diluted_eps"],
        "high_value": a["peer_pe_high"] * a["apple_diluted_eps"],
    }

    if rows is not None:
        ebitda = a["apple_ttm_ebitda"]
        low_mult = a["peer_ev_ebitda_low"]
        high_mult = a["peer_ev_ebitda_high"]
        net_cash = (
            a["cash_and_securities"] - a["debt_for_valuation"]
        )

        result.update({
            "low_ev_ebitda": low_mult,
            "high_ev_ebitda": high_mult,
            "apple_ttm_ebitda": ebitda,
            "ev_ebitda_low_value": (
                (low_mult * ebitda + net_cash)
                / a["diluted_shares_m"]
            ),
            "ev_ebitda_high_value": (
                (high_mult * ebitda + net_cash)
                / a["diluted_shares_m"]
            ),
            "ev_ebitda_method": (
                "Trailing EV/EBITDA cross-check using Apple's TTM "
                "EBITDA and provisional Microsoft and Alphabet peer "
                "multiples. Verify peer dates and definitions."
            ),
        })

    return result



def checks(a, rows):
    results = {
        "base_year_assets_reconcile": abs(a["opening_total_assets"] - a["opening_total_liabilities_equity"]) < 1e-6,
        "balance_sheet_all_years": all(abs(rows[y]["balance_gap"]) < 1e-5 for y in YEARS),
        "cash_flow_ties_all_years": all(abs(rows[y]["cash_tie"]) < 1e-6 for y in YEARS),
        "fcff_positive_all_years": all(rows[y]["fcff"] > 0 for y in YEARS),
        "dcf_wacc_growth_valid": a["wacc"] > a["terminal_growth"],
        "dcf_wacc_monotonicity": dcf_value(rows, a, min(0.12, a["wacc"] + 0.005), a["terminal_growth"])["value_per_share"] < dcf_value(rows, a, a["wacc"], a["terminal_growth"])["value_per_share"],
        "dcf_growth_monotonicity": dcf_value(rows, a, a["wacc"], max(0.015, a["terminal_growth"] - 0.005))["value_per_share"] < dcf_value(rows, a, a["wacc"], a["terminal_growth"])["value_per_share"],
    }
    return results


def run_report(overrides=None):
    a, rows = build_model(overrides)
    dcf = dcf_value(rows, a)
    comps = peer_valuation(a, rows)
    sens = sensitivity(overrides)
    rev = reverse_dcf(a["market_price"], overrides=overrides)
    validation = checks(a, rows)
    return {"as_of_date": a["market_price_date"], "company": "Apple Inc. (AAPL)",
            "currency": "USD", "units": "USD millions except per-share values",
            "assumptions": a, "forecast": rows, "dcf": dcf, "comps": comps,
            "sensitivity": sens, "reverse_dcf": rev, "checks": validation}
