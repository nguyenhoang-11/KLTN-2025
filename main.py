"""
Main entry point for DSS System
"""

import sys
from pathlib import Path

# Add dss_system to path
sys.path.insert(0, str(Path(__file__).parent))

from dss_system.data.loader import SupplyChainDataLoader
from dss_system.data.validator import DataValidator
from dss_system.network.graph import SupplyChainNetwork
from dss_system.network.analysis import NetworkAnalyzer
from dss_system.visualization.dashboard import Dashboard
from dss_system.utils.config import config


def main():
    """Main execution flow"""
    print("="*80)
    print("DECISION SUPPORT SYSTEM FOR INVENTORY POOLING")
    print("B2B Supply Network - Lateral Transshipment & Coordinated Replenishment")
    print("="*80)

    # Ensure output directories exist
    config.ensure_directories()

    # Step 1: Load data
    print("\n[1/5] Loading data...")
    loader = SupplyChainDataLoader()
    data = loader.load_all()

    # Step 2: Validate data
    print("\n[2/5] Validating data...")
    validator = DataValidator(loader)
    validator.print_validation_report()

    # Step 3: Build network
    print("\n[3/5] Building network graph...")
    network = SupplyChainNetwork(loader)
    metrics = network.calculate_network_metrics()
    print(f"✓ Network built: {metrics['num_nodes']} nodes, {metrics['num_edges']} edges")

    # Step 4: Analyze network
    print("\n[4/5] Analyzing network and data...")
    analyzer = NetworkAnalyzer(network, loader)

    demand_analysis = analyzer.analyze_demand_patterns()
    print(f"✓ Total demand: {demand_analysis['total_demand']:,.0f} units")

    inv_analysis = analyzer.analyze_inventory_metrics()
    print(f"✓ Total inventory: {inv_analysis['total_on_hand']:,.0f} units")

    # Step 5: Generate outputs
    print("\n[5/5] Generating visualizations and reports...")
    dashboard = Dashboard(network, loader, analyzer)

    # Create visualizations
    viz_dir = config.get('paths.visualizations')
    dashboard.create_all_visualizations(viz_dir)

    # Export reports
    report_dir = config.get('paths.reports')
    dashboard.export_results(report_dir)

    # Print summary
    print("\n" + "="*80)
    print("DSS SYSTEM INITIALIZATION COMPLETE!")
    print("="*80)
    print(f"\n📊 Visualizations: {viz_dir}")
    print(f"📄 Reports: {report_dir}")
    print(f"📈 Results: {config.get('paths.results')}")

    print("\n📌 Next Steps:")
    print("  1. Review visualizations in browser")
    print("  2. Analyze optimization opportunities in report")
    print("  3. Run optimization models (coming soon)")

    # Print optimization opportunities
    opportunities = analyzer.identify_optimization_opportunities()
    if opportunities['inventory_rebalancing']:
        print(f"\n💡 Found {len(opportunities['inventory_rebalancing'])} inventory rebalancing opportunities")
        print("   Run optimization models to get detailed recommendations")


if __name__ == "__main__":
    main()
