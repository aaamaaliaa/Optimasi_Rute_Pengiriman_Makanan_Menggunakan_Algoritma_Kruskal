import numpy as np
from geopy.distance import geodesic
from ortools.constraint_solver import pywrapcp, routing_enums_pb2

AVERAGE_SPEED = 30  # km/jam
CIREBON_BOUNDS = {
    "lat_min": -6.9,
    "lat_max": -6.5,
    "lon_min": 108.4,
    "lon_max": 108.7
}

def validate_coords(lat, lon):
    """Memastikan koordinat berada di wilayah Cirebon."""
    return (CIREBON_BOUNDS["lat_min"] <= lat <= CIREBON_BOUNDS["lat_max"] and
            CIREBON_BOUNDS["lon_min"] <= lon <= CIREBON_BOUNDS["lon_max"])

def calculate_distance(coord1, coord2):
    """Menghitung jarak antar dua koordinat dalam kilometer."""
    return geodesic(coord1, coord2).kilometers

def calculate_travel_time(distance_km, speed_kmh=AVERAGE_SPEED):
    """Menghitung waktu tempuh dalam menit berdasarkan jarak."""
    return (distance_km / speed_kmh) * 60

def create_distance_matrix(points):
    """Membuat matriks jarak antar semua titik."""
    n = len(points)
    matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            if i != j:
                matrix[i][j] = calculate_distance(points[i]["coords"], points[j]["coords"])
    return matrix

class UnionFind:
    """Struktur data untuk algoritma Kruskal."""
    def __init__(self, size):
        self.parent = list(range(size))
        self.rank = [0] * size

    def find(self, x):
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x, y):
        px, py = self.find(x), self.find(y)
        if px == py:
            return False
        if self.rank[px] < self.rank[py]:
            px, py = py, px
        self.parent[py] = px
        if self.rank[px] == self.rank[py]:
            self.rank[px] += 1
        return True

def kruskal_mst(points, distance_matrix):
    """Membuat Minimum Spanning Tree dengan algoritma Kruskal."""
    n = len(points)
    edges = [(distance_matrix[i][j], i, j) for i in range(n) for j in range(i + 1, n)]
    edges.sort()

    uf = UnionFind(n)
    mst_edges = []
    total_weight = 0

    for weight, u, v in edges:
        if uf.union(u, v):
            mst_edges.append((u, v, weight))
            total_weight += weight

    return mst_edges, total_weight

def find_shortest_route(distance_matrix, num_vehicles=1, start_idx=0):
    """Mencari rute terpendek untuk satu pesanan menggunakan OR-Tools."""
    manager = pywrapcp.RoutingIndexManager(len(distance_matrix), num_vehicles, start_idx)
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return int(distance_matrix[from_node][to_node] * 1000)

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    search_parameters.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    search_parameters.time_limit.seconds = 10

    solution = routing.SolveWithParameters(search_parameters)
    if not solution:
        return None, None, None

    route = []
    total_distance = 0
    index = routing.Start(0)
    while not routing.IsEnd(index):
        route.append(manager.IndexToNode(index))
        previous_index = index
        index = solution.Value(routing.NextVar(index))
        if not routing.IsEnd(index):
            total_distance += distance_matrix[route[-1]][manager.IndexToNode(index)]
    route.append(start_idx)
    total_distance += distance_matrix[route[-2]][start_idx]
    
    segment_distances = []
    segment_times = []
    for i in range(len(route) - 1):
        dist = distance_matrix[route[i]][route[i + 1]]
        segment_distances.append(dist)
        segment_times.append(calculate_travel_time(dist))
    
    return route, total_distance, (segment_distances, segment_times)

def find_multi_drop_route(points, distance_matrix, max_stops=10):
    """Mencari rute multi-drop untuk semua pesanan."""
    mst_edges, _ = kruskal_mst(points, distance_matrix)
    
    manager = pywrapcp.RoutingIndexManager(len(distance_matrix), 1, 0)
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return int(distance_matrix[from_node][to_node] * 1000)

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    routing.AddConstantDimension(1, max_stops, True, "Stops")

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    search_parameters.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    search_parameters.time_limit.seconds = 10

    solution = routing.SolveWithParameters(search_parameters)
    if not solution:
        return None, None, None, None

    route = []
    total_distance = 0
    index = routing.Start(0)
    while not routing.IsEnd(index):
        route.append(manager.IndexToNode(index))
        previous_index = index
        index = solution.Value(routing.NextVar(index))
        if not routing.IsEnd(index):
            total_distance += distance_matrix[route[-1]][manager.IndexToNode(index)]
    route.append(0)
    total_distance += distance_matrix[route[-2]][0]

    segment_distances = []
    segment_times = []
    for i in range(len(route) - 1):
        dist = distance_matrix[route[i]][route[i + 1]]
        segment_distances.append(dist)
        segment_times.append(calculate_travel_time(dist))

    return route, total_distance, (segment_distances, segment_times), mst_edges