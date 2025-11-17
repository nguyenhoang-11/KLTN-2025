"""
Data Loader Module for Supply Chain DSS
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime


class SupplyChainDataLoader:
    """Load and manage all supply chain data"""

    def __init__(self, data_dir: str = None):
        from ..utils.config import config
        self.data_dir = Path(data_dir) if data_dir else config.get_data_dir()
        self.facilities = None
        self.products = None
        self.demand = None
        self.inventory = None
        self.transfers = None
        self.transportation = None
        self.procurement = None
        self.production = None

    def load_all(self) -> Dict[str, pd.DataFrame]:
        """Load all CSV files into DataFrames"""
        print(f"Loading supply chain data from {self.data_dir}...")

        # Load each file
        self.facilities = pd.read_csv(self.data_dir / "facilities.csv")
        self.products = pd.read_csv(self.data_dir / "products.csv")
        self.demand = pd.read_csv(self.data_dir / "demand.csv")
        self.inventory = pd.read_csv(self.data_dir / "inventory.csv")
        self.transfers = pd.read_csv(self.data_dir / "transfers.csv")
        self.transportation = pd.read_csv(self.data_dir / "transportation.csv")
        self.procurement = pd.read_csv(self.data_dir / "procurement.csv")

        try:
            self.production = pd.read_csv(self.data_dir / "production.csv")
        except FileNotFoundError:
            print("Warning: production.csv not found")

        # Convert date columns
        self._convert_dates()

        print(f"✓ Loaded {len(self.facilities)} facilities")
        print(f"✓ Loaded {len(self.products)} products")
        print(f"✓ Loaded {len(self.demand)} demand records")
        print(f"✓ Loaded {len(self.inventory)} inventory records")
        print(f"✓ Loaded {len(self.transfers)} transfer transactions")

        return self.get_all_data()

    def _convert_dates(self):
        """Convert date columns to datetime"""
        date_columns = {
            'demand': 'demand_date',
            'inventory': 'inventory_date',
            'transfers': 'transfer_date',
            'procurement': 'procurement_date'
        }

        for df_name, col_name in date_columns.items():
            df = getattr(self, df_name)
            if df is not None and col_name in df.columns:
                df[col_name] = pd.to_datetime(df[col_name])

    def get_all_data(self) -> Dict[str, pd.DataFrame]:
        """Return dictionary of all DataFrames"""
        return {
            'facilities': self.facilities,
            'products': self.products,
            'demand': self.demand,
            'inventory': self.inventory,
            'transfers': self.transfers,
            'transportation': self.transportation,
            'procurement': self.procurement,
            'production': self.production
        }

    def get_network_summary(self) -> Dict:
        """Get high-level network summary"""
        summary = {
            'num_facilities': len(self.facilities),
            'num_products': len(self.products),
            'num_routes': len(self.transportation),
            'date_range': (
                self.demand['demand_date'].min(),
                self.demand['demand_date'].max()
            ),
            'total_days': (self.demand['demand_date'].max() -
                          self.demand['demand_date'].min()).days + 1,
            'facilities_by_type': self.facilities.groupby('facility_type').size().to_dict(),
            'products_by_classification': self.products.groupby('abc_classification').size().to_dict()
        }
        return summary

    def get_facility_info(self, facility_code: str = None) -> pd.DataFrame:
        """Get facility information"""
        if facility_code:
            return self.facilities[self.facilities['facility_code'] == facility_code]
        return self.facilities

    def get_product_info(self, product_code: str = None) -> pd.DataFrame:
        """Get product information"""
        if product_code:
            return self.products[self.products['product_code'] == product_code]
        return self.products

    def get_demand_by_facility(self, facility_code: str) -> pd.DataFrame:
        """Get demand data for specific facility"""
        return self.demand[self.demand['facility_code'] == facility_code].copy()

    def get_demand_by_product(self, product_code: str) -> pd.DataFrame:
        """Get demand data for specific product"""
        return self.demand[self.demand['product_code'] == product_code].copy()

    def get_inventory_snapshot(self, facility_code: str = None) -> pd.DataFrame:
        """Get current inventory snapshot"""
        if facility_code:
            return self.inventory[self.inventory['facility_code'] == facility_code].copy()
        return self.inventory

    def get_transfer_history(self, from_facility: str = None,
                            to_facility: str = None) -> pd.DataFrame:
        """Get transfer history with optional filtering"""
        df = self.transfers.copy()
        if from_facility:
            df = df[df['from_facility'] == from_facility]
        if to_facility:
            df = df[df['to_facility'] == to_facility]
        return df

    def get_transportation_costs(self, from_facility: str = None,
                                to_facility: str = None) -> pd.DataFrame:
        """Get transportation cost matrix"""
        df = self.transportation.copy()
        if from_facility:
            df = df[df['from_facility'] == from_facility]
        if to_facility:
            df = df[df['to_facility'] == to_facility]
        return df
