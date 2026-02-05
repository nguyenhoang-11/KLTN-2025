from ortools.linear_solver import pywraplp
from tkinter import simpledialog, messagebox, filedialog
from openpyxl import load_workbook
import tkinter as tk
import pandas as pd

# Hide main tkinter window
root = tk.Tk()
root.withdraw()

# Select file box
file_path = filedialog.askopenfilename(
    title="SELECT MS EXCEL SOURCE FILE",
    filetypes=[("Excel files", "*.xlsx *.xlsb")]
)
print(f"📂 CHOOSE SETUP FILE: {file_path}")

# Import from excel
dfItem = pd.read_excel(file_path, sheet_name="ITEM", engine="pyxlsb")
dfTime = pd.read_excel(file_path, sheet_name="TIME_SERIES", engine="pyxlsb")
dfECO = pd.read_excel(file_path, sheet_name="ECO", engine="pyxlsb")

# Establishing fixed parameters
itemList = dfItem['ITEM'].unique().tolist()
whList = dfItem['WHIDI1'].unique().tolist()
ECOList = dfECO['CODE4'].unique().tolist()

# Sum
I, J, K = len(itemList), len(whList), len(ECOList)

# INDEX
iDict = {i+1: item for i, item in enumerate(itemList)}
jDict = {j+1: wh for j, wh in enumerate(whList)}
kDict = {k+1: group for k, group in enumerate(ECOList)}
t_start, t_firm, t_end = 3, 4, 5

# PARAMETER
def para_2(df, col_item, col_wh, iDict, jDict, field):
    data = {}
    I, J = len(iDict), len(jDict)

    for i in range(1, I + 1):
        for j in range(1, J + 1):
            mask = (df[col_item] == iDict[i]) & (df[col_wh] == jDict[j])
            if not df[mask].empty:
                val = df.loc[mask, field].iloc[0]
                data[(i, j)] = val
    return data

def para_3(df, col_item, col_wh, iDict, jDict, prefix, t_start, t_end):
    data = {}
    I, J = len(iDict), len(jDict)

    for i in range(1, I + 1):
        for j in range(1, J + 1):
            mask = (df[col_item] == iDict[i]) & (df[col_wh] == jDict[j])
            if not df[mask].empty:
                for t in range(t_start, t_end + 1):
                    col_name = f"{prefix}W{t}"
                    if col_name in df.columns:
                        val = df.loc[mask, col_name].iloc[0]
                        data[(i, j, t)] = val
    return data

def group(df, iDict, kDict, col_item="ITEM", col_group="CODE4"):
    G_k = {k: [] for k in kDict.keys()}
    for i, item in iDict.items():
        mask = df[col_item] == item
        if not df[mask].empty:
            code4_value = df.loc[mask, col_group].iloc[0]
            k = next((key for key, val in kDict.items() if val == code4_value), None)
            if k is not None:
                G_k[k].append(i)
    return G_k

begin = para_2(dfItem, 'ITEM', 'WHIDI1', iDict, jDict, 'BEGIN')
mult = para_2(dfItem, 'ITEM', 'WHIDI1', iDict, jDict, 'MULT')
ovst_c = para_2(dfItem, 'ITEM', 'WHIDI1', iDict, jDict, 'OVST_C')
unst_c = para_2(dfItem, 'ITEM', 'WHIDI1', iDict, jDict, 'UNST_C')
pel_c = para_2(dfItem, 'ITEM', 'WHIDI1', iDict, jDict, 'PEL_C')
act_c = para_2(dfItem, 'ITEM', 'WHIDI1', iDict, jDict, 'ACT_C')
bck_c  = para_2(dfECO, 'WHIDI1', 'CODE4', jDict, kDict, 'BCK_C')

bal = para_3(dfTime, 'ITEM', 'WHIDI1', iDict, jDict, 'BAL_', t_start, t_end)
lower = para_3(dfTime, 'ITEM', 'WHIDI1', iDict, jDict, 'LOWER_', t_start, t_end)
upper = para_3(dfTime, 'ITEM', 'WHIDI1', iDict, jDict, 'UPPER_', t_start, t_end)
firm = para_3(dfTime, 'ITEM', 'WHIDI1', iDict, jDict, 'FIRMPO_', t_start, t_firm)

G_k = group(dfItem, iDict, kDict, col_item="ITEM", col_group="CODE4")
HV = 9999

# ==================== DSS FUNCTIONS ====================

def calculate_baseline_cost(firm, begin, bal, mult, upper, lower, ovst_c, unst_c, bck_c, 
                           index_i_j_t, index_j_k, G_k, alpha):
    """Calculate cost if we keep the original firm PO without changing destination"""
    baseline_SI = {}
    baseline_ovst = {}
    baseline_unst = {}
    baseline_bck = {}
    
    # Calculate SI using firm PO
    for (i, j, t) in index_i_j_t:
        if t == 3:
            firm_qty = firm.get((i, j, t), 0)
            baseline_SI[i, j, t] = begin.get((i, j), 0) + bal.get((i, j, t), 0) + firm_qty
        elif t == 4:
            firm_qty = firm.get((i, j, t), 0)
            baseline_SI[i, j, t] = baseline_SI.get((i, j, 3), 0) + bal.get((i, j, t), 0) + firm_qty
        else:  # t >= 5
            baseline_SI[i, j, t] = baseline_SI.get((i, j, t-1), 0) + bal.get((i, j, t), 0)
    
    # Calculate overstock and understock
    for (i, j, t) in index_i_j_t:
        si_val = baseline_SI.get((i, j, t), 0)
        upper_val = upper.get((i, j, t), float('inf'))
        lower_val = lower.get((i, j, t), 0)
        
        baseline_ovst[i, j, t] = max(0, si_val - upper_val)
        baseline_unst[i, j, t] = max(0, lower_val - si_val)
    
    # Calculate backlog
    for (j, k) in index_j_k:
        for t in range(t_start, t_end + 1):
            total_si = sum(baseline_SI.get((i, j, t), 0) for i in G_k.get(k, []))
            baseline_bck[j, k, t] = max(0, -total_si)
    
    # Calculate total cost
    w3_stock = sum(ovst_c.get((i, j), 0) * baseline_ovst.get((i, j, t_start), 0) + 
                   unst_c.get((i, j), 0) * baseline_unst.get((i, j, t_start), 0) 
                   for (i, j, t) in index_i_j_t if t == t_start)
    
    w3_bck = sum(bck_c.get((j, k), 0) * baseline_bck.get((j, k, t_start), 0) 
                 for (j, k) in index_j_k)
    
    w4_stock = sum(ovst_c.get((i, j), 0) * baseline_ovst.get((i, j, t), 0) + 
                   unst_c.get((i, j), 0) * baseline_unst.get((i, j, t), 0) 
                   for (i, j, t) in index_i_j_t if t_start + 1 <= t <= t_end)
    
    w4_bck = sum(bck_c.get((j, k), 0) * baseline_bck.get((j, k, t), 0) 
                 for (j, k) in index_j_k for t in range(t_start + 1, t_end + 1))
    
    total_baseline = alpha * (w3_stock + w3_bck) + w4_stock + w4_bck
    
    return {
        'total': total_baseline,
        'w3_stock': w3_stock,
        'w3_bck': w3_bck,
        'w4_stock': w4_stock,
        'w4_bck': w4_bck,
        'penalty': 0,  # No penalty in baseline
        'action': 0    # No action in baseline
    }

def calculate_optimized_cost(solver_vars, costs, alpha, index_i_j_t, index_i_j_t_firm, index_j_k):
    """Calculate cost breakdown from optimization results"""
    ovst, unst, bck, pel, act = solver_vars
    ovst_c, unst_c, bck_c, pel_c, act_c = costs
    
    # Week 3 costs
    w3_stock = sum(ovst_c.get((i, j), 0) * ovst[i, j, t].solution_value() + 
                   unst_c.get((i, j), 0) * unst[i, j, t].solution_value() 
                   for (i, j, t) in index_i_j_t if (i, j) in ovst_c and t == t_start)
    
    w3_bck = sum(bck_c.get((j, k), 0) * bck[j, k, t].solution_value() 
                 for (j, k, t) in bck if (j, k) in bck_c and t == t_start)
    
    # Week 4-5 costs
    w4_stock = sum(ovst_c.get((i, j), 0) * ovst[i, j, t].solution_value() + 
                   unst_c.get((i, j), 0) * unst[i, j, t].solution_value() 
                   for (i, j, t) in index_i_j_t if (i, j) in ovst_c and t_start + 1 <= t <= t_end)
    
    w4_bck = sum(bck_c.get((j, k), 0) * bck[j, k, t].solution_value() 
                 for (j, k, t) in bck if (j, k) in bck_c and t_start + 1 <= t <= t_end)
    
    # Penalty and action costs
    penalty = sum(pel_c.get((i, j), 0) * pel[i, j, t].solution_value() 
                  for (i, j, t) in index_i_j_t_firm if (i, j) in pel_c)
    
    action = sum(act_c.get((i, j), 0) * act[i, j, t].solution_value() 
                 for (i, j, t) in index_i_j_t_firm if (i, j) in act_c)
    
    total_optimized = alpha * (w3_stock + w3_bck) + w4_stock + w4_bck + penalty + action
    
    return {
        'total': total_optimized,
        'w3_stock': w3_stock,
        'w3_bck': w3_bck,
        'w4_stock': w4_stock,
        'w4_bck': w4_bck,
        'penalty': penalty,
        'action': action
    }

def create_summary_report(baseline_cost, optimized_cost, act_result, pack_result, firm, alpha):
    """Create executive summary report"""
    savings = baseline_cost['total'] - optimized_cost['total']
    savings_pct = (savings / baseline_cost['total'] * 100) if baseline_cost['total'] > 0 else 0
    
    # Count number of destination changes
    num_changes = sum(1 for val in act_result.values() if val > 0.5)
    
    # Count total firm PO lines
    total_po_lines = len([v for v in firm.values() if v > 0])
    
    # Calculate change percentage
    change_pct = (num_changes / total_po_lines * 100) if total_po_lines > 0 else 0
    
    summary = {
        'Alpha': alpha,
        'Baseline Cost': baseline_cost['total'],
        'Optimized Cost': optimized_cost['total'],
        'Total Savings': savings,
        'Savings %': savings_pct,
        'Number of Changes': num_changes,
        'Total PO Lines': total_po_lines,
        'Change %': change_pct,
        'Status': 'OPTIMAL' if savings > 0 else 'NO IMPROVEMENT'
    }
    
    return summary

def export_dss_report(file_path_xlsx, baseline_cost, optimized_cost, summary, 
                      pack_result, f_result, SI_result, pel_result, act_result, 
                      firm, iDict, jDict, alpha):
    """Export comprehensive DSS report with multiple sheets"""
    from datetime import datetime
    
    wb = load_workbook(file_path_xlsx)
    
    # ========== SHEET 1: SUMMARY ==========
    if 'SUMMARY' in wb.sheetnames:
        del wb['SUMMARY']
    ws_summary = wb.create_sheet('SUMMARY', 0)
    
    ws_summary['A1'] = 'DESTINATION CHANGE OPTIMIZATION - EXECUTIVE SUMMARY'
    ws_summary['A1'].font = ws_summary['A1'].font.copy(bold=True, size=14)
    ws_summary['A2'] = f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    row = 4
    ws_summary[f'A{row}'] = 'KEY METRICS'
    ws_summary[f'A{row}'].font = ws_summary[f'A{row}'].font.copy(bold=True, size=12)
    row += 1
    
    for key, value in summary.items():
        ws_summary[f'A{row}'] = key
        ws_summary[f'B{row}'] = value
        if 'Cost' in key or 'Savings' in key:
            ws_summary[f'B{row}'].number_format = '#,##0.00'
        elif '%' in key:
            ws_summary[f'B{row}'].number_format = '0.00"%"'
        row += 1
    
    # ========== SHEET 2: COST_BREAKDOWN ==========
    if 'COST_BREAKDOWN' in wb.sheetnames:
        del wb['COST_BREAKDOWN']
    ws_cost = wb.create_sheet('COST_BREAKDOWN', 1)
    
    ws_cost['A1'] = 'COST BREAKDOWN ANALYSIS'
    ws_cost['A1'].font = ws_cost['A1'].font.copy(bold=True, size=14)
    
    # Header
    headers = ['Cost Component', 'Baseline', 'Optimized', 'Savings', 'Savings %']
    for col, header in enumerate(headers, start=1):
        cell = ws_cost.cell(3, col, header)
        cell.font = cell.font.copy(bold=True)
    
    # Cost components
    components = [
        ('Week 3 Stock Cost', 'w3_stock'),
        ('Week 3 Backlog Cost', 'w3_bck'),
        ('Week 4-5 Stock Cost', 'w4_stock'),
        ('Week 4-5 Backlog Cost', 'w4_bck'),
        ('Penalty Cost', 'penalty'),
        ('Action Cost', 'action')
    ]
    
    row = 4
    for comp_name, comp_key in components:
        base_val = baseline_cost.get(comp_key, 0)
        opt_val = optimized_cost.get(comp_key, 0)
        saving = base_val - opt_val
        saving_pct = (saving / base_val * 100) if base_val > 0 else 0
        
        ws_cost.cell(row, 1, comp_name)
        ws_cost.cell(row, 2, base_val).number_format = '#,##0.00'
        ws_cost.cell(row, 3, opt_val).number_format = '#,##0.00'
        ws_cost.cell(row, 4, saving).number_format = '#,##0.00'
        ws_cost.cell(row, 5, saving_pct).number_format = '0.00"%"'
        row += 1
    
    # Total row
    ws_cost.cell(row, 1, 'TOTAL').font = ws_cost.cell(row, 1).font.copy(bold=True)
    ws_cost.cell(row, 2, baseline_cost['total']).number_format = '#,##0.00'
    ws_cost.cell(row, 3, optimized_cost['total']).number_format = '#,##0.00'
    ws_cost.cell(row, 4, summary['Total Savings']).number_format = '#,##0.00'
    ws_cost.cell(row, 5, summary['Savings %']).number_format = '0.00"%"'
    
    # ========== SHEET 3: CHANGES_LOG ==========
    if 'CHANGES_LOG' in wb.sheetnames:
        del wb['CHANGES_LOG']
    ws_changes = wb.create_sheet('CHANGES_LOG', 2)
    
    ws_changes['A1'] = 'DESTINATION CHANGES LOG'
    ws_changes['A1'].font = ws_changes['A1'].font.copy(bold=True, size=14)
    
    # Header
    change_headers = ['Item', 'Warehouse', 'Week', 'Firm PO', 'New Pack', 'New F', 'New Total', 'Change', 'Changed?']
    for col, header in enumerate(change_headers, start=1):
        cell = ws_changes.cell(3, col, header)
        cell.font = cell.font.copy(bold=True)
    
    row = 4
    for (item, wh, t), act_val in sorted(act_result.items()):
        # Find index
        i = next((k for k, v in iDict.items() if v == item), None)
        j = next((k for k, v in jDict.items() if v == wh), None)
        
        if i and j:
            firm_val = firm.get((i, j, t), 0)
            pack_val = pack_result.get((item, wh, t), 0)
            f_val = f_result.get((item, wh, t), 0)
            
            # Find multiplier
            mult_val = mult.get((i, j), 1)
            new_total = pack_val * mult_val + f_val
            change = new_total - firm_val
            changed = 'YES' if act_val > 0.5 else 'NO'
            
            ws_changes.cell(row, 1, item)
            ws_changes.cell(row, 2, wh)
            ws_changes.cell(row, 3, t)
            ws_changes.cell(row, 4, firm_val)
            ws_changes.cell(row, 5, pack_val)
            ws_changes.cell(row, 6, f_val)
            ws_changes.cell(row, 7, new_total)
            ws_changes.cell(row, 8, change)
            ws_changes.cell(row, 9, changed)
            row += 1
    
    return wb

# Input alpha
alpha = None
while True:
    alpha = simpledialog.askstring(
        title="Input Alpha",
        prompt="Input alpha:"
    )

    if alpha is None or alpha.strip() == "":
        messagebox.showwarning("WARNING", "Do not allow null alpha!")
        continue

    try:
        alpha = float(alpha)
        break
    except:
        messagebox.showwarning("ERROR", "Alpha must be valid!")
        continue

print("Valid alpha =", alpha)

# VALID PAIR
valid_item_wh = dfItem[['ITEM', 'WHIDI1']].drop_duplicates().values.tolist()
valid_wh_eco  = dfECO[['WHIDI1', 'CODE4']].drop_duplicates().values.tolist()
valid_item_wh_time = [(i, j, t) for (i, j) in valid_item_wh for t in range(t_start, t_end + 1)]
firm_item_wh_time  = [(i, j, t) for (i, j) in valid_item_wh for t in range(t_start, t_firm + 1)]

# INDEX PAIR
index_i_j = [(i_idx, j_idx)
    for (item, wh) in valid_item_wh
    for i_idx, item_val in iDict.items() if item_val == item
    for j_idx, wh_val in jDict.items() if wh_val == wh
]

index_j_k = [(j_idx, k_idx)
    for (wh, eco) in valid_wh_eco
    for j_idx, wh_val in jDict.items() if wh_val == wh
    for k_idx, eco_val in kDict.items() if eco_val == eco
]

index_i_j_t = [(i_idx, j_idx, t)
    for (item, wh, t) in valid_item_wh_time
    for i_idx, item_val in iDict.items() if item_val == item
    for j_idx, wh_val in jDict.items() if wh_val == wh
]

index_i_j_t_firm = [(i_idx, j_idx, t)
    for (item, wh, t) in firm_item_wh_time
    for i_idx, item_val in iDict.items() if item_val == item
    for j_idx, wh_val in jDict.items() if wh_val == wh
]

# CREATE SOLVER
solver = pywraplp.Solver.CreateSolver('SCIP')

# VARIABLES
pack, f, SI, ovst, unst, pel, act = {}, {}, {}, {}, {}, {}, {}
bck = {}

# --- (1) item–warehouse–time variables---
for item, wh in valid_item_wh:
    i = next(k for k, v in iDict.items() if v == item)
    j = next(k for k, v in jDict.items() if v == wh)

    for t in range(t_start, t_firm + 1):
        pack[i, j, t] = solver.IntVar(0, solver.infinity(), f'pack_{i}_{j}_{t}')
        f[i, j, t]    = solver.IntVar(0, solver.infinity(), f'f_{i}_{j}_{t}')
        pel[i, j, t]  = solver.BoolVar(f'pel_{i}_{j}_{t}')
        act[i, j, t]  = solver.BoolVar(f'act_{i}_{j}_{t}')
    for t in range(t_start, t_end + 1):
        SI[i, j, t]   = solver.IntVar(-solver.infinity(), solver.infinity(), f'SI_{i}_{j}_{t}')
        ovst[i, j, t] = solver.IntVar(0, solver.infinity(), f'ovst_{i}_{j}_{t}')
        unst[i, j, t] = solver.IntVar(0, solver.infinity(), f'unst_{i}_{j}_{t}')

# --- (2) warehouse–ECO–time variables ---
for wh, eco in valid_wh_eco:
    j = next(k for k, v in jDict.items() if v == wh)
    k = next(k for k, v in kDict.items() if v == eco)

    for t in range(t_start, t_end + 1):
        bck[j, k, t] = solver.IntVar(0, solver.infinity(), f'bck_{j}_{k}_{t}')

# OBJECTIVE FUNCTION
objective = solver.Objective()
w3Stock_cost = solver.Sum(ovst_c[i, j] * ovst[i, j, t] + unst_c[i, j] * unst[i, j, t] for (i, j, t) in ovst if (i, j) in ovst_c and t == t_start)
w3Bck_cost = solver.Sum(bck_c[j, k] * bck[j, k ,t] for (j, k, t) in bck if (i, j) in bck_c and t == t_start)
w4Bck_cost = solver.Sum(bck_c[j, k] * bck[j, k ,t] for (j, k, t) in bck if (i, j) in bck_c and t_start + 1 <= t <= t_end)
w4Stock_cost = solver.Sum(ovst_c[i, j] * ovst[i, j, t] + unst_c[i, j] * unst[i, j, t] for (i, j, t) in ovst if (i, j) in ovst_c and t_start + 1 <= t <= t_end)
pelCost = solver.Sum(pel_c[i, j] * pel[i, j ,t] for (i, j, t) in pel if (i, j) in pel_c) # Penalty cost (multiple box condition)
actCost = solver.Sum(act_c[i, j] * act[i, j ,t] for (i, j, t) in act if (i, j) in act_c) # Action cost (avoid unnecessary change)
solver.Minimize(alpha*(w3Stock_cost + w3Bck_cost) + w4Stock_cost + w4Bck_cost + pelCost + actCost)

# CONSTRAINTS
# Constraint 2: Shippable Inventory at Week 3
for (i, j, t) in index_i_j_t:
    solver.Add(SI[i, j, 3] == begin[i, j] + bal[i, j, 3] +  pack[i, j, 3] * mult[i, j] +  f[i, j, 3])

# Constraint 3: Shippable Inventory at Week 4
for (i, j, t) in index_i_j_t:
    solver.Add(SI[i, j, 4] == SI[i, j, 3] + bal[i, j, 4] +  pack[i, j, 4] * mult[i, j] +  f[i, j, 4])

# Constraint 4: Shippable Inventory at other weeks
for (i, j, t) in index_i_j_t:
    if t >= 5:
        solver.Add(SI[i, j, t] == SI[i, j, t-1] + bal[i, j, t])

# Constraint 5: Unchanged total firm POs
for t in range(t_start, t_firm + 1):
    for i in iDict.keys():
        j_list = [j for (ii, j) in index_i_j if ii == i]
        solver.Add(
            solver.Sum([pack[i, j, t] * mult[i, j] + f[i, j, t] - firm[i, j, t]
                        for j in j_list if (i, j, t) in pack]) == 0
        )

# Constraint 6: Backlog quantity
for (j, k) in index_j_k:
    for t in range(t_start, t_end + 1):
        solver.Add(
            bck[j, k, t] >= -solver.Sum(SI[i, j, t] for i in G_k[k] if (i, j, t) in SI)
        )

# Constraint 7: Overstock quantity
for (i, j, t) in index_i_j_t:
    solver.Add(ovst[i, j, t] >= SI[i, j, t] - upper[i, j, t])

# Constraint 8: Understock quantity
for (i, j, t) in index_i_j_t:
    solver.Add(unst[i, j, t] >= lower[i, j, t] - SI[i, j, t])

# Constraint 9: Penalty for multiple box at Week 3 & 4 (pt.1)
for (i, j, t) in index_i_j_t_firm:
    solver.Add(f[i, j, t] <= HV * pel[i, j, t])

# Constraint 10: Penalty for multiple box at Week 3 & 4 (pt.2)
for (i, j, t) in index_i_j_t_firm:
    solver.Add(f[i, j, t] >= HV * (pel[i, j, t] - 1) + 1) 

# Constraint 11: Action at Week 3 & 4 (pt.1)
for t in range(t_start, t_firm + 1):
    for i in iDict.keys():
        j_list = [j for (ii, j) in index_i_j if ii == i]
        for j in j_list:
            if (i, j, t) in pack:
                solver.Add(
                    firm[i, j, t] - (pack[i, j, t] * mult[i, j] + f[i, j, t])
                    <= HV * act[i, j, t]
                )

# Constraint 12: Action at Week 3 & 4 (pt.2)
for t in range(t_start, t_firm + 1):
    for i in iDict.keys():
        j_list = [j for (ii, j) in index_i_j if ii == i]
        for j in j_list:
            if (i, j, t) in pack:
                solver.Add(
                    firm[i, j, t] - (pack[i, j, t] * mult[i, j] + f[i, j, t])
                    >= (-HV) * act[i, j, t]
                )

# Statistic
print("🔎 Total constraints:", solver.NumConstraints())
print("🔎 Total variables:", solver.NumVariables())

# Check parameter
missing_upper = [(i,j,t) for (i,j,t) in SI if (i,j,t) not in upper]
print("⚠️ Missing upper bounds:", len(missing_upper))

missing_lower = [(i,j,t) for (i,j,t) in SI if (i,j,t) not in lower]
print("⚠️ Missing lower bounds:", len(missing_lower))

missing_mult = list({(i, j) for (i, j, t) in SI if (i, j) not in mult})
print("⚠️ Missing MULT:", len(missing_mult))

status = solver.Solve()

if status == pywraplp.Solver.OPTIMAL or status == pywraplp.Solver.FEASIBLE:
    print("✅ Solution found!")
    
    # pack result
    pack_result = {(iDict[i], jDict[j], t): pack[i, j, t].solution_value() for (i, j, t) in index_i_j_t_firm}
    
    # f result
    f_result = {(iDict[i], jDict[j], t): f[i, j, t].solution_value() for (i, j, t) in index_i_j_t_firm}

    # SI result
    SI_result = {(iDict[i], jDict[j], t): SI[i, j, t].solution_value() for (i, j, t) in index_i_j_t}    

    # pel result
    pel_result = {(iDict[i], jDict[j], t): pel[i, j, t].solution_value() for (i, j, t) in index_i_j_t_firm}    

    # act result
    act_result = {(iDict[i], jDict[j], t): act[i, j, t].solution_value() for (i, j, t) in index_i_j_t_firm}
    
    # ========== DSS ANALYSIS ==========
    print("\n" + "="*60)
    print("📊 DSS COST ANALYSIS")
    print("="*60)
    
    # Calculate baseline cost
    print("🔄 Calculating baseline cost (no destination change)...")
    baseline_cost = calculate_baseline_cost(
        firm, begin, bal, mult, upper, lower, ovst_c, unst_c, bck_c,
        index_i_j_t, index_j_k, G_k, alpha
    )
    
    # Calculate optimized cost
    print("🔄 Calculating optimized cost...")
    optimized_cost = calculate_optimized_cost(
        (ovst, unst, bck, pel, act),
        (ovst_c, unst_c, bck_c, pel_c, act_c),
        alpha, index_i_j_t, index_i_j_t_firm, index_j_k
    )
    
    # Create summary report
    summary = create_summary_report(baseline_cost, optimized_cost, act_result, pack_result, firm, alpha)
    
    # Display results
    print(f"\n💰 BASELINE COST:     ${baseline_cost['total']:,.2f}")
    print(f"💰 OPTIMIZED COST:    ${optimized_cost['total']:,.2f}")
    print(f"💵 TOTAL SAVINGS:     ${summary['Total Savings']:,.2f} ({summary['Savings %']:.2f}%)")
    print(f"🔄 CHANGES MADE:      {summary['Number of Changes']}/{summary['Total PO Lines']} ({summary['Change %']:.1f}%)")
    print(f"📈 STATUS:            {summary['Status']}")
    
    print("\n📋 COST BREAKDOWN:")
    print(f"  W3 Stock:     ${baseline_cost['w3_stock']:>12,.2f} → ${optimized_cost['w3_stock']:>12,.2f}")
    print(f"  W3 Backlog:   ${baseline_cost['w3_bck']:>12,.2f} → ${optimized_cost['w3_bck']:>12,.2f}")
    print(f"  W4-5 Stock:   ${baseline_cost['w4_stock']:>12,.2f} → ${optimized_cost['w4_stock']:>12,.2f}")
    print(f"  W4-5 Backlog: ${baseline_cost['w4_bck']:>12,.2f} → ${optimized_cost['w4_bck']:>12,.2f}")
    print(f"  Penalty:      ${baseline_cost['penalty']:>12,.2f} → ${optimized_cost['penalty']:>12,.2f}")
    print(f"  Action:       ${baseline_cost['action']:>12,.2f} → ${optimized_cost['action']:>12,.2f}")
    print("="*60 + "\n")
    
else:
    print("❌ No solution found. Status:", status)
    summary = None
    baseline_cost = None
    optimized_cost = None

# EXTRACT TO XLXS TEMPLATE
if summary is None:
    print("⚠️ No optimization result to export!")
else:
    file_path_xlsx = filedialog.askopenfilename(
        title="CHOOSE EXCEL TEMPLATE FILE",
        filetypes=[("Excel Files", "*.xlsx *.xls")]
    )

    if not file_path_xlsx:
        raise Exception("❌ DO NOT CHOOSE EXCEL FILE!")

    print(f"\n📂 CHOOSE RESULT FILE: {file_path_xlsx}")
    print("📝 Generating DSS report with multiple sheets...")

    # Use DSS export function
    wb = export_dss_report(
        file_path_xlsx, baseline_cost, optimized_cost, summary,
        pack_result, f_result, SI_result, pel_result, act_result,
        firm, iDict, jDict, alpha
    )
    
    # ========== SHEET 4: DEST_CH (Original Output) ==========
    if 'DEST_CH' not in wb.sheetnames:
        wb.create_sheet('DEST_CH')
    
    ws = wb['DEST_CH']
    
    # SETUP WAREHOUSES AND ITEMS
    whs = sorted(set(str(j).strip() for (_, j, _) in pack_result.keys()))
    items = sorted(set(i for (i, _, _) in list(pack_result.keys())))

    # RECORD ITEM NAMES (Column A)
    for r_idx, item in enumerate(items, start=3):
        ws.cell(row=r_idx, column=1, value=item)

    # COLUMN MAPPING
    col_pack_start = {3: 2, 4: 14}
    col_f_start    = {3: 8, 4: 20}
    col_SI_start    = {3: 26, 4: 32, 5: 38}
    col_pel_start  = {3: 44, 4: 50}
    col_act_start  = {3: 56, 4: 62}

    col_map = {
        "pack": col_pack_start,
        "f":    col_f_start,
        "SI":    col_SI_start,
        "pel":  col_pel_start,
        "act":  col_act_start,
    }

    # DATA SOURCES (SI removed)
    data_sources = {
        "pack": pack_result,
        "f":    f_result,
        "SI":    SI_result,
        "pel":  pel_result,
        "act":  act_result,
    }

    # CLEAN RESULT KEYS
    def clean_result(dic):
        return {(i, str(j).strip(), t): v for (i, j, t), v in dic.items()}

    for key in data_sources:
        data_sources[key] = clean_result(data_sources[key])

    # WRITE DATA
    for t in range(t_start, t_end + 1):
        for c_idx, wh in enumerate(whs):
            # Start columns for each type
            cols = {
                key: (col_map[key].get(t) + c_idx if col_map[key].get(t) is not None else None)
                for key in col_map
            }

            if all(v is None for v in cols.values()):
                continue

            # Write warehouse name in row 2
            for key, col in cols.items():
                if col is not None:
                    ws.cell(row=2, column=col, value=wh)

            # Write data for each item
            for r_idx, item in enumerate(items, start=3):
                for key, col in cols.items():
                    if col is None:
                        continue
                    src = data_sources[key]
                    value = src.get((item, wh, t), 0)
                    ws.cell(row=r_idx, column=col, value=value)
                    
    # SAVE FILE
    wb.save(file_path_xlsx)
    print(f"\n✅ DSS REPORT SAVED SUCCESSFULLY!")
    print(f"📄 File: {file_path_xlsx}")
    print(f"📊 Sheets created:")
    print(f"   1. SUMMARY - Executive summary with savings")
    print(f"   2. COST_BREAKDOWN - Detailed cost analysis")
    print(f"   3. CHANGES_LOG - All destination changes")
    print(f"   4. DEST_CH - Optimization results")
    print("\n" + "="*60)
