import pandas as pd
import networkx as nx
import folium
import os

# --- 1. Configuration ---
DATA_PATH = os.path.join("data", "europe_air_routes.csv")
MAP_OUTPUT = "flight_network_map.html"

def load_data():
    """
    Loads and cleans the flight dataset.
    Removes rows with missing geographical coordinates to ensure graph integrity.
    """
    print("✈️  Loading and preprocessing data...")
    df = pd.read_csv(DATA_PATH)
    
    # Drop flights with missing coordinates
    df_clean = df.dropna(subset=['departure_latitude', 'departure_longitude', 
                                 'arrival_latitude', 'arrival_longitude'])
    return df_clean

def build_graph(df):
    """
    Constructs the Flight Network Graph.
    - Nodes: Airports (with city and coordinate attributes).
    - Edges: Flight routes (weighted by flight duration).
    """
    print("🌐 Building network graph from data...")
    G = nx.Graph()
    
    for _, row in df.iterrows():
        # Add edge (Route)
        G.add_edge(
            row['iata_from'], 
            row['iata_to'], 
            weight=row['common_duration'] # Weight = Flight duration in minutes
        )
        
        # Add node attributes (Coordinates & City Name)
        G.nodes[row['iata_from']]['pos'] = (row['departure_latitude'], row['departure_longitude'])
        G.nodes[row['iata_from']]['city'] = row['departure_city']
        
        G.nodes[row['iata_to']]['pos'] = (row['arrival_latitude'], row['arrival_longitude'])
        G.nodes[row['iata_to']]['city'] = row['arrival_airport_city_name']
        
    return G

def find_top_hubs(G, n=5):
    """
    Identifies the busiest airports using Degree Centrality.
    Returns the top N hubs with the most direct connections.
    """
    degree_dict = dict(G.degree(G.nodes()))
    sorted_degree = sorted(degree_dict.items(), key=lambda item: item[1], reverse=True)
    
    print(f"\n🏆 TOP {n} BUSIEST HUBS IN EUROPE:")
    for i, (airport, degree) in enumerate(sorted_degree[:n], 1):
        city = G.nodes[airport].get('city', 'Unknown')
        print(f"{i}. {airport} ({city}) - {degree} connections")

def find_shortest_path(G, start_code, end_code):
    """
    Calculates the optimal route between two cities using Dijkstra's algorithm.
    It finds the path with the minimum total weight (duration).
    """
    try:
        path = nx.shortest_path(G, source=start_code, target=end_code, weight='weight')
        print(f"\n📍 OPTIMAL ROUTE ({start_code} -> {end_code}):")
        print(" -> ".join(path))
        return path
    except nx.NetworkXNoPath:
        print(f"\n❌ No path found between {start_code} and {end_code}")
        return None

def visualize_map(G, df):
    """
    Generates an interactive HTML map using Folium.
    Visualizes major hubs and flight paths.
    """
    print(f"\n🗺️  Generating interactive map ({MAP_OUTPUT})...")
    
    # Center map on Europe (approx. Munich coordinates)
    m = folium.Map(location=[48.1351, 11.5820], zoom_start=4, tiles="CartoDB dark_matter")

    # Visualize Top 50 Hubs
    degree_dict = dict(G.degree(G.nodes()))
    top_nodes = sorted(degree_dict.items(), key=lambda item: item[1], reverse=True)[:50]
    
    for airport, count in top_nodes:
        if 'pos' in G.nodes[airport]:
            lat, lon = G.nodes[airport]['pos']
            city = G.nodes[airport].get('city', airport)
            
            # Marker size depends on the number of connections
            folium.CircleMarker(
                location=[lat, lon],
                radius=count / 10, 
                color="#3498db",
                fill=True,
                fill_color="#3498db",
                popup=f"{city} ({airport}): {count} routes"
            ).add_to(m)

    # Visualize first 200 Routes (to maintain performance)
    for _, row in df.head(200).iterrows():
        start_pos = (row['departure_latitude'], row['departure_longitude'])
        end_pos = (row['arrival_latitude'], row['arrival_longitude'])
        
        folium.PolyLine(
            locations=[start_pos, end_pos],
            color="#2ecc71",
            weight=0.5,
            opacity=0.5
        ).add_to(m)

    m.save(MAP_OUTPUT)
    print(f"✅ Map saved successfully! Open '{MAP_OUTPUT}' in your browser.")

# --- Main Execution Flow ---
if __name__ == "__main__":
    # Step 1: Load Data
    df = load_data()
    
    # Step 2: Build Graph
    flight_graph = build_graph(df)
    
    # Step 3: Analyze Network
    find_top_hubs(flight_graph)
