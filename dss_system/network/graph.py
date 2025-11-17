"""Network graph representation using NetworkX"""

import networkx as nx
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional


class SupplyChainNetwork:
    """Supply chain network representation and analysis"""

    def __init__(self, loader):
        from ..data.loader import SupplyChainDataLoader
        self.loader: SupplyChainDataLoader = loader
        self.graph = nx.DiGraph()  # Directed graph for supply flow
        self.undirected_graph = nx.Graph()  # For lateral transshipment
        self._build_network()

    def _build_network(self):
        """Build network graph from facilities and transportation data"""
        # Add nodes (facilities)
        for _, facility in self.loader.facilities.iterrows():
            self.graph.add_node(
                facility['facility_code'],
                name=facility['facility_name'],
                location=facility['location'],
                country=facility['country'],
                facility_type=facility['facility_type'],
                daily_capacity=facility['daily_capacity'],
                operating_cost=facility['operating_cost_per_day'],
                storage_cost=facility['storage_cost_per_unit_per_day']
            )
            self.undirected_graph.add_node(facility['facility_code'])

        # Add edges (transportation routes)
        for _, route in self.loader.transportation.iterrows():
            self.graph.add_edge(
                route['from_facility'],
                route['to_facility'],
                cost_per_unit=route['cost_per_unit'],
                lead_time_days=route['lead_time_days'],
                transport_mode=route['transport_mode']
            )

            # Add to undirected graph for lateral transshipment (US facilities only)
            if (route['from_facility'].startswith('US_') and
                route['to_facility'].startswith('US_')):
                if not self.undirected_graph.has_edge(route['from_facility'],
                                                      route['to_facility']):
                    self.undirected_graph.add_edge(
                        route['from_facility'],
                        route['to_facility'],
                        cost_per_unit=route['cost_per_unit'],
                        lead_time_days=route['lead_time_days']
                    )

    def get_facility_types(self) -> Dict[str, List[str]]:
        """Get facilities grouped by type"""
        facilities_by_type = {}
        for node, data in self.graph.nodes(data=True):
            ftype = data['facility_type']
            if ftype not in facilities_by_type:
                facilities_by_type[ftype] = []
            facilities_by_type[ftype].append(node)
        return facilities_by_type

    def get_manufacturing_facilities(self) -> List[str]:
        """Get list of manufacturing facilities"""
        return [n for n, d in self.graph.nodes(data=True)
                if d['facility_type'] == 'manufacturing']

    def get_finishing_facilities(self) -> List[str]:
        """Get list of finishing facilities"""
        return [n for n, d in self.graph.nodes(data=True)
                if d['facility_type'] == 'finishing']

    def get_route_info(self, from_facility: str, to_facility: str) -> Optional[Dict]:
        """Get transportation route information"""
        if self.graph.has_edge(from_facility, to_facility):
            return self.graph.edges[from_facility, to_facility]
        return None

    def get_shortest_path(self, from_facility: str, to_facility: str,
                         weight: str = 'cost_per_unit') -> Tuple[List[str], float]:
        """Get shortest path between facilities based on cost or time"""
        try:
            path = nx.shortest_path(self.graph, from_facility, to_facility, weight=weight)
            total_cost = nx.shortest_path_length(self.graph, from_facility,
                                                 to_facility, weight=weight)
            return path, total_cost
        except nx.NetworkXNoPath:
            return [], float('inf')

    def get_transshipment_candidates(self, facility_code: str) -> List[str]:
        """Get facilities that can participate in lateral transshipment"""
        if facility_code.startswith('US_'):
            return [n for n in self.undirected_graph.neighbors(facility_code)]
        return []

    def get_transshipment_cost(self, from_facility: str,
                              to_facility: str) -> Optional[float]:
        """Get lateral transshipment cost between facilities"""
        if self.undirected_graph.has_edge(from_facility, to_facility):
            return self.undirected_graph.edges[from_facility, to_facility]['cost_per_unit']
        return None

    def get_transshipment_lead_time(self, from_facility: str,
                                   to_facility: str) -> Optional[float]:
        """Get lateral transshipment lead time between facilities"""
        if self.undirected_graph.has_edge(from_facility, to_facility):
            return self.undirected_graph.edges[from_facility, to_facility]['lead_time_days']
        return None

    def calculate_network_metrics(self) -> Dict:
        """Calculate network topology metrics"""
        metrics = {
            'num_nodes': self.graph.number_of_nodes(),
            'num_edges': self.graph.number_of_edges(),
            'is_connected': nx.is_weakly_connected(self.graph),
            'num_components': nx.number_weakly_connected_components(self.graph),
            'avg_degree': sum(dict(self.graph.degree()).values()) / self.graph.number_of_nodes(),
            'diameter': None,
            'avg_shortest_path': None
        }

        if metrics['is_connected']:
            try:
                metrics['diameter'] = nx.diameter(self.graph.to_undirected())
                metrics['avg_shortest_path'] = nx.average_shortest_path_length(
                    self.graph.to_undirected()
                )
            except:
                pass

        return metrics

    def get_facility_info(self, facility_code: str) -> Dict:
        """Get detailed facility information"""
        if facility_code in self.graph:
            return self.graph.nodes[facility_code]
        return {}

    def get_all_routes(self) -> pd.DataFrame:
        """Get all transportation routes as DataFrame"""
        routes = []
        for u, v, data in self.graph.edges(data=True):
            routes.append({
                'from_facility': u,
                'to_facility': v,
                **data
            })
        return pd.DataFrame(routes)

    def get_transshipment_network(self) -> nx.Graph:
        """Get the lateral transshipment network (US facilities only)"""
        return self.undirected_graph

    def get_echelon_structure(self) -> Dict[int, List[str]]:
        """Get facilities organized by echelon level"""
        echelons = {}
        manufacturing = self.get_manufacturing_facilities()
        if manufacturing:
            echelons[0] = manufacturing
        finishing = self.get_finishing_facilities()
        if finishing:
            echelons[1] = finishing
        return echelons
