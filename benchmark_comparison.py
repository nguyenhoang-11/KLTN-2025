"""
Benchmark Comparison: Destination Change MILP vs Simple Baselines
Compare MILP optimization with no-optimization baseline and simple random allocation
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from dss_system.data.loader_afi import AFIDataLoader
from dss_system.optimization import DestinationChangeOptimizer
import pandas as pd
import numpy as np
from datetime import datetime


def main():
    print("="*80)
    print("BENCHMARK COMPARISON: MILP OPTIMIZATION VS BASELINE")
    print("="*80)
    print(f"\nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n" + "="*80)

    # Load AFI data
    print("\n[1/2] Loading AFI data...")
    loader = AFIDataLoader(file_path='AFI - DESTINATION CHANGE FOR UN KIT - TEST (1).xlsb')
    loader.load_all()
    print(f"   Loaded: {len(loader.item)} item records, {len(loader.time_series)} time series records")

    # Run Destination Change MILP
    print("\n[2/2] Running Destination Change MILP Optimization...")
    print("-" * 80)
    dc_optimizer = DestinationChangeOptimizer(
        loader,
        alpha=2.0,
        pel_cost=None,
        act_cost=None
    )
    dc_summary = dc_optimizer.optimize(verbose=True)

    # Get baseline cost from Destination Change model
    baseline_cost = dc_summary['Baseline Cost']
    optimized_cost = dc_summary['Optimized Cost']
    savings = dc_summary['Total Savings']
    savings_pct = dc_summary['Savings %']

    # Generate Comparison Report
    print("\n" + "="*80)
    print(" "*20 + "BENCHMARK COMPARISON RESULTS")
    print("="*80)
    print(f"\nBaseline: ${baseline_cost:,.2f} (Original firm PO allocation)")
    print(f"MILP Optimized: ${optimized_cost:,.2f}")
    print(f"Savings: ${savings:,.2f} ({savings_pct:.2f}%)")

    # Create comparison table
    methods_data = []

    # Baseline (No Optimization)
    methods_data.append({
        'Method': 'Baseline (No Optimization)',
        'Total Cost ($)': baseline_cost,
        'Savings ($)': 0.0,
        'Savings (%)': 0.0,
        'Description': 'Keep original firm PO allocation as-is'
    })

    # Destination Change MILP
    methods_data.append({
        'Method': 'Destination Change MILP',
        'Total Cost ($)': optimized_cost,
        'Savings ($)': savings,
        'Savings (%)': savings_pct,
        'Description': 'Alpha-weighted MILP optimization with safety stock constraints'
    })

    comparison_df = pd.DataFrame(methods_data)

    # Display comparison
    print("\n" + "-"*80)
    print("COMPARISON TABLE")
    print("-"*80)
    print("\n" + comparison_df.to_string(index=False))

    # Performance Analysis
    print("\n" + "="*80)
    print("PERFORMANCE ANALYSIS")
    print("="*80)
    print(f"\nYour MILP model achieves {savings_pct:.2f}% cost savings")
    print(f"This represents ${savings:,.2f} in cost reduction")

    if savings_pct > 10:
        print(f"\n[EXCELLENT] Savings > 10% indicates strong optimization value!")
    elif savings_pct > 5:
        print(f"\n[GOOD] Savings > 5% shows meaningful optimization impact")
    elif savings_pct > 0:
        print(f"\n[POSITIVE] Model achieves cost reduction")
    else:
        print(f"\n[WARNING] No savings achieved")

    # Cost Breakdown
    print("\n" + "="*80)
    print("DETAILED COST BREAKDOWN")
    print("="*80)

    print(f"\nBaseline (No Optimization):")
    print(f"   Total Cost: ${baseline_cost:,.2f}")
    print(f"   Strategy: Keep firm PO destination as originally allocated")

    print(f"\nDestination Change MILP:")
    print(f"   Total Cost: ${optimized_cost:,.2f}")
    print(f"   Alpha Weight: {dc_optimizer.alpha} (prioritizes W3-W4 over W5-W6)")
    print(f"   Savings: ${savings:,.2f} ({savings_pct:.2f}%)")

    print(f"\nKey Optimization Features:")
    print(f"   - PO destination reallocation across warehouses")
    print(f"   - Alpha-weighted objective (near-term priority)")
    print(f"   - Safety stock constraint enforcement")
    print(f"   - Handling cost vs stockout cost balance")

    # Export results
    print("\n" + "="*80)
    print("EXPORT RESULTS")
    print("="*80)

    # Save comparison to CSV
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"benchmark_results_{timestamp}.csv"
    comparison_df.to_csv(filename, index=False)
    print(f"\n[SUCCESS] Comparison table saved to: {filename}")

    # Save detailed report
    report_filename = f"benchmark_report_{timestamp}.txt"
    with open(report_filename, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("BENCHMARK COMPARISON REPORT\n")
        f.write("DESTINATION CHANGE MILP OPTIMIZATION\n")
        f.write("="*80 + "\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        f.write("COMPARISON TABLE:\n")
        f.write(comparison_df.to_string(index=False) + "\n\n")

        f.write("="*80 + "\n")
        f.write("PERFORMANCE SUMMARY\n")
        f.write("="*80 + "\n\n")
        f.write(f"Baseline Cost (Firm PO, no optimization): ${baseline_cost:,.2f}\n")
        f.write(f"Optimized Cost (MILP):                     ${optimized_cost:,.2f}\n")
        f.write(f"Total Savings:                             ${savings:,.2f}\n")
        f.write(f"Savings Percentage:                        {savings_pct:.2f}%\n\n")

        f.write("="*80 + "\n")
        f.write("METHODOLOGY\n")
        f.write("="*80 + "\n\n")

        f.write("Baseline Approach:\n")
        f.write("- Keep firm purchase orders allocated to original warehouses\n")
        f.write("- No optimization or reallocation\n")
        f.write("- Represents current business practice\n\n")

        f.write("MILP Optimization Approach:\n")
        f.write(f"- Alpha-weighted objective function (alpha = {dc_optimizer.alpha})\n")
        f.write("- Prioritizes near-term inventory balance (weeks 3-4)\n")
        f.write("- Considers weeks 5-6 with reduced weight\n")
        f.write("- Enforces safety stock lower/upper bound constraints\n")
        f.write("- Minimizes handling cost (overstocking) + stockout cost (understocking)\n")
        f.write("- Penalty costs for bound violations\n\n")

        f.write("="*80 + "\n")
        f.write("CONCLUSION\n")
        f.write("="*80 + "\n\n")

        if savings_pct > 10:
            f.write(f"The Destination Change MILP model achieves EXCELLENT results with\n")
            f.write(f"{savings_pct:.2f}% cost savings (${savings:,.2f}) compared to baseline.\n\n")
            f.write(f"This demonstrates significant value from optimization:\n")
            f.write(f"1. Strategic PO reallocation reduces total cost\n")
            f.write(f"2. Alpha-weighted objective effectively prioritizes near-term\n")
            f.write(f"3. Safety stock constraints prevent excessive imbalance\n")
            f.write(f"4. MILP formulation finds optimal allocation\n\n")
            f.write(f"RECOMMENDATION: Deploy this model for production use\n")
        elif savings_pct > 5:
            f.write(f"The Destination Change MILP model achieves GOOD results with\n")
            f.write(f"{savings_pct:.2f}% cost savings (${savings:,.2f}) compared to baseline.\n\n")
            f.write(f"This shows meaningful optimization value that justifies deployment.\n")
        elif savings_pct > 0:
            f.write(f"The MILP model achieves positive savings of {savings_pct:.2f}%.\n")
            f.write(f"Consider parameter tuning (alpha, costs) for better results.\n")
        else:
            f.write(f"Model requires further investigation and tuning.\n")

    print(f"[SUCCESS] Detailed report saved to: {report_filename}")

    print("\n" + "="*80)
    print("BENCHMARK COMPARISON COMPLETED")
    print("="*80)


if __name__ == "__main__":
    main()
