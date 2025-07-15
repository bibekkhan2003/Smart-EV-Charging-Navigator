import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import folium_static
import numpy as np
from datetime import datetime, timedelta
import json
import time

# Page configuration
st.set_page_config(
    page_title="EV Charging Optimization Platform",
    page_icon="🔋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Backend API base URL
BACKEND_URL = "http://localhost:8000"

# Initialize session state
if 'user_location' not in st.session_state:
    st.session_state.user_location = None
if 'selected_city' not in st.session_state:
    st.session_state.selected_city = "Mumbai"

def get_stations_data(city):
    try:
        response = requests.get(f"{BACKEND_URL}/api/stations?city={city}", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to fetch stations data: {response.status_code}")
            return []
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to backend: {str(e)}")
        return []


def get_route_optimization(start_lat, start_lon, end_lat, end_lon):
    """Get optimized route using A* algorithm"""
    try:
        payload = {
            "start_lat": start_lat,
            "start_lon": start_lon,
            "end_lat": end_lat,
            "end_lon": end_lon
        }
        response = requests.post(f"{BACKEND_URL}/api/route", json=payload, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Route optimization failed: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error getting route: {str(e)}")
        return None

def get_utilization_prediction(station_id):
    """Get utilization prediction for a station"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/predict/{station_id}", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Prediction failed: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error getting prediction: {str(e)}")
        return None



def get_smart_recommendations(city, user_lat, user_lon):
    try:
        response = requests.get(
            f"{BACKEND_URL}/api/recommendations",
            params={"city": city, "lat": user_lat, "lon": user_lon},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.warning(f"Recommendation fetch failed: {response.status_code}")
            return None
    except Exception as e:
        st.warning(f"Error getting recommendations: {str(e)}")
        return None

def create_map(stations_data, center_lat=28.6139, center_lon=77.2090):
    """Create folium map with charging stations"""
    m = folium.Map(location=[center_lat, center_lon], zoom_start=11)
    
    for station in stations_data:
        # Color based on availability
        if station['available_slots'] > 5:
            color = 'green'
        elif station['available_slots'] > 0:
            color = 'orange'
        else:
            color = 'red'
        
        popup_html = f"""
        <b>{station['name']}</b><br>
        Available: {station['available_slots']}/{station['total_slots']}<br>
        Type: {station['type']}<br>
        Address: {station['address']}<br>
        Cost: ₹{station['cost_per_hour']}/hour
        """
        
        folium.Marker(
            [station['lat'], station['lon']],
            popup=popup_html,
            icon=folium.Icon(color=color, icon='bolt')
        ).add_to(m)
    
    return m
from math import radians, cos, sin, sqrt, atan2

def haversine(lat1, lon1, lat2, lon2):
    # Radius of Earth in km
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

def get_recommendations(stations, user_lat, user_lon):
    def distance(station):
        return haversine(user_lat, user_lon, station['lat'], station['lon'])

    def queue_time(station):
        return (station['total_slots'] - station['available_slots']) / station['total_slots'] if station['total_slots'] > 0 else float('inf')

    def cost(station):
        return station['cost_per_hour']

    def charging_speed(station):
        return 1 if station['type'].lower() == 'fast' else 2  # fast < normal

    sorted_by_distance = sorted(stations, key=distance)
    sorted_by_queue = sorted(stations, key=queue_time)
    sorted_by_cost = sorted(stations, key=cost)
    sorted_by_speed = sorted(stations, key=charging_speed)

    return {
        "Nearest": sorted_by_distance[0],
        "Lowest Queue Time": sorted_by_queue[0],
        "Lowest Cost": sorted_by_cost[0],
        "Fastest Charging": sorted_by_speed[0]
    }



def main():
    st.title("🔋 EV Charging Optimization Platform")
    st.markdown("*AI-powered charging station finder and route optimization*")
    
    # Sidebar for controls
    st.sidebar.header("🎯 Search Parameters")
    
    # City selection
    cities = ["Delhi", "Mumbai", "Bangalore", "Chennai", "Hyderabad", "Pune", "Kolkata"]
    selected_city = st.sidebar.selectbox("Select City", cities, index=cities.index(st.session_state.selected_city), key="city_selector")
    st.session_state.selected_city = selected_city
    
    # User location input
    #st.sidebar.subheader("📍 Your Location")
    #user_lat = st.sidebar.number_input("Latitude", value=28.6139, format="%.6f")
    #user_lon = st.sidebar.number_input("Longitude", value=77.2090, format="%.6f")'''
    
    if st.sidebar.button("Update Location"):
        st.session_state.user_location = (22.5726, 88.3639)
        st.sidebar.success("Location updated!")
    
    # Battery level
    battery_level = st.sidebar.slider("Current Battery Level (%)", 0, 100, 40)
    
    # Vehicle type
    vehicle_type = st.sidebar.selectbox("Vehicle Type", ["Car", "Bike", "Auto", "Bus"])
    
    # Fetch stations data
    with st.spinner("Loading charging stations..."):
      all_stations = get_stations_data(selected_city)

    if st.session_state.user_location:
            user_lat, user_lon = st.session_state.user_location
            stations_data = [
            s for s in all_stations
            if haversine(user_lat, user_lon, s['lat'], s['lon']) <= 10
        ]
    else:
        stations_data = all_stations

    # ✅ Add coordinate table here
    if stations_data:
        st.subheader("📌 Station Coordinates from Backend")
        st.dataframe(pd.DataFrame(stations_data)[['name', 'lat', 'lon', 'city']])


    
    if not stations_data:
        st.error("Unable to load charging stations.")
        st.stop()
    # 💡 Smart Recommendations Section
    recos=None
    if st.session_state.user_location:
        recos = get_smart_recommendations(selected_city, *st.session_state.user_location)
    if recos:
        st.subheader("💡 Smart Station Recommendations")
        rec_cols = st.columns(4)

        with rec_cols[0]:
            st.markdown("### 📍 Nearest")
            s = recos["nearest"]
            st.success(s["name"])
            st.write(f"📍 {s['address']}")
            st.write(f"🔌 {s['available_slots']} / {s['total_slots']} slots")
            st.write(f"💰 ₹{s['cost_per_hour']} / hr")

        with rec_cols[1]:
            st.markdown("### 💸 Cheapest")
            s = recos["cheapest"]
            st.success(s["name"])
            st.write(f"📍 {s['address']}")
            st.write(f"💰 ₹{s['cost_per_hour']} / hr")
            st.write(f"🔌 {s['available_slots']} slots")

        with rec_cols[2]:
            st.markdown("### ⚡ Fast Charging")
            s = recos["fastest"]
            st.success(s["name"])
            st.write(f"📍 {s['address']}")
            st.write(f"⚡ {s['type']}")
            st.write(f"💰 ₹{s['cost_per_hour']} / hr")

        with rec_cols[3]:
            st.markdown("### 🕒 Lowest Queue")
            s = recos["least_queue"]
            st.success(s["name"])
            st.write(f"📍 {s['address']}")
            st.write(f"🔌 {s['available_slots']} available")
            st.write(f"💰 ₹{s['cost_per_hour']} / hr")



    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🗺️ Charging Stations Map")
        
        # Create and display map
        if stations_data:
            city_coords = {
                "Delhi": (28.6139, 77.2090),
                "Mumbai": (19.0760, 72.8777),
                "Bangalore": (12.9716, 77.5946),
                "Chennai": (13.0827, 80.2707),
                "Hyderabad": (17.3850, 78.4867),
                "Pune": (18.5204, 73.8567),
                "Kolkata": (22.5726, 88.3639)
            }
            
            center_lat, center_lon = city_coords.get(selected_city, (28.6139, 77.2090))
            #st.sidebar.selectbox("Select City", cities, index=cities.index(st.session_state.selected_city), key="unique_city_selector")


            #st.session_state.selected_city = selected_city
            map_obj = create_map(stations_data, center_lat, center_lon)
            folium_static(map_obj, width=800, height=500)
            #st.session_state.user_location = city_coords[selected_city]
    
    with col2:
        st.subheader("📊 Station Statistics")
        
        if stations_data:
            # Calculate statistics
            total_stations = len(stations_data)
            available_stations = sum(1 for s in stations_data if s['available_slots'] > 0)
            total_slots = sum(s['total_slots'] for s in stations_data)
            available_slots = sum(s['available_slots'] for s in stations_data)
            
            st.metric("Total Stations", total_stations)
            st.metric("Available Stations", available_stations)
            st.metric("Total Slots", total_slots)
            st.metric("Available Slots", available_slots)
            
            # Availability chart
            availability_data = {
                'Status': ['Available', 'Occupied'],
                'Count': [available_slots, total_slots - available_slots]
            }
            
            fig = px.pie(
                values=availability_data['Count'],
                names=availability_data['Status'],
                title="Slot Availability",
                color_discrete_map={'Available': 'green', 'Occupied': 'red'}
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Station details and route optimization
    st.subheader("🎯 Station Details & Route Optimization")
    
    # Station selection
    station_names = [f"{s['name']} ({s['available_slots']}/{s['total_slots']} available)" for s in stations_data]
    selected_station_idx = st.selectbox("Select a station for details", range(len(station_names)), 
                                       format_func=lambda x: station_names[x])
    
    if selected_station_idx is not None:
        selected_station = stations_data[selected_station_idx]
        
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            st.info(f"**{selected_station['name']}**")
            st.write(f"📍 {selected_station['address']}")
            st.write(f"🔌 {selected_station['available_slots']}/{selected_station['total_slots']} slots available")
            st.write(f"⚡ Type: {selected_station['type']}")
            st.write(f"💰 Cost: ₹{selected_station['cost_per_hour']}/hour")
        
        with col2:
            if st.button("🗺️ Get Route"):
                if st.session_state.user_location:
                    with st.spinner("Calculating optimal route..."):
                        route_data = get_route_optimization(
                            st.session_state.user_location[0], st.session_state.user_location[1],
                            selected_station['lat'], selected_station['lon']
                        )
                        if route_data:
                            st.success(f"Distance: {route_data['distance']:.2f} km")
                            st.success(f"Estimated Time: {route_data['time']:.1f} minutes")
                            st.success(f"Energy Cost: {route_data['energy_cost']:.2f} kWh")
                else:
                    st.warning("Please set your location first!")
        
        with col3:
            if st.button("📈 View Predictions"):
                with st.spinner("Loading utilization predictions..."):
                    prediction_data = get_utilization_prediction(selected_station['id'])
                    if prediction_data:
                        st.success("Predictions loaded!")
                        # Display prediction chart
                        timestamps = prediction_data['timestamps']
                        utilization = prediction_data['utilization']
                        
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(
                            x=timestamps,
                            y=utilization,
                            mode='lines+markers',
                            name='Predicted Utilization'
                        ))
                        fig.update_layout(
                            title='24-Hour Utilization Prediction',
                            xaxis_title='Time',
                            yaxis_title='Utilization %'
                        )
                        st.plotly_chart(fig, use_container_width=True)
    
    # Analytics section
    st.subheader("📊 Analytics Dashboard")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Station type distribution
        if stations_data:
            type_counts = {}
            for station in stations_data:
                station_type = station['type']
                type_counts[station_type] = type_counts.get(station_type, 0) + 1
            
            fig = px.bar(
                x=list(type_counts.keys()),
                y=list(type_counts.values()),
                title="Station Types Distribution",
                labels={'x': 'Station Type', 'y': 'Count'}
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Cost analysis
        if stations_data:
            costs = [s['cost_per_hour'] for s in stations_data]
            fig = px.histogram(
                x=costs,
                title="Cost Distribution (₹/hour)",
                labels={'x': 'Cost per Hour', 'y': 'Number of Stations'}
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Battery swapping network
    st.subheader("🔄 Battery Swapping Network")
    
    # Filter stations that support battery swapping
    swapping_stations = [s for s in stations_data if s.get('supports_swapping', False)]
    
    if swapping_stations:
        st.write(f"Found {len(swapping_stations)} battery swapping stations")
        
        # Create DataFrame for swapping stations
        swapping_df = pd.DataFrame(swapping_stations)
        st.dataframe(swapping_df[['name', 'address', 'available_slots', 'total_slots', 'cost_per_hour']])
    else:
        st.info("No battery swapping stations available in the selected city currently.")
    
    # Footer
    st.markdown("---")
    st.markdown("*Powered by AI algorithms - A* pathfinding and LSTM predictions*")
    
    # Auto-refresh option
    if st.checkbox("Auto-refresh (30 seconds)"):
        time.sleep(30)
        st.rerun()

if __name__ == "__main__":
    main()
