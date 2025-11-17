"""Dashboard and report generation"""

import pandas as pd
import json
from pathlib import Path
from typing import Dict
from .network_viz import NetworkVisualizer


class Dashboard:
    """Generate dashboard and reports"""

    def __init__(self, network, loader, analyzer):
        self.network = network
        self.loader = loader
        self.analyzer = analyzer
        self.visualizer = NetworkVisualizer(network, loader)

    def create_all_visualizations(self, output_dir: str):
        """Create and save all visualizations"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        print("Creating visualizations...")

        # Network diagram
        fig1 = self.visualizer.create_network_diagram()
        fig1.write_html(output_path / "network_diagram.html")
        print("✓ Network diagram saved")

        # Inventory heatmap
        fig2 = self.visualizer.create_inventory_heatmap()
        fig2.write_html(output_path / "inventory_heatmap.html")
        print("✓ Inventory heatmap saved")

        # Demand pattern
        fig3 = self.visualizer.create_demand_pattern_chart()
        fig3.write_html(output_path / "demand_pattern.html")
        print("✓ Demand pattern chart saved")

        # Transfer flow
        fig4 = self.visualizer.create_transfer_flow_sankey()
        fig4.write_html(output_path / "transfer_flow.html")
        print("✓ Transfer flow diagram saved")

    def generate_text_report(self) -> str:
        """Generate comprehensive text report"""
        report = []
        report.append("="*80)
        report.append("SUPPLY CHAIN DECISION SUPPORT SYSTEM - ANALYSIS REPORT")
        report.append("="*80)

        # Network summary
        summary = self.loader.get_network_summary()
        report.append("\n## NETWORK OVERVIEW")
        report.append(f"Total Facilities: {summary['num_facilities']}")
        report.append(f"Total Products: {summary['num_products']}")
        report.append(f"Transportation Routes: {summary['num_routes']}")
        report.append(f"Data Period: {summary['date_range'][0]} to {summary['date_range'][1]} ({summary['total_days']} days)")

        # Demand analysis
        demand_analysis = self.analyzer.analyze_demand_patterns()
        report.append("\n## DEMAND ANALYSIS")
        report.append(f"Total Demand: {demand_analysis['total_demand']:,.0f} units")
        report.append(f"Average Daily Demand: {demand_analysis['avg_daily_demand']:.1f} units")
        report.append(f"Demand Variability (Std Dev): {demand_analysis['demand_variability']:.1f}")

        # Inventory analysis
        inv_analysis = self.analyzer.analyze_inventory_metrics()
        report.append("\n## INVENTORY ANALYSIS")
        report.append(f"Total On-Hand: {inv_analysis['total_on_hand']:,.0f} units")
        report.append(f"Total Available: {inv_analysis['total_available']:,.0f} units")
        report.append(f"Average Days of Supply: {inv_analysis['avg_days_of_supply']:.1f} days")

        if inv_analysis.get('stockout_risk', {}).get('num_items', 0) > 0:
            report.append(f"\n⚠ Stockout Risk: {inv_analysis['stockout_risk']['num_items']} items below safety stock")

        # Transfer analysis
        transfer_analysis = self.analyzer.analyze_transfer_patterns()
        report.append("\n## LATERAL TRANSSHIPMENT ANALYSIS")
        report.append(f"Total Transfers: {transfer_analysis['total_transfers']}")
        report.append(f"Total Quantity Transferred: {transfer_analysis['total_quantity']:,.0f} units")
        report.append(f"Total Transfer Cost: ${transfer_analysis['total_cost']:,.2f}")

        # Optimization opportunities
        opportunities = self.analyzer.identify_optimization_opportunities()
        report.append("\n## OPTIMIZATION OPPORTUNITIES")
        if opportunities['inventory_rebalancing']:
            report.append(f"\nInventory Rebalancing: {len(opportunities['inventory_rebalancing'])} opportunities")

        report.append("\n" + "="*80)
        return "\n".join(report)

    def export_results(self, output_dir: str):
        """Export all results"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Text report
        report = self.generate_text_report()
        with open(output_path / "analysis_report.txt", "w", encoding='utf-8') as f:
            f.write(report)
        print("✓ Analysis report saved")

        # JSON data
        analysis_data = {
            'demand_analysis': self.analyzer.analyze_demand_patterns(),
            'inventory_analysis': self.analyzer.analyze_inventory_metrics(),
            'transfer_analysis': self.analyzer.analyze_transfer_patterns(),
            'optimization_opportunities': self.analyzer.identify_optimization_opportunities()
        }

        # Convert types for JSON
        def convert_types(obj):
            import numpy as np
            if isinstance(obj, (np.integer, np.int64)):
                return int(obj)
            elif isinstance(obj, (np.floating, np.float64)):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, pd.Timestamp):
                return str(obj)
            elif isinstance(obj, dict):
                return {k: convert_types(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_types(item) for item in obj]
            return obj

        analysis_data = convert_types(analysis_data)

        with open(output_path / "analysis_data.json", "w", encoding='utf-8') as f:
            json.dump(analysis_data, f, indent=2, ensure_ascii=False)
        print("✓ Analysis data saved")

        print(f"\nAll outputs saved to: {output_path}")
