import pandas as pd

excel_path = 'Risk Register DIKBUD 2026.xlsx'
xls = pd.ExcelFile(excel_path)
print("Sheet names:", xls.sheet_names)

df_prio = pd.read_excel(excel_path, sheet_name='Form 5 Risiko Prioritas')
print("=== Form 5 Risiko Prioritas (Excel) ===")
print(df_prio.to_string())

df_rtp = pd.read_excel(excel_path, sheet_name='Form 7 Pengendalian & RTP')
print("\n=== Form 7 Pengendalian & RTP (Excel) ===")
print(df_rtp.to_string())