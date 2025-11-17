# Decision Support System for Supply Chain Management

Decision Support System for inventory management in B2B Intermediate Goods Supply Network.

## 📁 Project Structure (Simplified)

```
KLTN/
├── dss_system/              # Core DSS application
│   ├── data/               # Data layer
│   │   ├── loader.py       # Load CSV data
│   │   └── validator.py    # Validate data
│   ├── network/            # Network representation
│   │   ├── graph.py        # Network graph (NetworkX)
│   │   └── analysis.py     # Pattern analysis
│   ├── visualization/      # Visualization layer
│   │   ├── network_viz.py  # Charts (Plotly)
│   │   ├── dashboard.py    # Report generation
│   │   └── streamlit_app.py # Web dashboard ⭐
│   └── utils/              # Utilities
│       ├── config.py       # Configuration
│       └── helpers.py      # Helper functions
│
├── data/                   # Raw CSV data
│   └── lite_furniture_data/
│
├── scripts/                # Utility scripts
│   ├── run_analysis.py     # Run analysis
│   ├── run_dashboard.py    # Launch dashboard
│   └── generate_dataset.py # Generate data
│
├── outputs/                # Generated outputs
│   ├── reports/           # Text reports
│   ├── visualizations/    # HTML charts
│   └── results/           # Analysis results
│
├── main.py                # CLI analysis
├── dashboard.py           # Dashboard launcher
├── config.yaml            # Configuration
└── requirements.txt       # Dependencies
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Required packages:
- pandas, numpy - Data processing
- networkx - Network analysis
- plotly - Interactive charts
- streamlit - Web dashboard
- pyyaml - Configuration

### 2. Launch Interactive Dashboard 🌐 (Recommended)

```bash
# Simple launcher
python dashboard.py

# Or direct command
streamlit run dss_system/visualization/streamlit_app.py
```

Dashboard opens at: **http://localhost:8501**

**Features:**
- 🏠 **Overview** - KPIs and metrics
- 📈 **Data Analysis** - Demand, inventory, transfers
- 🔗 **Network** - Interactive network visualization
- 📊 **Reports** - Generate and export reports

### 3. Run CLI Analysis (Alternative)

```bash
python main.py
```

Generates:
- Network visualizations (HTML files)
- Demand/inventory analysis
- Transfer pattern analysis
- Reports (TXT, JSON)

## 📊 Dashboard Pages

### 🏠 Overview
- **KPIs Dashboard**: Facilities, products, inventory, demand, transfers
- **Visual Charts**: Pie charts, bar charts
- **Alerts**: Stockout risk, excess inventory warnings

### 📈 Data Analysis
- **Demand Tab**: Patterns, trends, by facility/product
- **Inventory Tab**: Levels, heatmap, stockout risk
- **Transfers Tab**: Transshipment analysis
- **Opportunities Tab**: Optimization suggestions

### 🔗 Network
- **Interactive Graph**: Facilities and routes
- **Network Metrics**: Connectivity, topology
- **Echelon Structure**: Supply chain layers

### 📊 Reports
- **Generate Reports**: Text reports
- **Export Data**: Download CSV

## ⚙️ Configuration

Edit `config.yaml`:

```yaml
data:
  data_dir: D:/KLTN/data/lite_furniture_data
  output_dir: D:/KLTN/outputs

costs:
  stockout_penalty: 100

policies:
  safety_stock_service_level: 0.95
  review_period_days: 7
```

## 📈 Output Files

### CLI Analysis (`outputs/`)
- `visualizations/network_diagram.html` - Network graph
- `visualizations/inventory_heatmap.html` - Inventory levels
- `visualizations/demand_pattern.html` - Demand trends
- `visualizations/transfer_flow.html` - Transfer flows
- `reports/analysis_report.txt` - Text report
- `reports/analysis_data.json` - JSON data

## 🎯 Features

### ✅ Current Features
- ✅ Data loading and validation
- ✅ Network graph representation (NetworkX)
- ✅ Demand pattern analysis
- ✅ Inventory metrics analysis
- ✅ Transfer pattern analysis
- ✅ Interactive web dashboard (Streamlit)
- ✅ Real-time visualization (Plotly)
- ✅ Report generation (TXT, JSON, CSV)

### 🔜 Future Features (To be added)
- 🔲 Optimization models (Inventory pooling, transshipment, replenishment)
- 🔲 Machine learning for demand forecasting
- 🔲 Decision recommendation engine
- 🔲 Multi-objective optimization
- 🔲 React.js frontend (Advanced UI)

## 📚 Dataset

**Location:** `data/lite_furniture_data/`

**Files:**
- `facilities.csv` (4 facilities: 1 VN manufacturing + 3 US finishing)
- `products.csv` (24 products: 3 series × 4 colors × 2 types)
- `demand.csv` (2160 records: 30 days history)
- `inventory.csv` (72 records: Current inventory)
- `transfers.csv` (50 records: Transshipment history)
- `transportation.csv` (12 routes with costs & lead times)
- `procurement.csv` (4 materials)
- `production.csv` (10 production records)

## 🛠️ Tech Stack

**Backend:**
- Python 3.11+
- pandas & numpy (Data processing)
- NetworkX (Network analysis)
- Plotly (Interactive charts)

**Frontend:**
- Streamlit (Web dashboard)
- Custom CSS (Beautiful design)

**Data:**
- CSV files
- YAML configuration

## 📝 Usage Examples

### Load and Analyze Data (Python)
```python
from dss_system.data.loader import SupplyChainDataLoader
from dss_system.network.graph import SupplyChainNetwork
from dss_system.network.analysis import NetworkAnalyzer

# Load data
loader = SupplyChainDataLoader()
loader.load_all()

# Build network
network = SupplyChainNetwork(loader)

# Analyze
analyzer = NetworkAnalyzer(network, loader)
demand_analysis = analyzer.analyze_demand_patterns()
print(demand_analysis)
```

### Launch Dashboard (CLI)
```bash
# Method 1: Simple launcher
python dashboard.py

# Method 2: Direct Streamlit
streamlit run dss_system/visualization/streamlit_app.py

# Method 3: Via script
python scripts/run_dashboard.py
```

## 🎨 Dashboard Design

**Color Scheme:**
- Primary: Purple gradient `#667eea → #764ba2`
- Secondary: Blue `#1e40af`
- Background: Soft gradient
- Cards: White with shadow

**Features:**
- Responsive design
- Smooth animations
- Hover effects
- Modern UI/UX
- Interactive charts

## 🔧 Troubleshooting

**Issue: Module not found**
```bash
pip install -r requirements.txt
```

**Issue: Data not loading**
- Check `config.yaml` data_dir path
- Ensure CSV files exist in `data/lite_furniture_data/`

**Issue: Dashboard not opening**
```bash
# Check if port 8501 is free
netstat -ano | findstr :8501

# Use different port
streamlit run streamlit_app.py --server.port=8502
```

## 📖 Documentation

- `PROJECT_STRUCTURE.md` - Detailed file structure
- `DASHBOARD_METRICS_GUIDE.md` - Metrics explanation
- `config.yaml` - Configuration options

## 📞 Support

For issues or questions:
1. Check configuration in `config.yaml`
2. Verify data files in `data/lite_furniture_data/`
3. Review logs in terminal

## 📝 License

Academic project - Khóa luận tốt nghiệp (KLTN)

**Topic:** Decision Support System for Inventory Pooling in B2B Supply Networks

---

**Last Updated:** 2025-11-17
**Version:** 1.0.0 (Simplified)
