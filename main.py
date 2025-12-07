import pandas as pd
import networkx as nx
import folium
import os

# --- 1. Налаштування ---
DATA_PATH = os.path.join("data", "europe_air_routes.csv")
MAP_OUTPUT = "flight_network_map.html"

def load_data():
    """Завантажує та очищує дані."""
    print("✈️  Loading data...")
    df = pd.read_csv(DATA_PATH)
    
    # Видаляємо рейси без координат (якщо такі є)
    df_clean = df.dropna(subset=['departure_latitude', 'departure_longitude', 
                                 'arrival_latitude', 'arrival_longitude'])
    return df_clean

def build_graph(df):
    """Створює граф польотів (Аеропорти = Вузли, Рейси = Ребра)."""
    print("🌐 Building network graph...")
    G = nx.Graph()
    
    for _, row in df.iterrows():
        # Додаємо маршрут (ребро)
        G.add_edge(
            row['iata_from'], 
            row['iata_to'], 
            weight=row['common_duration'] # Вага = тривалість польоту
        )
        
        # Додаємо координати аеропортів (атрибути вузла)
        G.nodes[row['iata_from']]['pos'] = (row['departure_latitude'], row['departure_longitude'])
        G.nodes[row['iata_from']]['city'] = row['departure_city']
        
        G.nodes[row['iata_to']]['pos'] = (row['arrival_latitude'], row['arrival_longitude'])
        G.nodes[row['iata_to']]['city'] = row['arrival_airport_city_name']
        
    return G

def find_top_hubs(G, n=5):
    """Знаходить топ аеропортів за кількістю сполучень (Degree Centrality)."""
    degree_dict = dict(G.degree(G.nodes()))
    sorted_degree = sorted(degree_dict.items(), key=lambda item: item[1], reverse=True)
    
    print(f"\n🏆 TOP {n} BUSIEST HUBS IN EUROPE:")
    for i, (airport, degree) in enumerate(sorted_degree[:n], 1):
        city = G.nodes[airport].get('city', 'Unknown')
        print(f"{i}. {airport} ({city}) - {degree} connections")

def find_shortest_path(G, start_code, end_code):
    """Знаходить оптимальний маршрут між двома містами (Dijkstra algorithm)."""
    try:
        path = nx.shortest_path(G, source=start_code, target=end_code, weight='weight')
        print(f"\n📍 OPTIMAL ROUTE ({start_code} -> {end_code}):")
        print(" -> ".join(path))
        return path
    except nx.NetworkXNoPath:
        print(f"\n❌ No path found between {start_code} and {end_code}")
        return None

def visualize_map(G, df):
    """Створює інтерактивну карту (відображає тільки Топ-100 маршрутів для швидкості)."""
    print(f"\n🗺️  Generating interactive map ({MAP_OUTPUT})...")
    
    # Центр карти - десь у Європі (Мюнхен)
    m = folium.Map(location=[48.1351, 11.5820], zoom_start=4, tiles="CartoDB dark_matter")

    # Малюємо хаби (топ 50)
    degree_dict = dict(G.degree(G.nodes()))
    top_nodes = sorted(degree_dict.items(), key=lambda item: item[1], reverse=True)[:50]
    
    for airport, count in top_nodes:
        if 'pos' in G.nodes[airport]:
            lat, lon = G.nodes[airport]['pos']
            city = G.nodes[airport].get('city', airport)
            
            folium.CircleMarker(
                location=[lat, lon],
                radius=count / 10, # Розмір залежить від кількості рейсів
                color="#3498db",
                fill=True,
                fill_color="#3498db",
                popup=f"{city} ({airport}): {count} routes"
            ).add_to(m)

    # Малюємо топ маршрути (щоб карта не висла)
    # Беремо перші 200 маршрутів з файлу для прикладу
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
    print("✅ Map saved! Open 'flight_network_map.html' in your browser.")

# --- Головний запуск ---
if __name__ == "__main__":
    df = load_data()
    flight_graph = build_graph(df)
    
    find_top_hubs(flight_graph)
    
    # Тест маршруту: Спробуємо долетіти з Шеннона (Ірландія) в Афіни
    find_shortest_path(flight_graph, 'SNN', 'ATH')
    
    visualize_map(flight_graph, df)
