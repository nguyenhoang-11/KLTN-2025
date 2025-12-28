"""
Analyze AFI XLSB data file
"""

from pyxlsb import open_workbook
import pandas as pd

file_path = 'AFI - DESTINATION CHANGE FOR UN KIT - TEST (1).xlsb'

print('='*80)
print('PHAN TICH FILE DATA AFI - DESTINATION CHANGE')
print('='*80)

wb = open_workbook(file_path)

# Get all sheets
sheets_info = {}

for sheet_name in wb.sheets:
    with wb.get_sheet(sheet_name) as sheet:
        rows = []
        row_count = 0
        for row in sheet.rows():
            rows.append([item.v if item is not None else None for item in row])
            row_count += 1
            if row_count >= 100:  # Max 100 rows per sheet
                break

        if len(rows) > 1:
            df = pd.DataFrame(rows[1:], columns=rows[0])
            sheets_info[sheet_name] = {
                'rows': len(df),
                'columns': len(df.columns),
                'df': df
            }
        else:
            sheets_info[sheet_name] = {
                'rows': 0,
                'columns': len(rows[0]) if len(rows) > 0 else 0,
                'df': None
            }

wb.close()

# Summary
print('\n1. TONG QUAN CÁC SHEETS:')
print('-'*80)
for sheet_name, info in sheets_info.items():
    print(f'   {sheet_name:20s} | Rows: {info["rows"]:4d} | Cols: {info["columns"]:3d}')

# Detail analysis of key sheets
print('\n2. PHAN TICH CHI TIET:')
print('='*80)

key_sheets = [
    ('ITEM', 'Thong tin san pham/item'),
    ('ETD', 'Thong tin ETD (Estimated Time of Departure) - Du bao inventory theo tuan'),
    ('TIME_SERIES', 'Du lieu time-series - Balance, Lower/Upper bounds, Firm POs'),
    ('HOT LIST', 'Danh sach san pham priority cao'),
    ('DEST_CH', 'Destination Change - Thay doi warehouse destination'),
    ('ECO', 'Economic data'),
    ('WORKLOAD', 'Workload planning')
]

for sheet_name, description in key_sheets:
    if sheet_name in sheets_info and sheets_info[sheet_name]['df'] is not None:
        df = sheets_info[sheet_name]['df']

        print(f'\n>>> {sheet_name}: {description}')
        print('-'*80)
        print(f'So dong: {len(df)}')
        print(f'So cot: {len(df.columns)}')

        # List columns
        print(f'\nCAC COT:')
        for i, col in enumerate(df.columns, 1):
            # Count non-null
            non_null = df[col].notna().sum()
            if non_null > 0:
                # Get sample value
                sample_val = df[col].dropna().iloc[0] if non_null > 0 else None
                print(f'   {i:2d}. {str(col):30s} | {non_null:4d} values | Sample: {sample_val}')

        # Show sample data
        if len(df) > 0:
            print(f'\nSAMPLE DATA (3 dong dau):')
            # Get first few columns with data
            cols_with_data = [col for col in df.columns if df[col].notna().sum() > 0][:10]
            print(df[cols_with_data].head(3).to_string(index=False, max_colwidth=20))

print('\n' + '='*80)
print('DONE!')
