"""
AFI Data Loader - Load real enterprise data from XLSB file
Handles Ashley Furniture Industries supply chain data
"""

import pandas as pd
import numpy as np
from pathlib import Path
from pyxlsb import open_workbook
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AFIDataLoader:
    """
    Load and process AFI enterprise supply chain data

    Data structure:
    - ITEM: Product master data (99 items × 17 warehouses)
    - ETD: 12-week forecast by warehouse
    - TIME_SERIES: Inventory balance, bounds, firm POs
    - HOT LIST: Priority items tracking
    - ECO: Economic costs (backorder costs)
    - DEST_CH: Destination change analysis
    """

    def __init__(self, file_path: str = None):
        """
        Initialize AFI data loader

        Args:
            file_path: Path to XLSB file. Defaults to AFI file in project root.
        """
        if file_path is None:
            # Default to AFI file in project root
            file_path = Path(__file__).parent.parent.parent / 'AFI - DESTINATION CHANGE FOR UN KIT - TEST (1).xlsb'

        self.file_path = Path(file_path)

        if not self.file_path.exists():
            raise FileNotFoundError(f"AFI data file not found: {self.file_path}")

        # Data containers
        self.item = None
        self.etd = None
        self.time_series = None
        self.hot_list = None
        self.eco = None
        self.dest_ch = None
        self.workload = None

        logger.info(f"AFI Data Loader initialized with file: {self.file_path}")

    def load_all(self):
        """Load all sheets from XLSB file"""
        logger.info("Loading all AFI data sheets...")

        try:
            wb = open_workbook(str(self.file_path))

            # Load key sheets
            self.item = self._load_sheet(wb, 'ITEM')
            self.etd = self._load_sheet(wb, 'ETD')
            self.time_series = self._load_sheet(wb, 'TIME_SERIES')
            self.hot_list = self._load_sheet(wb, 'HOT LIST')
            self.eco = self._load_sheet(wb, 'ECO')
            self.dest_ch = self._load_sheet(wb, 'DEST_CH')
            self.workload = self._load_sheet(wb, 'WORKLOAD')

            wb.close()

            # Post-process data
            self._process_dates()
            self._clean_data()

            logger.info("All AFI data loaded successfully")
            self._print_summary()

        except Exception as e:
            logger.error(f"Error loading AFI data: {e}")
            raise

    def _load_sheet(self, workbook, sheet_name: str) -> pd.DataFrame:
        """Load a single sheet from workbook"""
        logger.info(f"  Loading sheet: {sheet_name}")

        try:
            with workbook.get_sheet(sheet_name) as sheet:
                data = []
                for row in sheet.rows():
                    data.append([item.v if item is not None else None for item in row])

                if len(data) <= 1:
                    logger.warning(f"    WARNING: Sheet {sheet_name} is empty or has only header")
                    return pd.DataFrame()

                # First row is header
                df = pd.DataFrame(data[1:], columns=data[0])

                logger.info(f"    Loaded {len(df)} rows x {len(df.columns)} columns")
                return df

        except Exception as e:
            logger.error(f"    ERROR: Loading sheet {sheet_name}: {e}")
            return pd.DataFrame()

    def _process_dates(self):
        """Convert Excel date numbers to datetime"""
        if self.etd is not None and not self.etd.empty:
            # ETD sheet has date columns as numbers (45976, 45983, etc.)
            # These are Excel serial dates
            date_cols = [col for col in self.etd.columns if str(col).replace('.', '').isdigit()]

            for col in date_cols:
                # Keep original for now, will convert during analysis
                pass

    def _clean_data(self):
        """Clean and standardize data"""
        # Convert numeric columns
        if self.time_series is not None:
            numeric_cols = ['BAL_W3', 'BAL_W4', 'BAL_W5', 'BAL_W6',
                          'LOWER_W3', 'LOWER_W4', 'LOWER_W5', 'LOWER_W6',
                          'UPPER_W3', 'UPPER_W4', 'UPPER_W5', 'UPPER_W6',
                          'FIRMPO_W3', 'FIRMPO_W4', 'SUM_FIRM']

            for col in numeric_cols:
                if col in self.time_series.columns:
                    self.time_series[col] = pd.to_numeric(self.time_series[col], errors='coerce')

        if self.item is not None:
            numeric_cols = ['BEGIN', 'MULT', 'OVST_C', 'UNST_C', 'PEL_C']
            for col in numeric_cols:
                if col in self.item.columns:
                    self.item[col] = pd.to_numeric(self.item[col], errors='coerce')

        if self.eco is not None and 'BCK_C' in self.eco.columns:
            self.eco['BCK_C'] = pd.to_numeric(self.eco['BCK_C'], errors='coerce')

    def _print_summary(self):
        """Print data loading summary"""
        logger.info("\n" + "="*70)
        logger.info("AFI DATA SUMMARY")
        logger.info("="*70)

        datasets = {
            'ITEM (Product Master)': self.item,
            'ETD (12-Week Forecast)': self.etd,
            'TIME_SERIES (Balance & Bounds)': self.time_series,
            'HOT LIST (Priority Items)': self.hot_list,
            'ECO (Economic Costs)': self.eco,
            'DEST_CH (Destination Change)': self.dest_ch,
            'WORKLOAD': self.workload
        }

        for name, df in datasets.items():
            if df is not None and not df.empty:
                logger.info(f"  {name:35s} | {len(df):4d} rows x {len(df.columns):3d} cols")
            else:
                logger.info(f"  {name:35s} | Empty")

        logger.info("="*70)

    # =========================================================================
    # DATA ACCESS METHODS
    # =========================================================================

    def get_warehouses(self) -> List[str]:
        """Get unique warehouse IDs"""
        if self.time_series is not None:
            return sorted(self.time_series['WHIDI1'].unique().tolist())
        return []

    def get_items(self) -> List[str]:
        """Get unique item codes"""
        if self.item is not None:
            return sorted(self.item['ITEM'].unique().tolist())
        return []

    def get_inventory_position(self, week: str = 'W3') -> pd.DataFrame:
        """
        Get current inventory position for a specific week

        Args:
            week: Week identifier (W3, W4, W5, W6)

        Returns:
            DataFrame with columns: ITEM, WHIDI1, BAL, LOWER, UPPER
        """
        if self.time_series is None:
            return pd.DataFrame()

        bal_col = f'BAL_{week}'
        lower_col = f'LOWER_{week}'
        upper_col = f'UPPER_{week}'

        if bal_col not in self.time_series.columns:
            return pd.DataFrame()

        result = self.time_series[['ITEM', 'WHIDI1', 'CODE1', 'CODE4',
                                    bal_col, lower_col, upper_col]].copy()
        result.columns = ['ITEM', 'WAREHOUSE', 'CODE1', 'CODE4', 'BALANCE', 'LOWER_BOUND', 'UPPER_BOUND']

        return result

    def get_forecast_data(self) -> pd.DataFrame:
        """
        Get 12-week forecast data from ETD sheet

        Returns:
            DataFrame in long format: ITEM, WAREHOUSE, WEEK, FORECAST_VALUE
        """
        if self.etd is None or self.etd.empty:
            return pd.DataFrame()

        # Find date columns (Excel serial numbers)
        date_cols = [col for col in self.etd.columns
                    if str(col).replace('.', '').replace('-', '').isdigit() and len(str(col)) >= 5]

        if len(date_cols) == 0:
            return pd.DataFrame()

        # Filter to safety stock data
        safety_stock = self.etd[self.etd['DATA'] == '03_SAFETY STK'].copy()

        if safety_stock.empty:
            return pd.DataFrame()

        # Melt to long format
        id_vars = ['ITEM', 'WHSE', 'BOX']
        result = safety_stock.melt(
            id_vars=id_vars,
            value_vars=date_cols,
            var_name='WEEK_DATE',
            value_name='SAFETY_STOCK'
        )

        # Convert Excel dates to datetime
        result['WEEK_DATE_NUM'] = pd.to_numeric(result['WEEK_DATE'], errors='coerce')
        result['WEEK'] = result['WEEK_DATE_NUM'].apply(self._excel_to_datetime)

        # Add week number
        if len(date_cols) > 0:
            result['WEEK_NUMBER'] = result.groupby(id_vars)['WEEK_DATE_NUM'].transform(
                lambda x: pd.factorize(x)[0] + 1
            )

        return result[['ITEM', 'WHSE', 'WEEK_NUMBER', 'WEEK', 'SAFETY_STOCK', 'BOX']]

    def get_shortages(self, week: str = 'W3') -> pd.DataFrame:
        """
        Identify items with inventory below lower bound (shortage)

        Args:
            week: Week identifier

        Returns:
            DataFrame with shortage items
        """
        position = self.get_inventory_position(week)

        if position.empty:
            return pd.DataFrame()

        shortages = position[position['BALANCE'] < position['LOWER_BOUND']].copy()
        shortages['SHORTAGE_QTY'] = shortages['LOWER_BOUND'] - shortages['BALANCE']

        # Merge with ECO for backorder cost
        if self.eco is not None:
            shortages = shortages.merge(
                self.eco[['CODE4', 'WHIDI1', 'BCK_C']],
                left_on=['CODE4', 'WAREHOUSE'],
                right_on=['CODE4', 'WHIDI1'],
                how='left'
            )
            shortages['BACKORDER_RISK_COST'] = shortages['SHORTAGE_QTY'] * shortages['BCK_C'].fillna(0)

        return shortages.sort_values('SHORTAGE_QTY', ascending=False)

    def get_excess(self, week: str = 'W3') -> pd.DataFrame:
        """
        Identify items with inventory above upper bound (excess)

        Args:
            week: Week identifier

        Returns:
            DataFrame with excess items
        """
        position = self.get_inventory_position(week)

        if position.empty:
            return pd.DataFrame()

        excess = position[position['BALANCE'] > position['UPPER_BOUND']].copy()
        excess['EXCESS_QTY'] = excess['BALANCE'] - excess['UPPER_BOUND']

        return excess.sort_values('EXCESS_QTY', ascending=False)

    def get_firm_pos(self) -> pd.DataFrame:
        """Get firm purchase orders from TIME_SERIES"""
        if self.time_series is None:
            return pd.DataFrame()

        po_cols = ['ITEM', 'WHIDI1', 'FIRMPO_W3', 'FIRMPO_W4', 'SUM_FIRM']
        available_cols = [col for col in po_cols if col in self.time_series.columns]

        return self.time_series[available_cols].copy()

    def get_hot_list_items(self) -> pd.DataFrame:
        """Get priority/hot list items"""
        if self.hot_list is None or self.hot_list.empty:
            return pd.DataFrame()

        return self.hot_list.copy()

    def identify_transshipment_opportunities(self, week: str = 'W3') -> List[Dict]:
        """
        Identify transshipment opportunities by matching shortages with excess

        Args:
            week: Week identifier

        Returns:
            List of transshipment opportunities
        """
        shortages = self.get_shortages(week)
        excess = self.get_excess(week)

        if shortages.empty or excess.empty:
            return []

        opportunities = []

        for _, short_row in shortages.iterrows():
            item = short_row['ITEM']
            to_wh = short_row['WAREHOUSE']
            shortage_qty = short_row['SHORTAGE_QTY']

            # Find excess of same item in different warehouse
            candidates = excess[
                (excess['ITEM'] == item) &
                (excess['WAREHOUSE'] != to_wh)
            ]

            for _, exc_row in candidates.iterrows():
                from_wh = exc_row['WAREHOUSE']
                excess_qty = exc_row['EXCESS_QTY']

                # Calculate transfer quantity
                transfer_qty = min(shortage_qty, excess_qty * 0.8)  # Max 80% of excess

                if transfer_qty >= 10:  # Minimum transfer quantity
                    # Calculate benefit
                    backorder_cost = short_row.get('BCK_C', 0)
                    avoided_cost = transfer_qty * backorder_cost

                    # Assume transport cost = $5/unit (can be improved)
                    transport_cost = transfer_qty * 5

                    net_benefit = avoided_cost - transport_cost

                    if net_benefit > 0:
                        opportunities.append({
                            'item': item,
                            'from_warehouse': from_wh,
                            'to_warehouse': to_wh,
                            'transfer_qty': round(transfer_qty, 0),
                            'shortage_qty': round(shortage_qty, 0),
                            'excess_qty': round(excess_qty, 0),
                            'avoided_backorder_cost': round(avoided_cost, 2),
                            'transport_cost': round(transport_cost, 2),
                            'net_benefit': round(net_benefit, 2),
                            'priority': 'HIGH' if net_benefit > 500 else 'MEDIUM'
                        })

        # Sort by net benefit
        opportunities.sort(key=lambda x: x['net_benefit'], reverse=True)

        return opportunities

    @staticmethod
    def _excel_to_datetime(excel_date):
        """Convert Excel serial date to datetime"""
        if pd.isna(excel_date):
            return None
        try:
            return datetime(1899, 12, 30) + timedelta(days=int(excel_date))
        except:
            return None

    # =========================================================================
    # ANALYSIS METHODS
    # =========================================================================

    def get_coverage_percentage(self, week: str = 'W3') -> float:
        """
        Calculate percentage of items meeting safety stock (BAL >= LOWER)

        Args:
            week: Week identifier

        Returns:
            Coverage percentage (0-100)
        """
        position = self.get_inventory_position(week)

        if position.empty:
            return 0.0

        meeting_ss = len(position[position['BALANCE'] >= position['LOWER_BOUND']])
        total = len(position)

        return (meeting_ss / total) * 100 if total > 0 else 0.0

    def get_total_backorder_risk(self, week: str = 'W3') -> float:
        """
        Calculate total backorder risk cost

        Args:
            week: Week identifier

        Returns:
            Total backorder risk in dollars
        """
        shortages = self.get_shortages(week)

        if 'BACKORDER_RISK_COST' in shortages.columns:
            return shortages['BACKORDER_RISK_COST'].sum()

        return 0.0

    def get_summary_stats(self, week: str = 'W3') -> Dict:
        """
        Get summary statistics for dashboard

        Args:
            week: Week identifier

        Returns:
            Dictionary of summary metrics
        """
        position = self.get_inventory_position(week)
        shortages = self.get_shortages(week)
        excess = self.get_excess(week)
        opportunities = self.identify_transshipment_opportunities(week)

        return {
            'total_warehouses': len(self.get_warehouses()),
            'total_items': len(self.get_items()),
            'total_skus': len(position) if not position.empty else 0,
            'items_below_lower': len(shortages),
            'items_above_upper': len(excess),
            'coverage_percentage': self.get_coverage_percentage(week),
            'total_backorder_risk': self.get_total_backorder_risk(week),
            'transshipment_opportunities': len(opportunities),
            'total_potential_savings': sum(opp['net_benefit'] for opp in opportunities),
            'hot_list_items': len(self.hot_list) if self.hot_list is not None else 0
        }


# Example usage
if __name__ == "__main__":
    loader = AFIDataLoader()
    loader.load_all()

    # Get summary
    summary = loader.get_summary_stats()
    print("\nAFI DATA SUMMARY:")
    for key, value in summary.items():
        print(f"  {key}: {value}")

    # Get shortages
    shortages = loader.get_shortages()
    print(f"\nSHORTAGES: {len(shortages)} items")
    if not shortages.empty:
        print(shortages[['ITEM', 'WAREHOUSE', 'SHORTAGE_QTY', 'BACKORDER_RISK_COST']].head())

    # Get transshipment opportunities
    opportunities = loader.identify_transshipment_opportunities()
    print(f"\nTRANSSHIPMENT OPPORTUNITIES: {len(opportunities)}")
    if opportunities:
        for opp in opportunities[:5]:
            print(f"  {opp['item']}: {opp['from_warehouse']} -> {opp['to_warehouse']} | {opp['transfer_qty']} units | Benefit: ${opp['net_benefit']}")
