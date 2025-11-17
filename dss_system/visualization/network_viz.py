"""Network visualization using Plotly"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import Dict, Optional


class NetworkVisualizer:
    """Visualize supply chain network"""

    def __init__(self, network, loader):
        self.network = network
        self.loader = loader

        # Define layout positions for facilities
        self.positions = {
            'VN_FAC_1': (0, 0),      # Vietnam at origin
            'US_FAC_1': (10, 2),     # West Coast (LA)
            'US_FAC_2': (10, 0),     # East Coast (NY)
            'US_FAC_3': (10, -2)     # Central (Chicago)
        }

        # Color scheme
        self.colors = {
            'manufacturing': '#FF6B6B',
            'finishing': '#4ECDC4',
            'edge': '#95A5A6',
            'transshipment': '#F39C12'
        }

    def create_network_diagram(self, show_costs: bool = True,
                              show_lead_times: bool = True) -> go.Figure:
        """Create interactive network diagram"""
        G = self.network.graph

        # Node data
        node_x, node_y, node_text, node_colors, node_sizes = [], [], [], [], []

        for node in G.nodes():
            x, y = self.positions.get(node, (0, 0))
            node_x.append(x)
            node_y.append(y)

            node_data = G.nodes[node]
            facility_type = node_data['facility_type']
            node_colors.append(self.colors[facility_type])

            capacity = node_data.get('daily_capacity', 100)
            node_sizes.append(capacity / 3)

            text = (f"<b>{node}</b><br>"
                   f"{node_data['name']}<br>"
                   f"{node_data['location']}<br>"
                   f"Type: {facility_type}<br>"
                   f"Capacity: {capacity} units/day<br>"
                   f"Operating Cost: ${node_data['operating_cost']:,.0f}/day<br>"
                   f"Storage Cost: ${node_data['storage_cost']:.2f}/unit/day")
            node_text.append(text)

        # Edge data
        edge_traces = []
        edge_annotations = []

        for edge in G.edges(data=True):
            x0, y0 = self.positions[edge[0]]
            x1, y1 = self.positions[edge[1]]

            is_transshipment = edge[0].startswith('US_') and edge[1].startswith('US_')
            edge_color = self.colors['transshipment'] if is_transshipment else self.colors['edge']

            edge_trace = go.Scatter(
                x=[x0, x1, None],
                y=[y0, y1, None],
                mode='lines',
                line=dict(width=2 if is_transshipment else 1, color=edge_color),
                hoverinfo='text',
                text=f"{edge[0]} → {edge[1]}<br>"
                     f"Cost: ${edge[2]['cost_per_unit']:.2f}/unit<br>"
                     f"Lead Time: {edge[2]['lead_time_days']:.1f} days<br>"
                     f"Mode: {edge[2]['transport_mode']}",
                showlegend=False
            )
            edge_traces.append(edge_trace)

            if show_costs or show_lead_times:
                mid_x = (x0 + x1) / 2
                mid_y = (y0 + y1) / 2
                label_parts = []

                if show_costs:
                    label_parts.append(f"${edge[2]['cost_per_unit']:.1f}")
                if show_lead_times:
                    label_parts.append(f"{edge[2]['lead_time_days']:.1f}d")

                edge_annotations.append(dict(
                    x=mid_x, y=mid_y,
                    text=' | '.join(label_parts),
                    showarrow=False,
                    font=dict(size=9, color=edge_color),
                    bgcolor='white',
                    opacity=0.8
                ))

        # Node trace
        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            marker=dict(size=node_sizes, color=node_colors,
                       line=dict(width=2, color='white')),
            text=[node for node in G.nodes()],
            textposition="top center",
            textfont=dict(size=10, color='black'),
            hoverinfo='text',
            hovertext=node_text,
            showlegend=False
        )

        fig = go.Figure(data=edge_traces + [node_trace])

        fig.update_layout(
            title={'text': 'Supply Chain Network Structure',
                  'x': 0.5, 'xanchor': 'center', 'font': {'size': 20}},
            showlegend=True,
            hovermode='closest',
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            width=1200, height=600,
            annotations=edge_annotations,
            plot_bgcolor='white'
        )

        return fig

    def create_inventory_heatmap(self) -> go.Figure:
        """Create heatmap of current inventory levels"""
        inv_df = self.loader.inventory.copy()

        pivot_df = inv_df.pivot_table(
            index='product_code',
            columns='facility_code',
            values='on_hand',
            fill_value=0
        )

        facility_order = ['US_FAC_1', 'US_FAC_2', 'US_FAC_3']
        pivot_df = pivot_df[facility_order]

        fig = go.Figure(data=go.Heatmap(
            z=pivot_df.values,
            x=pivot_df.columns,
            y=pivot_df.index,
            colorscale='Blues',
            text=pivot_df.values,
            texttemplate='%{text}',
            textfont={"size": 8},
            colorbar=dict(title="Units on Hand")
        ))

        fig.update_layout(
            title='Current Inventory Levels by Facility',
            xaxis_title='Facility',
            yaxis_title='Product',
            width=800, height=800
        )

        return fig

    def create_demand_pattern_chart(self, product_code: Optional[str] = None) -> go.Figure:
        """Create demand pattern visualization"""
        demand_df = self.loader.demand.copy()

        if product_code:
            demand_df = demand_df[demand_df['product_code'] == product_code]

        agg_df = demand_df.groupby(['demand_date', 'facility_code'])['total_demand'].sum().reset_index()

        fig = px.line(
            agg_df,
            x='demand_date',
            y='total_demand',
            color='facility_code',
            title=f'Demand Pattern Over Time' + (f' - {product_code}' if product_code else ''),
            labels={'total_demand': 'Total Demand', 'demand_date': 'Date'}
        )

        fig.update_layout(width=1200, height=500, hovermode='x unified')
        return fig

    def create_transfer_flow_sankey(self) -> go.Figure:
        """Create Sankey diagram of transfer flows"""
        transfers = self.loader.transfers.copy()

        route_agg = transfers.groupby(['from_facility', 'to_facility'])['quantity'].sum().reset_index()

        facilities = list(set(route_agg['from_facility'].unique()) |
                         set(route_agg['to_facility'].unique()))
        facility_to_idx = {f: i for i, f in enumerate(facilities)}

        source = [facility_to_idx[f] for f in route_agg['from_facility']]
        target = [facility_to_idx[f] for f in route_agg['to_facility']]
        value = route_agg['quantity'].tolist()

        fig = go.Figure(data=[go.Sankey(
            node=dict(
                pad=15, thickness=20,
                line=dict(color="black", width=0.5),
                label=facilities,
                color=[self.colors['finishing'] if f.startswith('US_')
                      else self.colors['manufacturing'] for f in facilities]
            ),
            link=dict(source=source, target=target, value=value,
                     color='rgba(128, 128, 128, 0.3)')
        )])

        fig.update_layout(
            title="Lateral Transshipment Flow (Total Quantities)",
            font_size=12, width=1000, height=600
        )

        return fig
