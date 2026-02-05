"""
Smart Summary Generator for Optimization Results
Supports AI-powered analysis (Google Gemini) with template fallback
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd


def load_env_file():
    """Load environment variables from .env file"""
    env_path = Path(__file__).parent.parent.parent / '.env'
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ.setdefault(key.strip(), value.strip())


# Load .env on module import
load_env_file()


class SummaryGenerator:
    """
    Generates executive summaries for optimization results.
    Uses Google Gemini API if available, falls back to rule-based templates.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the summary generator.

        Args:
            api_key: Google Gemini API key. If None, checks environment variable.
        """
        self.api_key = api_key or os.environ.get('GEMINI_API_KEY')
        self.model = None
        self.ai_available = False

        if self.api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                # Use gemini-2.0-flash (or fallback to template if quota exceeded)
                self.model = genai.GenerativeModel('gemini-2.0-flash')
                self.ai_available = True
            except ImportError:
                print("google-generativeai not installed. Using template mode.")
            except Exception as e:
                print(f"Failed to initialize Gemini: {e}. Using template mode.")

    def generate_summary(
        self,
        summary: Dict[str, Any],
        baseline_cost: Dict[str, float],
        optimized_cost: Dict[str, float],
        wh_breakdown: pd.DataFrame,
        use_ai: bool = True
    ) -> Dict[str, Any]:
        """
        Generate executive summary from optimization results.

        Args:
            summary: Overall optimization summary dict
            baseline_cost: Baseline cost breakdown
            optimized_cost: Optimized cost breakdown
            wh_breakdown: DataFrame with warehouse-level breakdown
            use_ai: Whether to attempt AI generation (default: True)

        Returns:
            Dict containing:
                - performance_rating: str (EXCELLENT/GOOD/MODERATE/POOR)
                - executive_summary: str (main summary text)
                - key_findings: list of str
                - recommendations: list of str
                - warnings: list of str (if any)
                - source: str ('ai' or 'template')
        """
        # Prepare analysis data
        analysis = self._analyze_data(summary, baseline_cost, optimized_cost, wh_breakdown)

        # Try AI generation first
        if use_ai and self.ai_available:
            try:
                return self._generate_ai_summary(analysis)
            except Exception as e:
                print(f"AI generation failed: {e}. Falling back to template.")

        # Fallback to template-based generation
        return self._generate_template_summary(analysis)

    def _analyze_data(
        self,
        summary: Dict[str, Any],
        baseline_cost: Dict[str, float],
        optimized_cost: Dict[str, float],
        wh_breakdown: pd.DataFrame
    ) -> Dict[str, Any]:
        """Extract key metrics for analysis."""

        # Basic metrics
        savings_pct = summary.get('Savings %', 0)
        total_savings = summary.get('Total Savings', 0)
        num_changes = summary.get('Number of Changes', 0)
        total_po_lines = summary.get('Total PO Lines', 0)
        change_pct = summary.get('Change %', 0)

        # Warehouse analysis
        top_warehouses = []
        problem_warehouses = []

        if not wh_breakdown.empty:
            # Top performers (positive savings)
            top_wh = wh_breakdown[wh_breakdown['Savings %'] > 0].head(3)
            for _, row in top_wh.iterrows():
                top_warehouses.append({
                    'name': row['Warehouse'],
                    'savings': row['Savings'],
                    'savings_pct': row['Savings %']
                })

            # Problem warehouses (negative savings)
            problem_wh = wh_breakdown[wh_breakdown['Savings %'] < 0]
            for _, row in problem_wh.iterrows():
                problem_warehouses.append({
                    'name': row['Warehouse'],
                    'savings': row['Savings'],
                    'savings_pct': row['Savings %']
                })

        # Cost component analysis
        cost_drivers = []

        # Check which cost component improved most
        components = [
            ('Week 3 Stock', baseline_cost.get('w3_stock', 0), optimized_cost.get('w3_stock', 0)),
            ('Week 3 Backlog', baseline_cost.get('w3_bck', 0), optimized_cost.get('w3_bck', 0)),
            ('Week 4-5 Stock', baseline_cost.get('w4_stock', 0), optimized_cost.get('w4_stock', 0)),
            ('Week 4-5 Backlog', baseline_cost.get('w4_bck', 0), optimized_cost.get('w4_bck', 0)),
        ]

        for name, baseline, optimized in components:
            if baseline > 0:
                improvement = ((baseline - optimized) / baseline) * 100
                cost_drivers.append({
                    'name': name,
                    'baseline': baseline,
                    'optimized': optimized,
                    'improvement_pct': improvement
                })

        # Sort by improvement
        cost_drivers.sort(key=lambda x: x['improvement_pct'], reverse=True)

        return {
            'savings_pct': savings_pct,
            'total_savings': total_savings,
            'num_changes': num_changes,
            'total_po_lines': total_po_lines,
            'change_pct': change_pct,
            'baseline_total': baseline_cost.get('total', 0),
            'optimized_total': optimized_cost.get('total', 0),
            'top_warehouses': top_warehouses,
            'problem_warehouses': problem_warehouses,
            'cost_drivers': cost_drivers,
            'num_warehouses': len(wh_breakdown) if not wh_breakdown.empty else 0
        }

    def _generate_ai_summary(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary using Google Gemini API."""

        prompt = f"""You are a supply chain optimization analyst. Analyze these optimization results and provide an executive summary.

DATA:
- Baseline Cost: ${analysis['baseline_total']:,.2f}
- Optimized Cost: ${analysis['optimized_total']:,.2f}
- Total Savings: ${analysis['total_savings']:,.2f} ({analysis['savings_pct']:.2f}%)
- Number of Changes: {analysis['num_changes']:,} out of {analysis['total_po_lines']:,} PO lines ({analysis['change_pct']:.1f}%)
- Number of Warehouses: {analysis['num_warehouses']}

TOP PERFORMING WAREHOUSES:
{self._format_warehouses(analysis['top_warehouses'])}

WAREHOUSES REQUIRING ATTENTION (negative savings):
{self._format_warehouses(analysis['problem_warehouses'])}

COST COMPONENT IMPROVEMENTS:
{self._format_cost_drivers(analysis['cost_drivers'])}

Please provide a response in this EXACT JSON format (no markdown, no code blocks):
{{
    "performance_rating": "EXCELLENT or GOOD or MODERATE or POOR",
    "executive_summary": "2-3 sentence summary of the optimization results",
    "key_findings": ["finding 1", "finding 2", "finding 3"],
    "recommendations": ["recommendation 1", "recommendation 2", "recommendation 3"],
    "warnings": ["warning 1 if any, or empty array if none"]
}}

Guidelines:
- EXCELLENT: >15% savings
- GOOD: 10-15% savings
- MODERATE: 5-10% savings
- POOR: <5% savings
- Be specific with numbers and warehouse names
- Keep language professional and concise
- Warnings should highlight negative savings warehouses"""

        response = self.model.generate_content(prompt)
        response_text = response.text.strip()

        # Clean up response (remove markdown code blocks if present)
        if response_text.startswith('```'):
            response_text = response_text.split('```')[1]
            if response_text.startswith('json'):
                response_text = response_text[4:]
        response_text = response_text.strip()

        import json
        result = json.loads(response_text)
        result['source'] = 'ai'

        return result

    def _generate_template_summary(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary using rule-based templates."""

        savings_pct = analysis['savings_pct']

        # Determine performance rating
        if savings_pct >= 15:
            rating = "EXCELLENT"
            rating_desc = "exceptional"
        elif savings_pct >= 10:
            rating = "GOOD"
            rating_desc = "significant"
        elif savings_pct >= 5:
            rating = "MODERATE"
            rating_desc = "moderate"
        else:
            rating = "POOR"
            rating_desc = "limited"

        # Build executive summary
        exec_summary = (
            f"The destination change optimization achieved {rating_desc} results with "
            f"a {analysis['savings_pct']:.2f}% cost reduction, saving ${analysis['total_savings']:,.2f}. "
            f"This required {analysis['num_changes']:,} destination changes across "
            f"{analysis['num_warehouses']} warehouses."
        )

        # Key findings
        key_findings = []

        # Finding 1: Overall performance
        key_findings.append(
            f"Total supply chain cost reduced from ${analysis['baseline_total']:,.2f} "
            f"to ${analysis['optimized_total']:,.2f} ({analysis['savings_pct']:.2f}% savings)."
        )

        # Finding 2: Top warehouse
        if analysis['top_warehouses']:
            top = analysis['top_warehouses'][0]
            key_findings.append(
                f"Warehouse {top['name']} shows the highest improvement with "
                f"{top['savings_pct']:.2f}% cost reduction (${top['savings']:,.2f} saved)."
            )

        # Finding 3: Change efficiency
        if analysis['change_pct'] > 0:
            key_findings.append(
                f"Only {analysis['change_pct']:.1f}% of PO lines required changes, "
                f"minimizing operational disruption."
            )

        # Finding 4: Cost driver
        if analysis['cost_drivers']:
            best_driver = analysis['cost_drivers'][0]
            key_findings.append(
                f"{best_driver['name']} costs improved the most with "
                f"{best_driver['improvement_pct']:.1f}% reduction."
            )

        # Recommendations
        recommendations = []

        # Rec 1: Priority warehouses
        if analysis['top_warehouses']:
            top_names = [w['name'] for w in analysis['top_warehouses'][:3]]
            recommendations.append(
                f"Prioritize implementing changes in warehouses {', '.join(top_names)} "
                f"for maximum impact."
            )

        # Rec 2: Problem warehouses
        if analysis['problem_warehouses']:
            problem_names = [w['name'] for w in analysis['problem_warehouses']]
            recommendations.append(
                f"Review cost structure for warehouse(s) {', '.join(problem_names)} "
                f"which show increased costs after optimization."
            )
        else:
            recommendations.append(
                "All warehouses show positive or neutral cost impact - proceed with full implementation."
            )

        # Rec 3: Projected annual savings
        annual_savings = analysis['total_savings'] * 52  # Weekly to annual
        recommendations.append(
            f"If applied weekly, estimated annual savings could reach ${annual_savings:,.2f}."
        )

        # Warnings
        warnings = []
        if analysis['problem_warehouses']:
            for pw in analysis['problem_warehouses']:
                warnings.append(
                    f"Warehouse {pw['name']} shows {pw['savings_pct']:.2f}% cost increase "
                    f"(${abs(pw['savings']):,.2f}) - requires inventory rebalancing from other locations."
                )

        return {
            'performance_rating': rating,
            'executive_summary': exec_summary,
            'key_findings': key_findings,
            'recommendations': recommendations,
            'warnings': warnings,
            'source': 'template'
        }

    def _format_warehouses(self, warehouses: list) -> str:
        """Format warehouse list for prompt."""
        if not warehouses:
            return "None"

        lines = []
        for wh in warehouses:
            lines.append(f"- {wh['name']}: ${wh['savings']:,.2f} ({wh['savings_pct']:.2f}%)")
        return '\n'.join(lines)

    def _format_cost_drivers(self, drivers: list) -> str:
        """Format cost drivers for prompt."""
        if not drivers:
            return "None"

        lines = []
        for d in drivers:
            lines.append(f"- {d['name']}: {d['improvement_pct']:.1f}% improvement")
        return '\n'.join(lines)


def render_summary_streamlit(summary_result: Dict[str, Any]):
    """
    Render the summary in Streamlit with nice formatting.

    Args:
        summary_result: Dict from SummaryGenerator.generate_summary()
    """
    import streamlit as st

    # Performance rating with color
    rating = summary_result.get('performance_rating', 'N/A')
    rating_colors = {
        'EXCELLENT': '#28a745',  # Green
        'GOOD': '#17a2b8',       # Blue
        'MODERATE': '#ffc107',   # Yellow
        'POOR': '#dc3545'        # Red
    }
    rating_color = rating_colors.get(rating, '#6c757d')

    # Source indicator
    source = summary_result.get('source', 'unknown')
    source_icon = "sparkles" if source == 'ai' else "file-text"
    source_text = "AI-Generated" if source == 'ai' else "Auto-Generated"

    # Header with rating
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, {rating_color}22, {rating_color}11);
                border-left: 4px solid {rating_color};
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 20px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h2 style="margin: 0; color: #333;">Executive Summary</h2>
                <span style="background: {rating_color}; color: white; padding: 4px 12px;
                       border-radius: 4px; font-weight: bold; font-size: 14px;">
                    {rating}
                </span>
            </div>
            <div style="text-align: right; color: #666; font-size: 12px;">
                {source_text}
            </div>
        </div>
        <p style="margin-top: 15px; font-size: 16px; color: #444; line-height: 1.6;">
            {summary_result.get('executive_summary', '')}
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Key Findings and Recommendations in columns
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Key Findings")
        for i, finding in enumerate(summary_result.get('key_findings', []), 1):
            st.markdown(f"""
            <div style="background: #f8f9fa; padding: 10px 15px; border-radius: 6px;
                        margin-bottom: 8px; border-left: 3px solid #17a2b8;">
                <strong>{i}.</strong> {finding}
            </div>
            """, unsafe_allow_html=True)

    with col2:
        st.markdown("#### Recommendations")
        for i, rec in enumerate(summary_result.get('recommendations', []), 1):
            st.markdown(f"""
            <div style="background: #f8f9fa; padding: 10px 15px; border-radius: 6px;
                        margin-bottom: 8px; border-left: 3px solid #28a745;">
                <strong>{i}.</strong> {rec}
            </div>
            """, unsafe_allow_html=True)

    # Warnings (if any)
    warnings = summary_result.get('warnings', [])
    if warnings:
        st.markdown("#### Attention Required")
        for warning in warnings:
            st.markdown(f"""
            <div style="background: #fff3cd; padding: 10px 15px; border-radius: 6px;
                        margin-bottom: 8px; border-left: 3px solid #ffc107; color: #856404;">
                {warning}
            </div>
            """, unsafe_allow_html=True)
