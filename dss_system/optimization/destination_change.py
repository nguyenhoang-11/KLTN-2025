"""
Destination Change Optimization Module
Optimizes firm PO destination allocation to minimize total supply chain costs
"""

from ortools.linear_solver import pywraplp
from typing import Dict, Tuple, List, Any
import pandas as pd
from datetime import datetime


class DestinationChangeOptimizer:
    """
    Destination Change Optimization using OR-Tools SCIP solver

    Minimizes total cost by reallocating firm purchase orders between warehouses
    while maintaining total PO quantities.
    """

    def __init__(self, loader, alpha: float = 2.0, pel_cost: float = None, act_cost: float = None):
        """
        Initialize optimizer with AFI data loader

        Args:
            loader: AFIDataLoader instance with loaded data
            alpha: Weight for Week 3 costs (default: 2.0, prioritizes near-term)
            pel_cost: Override penalty cost (optional, uses data if None)
            act_cost: Override action cost (optional, uses data if None)
        """
        self.loader = loader
        self.alpha = alpha
        self.pel_cost_override = pel_cost
        self.act_cost_override = act_cost

        # Time parameters
        self.t_start = 3  # Week 3
        self.t_firm = 4   # Week 4 (last firm PO week)
        self.t_end = 5    # Week 5

        # Big M constant for binary constraints
        self.HV = 9999

        # Results storage
        self.solver = None
        self.pack_result = None
        self.f_result = None
        self.SI_result = None
        self.pel_result = None
        self.act_result = None
        self.baseline_cost = None
        self.optimized_cost = None
        self.summary = None

        # Detailed results for per-warehouse breakdown
        self.baseline_ovst = None
        self.baseline_unst = None
        self.baseline_bck = None
        self.optimized_ovst = None
        self.optimized_unst = None
        self.optimized_bck = None

    def _extract_parameters(self):
        """Extract and prepare optimization parameters from loader data"""

        # Get basic dimensions
        self.itemList = self.loader.item['ITEM'].unique().tolist()
        self.whList = self.loader.item['WHIDI1'].unique().tolist()
        self.ECOList = self.loader.eco['CODE4'].unique().tolist()

        self.I = len(self.itemList)
        self.J = len(self.whList)
        self.K = len(self.ECOList)

        # Create index dictionaries
        self.iDict = {i+1: item for i, item in enumerate(self.itemList)}
        self.jDict = {j+1: wh for j, wh in enumerate(self.whList)}
        self.kDict = {k+1: group for k, group in enumerate(self.ECOList)}

        # Extract 2D parameters (item x warehouse)
        self.begin = self._para_2(self.loader.item, 'ITEM', 'WHIDI1', 'BEGIN')
        self.mult = self._para_2(self.loader.item, 'ITEM', 'WHIDI1', 'MULT')
        self.ovst_c = self._para_2(self.loader.item, 'ITEM', 'WHIDI1', 'OVST_C')
        self.unst_c = self._para_2(self.loader.item, 'ITEM', 'WHIDI1', 'UNST_C')

        # Penalty and action costs (can be overridden)
        if self.pel_cost_override is not None:
            self.pel_c = {(i, j): self.pel_cost_override for i in self.iDict.keys() for j in self.jDict.keys()}
        else:
            # Try to load from data, if not available use default value of 0
            if 'PEL_C' in self.loader.item.columns:
                self.pel_c = self._para_2(self.loader.item, 'ITEM', 'WHIDI1', 'PEL_C')
            else:
                self.pel_c = {(i, j): 0 for i in self.iDict.keys() for j in self.jDict.keys()}

        if self.act_cost_override is not None:
            self.act_c = {(i, j): self.act_cost_override for i in self.iDict.keys() for j in self.jDict.keys()}
        else:
            # ACT_C usually not in data, use default value of 0
            if 'ACT_C' in self.loader.item.columns:
                self.act_c = self._para_2(self.loader.item, 'ITEM', 'WHIDI1', 'ACT_C')
            else:
                self.act_c = {(i, j): 0 for i in self.iDict.keys() for j in self.jDict.keys()}

        # Backlog cost (warehouse x ECO)
        self.bck_c = self._para_2_eco(self.loader.eco, 'WHIDI1', 'CODE4', 'BCK_C')

        # Extract 3D parameters (item x warehouse x time)
        self.bal = self._para_3(self.loader.time_series, 'ITEM', 'WHIDI1', 'BAL_')
        self.lower = self._para_3(self.loader.time_series, 'ITEM', 'WHIDI1', 'LOWER_')
        self.upper = self._para_3(self.loader.time_series, 'ITEM', 'WHIDI1', 'UPPER_')
        self.firm = self._para_3(self.loader.time_series, 'ITEM', 'WHIDI1', 'FIRMPO_', t_start=self.t_start, t_end=self.t_firm)

        # Group items by ECO code
        self.G_k = self._group_items_by_eco()

        # Valid combinations
        self.valid_item_wh = self.loader.item[['ITEM', 'WHIDI1']].drop_duplicates().values.tolist()
        self.valid_wh_eco = self.loader.eco[['WHIDI1', 'CODE4']].drop_duplicates().values.tolist()

        # Create index pairs
        self._create_index_pairs()

    def _para_2(self, df, col_item, col_wh, field):
        """Extract 2D parameter (item x warehouse)"""
        data = {}
        for i in range(1, self.I + 1):
            for j in range(1, self.J + 1):
                mask = (df[col_item] == self.iDict[i]) & (df[col_wh] == self.jDict[j])
                if not df[mask].empty:
                    val = df.loc[mask, field].iloc[0]
                    data[(i, j)] = val
        return data

    def _para_2_eco(self, df, col_wh, col_eco, field):
        """Extract 2D parameter (warehouse x ECO)"""
        data = {}
        for j in range(1, self.J + 1):
            for k in range(1, self.K + 1):
                mask = (df[col_wh] == self.jDict[j]) & (df[col_eco] == self.kDict[k])
                if not df[mask].empty:
                    val = df.loc[mask, field].iloc[0]
                    data[(j, k)] = val
        return data

    def _para_3(self, df, col_item, col_wh, prefix, t_start=None, t_end=None):
        """Extract 3D parameter (item x warehouse x time)"""
        if t_start is None:
            t_start = self.t_start
        if t_end is None:
            t_end = self.t_end

        data = {}
        for i in range(1, self.I + 1):
            for j in range(1, self.J + 1):
                mask = (df[col_item] == self.iDict[i]) & (df[col_wh] == self.jDict[j])
                if not df[mask].empty:
                    for t in range(t_start, t_end + 1):
                        col_name = f"{prefix}W{t}"
                        if col_name in df.columns:
                            val = df.loc[mask, col_name].iloc[0]
                            data[(i, j, t)] = val
        return data

    def _group_items_by_eco(self):
        """Group items by ECO code"""
        G_k = {k: [] for k in self.kDict.keys()}
        for i, item in self.iDict.items():
            mask = self.loader.item['ITEM'] == item
            if not self.loader.item[mask].empty:
                code4_value = self.loader.item.loc[mask, 'CODE4'].iloc[0]
                k = next((key for key, val in self.kDict.items() if val == code4_value), None)
                if k is not None:
                    G_k[k].append(i)
        return G_k

    def _create_index_pairs(self):
        """Create all valid index combinations"""
        # Item-Warehouse pairs
        self.index_i_j = [
            (i_idx, j_idx)
            for (item, wh) in self.valid_item_wh
            for i_idx, item_val in self.iDict.items() if item_val == item
            for j_idx, wh_val in self.jDict.items() if wh_val == wh
        ]

        # Warehouse-ECO pairs
        self.index_j_k = [
            (j_idx, k_idx)
            for (wh, eco) in self.valid_wh_eco
            for j_idx, wh_val in self.jDict.items() if wh_val == wh
            for k_idx, eco_val in self.kDict.items() if eco_val == eco
        ]

        # Item-Warehouse-Time triplets (all weeks)
        self.index_i_j_t = [
            (i_idx, j_idx, t)
            for (item, wh) in self.valid_item_wh
            for t in range(self.t_start, self.t_end + 1)
            for i_idx, item_val in self.iDict.items() if item_val == item
            for j_idx, wh_val in self.jDict.items() if wh_val == wh
        ]

        # Item-Warehouse-Time triplets (firm PO weeks only)
        self.index_i_j_t_firm = [
            (i_idx, j_idx, t)
            for (item, wh) in self.valid_item_wh
            for t in range(self.t_start, self.t_firm + 1)
            for i_idx, item_val in self.iDict.items() if item_val == item
            for j_idx, wh_val in self.jDict.items() if wh_val == wh
        ]

    def _calculate_baseline_cost(self):
        """Calculate cost if we keep the original firm PO without changing destination"""
        baseline_SI = {}
        baseline_ovst = {}
        baseline_unst = {}
        baseline_bck = {}

        # Calculate SI using firm PO
        for (i, j, t) in self.index_i_j_t:
            if t == 3:
                firm_qty = self.firm.get((i, j, t), 0)
                baseline_SI[i, j, t] = self.begin.get((i, j), 0) + self.bal.get((i, j, t), 0) + firm_qty
            elif t == 4:
                firm_qty = self.firm.get((i, j, t), 0)
                baseline_SI[i, j, t] = baseline_SI.get((i, j, 3), 0) + self.bal.get((i, j, t), 0) + firm_qty
            else:  # t >= 5
                baseline_SI[i, j, t] = baseline_SI.get((i, j, t-1), 0) + self.bal.get((i, j, t), 0)

        # Calculate overstock and understock
        for (i, j, t) in self.index_i_j_t:
            si_val = baseline_SI.get((i, j, t), 0)
            upper_val = self.upper.get((i, j, t), float('inf'))
            lower_val = self.lower.get((i, j, t), 0)

            baseline_ovst[i, j, t] = max(0, si_val - upper_val)
            baseline_unst[i, j, t] = max(0, lower_val - si_val)

        # Calculate backlog
        for (j, k) in self.index_j_k:
            for t in range(self.t_start, self.t_end + 1):
                total_si = sum(baseline_SI.get((i, j, t), 0) for i in self.G_k.get(k, []))
                baseline_bck[j, k, t] = max(0, -total_si)

        # Calculate total cost
        w3_stock = sum(
            self.ovst_c.get((i, j), 0) * baseline_ovst.get((i, j, self.t_start), 0) +
            self.unst_c.get((i, j), 0) * baseline_unst.get((i, j, self.t_start), 0)
            for (i, j, t) in self.index_i_j_t if t == self.t_start
        )

        w3_bck = sum(
            self.bck_c.get((j, k), 0) * baseline_bck.get((j, k, self.t_start), 0)
            for (j, k) in self.index_j_k
        )

        w4_stock = sum(
            self.ovst_c.get((i, j), 0) * baseline_ovst.get((i, j, t), 0) +
            self.unst_c.get((i, j), 0) * baseline_unst.get((i, j, t), 0)
            for (i, j, t) in self.index_i_j_t if self.t_start + 1 <= t <= self.t_end
        )

        w4_bck = sum(
            self.bck_c.get((j, k), 0) * baseline_bck.get((j, k, t), 0)
            for (j, k) in self.index_j_k for t in range(self.t_start + 1, self.t_end + 1)
        )

        total_baseline = self.alpha * (w3_stock + w3_bck) + w4_stock + w4_bck

        # Store detailed baseline data for per-warehouse breakdown
        self.baseline_ovst = baseline_ovst
        self.baseline_unst = baseline_unst
        self.baseline_bck = baseline_bck

        return {
            'total': total_baseline,
            'w3_stock': w3_stock,
            'w3_bck': w3_bck,
            'w4_stock': w4_stock,
            'w4_bck': w4_bck,
            'penalty': 0,  # No penalty in baseline
            'action': 0    # No action in baseline
        }

    def _calculate_optimized_cost(self, ovst, unst, bck, pel, act):
        """Calculate cost breakdown from optimization results"""

        # Week 3 costs
        w3_stock = sum(
            self.ovst_c.get((i, j), 0) * ovst[i, j, t].solution_value() +
            self.unst_c.get((i, j), 0) * unst[i, j, t].solution_value()
            for (i, j, t) in self.index_i_j_t if (i, j) in self.ovst_c and t == self.t_start
        )

        w3_bck = sum(
            self.bck_c.get((j, k), 0) * bck[j, k, t].solution_value()
            for (j, k, t) in bck if (j, k) in self.bck_c and t == self.t_start
        )

        # Week 4-5 costs
        w4_stock = sum(
            self.ovst_c.get((i, j), 0) * ovst[i, j, t].solution_value() +
            self.unst_c.get((i, j), 0) * unst[i, j, t].solution_value()
            for (i, j, t) in self.index_i_j_t if (i, j) in self.ovst_c and self.t_start + 1 <= t <= self.t_end
        )

        w4_bck = sum(
            self.bck_c.get((j, k), 0) * bck[j, k, t].solution_value()
            for (j, k, t) in bck if (j, k) in self.bck_c and self.t_start + 1 <= t <= self.t_end
        )

        # Penalty and action costs
        penalty = sum(
            self.pel_c.get((i, j), 0) * pel[i, j, t].solution_value()
            for (i, j, t) in self.index_i_j_t_firm if (i, j) in self.pel_c
        )

        action = sum(
            self.act_c.get((i, j), 0) * act[i, j, t].solution_value()
            for (i, j, t) in self.index_i_j_t_firm if (i, j) in self.act_c
        )

        total_optimized = self.alpha * (w3_stock + w3_bck) + w4_stock + w4_bck + penalty + action

        # Store detailed optimized data for per-warehouse breakdown
        self.optimized_ovst = {(i, j, t): ovst[i, j, t].solution_value() for (i, j, t) in ovst}
        self.optimized_unst = {(i, j, t): unst[i, j, t].solution_value() for (i, j, t) in unst}
        self.optimized_bck = {(j, k, t): bck[j, k, t].solution_value() for (j, k, t) in bck}
        self.optimized_pel = {(i, j, t): pel[i, j, t].solution_value() for (i, j, t) in pel}
        self.optimized_act = {(i, j, t): act[i, j, t].solution_value() for (i, j, t) in act}

        return {
            'total': total_optimized,
            'w3_stock': w3_stock,
            'w3_bck': w3_bck,
            'w4_stock': w4_stock,
            'w4_bck': w4_bck,
            'penalty': penalty,
            'action': action
        }

    def _create_summary_report(self):
        """Create executive summary report"""
        savings = self.baseline_cost['total'] - self.optimized_cost['total']
        savings_pct = (savings / self.baseline_cost['total'] * 100) if self.baseline_cost['total'] > 0 else 0

        # Count number of destination changes
        num_changes = sum(1 for val in self.act_result.values() if val > 0.5)

        # Count total firm PO lines
        total_po_lines = len([v for v in self.firm.values() if v > 0])

        # Calculate change percentage
        change_pct = (num_changes / total_po_lines * 100) if total_po_lines > 0 else 0

        self.summary = {
            'Alpha': self.alpha,
            'Baseline Cost': self.baseline_cost['total'],
            'Optimized Cost': self.optimized_cost['total'],
            'Total Savings': savings,
            'Savings %': savings_pct,
            'Number of Changes': num_changes,
            'Total PO Lines': total_po_lines,
            'Change %': change_pct,
            'Status': 'OPTIMAL' if savings > 0 else 'NO IMPROVEMENT'
        }

        return self.summary

    def optimize(self, verbose: bool = True):
        """
        Run optimization

        Args:
            verbose: Print detailed progress (default: True)

        Returns:
            dict: Summary results with savings and cost breakdown
        """
        if verbose:
            print("Extracting parameters from AFI data loader...")

        # Extract parameters
        self._extract_parameters()

        if verbose:
            print(f"Problem size: {self.I} items, {self.J} warehouses, {self.K} ECO groups")

        # Create solver
        if verbose:
            print("Creating OR-Tools SCIP solver...")
        self.solver = pywraplp.Solver.CreateSolver('SCIP')

        # Create variables
        if verbose:
            print("Creating decision variables...")
        pack, f, SI, ovst, unst, pel, act = {}, {}, {}, {}, {}, {}, {}
        bck = {}

        # Item-warehouse-time variables
        for item, wh in self.valid_item_wh:
            i = next(k for k, v in self.iDict.items() if v == item)
            j = next(k for k, v in self.jDict.items() if v == wh)

            for t in range(self.t_start, self.t_firm + 1):
                pack[i, j, t] = self.solver.IntVar(0, self.solver.infinity(), f'pack_{i}_{j}_{t}')
                f[i, j, t] = self.solver.IntVar(0, self.solver.infinity(), f'f_{i}_{j}_{t}')
                pel[i, j, t] = self.solver.BoolVar(f'pel_{i}_{j}_{t}')
                act[i, j, t] = self.solver.BoolVar(f'act_{i}_{j}_{t}')

            for t in range(self.t_start, self.t_end + 1):
                SI[i, j, t] = self.solver.IntVar(-self.solver.infinity(), self.solver.infinity(), f'SI_{i}_{j}_{t}')
                ovst[i, j, t] = self.solver.IntVar(0, self.solver.infinity(), f'ovst_{i}_{j}_{t}')
                unst[i, j, t] = self.solver.IntVar(0, self.solver.infinity(), f'unst_{i}_{j}_{t}')

        # Warehouse-ECO-time variables
        for wh, eco in self.valid_wh_eco:
            j = next(k for k, v in self.jDict.items() if v == wh)
            k = next(k for k, v in self.kDict.items() if v == eco)

            for t in range(self.t_start, self.t_end + 1):
                bck[j, k, t] = self.solver.IntVar(0, self.solver.infinity(), f'bck_{j}_{k}_{t}')

        # Objective function
        if verbose:
            print("Setting up objective function...")
        objective = self.solver.Objective()

        w3Stock_cost = self.solver.Sum(
            self.ovst_c[i, j] * ovst[i, j, t] + self.unst_c[i, j] * unst[i, j, t]
            for (i, j, t) in ovst if (i, j) in self.ovst_c and t == self.t_start
        )
        w3Bck_cost = self.solver.Sum(
            self.bck_c[j, k] * bck[j, k, t]
            for (j, k, t) in bck if (j, k) in self.bck_c and t == self.t_start
        )
        w4Stock_cost = self.solver.Sum(
            self.ovst_c[i, j] * ovst[i, j, t] + self.unst_c[i, j] * unst[i, j, t]
            for (i, j, t) in ovst if (i, j) in self.ovst_c and self.t_start + 1 <= t <= self.t_end
        )
        w4Bck_cost = self.solver.Sum(
            self.bck_c[j, k] * bck[j, k, t]
            for (j, k, t) in bck if (j, k) in self.bck_c and self.t_start + 1 <= t <= self.t_end
        )
        pelCost = self.solver.Sum(
            self.pel_c[i, j] * pel[i, j, t]
            for (i, j, t) in pel if (i, j) in self.pel_c
        )
        actCost = self.solver.Sum(
            self.act_c[i, j] * act[i, j, t]
            for (i, j, t) in act if (i, j) in self.act_c
        )

        self.solver.Minimize(
            self.alpha * (w3Stock_cost + w3Bck_cost) + w4Stock_cost + w4Bck_cost + pelCost + actCost
        )

        # Add constraints
        if verbose:
            print("Adding constraints...")

        # Constraint 2: SI at Week 3
        for (i, j, t) in self.index_i_j_t:
            self.solver.Add(
                SI[i, j, 3] == self.begin[i, j] + self.bal[i, j, 3] + pack[i, j, 3] * self.mult[i, j] + f[i, j, 3]
            )

        # Constraint 3: SI at Week 4
        for (i, j, t) in self.index_i_j_t:
            self.solver.Add(
                SI[i, j, 4] == SI[i, j, 3] + self.bal[i, j, 4] + pack[i, j, 4] * self.mult[i, j] + f[i, j, 4]
            )

        # Constraint 4: SI at other weeks
        for (i, j, t) in self.index_i_j_t:
            if t >= 5:
                self.solver.Add(SI[i, j, t] == SI[i, j, t-1] + self.bal[i, j, t])

        # Constraint 5: Unchanged total firm POs
        for t in range(self.t_start, self.t_firm + 1):
            for i in self.iDict.keys():
                j_list = [j for (ii, j) in self.index_i_j if ii == i]
                self.solver.Add(
                    self.solver.Sum([
                        pack[i, j, t] * self.mult[i, j] + f[i, j, t] - self.firm[i, j, t]
                        for j in j_list if (i, j, t) in pack
                    ]) == 0
                )

        # Constraint 6: Backlog quantity
        for (j, k) in self.index_j_k:
            for t in range(self.t_start, self.t_end + 1):
                self.solver.Add(
                    bck[j, k, t] >= -self.solver.Sum(SI[i, j, t] for i in self.G_k[k] if (i, j, t) in SI)
                )

        # Constraint 7: Overstock quantity
        for (i, j, t) in self.index_i_j_t:
            self.solver.Add(ovst[i, j, t] >= SI[i, j, t] - self.upper[i, j, t])

        # Constraint 8: Understock quantity
        for (i, j, t) in self.index_i_j_t:
            self.solver.Add(unst[i, j, t] >= self.lower[i, j, t] - SI[i, j, t])

        # Constraint 9: Penalty for multiple box (pt.1)
        for (i, j, t) in self.index_i_j_t_firm:
            self.solver.Add(f[i, j, t] <= self.HV * pel[i, j, t])

        # Constraint 10: Penalty for multiple box (pt.2)
        for (i, j, t) in self.index_i_j_t_firm:
            self.solver.Add(f[i, j, t] >= self.HV * (pel[i, j, t] - 1) + 1)

        # Constraint 11: Action indicator (pt.1)
        for t in range(self.t_start, self.t_firm + 1):
            for i in self.iDict.keys():
                j_list = [j for (ii, j) in self.index_i_j if ii == i]
                for j in j_list:
                    if (i, j, t) in pack:
                        self.solver.Add(
                            self.firm[i, j, t] - (pack[i, j, t] * self.mult[i, j] + f[i, j, t])
                            <= self.HV * act[i, j, t]
                        )

        # Constraint 12: Action indicator (pt.2)
        for t in range(self.t_start, self.t_firm + 1):
            for i in self.iDict.keys():
                j_list = [j for (ii, j) in self.index_i_j if ii == i]
                for j in j_list:
                    if (i, j, t) in pack:
                        self.solver.Add(
                            self.firm[i, j, t] - (pack[i, j, t] * self.mult[i, j] + f[i, j, t])
                            >= (-self.HV) * act[i, j, t]
                        )

        if verbose:
            print(f"Total constraints: {self.solver.NumConstraints()}")
            print(f"Total variables: {self.solver.NumVariables()}")

        # Solve
        if verbose:
            print("\nSolving optimization problem...")
        status = self.solver.Solve()

        if status == pywraplp.Solver.OPTIMAL or status == pywraplp.Solver.FEASIBLE:
            if verbose:
                print("Solution found!")

            # Extract results
            self.pack_result = {
                (self.iDict[i], self.jDict[j], t): pack[i, j, t].solution_value()
                for (i, j, t) in self.index_i_j_t_firm
            }

            self.f_result = {
                (self.iDict[i], self.jDict[j], t): f[i, j, t].solution_value()
                for (i, j, t) in self.index_i_j_t_firm
            }

            self.SI_result = {
                (self.iDict[i], self.jDict[j], t): SI[i, j, t].solution_value()
                for (i, j, t) in self.index_i_j_t
            }

            self.pel_result = {
                (self.iDict[i], self.jDict[j], t): pel[i, j, t].solution_value()
                for (i, j, t) in self.index_i_j_t_firm
            }

            self.act_result = {
                (self.iDict[i], self.jDict[j], t): act[i, j, t].solution_value()
                for (i, j, t) in self.index_i_j_t_firm
            }

            # Calculate baseline cost
            if verbose:
                print("\nCalculating baseline cost (no destination change)...")
            self.baseline_cost = self._calculate_baseline_cost()

            # Calculate optimized cost
            if verbose:
                print("Calculating optimized cost...")
            self.optimized_cost = self._calculate_optimized_cost(ovst, unst, bck, pel, act)

            # Create summary
            summary = self._create_summary_report()

            if verbose:
                self._print_results()

            return summary

        else:
            if verbose:
                print(f"No solution found. Status: {status}")
            return None

    def _print_results(self):
        """Print formatted optimization results"""
        print("\n" + "="*60)
        print("DSS COST ANALYSIS")
        print("="*60)

        print(f"\nBASELINE COST:     ${self.baseline_cost['total']:,.2f}")
        print(f"OPTIMIZED COST:    ${self.optimized_cost['total']:,.2f}")
        print(f"TOTAL SAVINGS:     ${self.summary['Total Savings']:,.2f} ({self.summary['Savings %']:.2f}%)")
        print(f"CHANGES MADE:      {self.summary['Number of Changes']}/{self.summary['Total PO Lines']} ({self.summary['Change %']:.1f}%)")
        print(f"STATUS:            {self.summary['Status']}")

        print("\nCOST BREAKDOWN:")
        print(f"  W3 Stock:     ${self.baseline_cost['w3_stock']:>12,.2f} -> ${self.optimized_cost['w3_stock']:>12,.2f}")
        print(f"  W3 Backlog:   ${self.baseline_cost['w3_bck']:>12,.2f} -> ${self.optimized_cost['w3_bck']:>12,.2f}")
        print(f"  W4-5 Stock:   ${self.baseline_cost['w4_stock']:>12,.2f} -> ${self.optimized_cost['w4_stock']:>12,.2f}")
        print(f"  W4-5 Backlog: ${self.baseline_cost['w4_bck']:>12,.2f} -> ${self.optimized_cost['w4_bck']:>12,.2f}")
        print(f"  Penalty:      ${self.baseline_cost['penalty']:>12,.2f} -> ${self.optimized_cost['penalty']:>12,.2f}")
        print(f"  Action:       ${self.baseline_cost['action']:>12,.2f} -> ${self.optimized_cost['action']:>12,.2f}")
        print("="*60 + "\n")

    def get_changes_dataframe(self):
        """Get all destination changes as a DataFrame"""
        changes = []
        for (item, wh, t), act_val in sorted(self.act_result.items()):
            if act_val > 0.5:  # Only include actual changes
                i = next((k for k, v in self.iDict.items() if v == item), None)
                j = next((k for k, v in self.jDict.items() if v == wh), None)

                if i and j:
                    firm_val = self.firm.get((i, j, t), 0)
                    pack_val = self.pack_result.get((item, wh, t), 0)
                    f_val = self.f_result.get((item, wh, t), 0)
                    mult_val = self.mult.get((i, j), 1)
                    new_total = pack_val * mult_val + f_val
                    change = new_total - firm_val

                    changes.append({
                        'Item': item,
                        'Warehouse': wh,
                        'Week': t,
                        'Firm PO': firm_val,
                        'New Pack': pack_val,
                        'New F': f_val,
                        'New Total': new_total,
                        'Change': change
                    })

        return pd.DataFrame(changes)

    def get_cost_breakdown_dataframe(self):
        """Get cost breakdown comparison as DataFrame"""
        components = [
            ('Week 3 Stock Cost', 'w3_stock'),
            ('Week 3 Backlog Cost', 'w3_bck'),
            ('Week 4-5 Stock Cost', 'w4_stock'),
            ('Week 4-5 Backlog Cost', 'w4_bck'),
            ('Penalty Cost', 'penalty'),
            ('Action Cost', 'action')
        ]

        data = []
        for comp_name, comp_key in components:
            base_val = self.baseline_cost.get(comp_key, 0)
            opt_val = self.optimized_cost.get(comp_key, 0)
            saving = base_val - opt_val
            saving_pct = (saving / base_val * 100) if base_val > 0 else 0

            data.append({
                'Cost Component': comp_name,
                'Baseline': base_val,
                'Optimized': opt_val,
                'Savings': saving,
                'Savings %': saving_pct
            })

        # Add total row
        data.append({
            'Cost Component': 'TOTAL',
            'Baseline': self.baseline_cost['total'],
            'Optimized': self.optimized_cost['total'],
            'Savings': self.summary['Total Savings'],
            'Savings %': self.summary['Savings %']
        })

        return pd.DataFrame(data)

    def get_warehouse_cost_breakdown(self):
        """
        Get cost breakdown by warehouse for detailed analysis

        Calculates actual costs per warehouse based on:
        - Stock costs (overstock + understock) for items in each warehouse
        - Backlog costs allocated to each warehouse
        - Penalty and action costs for items in each warehouse

        Returns:
            DataFrame with columns: Warehouse, Baseline_Cost, Optimized_Cost, Savings, Savings_%
        """
        # Check if optimization has been run
        if self.summary is None or self.baseline_ovst is None:
            return pd.DataFrame()

        # Get all unique warehouses
        warehouses = set()
        for (i, j, t) in self.firm.keys():
            warehouses.add(self.jDict[j])

        if not warehouses:
            return pd.DataFrame()

        data = []
        for wh in sorted(warehouses):
            # Find j index for this warehouse
            j = next((k for k, v in self.jDict.items() if v == wh), None)
            if j is None:
                continue

            # === BASELINE COST for this warehouse ===
            # Stock costs (overstock + understock) for all items in this warehouse
            baseline_w3_stock = sum(
                self.ovst_c.get((i, j), 0) * self.baseline_ovst.get((i, j, self.t_start), 0) +
                self.unst_c.get((i, j), 0) * self.baseline_unst.get((i, j, self.t_start), 0)
                for i in self.iDict.keys() if (i, j) in self.ovst_c
            )

            baseline_w4_stock = sum(
                self.ovst_c.get((i, j), 0) * self.baseline_ovst.get((i, j, t), 0) +
                self.unst_c.get((i, j), 0) * self.baseline_unst.get((i, j, t), 0)
                for i in self.iDict.keys()
                for t in range(self.t_start + 1, self.t_end + 1)
                if (i, j) in self.ovst_c
            )

            # Backlog costs for ECO groups in this warehouse
            baseline_w3_bck = sum(
                self.bck_c.get((j, k), 0) * self.baseline_bck.get((j, k, self.t_start), 0)
                for k in self.kDict.keys() if (j, k) in self.bck_c
            )

            baseline_w4_bck = sum(
                self.bck_c.get((j, k), 0) * self.baseline_bck.get((j, k, t), 0)
                for k in self.kDict.keys()
                for t in range(self.t_start + 1, self.t_end + 1)
                if (j, k) in self.bck_c
            )

            baseline_wh_cost = (
                self.alpha * (baseline_w3_stock + baseline_w3_bck) +
                baseline_w4_stock + baseline_w4_bck
            )

            # === OPTIMIZED COST for this warehouse ===
            # Stock costs
            optimized_w3_stock = sum(
                self.ovst_c.get((i, j), 0) * self.optimized_ovst.get((i, j, self.t_start), 0) +
                self.unst_c.get((i, j), 0) * self.optimized_unst.get((i, j, self.t_start), 0)
                for i in self.iDict.keys() if (i, j) in self.ovst_c
            )

            optimized_w4_stock = sum(
                self.ovst_c.get((i, j), 0) * self.optimized_ovst.get((i, j, t), 0) +
                self.unst_c.get((i, j), 0) * self.optimized_unst.get((i, j, t), 0)
                for i in self.iDict.keys()
                for t in range(self.t_start + 1, self.t_end + 1)
                if (i, j) in self.ovst_c
            )

            # Backlog costs
            optimized_w3_bck = sum(
                self.bck_c.get((j, k), 0) * self.optimized_bck.get((j, k, self.t_start), 0)
                for k in self.kDict.keys() if (j, k) in self.bck_c
            )

            optimized_w4_bck = sum(
                self.bck_c.get((j, k), 0) * self.optimized_bck.get((j, k, t), 0)
                for k in self.kDict.keys()
                for t in range(self.t_start + 1, self.t_end + 1)
                if (j, k) in self.bck_c
            )

            # Penalty and action costs for items in this warehouse
            penalty_cost = sum(
                self.pel_c.get((i, j), 0) * self.optimized_pel.get((i, j, t), 0)
                for i in self.iDict.keys()
                for t in range(self.t_start, self.t_firm + 1)
                if (i, j, t) in self.optimized_pel and (i, j) in self.pel_c
            )

            action_cost = sum(
                self.act_c.get((i, j), 0) * self.optimized_act.get((i, j, t), 0)
                for i in self.iDict.keys()
                for t in range(self.t_start, self.t_firm + 1)
                if (i, j, t) in self.optimized_act and (i, j) in self.act_c
            )

            optimized_wh_cost = (
                self.alpha * (optimized_w3_stock + optimized_w3_bck) +
                optimized_w4_stock + optimized_w4_bck +
                penalty_cost + action_cost
            )

            # Calculate savings
            savings = baseline_wh_cost - optimized_wh_cost
            savings_pct = (savings / baseline_wh_cost * 100) if baseline_wh_cost > 0 else 0

            # Calculate firm PO volume for this warehouse
            wh_volume = sum(
                self.firm.get((i, j, t), 0)
                for i in self.iDict.keys()
                for t in range(self.t_start, self.t_firm + 1)
                if (i, j, t) in self.firm
            )

            # Count number of changes for this warehouse
            num_changes = sum(
                1 for i in self.iDict.keys()
                for t in range(self.t_start, self.t_firm + 1)
                if self.optimized_act.get((i, j, t), 0) > 0.5
            )

            data.append({
                'Warehouse': wh,
                'Baseline Cost': baseline_wh_cost,
                'Optimized Cost': optimized_wh_cost,
                'Savings': savings,
                'Savings %': savings_pct,
                'Firm PO Volume': wh_volume,
                'Num Changes': num_changes
            })

        df = pd.DataFrame(data)
        df = df.sort_values('Savings', ascending=False)
        return df
