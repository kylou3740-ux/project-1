import csv, json
from pathlib import Path
import model
ROOT=Path(__file__).resolve().parent
out=ROOT/'output'; out.mkdir(exist_ok=True)
r=model.run_report()
# JSON is human-readable, with all inputs and outputs for cold inspection.
(out/'visible_output.json').write_text(json.dumps(r, indent=2), encoding='utf-8')
fields=['revenue','gross_profit','operating_income','net_income','cfo','cfi','cff','net_change_cash','fcff','cash','inventory','ppe','other_assets','debt','other_liabilities','equity','total_assets','total_liabilities','balance_gap','cash_tie']
with (out/'forecast.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.writer(f); w.writerow(['year']+fields)
 for y in model.YEARS: w.writerow([y]+[r['forecast'][y][x] for x in fields])
with (out/'sensitivity.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.DictWriter(f,fieldnames=['wacc','terminal_growth','value_per_share']); w.writeheader(); w.writerows(r['sensitivity'])
# Compact, readable terminal result snapshot.
lines=['APPLE INC. (AAPL) — FIN 43900 PROJECT 1 MODEL OUTPUT','Market reference: $326.57 on 2026-09-10 (verify before final submission)','Current research thesis: WATCH / DEFER','All monetary values USD millions except per-share values.','', 'FIVE-YEAR FORECAST']
for y in model.YEARS:
 x=r['forecast'][y]
 lines.append(f"FY{y}E Revenue ${x['revenue']:,.0f}m | EBIT ${x['operating_income']:,.0f}m | Net income ${x['net_income']:,.0f}m | FCFF ${x['fcff']:,.0f}m | Cash ${x['cash']:,.0f}m | Balance gap ${x['balance_gap']:,.6f}m")
d=r['dcf']; lines += ['', 'FCFF DCF', f"WACC {r['assumptions']['wacc']:.4%}; terminal growth {r['assumptions']['terminal_growth']:.4%}", f"Enterprise value ${d['enterprise_value']:,.0f}m", f"Equity value ${d['equity_value']:,.0f}m", f"Value per diluted share ${d['value_per_share']:.2f}", f"PV terminal value / enterprise value {d['terminal_value_share']:.1%}", '', 'EQUITY P/E REFERENCE CROSS-CHECK', f"{r['comps']['low_pe']:.2f}x → ${r['comps']['low_value']:.2f}/share", f"{r['comps']['high_pe']:.2f}x → ${r['comps']['high_value']:.2f}/share", '', 'VALIDATION CHECKS']
for k,v in r['checks'].items(): lines.append(f"{'PASS' if v else 'FAIL'} — {k}")
(out/'visible_output.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('\n'.join(lines))
