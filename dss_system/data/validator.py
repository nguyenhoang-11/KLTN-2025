"""Data validation module"""

import pandas as pd
from typing import Dict, List
from .loader import SupplyChainDataLoader


class DataValidator:
    """Validate data integrity and quality"""

    def __init__(self, loader: SupplyChainDataLoader):
        self.loader = loader

    def validate_all(self) -> Dict[str, List[str]]:
        """Validate all data and return issues"""
        issues = {
            'missing_values': [],
            'data_quality': [],
            'referential_integrity': []
        }

        # Check for missing values
        for name, df in self.loader.get_all_data().items():
            if df is not None:
                missing = df.isnull().sum()
                if missing.any():
                    issues['missing_values'].append(
                        f"{name}: {missing[missing > 0].to_dict()}"
                    )

        # Check referential integrity
        facility_codes = set(self.loader.facilities['facility_code'])
        product_codes = set(self.loader.products['product_code'])

        # Check demand references
        invalid_facilities = set(self.loader.demand['facility_code']) - facility_codes
        if invalid_facilities:
            issues['referential_integrity'].append(
                f"Demand has invalid facility codes: {invalid_facilities}"
            )

        invalid_products = set(self.loader.demand['product_code']) - product_codes
        if invalid_products:
            issues['referential_integrity'].append(
                f"Demand has invalid product codes: {invalid_products}"
            )

        # Check inventory references
        invalid_inv_facilities = set(self.loader.inventory['facility_code']) - facility_codes
        if invalid_inv_facilities:
            issues['referential_integrity'].append(
                f"Inventory has invalid facility codes: {invalid_inv_facilities}"
            )

        # Check data quality
        if (self.loader.inventory['available_quantity'] >
            self.loader.inventory['on_hand']).any():
            issues['data_quality'].append(
                "Some inventory records have available_quantity > on_hand"
            )

        return issues

    def print_validation_report(self):
        """Print validation report"""
        issues = self.validate_all()

        print("="*60)
        print("DATA VALIDATION REPORT")
        print("="*60)

        for category, problems in issues.items():
            print(f"\n{category.upper().replace('_', ' ')}:")
            if problems:
                for problem in problems:
                    print(f"  ⚠ {problem}")
            else:
                print(f"  ✓ No issues found")
