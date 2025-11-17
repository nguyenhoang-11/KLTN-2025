"""Network analysis and metrics"""

import pandas as pd
import numpy as np
from typing import Dict, List
from .graph import SupplyChainNetwork


class NetworkAnalyzer:
    """Analyze network structure and patterns"""

    def __init__(self, network: SupplyChainNetwork, loader):
        self.network = network
        self.loader = loader

    def analyze_connectivity(self) -> Dict:
        """Analyze network connectivity patterns"""
        analysis = {
            'in_degree': dict(self.network.graph.in_degree()),
            'out_degree': dict(self.network.graph.out_degree()),
            'isolated_nodes': [],
            'hubs': []
        }

        import networkx as nx
        isolated = list(nx.isolates(self.network.graph))
        analysis['isolated_nodes'] = isolated

        # Identify hub facilities (high degree centrality)
        degree_centrality = nx.degree_centrality(self.network.graph)
        avg_centrality = np.mean(list(degree_centrality.values()))
        analysis['hubs'] = [node for node, cent in degree_centrality.items()
                           if cent > avg_centrality * 1.5]

        return analysis

    def analyze_demand_patterns(self) -> Dict:
        """Analyze demand patterns across facilities and products"""
        demand_df = self.loader.demand.copy()

        analysis = {
            'total_demand': demand_df['total_demand'].sum(),
            'avg_daily_demand': demand_df.groupby('demand_date')['total_demand'].sum().mean(),
            'demand_variability': demand_df.groupby('demand_date')['total_demand'].sum().std(),
            'coefficient_of_variation': None,
            'by_facility': {},
            'by_product': {},
            'by_abc_class': {}
        }

        # Calculate CV
        if analysis['avg_daily_demand'] > 0:
            analysis['coefficient_of_variation'] = (
                analysis['demand_variability'] / analysis['avg_daily_demand']
            )

        # Demand by facility
        for facility in demand_df['facility_code'].unique():
            fac_demand = demand_df[demand_df['facility_code'] == facility]['total_demand']
            analysis['by_facility'][facility] = {
                'total': fac_demand.sum(),
                'avg_daily': fac_demand.mean(),
                'std_dev': fac_demand.std(),
                'max': fac_demand.max(),
                'min': fac_demand.min()
            }

        # Demand by product
        product_demand = demand_df.groupby('product_code')['total_demand'].agg(
            ['sum', 'mean', 'std']
        ).to_dict('index')
        analysis['by_product'] = product_demand

        # Demand by ABC classification
        products = self.loader.products
        demand_with_abc = demand_df.merge(
            products[['product_code', 'abc_classification']],
            on='product_code'
        )
        abc_demand = demand_with_abc.groupby('abc_classification')['total_demand'].agg(
            ['sum', 'mean', 'count']
        )
        analysis['by_abc_class'] = abc_demand.to_dict('index')

        return analysis

    def analyze_inventory_metrics(self) -> Dict:
        """Analyze inventory metrics and performance"""
        inv_df = self.loader.inventory.copy()

        analysis = {
            'total_on_hand': inv_df['on_hand'].sum(),
            'total_available': inv_df['available_quantity'].sum(),
            'total_safety_stock': inv_df['safety_stock'].sum(),
            'avg_days_of_supply': inv_df['days_of_supply'].mean(),
            'by_facility': {},
            'stockout_risk': {},
            'excess_inventory': {}
        }

        # Inventory by facility
        for facility in inv_df['facility_code'].unique():
            fac_inv = inv_df[inv_df['facility_code'] == facility]
            analysis['by_facility'][facility] = {
                'on_hand': fac_inv['on_hand'].sum(),
                'available': fac_inv['available_quantity'].sum(),
                'safety_stock': fac_inv['safety_stock'].sum(),
                'avg_days_supply': fac_inv['days_of_supply'].mean(),
                'num_products': len(fac_inv)
            }

        # Stockout risk
        stockout_risk = inv_df[inv_df['available_quantity'] < inv_df['safety_stock']]
        if len(stockout_risk) > 0:
            analysis['stockout_risk'] = {
                'num_items': len(stockout_risk),
                'items': stockout_risk[
                    ['facility_code', 'product_code', 'available_quantity', 'safety_stock']
                ].to_dict('records')
            }

        # Excess inventory
        excess = inv_df[inv_df['days_of_supply'] > 30]
        if len(excess) > 0:
            analysis['excess_inventory'] = {
                'num_items': len(excess),
                'total_units': excess['on_hand'].sum(),
                'items': excess[
                    ['facility_code', 'product_code', 'on_hand', 'days_of_supply']
                ].to_dict('records')
            }

        return analysis

    def analyze_transfer_patterns(self) -> Dict:
        """Analyze lateral transshipment patterns"""
        transfers = self.loader.transfers.copy()

        analysis = {
            'total_transfers': len(transfers),
            'total_quantity': transfers['quantity'].sum(),
            'total_cost': transfers['transport_cost'].sum(),
            'avg_cost_per_unit': transfers['transport_cost'].sum() / transfers['quantity'].sum()
                                if transfers['quantity'].sum() > 0 else 0,
            'by_route': {},
            'most_active_routes': []
        }

        # Transfers by route
        route_agg = transfers.groupby(['from_facility', 'to_facility']).agg({
            'quantity': 'sum',
            'transport_cost': 'sum',
            'transfer_id': 'count'
        }).reset_index()
        route_agg.columns = ['from_facility', 'to_facility', 'total_quantity',
                            'total_cost', 'num_transfers']
        route_agg['cost_per_unit'] = route_agg['total_cost'] / route_agg['total_quantity']

        analysis['by_route'] = route_agg.to_dict('records')
        analysis['most_active_routes'] = route_agg.nlargest(5, 'total_quantity').to_dict('records')

        return analysis

    def identify_optimization_opportunities(self) -> Dict:
        """Identify potential optimization opportunities"""
        opportunities = {
            'inventory_rebalancing': [],
            'cost_reduction': [],
            'service_improvement': []
        }

        inventory = self.loader.inventory
        demand = self.loader.demand
        products = self.loader.products

        # Inventory imbalance opportunities
        for product in inventory['product_code'].unique():
            prod_inv = inventory[inventory['product_code'] == product]
            excess_facilities = prod_inv[prod_inv['days_of_supply'] > 20]
            shortage_facilities = prod_inv[prod_inv['days_of_supply'] < 5]

            if len(excess_facilities) > 0 and len(shortage_facilities) > 0:
                opportunities['inventory_rebalancing'].append({
                    'product': product,
                    'excess_facilities': excess_facilities[
                        ['facility_code', 'on_hand', 'days_of_supply']
                    ].to_dict('records'),
                    'shortage_facilities': shortage_facilities[
                        ['facility_code', 'on_hand', 'days_of_supply']
                    ].to_dict('records'),
                    'action': 'Consider lateral transshipment from excess to shortage facilities'
                })

        return opportunities
