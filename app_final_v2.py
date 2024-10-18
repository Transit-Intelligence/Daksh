import streamlit as st
import folium as f
from streamlit_folium import st_folium
from streamlit_option_menu import option_menu
import datetime
import isochrones as iso
import geopandas as gpd
import pandas as pd
import json
import osmnx as ox
import subprocess
from pathlib import Path

# Set up paths for file uploads and notebook execution
UPLOAD_FOLDER = Path(r'C:\Users\Welcome\OneDrive - Transit Intelligence\Desktop\folder_v2')
OUTPUT_FOLDER = Path(r'C:\Users\Welcome\OneDrive - Transit Intelligence\Desktop\folder_v2')
NOTEBOOK_PATH = UPLOAD_FOLDER / 'Final_loop_V4.ipynb'
NOTEBOOK_PATH2 = UPLOAD_FOLDER / 'Final_loop_V5.ipynb'
#NOTEBOOK_PATH3 = UPLOAD_FOLDER / '12 Scheduling+Electrification Final.ipynb'
NOTEBOOK_PATH4 = UPLOAD_FOLDER / 'Depot Allocation Sections.ipynb'

# Ensure the upload and output directories exist
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

# Streamlit app configuration
st.set_page_config(layout="wide", page_title="Scheduling ,Hub Analysis and Coverage")

ox.settings.requests_timeout = 600

# Initialize session state variables
if "hub_list" not in st.session_state:
    st.session_state.hub_list = [] 

if "file_fg" not in st.session_state:
    st.session_state.file_fg = f.FeatureGroup()

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

# Initialize session state variables for the page
if 'page' not in st.session_state:
    st.session_state['page'] = 'scheduling'  # Default page

# Create a navigation using radio buttons
st.title("Transportation Analysis Dashboard")
selected= option_menu(
    menu_title = None,
    options = ["Scheduling", "Electrification", "Depot Allocation","Hub Accessibility Analysis", "New Route Coverage Analysis"],
    default_index = 0,
    orientation = "horizontal",
)

# Scheduling Tab
if selected == 'Scheduling':
    st.header("Upload Files for Scheduling")
    required_files = [
        'Route Input Sheet', 
        'stops_V3'
    ]
    
    user_input1 = st.text_input("Enter the value City Level Headway:", "hh:mm:ss")
    user_input2 = st.text_input("Enter the City Level Peak Headway", "hh:mm:ss")
    user_input3 = st.text_input("Enter the value for Break Time:", "hh:mm:ss")
    user_input4 = st.text_input("Enter the value for Lunch Break Time:", "hh:mm:ss")
    
    uploaded_files = {}
    for file_key in required_files:
        uploaded_file = st.file_uploader(f"Upload {file_key}", type=None, key=file_key)
        if uploaded_file:
            uploaded_files[file_key] = UPLOAD_FOLDER / uploaded_file.name
            with open(uploaded_files[file_key], "wb") as f:
                f.write(uploaded_file.getbuffer())

    if st.button("Solve"):
        if len(uploaded_files) == len(required_files):
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
            output_files = ['Route_wise_schedule.xlsx', 'stop_times.txt', 'trips.txt']
            
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

# Electrification Tab
elif selected == 'Electrification':
    st.header("Upload Files for Electrification")
    
    # Required files for Electrification
    required_files = [
        'Route_wise_schedule', 
        'electrification_parameters'
    ]
    
    uploaded_files = {}
    for file_key in required_files:
        uploaded_file = st.file_uploader(f"Upload {file_key}", type=None, key=file_key)
        if uploaded_file:
            uploaded_files[file_key] = UPLOAD_FOLDER / uploaded_file.name
            with open(uploaded_files[file_key], "wb") as f:
                f.write(uploaded_file.getbuffer())

    # Button to run the notebook for Electrification
    if st.button("Run Electrification Notebook"):
        if len(uploaded_files) == len(required_files):
            command = f'jupyter nbconvert --to notebook --execute "{NOTEBOOK_PATH2}" --output-dir="{OUTPUT_FOLDER}"'
            subprocess.run(command, shell=True)

            # List of expected output files
            output_files = [
                'Depot wise bus charging schedule.xlsx',
                'Location Wise No of Chargers.xlsx'
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
                st.error("No output files generated.")
        else:
            st.error("Please upload all required files.")

    # Section to download additional files manually
    st.header("Download Files")
    file_to_download = st.text_input("Enter the filename to download from the output folder")
    if st.button("Download"):
        download_file_path = OUTPUT_FOLDER / file_to_download
        if download_file_path.exists():
            with open(download_file_path, "rb") as f:
                st.download_button(f"Download {file_to_download}", f, file_name=file_to_download)
        else:
            st.error(f"{file_to_download} does not exist.")

# Depot allocation Tab
elif selected == 'Depot Allocation':
    st.header("Upload Files for Depot Allocation")
    
    # Required files for Electrification
    required_files = [
        'depot_route_time_matrix'
        
    ]
    
    uploaded_files = {}
    for file_key in required_files:
        uploaded_file = st.file_uploader(f"Upload {file_key}", type=None, key=file_key)
        if uploaded_file:
            uploaded_files[file_key] = UPLOAD_FOLDER / uploaded_file.name
            with open(uploaded_files[file_key], "wb") as f:
                f.write(uploaded_file.getbuffer())

    # Button to run the notebook for Electrification
    if st.button("Run Depot Allocation"):
        if len(uploaded_files) == len(required_files):
            command = f'jupyter nbconvert --to notebook --execute "{NOTEBOOK_PATH4}" --output-dir="{OUTPUT_FOLDER}"'
            subprocess.run(command, shell=True)

            # List of expected output files
            output_files = [
                'Depot_Route_Bus_Allocation_Results.xlsx'
                
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
                st.error("No output files generated.")
        else:
            st.error("Please upload all required files.")

    # Section to download additional files manually
    st.header("Download Files")
    file_to_download = st.text_input("Enter the filename to download from the output folder")
    if st.button("Download"):
        download_file_path = OUTPUT_FOLDER / file_to_download
        if download_file_path.exists():
            with open(download_file_path, "rb") as f:
                st.download_button(f"Download {file_to_download}", f, file_name=file_to_download)
        else:
            st.error(f"{file_to_download} does not exist.")
# Hub Accessibility Analysis Tab
elif selected == 'Hub Accessibility Analysis':
    
    # Hub Accessibility Analysis section
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

           m2 = f.Map(location=[lat_mid, lon_mid], zoom_start=11)

           color_dict = {"Public Transport": "red"}

           # Create a feature group for the isochrones
           isochrone_fg = f.FeatureGroup(name="Isochrones")

           if st.session_state.polygon_features:
               for polygon in st.session_state.polygon_features:
                   mode = polygon["features"][0]["properties"].get("mode", "Unknown")
                   color = color_dict.get(mode, "red")
                   style = lambda feature: {
                       "color": color,
                       "fillColor": color,
                       "fillOpacity": 0.2,
                   }
                   f.GeoJson(polygon, style_function=style, tooltip=mode).add_to(
                       isochrone_fg
                   )

           isochrone_fg.add_to(m2)

           # Create a feature group for the markers
           marker_fg = f.FeatureGroup(name="Bus Stops")

           if st.session_state.hub_list:
               for hub in st.session_state.hub_list:
                   lat, lon = hub["lat"], hub["lon"]
                   label = hub["name"]

                   # Determine marker color and icon
                   if hub["id"] == st.session_state.selected_hub:
                       color = "green"
                       icon = f.Icon(color=color, icon="star")
                   elif any(
                       feature["features"][0]["properties"].get("id") == hub["id"]
                       for feature in st.session_state.polygon_features
                   ):
                       color = "orange"
                       icon = f.Icon(color=color, icon="info-sign")
                   else:
                       color = "blue"
                       icon = f.Icon(color=color, icon="info-sign")

                   # Create marker with custom icon
                   marker = f.Marker(
                       location=[lat, lon], popup=label, tooltip=label, icon=icon
                   )
                   marker.add_to(marker_fg)

           marker_fg.add_to(m2)

           # Add layer control to toggle marker and isochrone visibility
           f.LayerControl().add_to(m2)

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
               st.session_state.file_fg = f.FeatureGroup()
               st.session_state.download_data = {
                   "type": "FeatureCollection",
                   "features": [],
                   "crs": {
                       "type": "name",
                       "properties": {"name": "urn:ogc:def:crs:EPSG::4326"},
                   },
               }
               st.rerun()
               
    st.header("Upload Files for Stop Times and Trips")

    # Upload stop_times.txt file
    st.subheader("Stop Times File Upload")
    stop_times = st.file_uploader("Upload stop_times.txt", type=['txt'], key="stop_times")
    if stop_times:
        stop_times_path = UPLOAD_FOLDER / stop_times.name
        with open(stop_times_path, "wb") as f:
            f.write(stop_times.getbuffer())
        st.write(f"Uploaded: {stop_times.name}")
    
    # Button to process stop_times file
    if st.button("Process stop_times.txt"):
        if stop_times:
            # Add your processing logic here
            st.success(f"Processing {stop_times.name} completed successfully.")
        else:
            st.error("Please upload stop_times.txt file.")

    # Upload trips.txt file
    st.subheader("Trips File Upload")
    trips = st.file_uploader("Upload trips.txt", type=['txt'], key="trips")
    if trips:
        trips_path = UPLOAD_FOLDER / trips.name
        with open(trips_path, "wb") as f:
            f.write(trips.getbuffer())
        st.write(f"Uploaded: {trips.name}")
    
    # Button to process trips file
    if st.button("Process trips.txt"):
        if trips:
            # Add your processing logic here
            st.success(f"Processing {trips.name} completed successfully.")
        else:
            st.error("Please upload trips.txt file.")       

# New Route Coverage Analysis Tab
elif selected == 'New Route Coverage Analysis':
    st.header("New Route Coverage Analysis")
    # Placeholder for New Route Coverage Analysis content
    st.write("New Route coverage content goes here...")
