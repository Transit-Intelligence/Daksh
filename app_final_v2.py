import folium
import streamlit as st
from folium.plugins import Draw
from streamlit_folium import st_folium
import requests
import datetime
import json
import polyline
from shapely.geometry import LineString, Point
from shapely import wkt
import pandas as pd
import os
import string
from pathlib import Path
import osmnx as ox
import isochrones as iso
import subprocess
import geopandas as gpd
st.set_page_config(layout = "wide", page_title="Scheduling ,Hub Analysis and coverage", page_icon=":bar_chart:", initial_sidebar_state="collapsed")
hide_streamlit_style = """
            <style>
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)
# Set up paths for file uploads and notebook execution
UPLOAD_FOLDER = Path(r"C:\Users\Welcome\OneDrive - Transit Intelligence\Desktop\app_final")
OUTPUT_FOLDER = Path(r"C:\Users\Welcome\OneDrive - Transit Intelligence\Desktop\app_final")
NOTEBOOK_PATH = UPLOAD_FOLDER / 'Final_loop_V2.ipynb'

# Ensure the upload and output directories exist
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
# Streamlit app configuration

ox.settings.requests_timeout = 600

# Initialize session state variables
if "hub_list" not in st.session_state:
    st.session_state.hub_list = [] 

if "file_fg" not in st.session_state:
    st.session_state.file_fg = folium.FeatureGroup()

if "zoom" not in st.session_state:
    st.session_state.zoom = 0

if "polygon_features" not in st.session_state:
    st.session_state.polygon_features = []
    
if "results" not in st.session_state:
    st.session_state.results = False

if "download_data" not in st.session_state:
    st.session_state.download_data = {
        "type": "FeatureCollection",
        "features": [],
        "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:EPSG::4326"}},
    }

if "selected_hub" not in st.session_state:
    st.session_state.selected_hub = None

# Initialize session state variables for login
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = True
    
if 'page' not in st.session_state:
    st.session_state['page'] = 'scheduling'  # Default page

# Function to create the navigation bar
def navigation_bar(current_page):
    st.markdown(f"""
        <style>
        .topnav {{
            background-color: #333;
            overflow: hidden;
        }}
        .topnav a {{
            float: left;
            color: #f2f2f2;
            text-align: center;
            padding: 14px 16px;
            text-decoration: none;
            font-size: 17px;
        }}
        .topnav a:hover {{
            background-color: #ddd;
            color: black;
        }}
        .topnav a.active {{
            background-color: #04AA6D;
            color: white;
        }}
        </style>
        <div class="topnav">
            <a href="?page=scheduling" class="{ 'active' if current_page == 'scheduling' else '' }">Scheduling & Electrification</a>
            <a href="?page=hub-analysis" class="{ 'active' if current_page == 'hub-analysis' else '' }">Hub Accessibility Analysis</a>
            <a href="?page=new-route-coverage" class="{ 'active' if current_page == 'new-route-coverage' else '' }">New Route Coverage Analysis</a>

        </div>
    """, unsafe_allow_html=True)

# Login page
# if not st.session_state['authenticated']:
#     st.title("Login to DAKSH Scheduling & Hub Analysis")

#     username = st.text_input("Username")
#     password = st.text_input("Password", type="password")

#     if st.button("Login"):
#         if username == "admin" and password == "123":  # Simple username/password check
#             st.session_state['authenticated'] = True
#             st.experimental_rerun()  # To re-run the app and show the navigation bar
#         else:
#             st.error("Invalid username or password")

# Main content after login
if st.session_state['authenticated']:
    # Retrieve query params and update the current page state
    query_params = st.query_params  # Keep this if it's supported in your version
    current_page = query_params.get('page', 'scheduling')  # Default to 'scheduling'

    # Display the navigation bar
    navigation_bar(current_page)

    if current_page == 'scheduling':
        st.header("Upload Files for Scheduling")
        required_files = [
            'Route Input Sheet', 
            'Charging Infra Parameters',
            'stops'
            ]
        user_input1 = st.text_input("Enter the value City Level Headway :",f"hh:mm:ss")
        user_input2 = st.text_input("Enter the City Level Peak Headway ",f"hh:mm:ss")
        user_input3 = st.text_input("Enter the value for Break Time:" ,f"hh:mm:ss")
        user_input4 = st.text_input("Enter the value for Lunch Break Time:",f"hh:mm:ss")
        uploaded_files = {}
        for file_key in required_files:
            uploaded_file = st.file_uploader(f"Upload {file_key}", type=None, key=file_key)
            if uploaded_file:
                uploaded_files[file_key] = UPLOAD_FOLDER / uploaded_file.name
                with open(uploaded_files[file_key], "wb") as f:
                    f.write(uploaded_file.getbuffer())
        
        
        
        
        
        
        
        
        if st.button("Run Scheduling Notebook"):
            if len(uploaded_files) <= len(required_files):
                with open('user_input3.json', 'w') as f:
                    json.dump({"user_input3": user_input3}, f)
                with open('user_input1.json', 'w') as f:
                    json.dump({"user_input1": user_input1}, f)
                with open('user_input2.json', 'w') as f:
                    json.dump({"user_input2": user_input2}, f)
                with open('user_input4.json', 'w') as f:
                    json.dump({"user_input4": user_input4}, f)
                    
                    
                command = f'jupyter nbconvert --to notebook --execute "{NOTEBOOK_PATH}" --output-dir="{OUTPUT_FOLDER}"'
                subprocess.run(command, shell=True)
                 
                # List of expected output files
                output_files = ['Route_wise_schedule.xlsx',
                     'stop_times.txt',
                    'trips.txt',
                    'Depot wise bus charging schedule.xlsx'
                ]
                # Display available output files for download
                st.header("Output Files")
                files_present = [f for f in output_files if (OUTPUT_FOLDER / f).exists()]
                
                if files_present:
                    for file in files_present:
                        file_path = OUTPUT_FOLDER / file
                        with open(file_path, "rb") as f:
                            st.download_button(f"Download {file}", f, file_name=file)
                else:
                    st.error("No output files generated")
            else:
                st.error("Please upload all required files.")

        st.header("Download Files")
        file_to_download = st.text_input("Enter the filename to download from the output folder")
        if st.button("Download"):
            download_file_path = OUTPUT_FOLDER / file_to_download
            if download_file_path.exists():
                with open(download_file_path, "rb") as f:
                    st.download_button(f"Download {file_to_download}", f, file_name=file_to_download)
            else:
                st.error(f"{file_to_download} does not exist.")
    elif current_page == 'hub-analysis':
        col1, col2 = st.columns([3, 1])

        with col1:

           input_container = st.empty()
           inputs = False
           mode_settings = []

           if not st.session_state.results:
               with input_container.container():
                   st.header("Public transportation attributes")
                   
                   public_transport = True
                   with st.expander("Define the trip attributes"):
                       weekday = st.selectbox(
                           "Departure Day",
                           (
                               "Monday",
                               "Tuesday",
                               "Wednesday",
                               "Thursday",
                               "Friday",
                               "Saturday",
                               "Sunday",
                           ),
                       )
                       start_time = st.time_input("Departure Time", value=datetime.time(12, 0))
                       max_travel_mins = st.number_input(
                           "Maximum Public Transport Travel Time (Minutes)", value=15
                       )
                       max_walk_mins = st.number_input(
                           "Maximum Walk Time to/from Public Transport Stops (Minutes)",
                           value=5,
                       )
                       pt_walk_speed_selector = st.selectbox(
                           "Walk Speed to Access Public Transport",
                           ("Slow", "Moderate", "Fast"),
                       )
                       if pt_walk_speed_selector == "Slow":
                           pt_walk_speed = 3.5
                       elif pt_walk_speed_selector == "Moderate":
                           pt_walk_speed = 4.25
                       elif pt_walk_speed_selector == "Fast":
                           pt_walk_speed = 5
                       transfers = st.toggle("Allow Transfers")

                   st.header("Location Selection")

                   st.write(
                       'Upload a CSV file of the bus stops. The CSV file should have an "id" column, a "name" column, a "lat" column, and a "lon" column.'
                   )
                   uploaded_points = st.file_uploader(
                       "Upload CSV here.", accept_multiple_files=False
                   )

                   if uploaded_points is not None:
                       points_df = pd.read_csv(uploaded_points)
                       st_data = {"all_drawings": []}

                       # Remove duplicates based on 'id' column
                       points_df = points_df.drop_duplicates(subset=["id"])

                       for index, row in points_df.iterrows():
                           id = row["id"]
                           name = row["name"]
                           lat = row["lat"]
                           lon = row["lon"]
                           upload_point_dict = {"id": id, "name": name, "lat": lat, "lon": lon}
                           st_data["all_drawings"].append(
                               {
                                   "type": "Feature",
                                   "properties": {"id": id, "name": name},
                                   "geometry": {"type": "Point", "coordinates": [lon, lat]},
                               }
                           )

                       all_drawings = st_data["all_drawings"]

                       hub_list = []
                       for drawing in all_drawings:
                           lat = drawing["geometry"]["coordinates"][1]
                           lon = drawing["geometry"]["coordinates"][0]
                           id = drawing["properties"]["id"]
                           name = drawing["properties"]["name"]
                           hub_dict = {"id": id, "name": name, "lat": lat, "lon": lon}
                           hub_list.append(hub_dict)

                       st.session_state.hub_list = hub_list

                       # Add a dropdown to select a specific bus stop
                       st.session_state.selected_hub = st.selectbox(
                           "Select a bus stop",
                           options=[hub["id"] for hub in hub_list],
                           format_func=lambda x: next(
                               (hub["name"] for hub in hub_list if hub["id"] == x), x
                           ),
                       )

                       if public_transport and len(st.session_state.hub_list) > 0:
                           if st.button("Run Analysis", type="primary"):
                               if public_transport:
                                   mode_settings.append(
                                       {
                                           "mode": "Public Transport",
                                           "weekday": weekday,
                                           "start_time": start_time,
                                           "max_travel_mins": max_travel_mins,
                                           "max_walk_mins": max_walk_mins,
                                           "pt_walk_speed": pt_walk_speed,
                                           "transfers": transfers,
                                       }
                                   )
                               inputs = True
                               input_container.empty()

               if inputs:
                   process_container = st.empty()
                   with process_container.container():
                       st.header("Analysis Progress")
                       selected_hub_name = next(
                           (
                               hub["name"]
                               for hub in hub_list
                               if hub["id"] == st.session_state.selected_hub
                           ),
                           st.session_state.selected_hub,
                       )
                       st.write(f"*Selected Bus Stop:* {selected_hub_name}")
                       mode_string = "Public Transport"
                       st.write("*Mode:* " + mode_string)

                       # Find the selected hub
                       selected_point = next(
                           (
                               hub
                               for hub in hub_list
                               if hub["id"] == st.session_state.selected_hub
                           ),
                           None,
                       )

                       if selected_point:
                           progress_bar = st.progress(0, text="0% Complete")
                           progress_prcnt = 0

                           centroid_lat = float(selected_point["lat"])
                           centroid_lon = float(selected_point["lon"])

                           budgets = []
                           for setting in mode_settings:
                               mode = setting["mode"]
                               if mode == "Public Transport":
                                   max_travel_mins = setting["max_travel_mins"]
                                   max_walk_mins = setting["max_walk_mins"]
                                   pt_walk_speed = setting["pt_walk_speed"]
                                   pt_walk_dist = max_walk_mins * (pt_walk_speed * 1000 / 60)
                                   transfers = setting["transfers"]
                                   start_time = str(setting["start_time"])[:-3]
                                   weekday = setting["weekday"]
                                   budgets.append(pt_walk_dist)

                           # Expands the extents by a certain number of meters.
                           buffer = int(max(budgets) + 1000)  # Meters

                           iso_list = []
                           for setting in mode_settings:
                               mode = setting["mode"]
                               if mode == "Public Transport":
                                   attributes = {"id": mode}
                                   pt_iso_stops = iso.accessed_stops(
                                       centroid_lat,
                                       centroid_lon,
                                       transfers,
                                       start_time,
                                       weekday,
                                       max_travel_mins,
                                       max_walk_mins,
                                   )

                                   progress_prcnt = 25
                                   progress_bar.progress(
                                       progress_prcnt, text=f"{progress_prcnt}% Complete"
                                   )

                                   stop_shapes = []
                                   for stop in pt_iso_stops:
                                       stop_name = stop["stop_name"]
                                       stop_lat = stop["stop_lat"]
                                       stop_lon = stop["stop_lon"]
                                       distances = [pt_walk_dist]
                                       attributes = {"id": stop_name}

                                       G = iso.get_network(stop_lat, stop_lon, distances)
                                       progress_prcnt = 50
                                       progress_bar.progress(
                                           progress_prcnt, text=f"{progress_prcnt}% Complete"
                                       )

                                       G_exploded = iso.process_network(G, stop_lat, stop_lon)
                                       progress_prcnt = 75
                                       progress_bar.progress(
                                           progress_prcnt, text=f"{progress_prcnt}% Complete"
                                       )

                                       pt_iso = iso.calculate_isochrones(
                                           stop_lat,
                                           stop_lon,
                                           G_exploded,
                                           attributes,
                                           distances,
                                       )

                                       pt_iso_shapes = pt_iso["shapes"]
                                       for poly in pt_iso_shapes:
                                           stop_shapes.append(poly["polygon"])

                                   pt_isochrone = gpd.GeoSeries(stop_shapes).unary_union
                                   pt_isochrone_json = json.loads(
                                       gpd.GeoSeries([pt_isochrone]).to_json()
                                   )

                                   iso_dict = {
                                       "json": pt_isochrone_json,
                                       "shapes": [
                                           {
                                               "polygon": pt_isochrone,
                                               "attributes": {
                                                   "id": selected_point["id"],
                                                   "name": selected_point["name"],
                                                   "mode": mode,
                                               },
                                           }
                                       ],
                                   }

                                   iso_list.append(iso_dict)

                                   progress_prcnt = 100
                                   progress_bar.progress(
                                       progress_prcnt, text=f"{progress_prcnt}% Complete"
                                   )

                           # Add the isochrones to the session state for plotting and download.
                           for isochrone in iso_list:
                               iso_shape_json = isochrone["json"]
                               st.session_state.polygon_features.append(iso_shape_json)
                               st.session_state.download_data["features"].append(
                                   iso_shape_json["features"][0]
                               )

                       st.session_state.results = True
                       process_container.empty()

           if st.session_state.results:
               st.header("Analysis Results")

               lat_min, lat_max = 90, -90
               lon_min, lon_max = 180, -180

               for hub in st.session_state.hub_list:
                   lat, lon = hub["lat"], hub["lon"]
                   lat_min, lat_max = min(lat_min, lat), max(lat_max, lat)
                   lon_min, lon_max = min(lon_min, lon), max(lon_max, lon)

               lat_mid = ((lat_max - lat_min) / 2) + lat_min
               lon_mid = ((lon_max - lon_min) / 2) + lon_min

               m2 = folium.Map(location=[lat_mid, lon_mid], zoom_start=11)

               color_dict = {"Public Transport": "red"}

               # Create a feature group for the isochrones
               isochrone_fg = folium.FeatureGroup(name="Isochrones")

               if st.session_state.polygon_features:
                   for polygon in st.session_state.polygon_features:
                       mode = polygon["features"][0]["properties"].get("mode", "Unknown")
                       color = color_dict.get(mode, "red")
                       style = lambda feature: {
                           "color": color,
                           "fillColor": color,
                           "fillOpacity": 0.2,
                       }
                       folium.GeoJson(polygon, style_function=style, tooltip=mode).add_to(
                           isochrone_fg
                       )

               isochrone_fg.add_to(m2)

               # Create a feature group for the markers
               marker_fg = folium.FeatureGroup(name="Bus Stops")

               if st.session_state.hub_list:
                   for hub in st.session_state.hub_list:
                       lat, lon = hub["lat"], hub["lon"]
                       label = hub["name"]

                       # Determine marker color and icon
                       if hub["id"] == st.session_state.selected_hub:
                           color = "green"
                           icon = folium.Icon(color=color, icon="star")
                       elif any(
                           feature["features"][0]["properties"].get("id") == hub["id"]
                           for feature in st.session_state.polygon_features
                       ):
                           color = "orange"
                           icon = folium.Icon(color=color, icon="info-sign")
                       else:
                           color = "blue"
                           icon = folium.Icon(color=color, icon="info-sign")

                       # Create marker with custom icon
                       marker = folium.Marker(
                           location=[lat, lon], popup=label, tooltip=label, icon=icon
                       )
                       marker.add_to(marker_fg)

               marker_fg.add_to(m2)

               # Add layer control to toggle marker and isochrone visibility
               folium.LayerControl().add_to(m2)

               st_data = st_folium(m2, height=500, width=1200)

               # Reverses the order of the features in the download data.
               download_features = st.session_state.download_data["features"]
               download_features.reverse()
               st.session_state.download_data["features"] = download_features

               # Prepares the download data for download.
               download_data = json.dumps(st.session_state.download_data)
               st.download_button(
                   label="Download Geospatial Data",
                   data=download_data,
                   file_name="hub_analysis.geojson",
                   mime="application/geo+json",
               )

               if st.button("New Analysis"):
                   st.session_state.results = False
                   st.session_state.polygon_features = []
                   st.session_state.file_fg = folium.FeatureGroup()
                   st.session_state.download_data = {
                       "type": "FeatureCollection",
                       "features": [],
                       "crs": {
                           "type": "name",
                           "properties": {"name": "urn:ogc:def:crs:EPSG::4326"},
                       },
                   }
                   st.rerun()

    elif current_page == 'new-route-coverage':
        def create_map(location=[39.949610, -75.150282], zoom_start=5):
            return folium.Map(location=location, zoom_start=5)

        # Function to snap to OSM using Valhalla API
        def snap_to_osm(coordinates):
            # Format coordinates as lat-lon pairs expected by Valhalla
            formatted_coordinates = [{"lat": lat, "lon": lon} for lon, lat in coordinates]

            # Create the payload
            payload = {
                "shape": formatted_coordinates,
                "costing": "auto",
                "shape_match": "map_snap"
            }

            url = 'https://valhalla1.openstreetmap.de/trace_route'  # Example Valhalla instance
            headers = {'Content-Type': 'application/json'}

            # Send the POST request
            response = requests.post(url, headers=headers, data=json.dumps(payload))

            if response.status_code == 200:
                return response.json()  # Return the parsed JSON response
            else:
                return {"error": f"Error: {response.status_code} - {response.text}"}

        # Function to generate stop names (A, B, C, ..., Z, AA, AB, etc.)
        def generate_stop_names(n):
            alphabet = list(string.ascii_uppercase)
            stop_names = []
            
            for i in range(n):
                name = ''
                while i >= 0:
                    name = alphabet[i % 26] + name
                    i = i // 26 - 1
                stop_names.append(name)
            
            return stop_names

        # Function to save WKT polyline to CSV with lat-lon swapped
        def save_wkt_to_csv(snapped_coords, file_name='wkt_polyline.csv'):
            # Swap lat, lon to lon, lat for WKT
            swapped_coords = [(lon, lat) for lat, lon in snapped_coords]
            wkt_polyline = LineString(swapped_coords).wkt
            
            # Save the WKT to CSV
            df = pd.DataFrame({'WKT': [wkt_polyline]})
            df.to_csv(file_name, index=False)

        # Function to save snapped clicked points to CSV with IDs, stop names, and stop IDs
        def save_snapped_points_to_csv(snapped_points, file_name='snapped_points.csv'):
            # Create a DataFrame with ID, Latitude, and Longitude
            df = pd.DataFrame(snapped_points, columns=['Latitude', 'Longitude'])
            
            # Add ID column
            df['ID'] = df.index + 1  # Sequential ID starting from 1
            
            # Add stop_name column (A, B, C, ..., Z, AA, AB, ...)
            df['stop_name'] = generate_stop_names(len(df))
            
            # Add stop_id column (e.g., 201_1, 201_2, ...)
            df['stop_id'] = df['ID'].apply(lambda x: f"201_{x}")
            
            # Reorder columns
            df = df[['ID', 'Latitude', 'Longitude', 'stop_name', 'stop_id']]
            
            # Save to CSV
            df.to_csv(file_name, index=False)

        # Function to extract coordinates from WKT
        def wkt_to_coords(wkt_polyline):
            line = wkt.loads(wkt_polyline)  # Using wkt.loads for WKT parsing
            return [(lat, lon) for lon, lat in line.coords]  # Return lat-lon pairs for Folium

        # Function to find closest point on the polyline to each clicked point
        def get_closest_points(clicked_coords, snapped_coords):
            closest_points = []
            for clicked_point in clicked_coords:
                clicked_point_geom = Point(clicked_point)
                # Find the closest point on the snapped polyline
                closest_point = min(snapped_coords, key=lambda p: Point(p).distance(clicked_point_geom))
                closest_points.append(closest_point)
            return closest_points

        # Create Streamlit app layout
        st.title("Interactive Drawing and Valhalla Response")

        # Initialize the Folium map for drawing
        m_draw = create_map()

        # Add the Draw plugin to the map
        draw = Draw(export=True, draw_options={'polyline': True, 'polygon': False, 'rectangle': False, 'circle': False, 'marker': False}).add_to(m_draw)

        # Render the drawing map
        st.subheader("Draw a Polyline")
        output = st_folium(m_draw, width=700, height=500)

        # Placeholder for the snapped result map
        result_map_placeholder = st.empty()

        # Button to snap features to OSM and show the raw response
        if st.button("Snap to OSM"):
            if 'last_active_drawing' in output:
                drawn_features = output['last_active_drawing']

                # Check if drawn_features is a dictionary and has the 'geometry' key
                if isinstance(drawn_features, dict) and 'geometry' in drawn_features:
                    try:
                        geometry_type = drawn_features['geometry']['type']

                        if geometry_type == 'LineString':
                            coordinates = drawn_features['geometry']['coordinates']  # [lon, lat] pairs

                            # Get the raw Valhalla response
                            snapped_data = snap_to_osm(coordinates)

                            # Display the raw Valhalla response
                            st.subheader("Valhalla API Response")
                            st.json(snapped_data)

                            # Check if there's a valid trip and extract shape from legs
                            snapped_coords = []
                            if 'trip' in snapped_data and 'legs' in snapped_data['trip']:
                                legs = snapped_data['trip']['legs']
                                
                                # Extract the snapped polyline coordinates
                                for leg in legs:
                                    if 'shape' in leg:
                                        shape = leg['shape']
                                        decoded_points = polyline.decode(shape)
                                        snapped_coords.extend([(lat / 10, lon / 10) for lat, lon in decoded_points])

                                # Get the closest points from the snapped polyline for each clicked point
                                clicked_coords = [(lat, lon) for lon, lat in coordinates]
                                closest_snapped_points = get_closest_points(clicked_coords, snapped_coords)

                                # Save the WKT polyline for the snapped route with swapped coordinates
                                save_wkt_to_csv(snapped_coords)

                                # Save only the snapped clicked points to CSV with IDs, stop names, and stop IDs
                                save_snapped_points_to_csv(closest_snapped_points)

                                # Create a new map to display the snapped polyline
                                m_result = create_map(location=snapped_coords[0])  # Center map on the first point
                                folium.PolyLine(locations=snapped_coords, color='red', weight=5).add_to(m_result)
                                for lat, lon in closest_snapped_points:
                                    folium.Marker(location=[lat, lon], icon=folium.Icon(color='red')).add_to(m_result)
                                # Clear the placeholder and render the new map with the polyline
                                result_map_placeholder.empty()  # Clear previous output
                                result_map_placeholder.subheader("Snapped OSM Polyline")
                                st_folium(m_result, width=700, height=500)

                            else:
                                st.error("No valid trip or legs found in the snapped response.")

                        else:
                            st.error("Drawn feature is not a LineString.")
                    except Exception as e:
                        st.error(f"Error parsing drawn features: {e}")
                else:
                    st.error("No geometry found in the drawn output or output is not a dictionary.")
            else:
                st.error("No features drawn yet.")

        # Second stage to display the CSVs
        st.subheader("Download Files")

        # WKT Polyline CSV
        if os.path.exists('wkt_polyline.csv'):
            st.download_button("Download WKT Polyline CSV", data=open('wkt_polyline.csv').read(), file_name="wkt_polyline.csv")

        # Snapped Points CSV
        if os.path.exists('snapped_points.csv'):
            st.download_button("Download Snapped Points CSV", data=open('snapped_points.csv').read(), file_name="snapped_points.csv")

            # Display the snapped points CSV
            df_snapped_points = pd.read_csv('snapped_points.csv')
            st.subheader("Snapped Points (Clicked and Snapped to Multiline)")
            st.dataframe(df_snapped_points)

            # Optionally, display snapped points on a map
            if not df_snapped_points.empty:
                snapped_points_coords = list(df_snapped_points[['Latitude', 'Longitude']].itertuples(index=False, name=None))
                snapped_points = list(df_snapped_points[['Latitude', 'Longitude']].itertuples(index=False, name=None))
                m_snapped_points = create_map(location=snapped_points_coords[0],zoom_start=1)
                folium.PolyLine(locations=snapped_points_coords, color='blue', weight=5).add_to(m_snapped_points)
                for lat, lon in snapped_points:
                        folium.Marker([lat, lon], popup=f"Location: ({lat}, {lon})", color='red').add_to(m_snapped_points)
                travel_time = num = st.number_input('Enter the walk travel time, for a moderate walk speed of 4 kmph:', min_value=0, max_value=50, value=5, step=1)
                if travel_time>0:
                    df_2 = df_snapped_points

                    df_2['geometry'] = df_2.apply(lambda row: Point(row['Longitude'], row['Latitude']), axis=1)

                    # Define the first point's location (latitude, longitude)
                    lat_point, lon_point = df_2.iloc[0]['Latitude'], df_2.iloc[0]['Longitude']

                    # Define a distance (25 km) to retrieve the OSM network around the first point
                    dist = 25000  # in meters (25 km)

                    # Download the street network within the radius from the point
                    G2 = ox.graph_from_point((lat_point, lon_point), dist=dist, network_type='walk')

                    # Project the graph for accurate distance calculations
                    G2 = ox.project_graph(G2)

                # Define travel time in minutes (e.g., 10 minutes) and convert it to distance (meters)
                    travel_speed = 4 * 1000 / 60  # meters per minute (assuming 4.5 km/h walking speed)
                    travel_distance = travel_speed * travel_time

                    # Function to calculate isochrone buffer
                    def create_isochrone(graph, lat, lon, travel_distance):
                        # Find the nearest node to the point
                        node = ox.distance.nearest_nodes(graph, lon, lat)
                        
                        # Use NetworkX to calculate travel time distances from the node
                        subgraph = nx.ego_graph(graph, node, radius=travel_distance, distance='length')
                        
                        # Generate an isochrone polygon
                        isochrone = ox.utils_graph.graph_to_gdfs(subgraph, nodes=False, edges=True)
                        return isochrone.unary_union

                    # Create buffers around each point
                    df_2['buffer'] = df_2.apply(lambda row: create_isochrone(G2, row['Latitude'], row['Longitude'], travel_distance), axis=1)
                    m_snapped_points = create_map(location=snapped_points_coords[0],zoom_start=1)

                    # Add original points to the map
                    for idx, row in df_2.iterrows():
                        folium.Marker(
                            location=[row['Latitude'], row['Longitude']],
                            popup=f"Point {idx+1}"
                        ).add_to(m_snapped_points)

                    # Add buffers (isochrones) to the map
                    for idx, row in df_2.iterrows():
                        folium.GeoJson(
                            data=row['buffer'].__geo_interface__,
                            style_function=lambda x: {'color': 'blue', 'fillColor': 'blue', 'opacity': 0.5, 'fillOpacity': 0.2}
                        ).add_to(m_snapped_points)

                    # Display the map in Streamlit
                    st_folium(m_snapped_points, width=700, height=500)
                else:
                    st.write("walk travel time value is less than anticipated")
            else:
                st.write("No snapped points CSV available yet.")
