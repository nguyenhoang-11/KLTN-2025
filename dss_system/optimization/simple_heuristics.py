"""
Simple Heuristics for Firm PO Allocation Benchmark
Compare MILP optimization with practical allocation rules
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple


class SimpleHeuristics:
    """
    Baseline heuristics for firm PO allocation across warehouses

    These represent common business rules used in practice:
    1. Pro-rata: Allocate based on demand proportion
    2. Greedy: Prioritize warehouses with lowest inventory coverage
    3. Round-robin: Distribute evenly in rotation
    """

    def __init__(self, loader):
        """
        Initialize heuristics with AFI data loader

        Args:
            loader: AFIDataLoader instance with loaded data
        """
        self.loader = loader
        self.results = {}

    def _extract_firm_po_data(self):
        """Extract firm PO data (weeks 3-4) and demand/inventory info"""

        # Get firm POs from time_series
        firm_po_mask = (
            (self.loader.time_series['FIRMPO_W3'].notna()) |
            (self.loader.time_series['FIRMPO_W4'].notna())
        )

        firm_data = self.loader.time_series[firm_po_mask].copy()

        # Calculate total firm PO quantity per item-warehouse
        firm_data['TOTAL_FIRM_QTY'] = (
            firm_data['FIRMPO_W3'].fillna(0) +
            firm_data['FIRMPO_W4'].fillna(0)
        )

        # Get demand (weeks 3-4)
        firm_data['DEMAND_3_4'] = (
            firm_data['BAL_W3'].abs() +
            firm_data['BAL_W4'].abs()
        )

        # Get current inventory from ITEM sheet
        firm_data = firm_data.merge(
            self.loader.item[['ITEM', 'WHIDI1', 'BEGIN', 'PEL_C', 'UNST_C']],
            on=['ITEM', 'WHIDI1'],
            how='left'
        )

        firm_data['CURRENT_INV'] = firm_data['BEGIN'].fillna(0)

        # Safety stock from LOWER_W3 (lower bound for week 3)
        firm_data['SAFETY_STOCK'] = firm_data['LOWER_W3'].fillna(0)

        return firm_data

    def _calculate_cost(self, allocation: pd.DataFrame) -> float:
        """
        Calculate total cost for a given allocation

        Args:
            allocation: DataFrame with columns [ITEM, WHIDI1, ALLOCATED_QTY]

        Returns:
            Total cost (handling + stockout)
        """

        # Merge with demand data
        cost_data = allocation.merge(
            self.loader.time_series[['ITEM', 'WHIDI1', 'BAL_W3', 'BAL_W4']],
            on=['ITEM', 'WHIDI1'],
            how='left'
        )

        # Merge with cost and inventory data
        cost_data = cost_data.merge(
            self.loader.item[['ITEM', 'WHIDI1', 'BEGIN', 'PEL_C', 'UNST_C']],
            on=['ITEM', 'WHIDI1'],
            how='left'
        )

        # Calculate inventory after allocation
        cost_data['FINAL_INV'] = (
            cost_data['BEGIN'].fillna(0) +
            cost_data['ALLOCATED_QTY'].fillna(0)
        )

        # Calculate demand (weeks 3-4)
        cost_data['DEMAND'] = (
            cost_data['BAL_W3'].abs() +
            cost_data['BAL_W4'].abs()
        )

        # Net inventory after demand
        cost_data['NET_INV'] = cost_data['FINAL_INV'] - cost_data['DEMAND']

        # Handling cost (positive inventory) - use PEL_C
        cost_data['HANDLING_COST'] = np.maximum(0, cost_data['NET_INV']) * cost_data['PEL_C']

        # Stockout cost (negative inventory) - use UNST_C
        cost_data['STOCKOUT_COST'] = np.maximum(0, -cost_data['NET_INV']) * cost_data['UNST_C']

        total_cost = (
            cost_data['HANDLING_COST'].sum() +
            cost_data['STOCKOUT_COST'].sum()
        )

        return total_cost

    def prorata_heuristic(self, verbose=True) -> Dict:
        """
        Pro-rata allocation: Distribute POs proportional to demand

        Logic:
        - For each item, collect total firm PO quantity
        - Allocate to warehouses based on their demand proportion
        - Simple, fair, commonly used in practice

        Returns:
            Dictionary with results
        """
        if verbose:
            print("\n" + "="*60)
            print("PRO-RATA HEURISTIC")
            print("="*60)
            print("Allocation Rule: Proportional to demand")

        firm_data = self._extract_firm_po_data()

        # Group by item to get total PO and distribute
        allocation_list = []

        for item in firm_data['ITEM'].unique():
            item_data = firm_data[firm_data['ITEM'] == item].copy()

            # Total firm PO for this item (sum across all original warehouses)
            total_po = item_data['TOTAL_FIRM_QTY'].sum()

            # Total demand across all warehouses for this item
            total_demand = item_data['DEMAND_3_4'].sum()

            if total_demand > 0:
                # Allocate proportionally to demand
                for _, row in item_data.iterrows():
                    allocated_qty = total_po * (row['DEMAND_3_4'] / total_demand)
                    allocation_list.append({
                        'ITEM': row['ITEM'],
                        'WHIDI1': row['WHIDI1'],
                        'ALLOCATED_QTY': allocated_qty
                    })
            else:
                # If no demand, distribute evenly
                n_warehouses = len(item_data)
                for _, row in item_data.iterrows():
                    allocation_list.append({
                        'ITEM': row['ITEM'],
                        'WHIDI1': row['WHIDI1'],
                        'ALLOCATED_QTY': total_po / n_warehouses
                    })

        allocation_df = pd.DataFrame(allocation_list)

        # Calculate cost
        total_cost = self._calculate_cost(allocation_df)

        if verbose:
            print(f"\nTotal Cost: ${total_cost:,.2f}")
            print(f"Items processed: {len(firm_data['ITEM'].unique())}")

        self.results['prorata'] = {
            'Method': 'Pro-rata Heuristic',
            'Total Cost': total_cost,
            'Allocation': allocation_df,
            'Description': 'Allocate PO proportional to warehouse demand'
        }

        return self.results['prorata']

    def greedy_heuristic(self, verbose=True) -> Dict:
        """
        Greedy allocation: Prioritize warehouses with lowest inventory coverage

        Logic:
        - For each item, rank warehouses by inventory coverage (INV / Demand)
        - Allocate PO to warehouse with lowest coverage first
        - Fill safety stock gaps before moving to next warehouse

        Returns:
            Dictionary with results
        """
        if verbose:
            print("\n" + "="*60)
            print("GREEDY HEURISTIC")
            print("="*60)
            print("Allocation Rule: Prioritize lowest inventory coverage")

        firm_data = self._extract_firm_po_data()

        allocation_list = []

        for item in firm_data['ITEM'].unique():
            item_data = firm_data[firm_data['ITEM'] == item].copy()

            # Total firm PO for this item
            total_po = item_data['TOTAL_FIRM_QTY'].sum()
            remaining_po = total_po

            # Calculate inventory coverage ratio
            item_data['COVERAGE'] = (
                item_data['CURRENT_INV'] /
                (item_data['DEMAND_3_4'] + 1)  # +1 to avoid division by zero
            )

            # Sort by coverage (lowest first)
            item_data = item_data.sort_values('COVERAGE')

            # Allocate greedily
            for _, row in item_data.iterrows():
                if remaining_po <= 0:
                    allocated_qty = 0
                else:
                    # Calculate gap to safety stock
                    gap = max(0, row['SAFETY_STOCK'] - row['CURRENT_INV'])

                    # Allocate min(gap + demand, remaining_po)
                    allocated_qty = min(gap + row['DEMAND_3_4'], remaining_po)
                    remaining_po -= allocated_qty

                allocation_list.append({
                    'ITEM': row['ITEM'],
                    'WHIDI1': row['WHIDI1'],
                    'ALLOCATED_QTY': allocated_qty
                })

        allocation_df = pd.DataFrame(allocation_list)

        # Calculate cost
        total_cost = self._calculate_cost(allocation_df)

        if verbose:
            print(f"\nTotal Cost: ${total_cost:,.2f}")
            print(f"Items processed: {len(firm_data['ITEM'].unique())}")

        self.results['greedy'] = {
            'Method': 'Greedy Heuristic',
            'Total Cost': total_cost,
            'Allocation': allocation_df,
            'Description': 'Prioritize warehouses with lowest inventory coverage'
        }

        return self.results['greedy']

    def roundrobin_heuristic(self, verbose=True) -> Dict:
        """
        Round-robin allocation: Distribute PO evenly in rotation

        Logic:
        - For each item, distribute total PO equally across all warehouses
        - Simple, unbiased baseline

        Returns:
            Dictionary with results
        """
        if verbose:
            print("\n" + "="*60)
            print("ROUND-ROBIN HEURISTIC")
            print("="*60)
            print("Allocation Rule: Equal distribution across warehouses")

        firm_data = self._extract_firm_po_data()

        allocation_list = []

        for item in firm_data['ITEM'].unique():
            item_data = firm_data[firm_data['ITEM'] == item]

            # Total firm PO for this item
            total_po = item_data['TOTAL_FIRM_QTY'].sum()

            # Number of warehouses for this item
            n_warehouses = len(item_data)

            # Distribute evenly
            qty_per_warehouse = total_po / n_warehouses

            for _, row in item_data.iterrows():
                allocation_list.append({
                    'ITEM': row['ITEM'],
                    'WHIDI1': row['WHIDI1'],
                    'ALLOCATED_QTY': qty_per_warehouse
                })

        allocation_df = pd.DataFrame(allocation_list)

        # Calculate cost
        total_cost = self._calculate_cost(allocation_df)

        if verbose:
            print(f"\nTotal Cost: ${total_cost:,.2f}")
            print(f"Items processed: {len(firm_data['ITEM'].unique())}")

        self.results['roundrobin'] = {
            'Method': 'Round-Robin Heuristic',
            'Total Cost': total_cost,
            'Allocation': allocation_df,
            'Description': 'Equal distribution across all warehouses'
        }

        return self.results['roundrobin']

    def run_all(self, verbose=True) -> Dict:
        """Run all three heuristics and return results"""

        if verbose:
            print("\n" + "="*80)
            print("RUNNING ALL SIMPLE HEURISTICS")
            print("="*80)

        self.prorata_heuristic(verbose=verbose)
        self.greedy_heuristic(verbose=verbose)
        self.roundrobin_heuristic(verbose=verbose)

        if verbose:
            print("\n" + "="*80)
            print("HEURISTICS SUMMARY")
            print("="*80)
            for key, result in self.results.items():
                print(f"\n{result['Method']}: ${result['Total Cost']:,.2f}")

        return self.results
