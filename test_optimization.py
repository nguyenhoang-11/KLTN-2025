"""
Test script for Destination Change Optimization
"""

from dss_system.data.loader_afi import AFIDataLoader
from dss_system.optimization import DestinationChangeOptimizer

# Load AFI data
print("Loading AFI data...")
loader = AFIDataLoader(file_path='AFI - DESTINATION CHANGE FOR UN KIT - TEST (1).xlsb')
loader.load_all()  # Load all data

# Create optimizer
print("\nCreating optimizer with alpha=2.0...")
optimizer = DestinationChangeOptimizer(loader, alpha=2.0)

# Run optimization
print("\nRunning optimization...")
summary = optimizer.optimize(verbose=True)

if summary:
    print("\n" + "="*60)
    print("OPTIMIZATION SUMMARY")
    print("="*60)
    for key, value in summary.items():
        if isinstance(value, float):
            print(f"{key:20s}: {value:,.2f}")
        else:
            print(f"{key:20s}: {value}")

    # Get changes dataframe
    print("\n" + "="*60)
    print("DESTINATION CHANGES (First 10)")
    print("="*60)
    changes_df = optimizer.get_changes_dataframe()
    print(changes_df.head(10))

    # Get cost breakdown
    print("\n" + "="*60)
    print("COST BREAKDOWN")
    print("="*60)
    cost_df = optimizer.get_cost_breakdown_dataframe()
    print(cost_df)
else:
    print("\nOptimization failed!")
