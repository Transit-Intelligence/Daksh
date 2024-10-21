import requests
import pandas as pd
from io import BytesIO
import base64
import streamlit as st
from streamlit_option_menu import option_menu
import json
import osmnx as ox

st.set_page_config(layout="wide", page_title="Scheduling, Hub Analysis, and Coverage")

ox.settings.requests_timeout = 600

# Initialize session state variables
if "hub_list" not in st.session_state:
    st.session_state.hub_list = []

if "file_fg" not in st.session_state:
    st.session_state.file_fg = None

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

# Page layout and selection menu
st.title("DAKSH tool for bus service planning and scheduling")
selected = option_menu(
    menu_title=None,
    options=["Bus Scheduling", "Depot-Route Allocation", "Charger Scheduling", "Accessibility"],
    default_index=0,
    orientation="horizontal",
)

# GitHub repository details

repo_owner = "LakshayTaneja"
repo_name = "DakshPrivate"
github_token = "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"
branch_name = "main"
UPLOAD_FOLDER = "UPLOAD_FOLDER"

# Function to upload/overwrite a file on GitHub
def upload_file_to_github(file_name, file_content, folder_url, github_token):
    file_path = f"{folder_url}/{file_name}"
    encoded_content = base64.b64encode(file_content).decode()

    file_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{file_path}"
    headers = {"Authorization": f"token {github_token}", "Content-Type": "application/json"}
    
    # Check if the file already exists
    response = requests.get(file_url, headers=headers)
    
    if response.status_code == 200:
        sha = response.json().get("sha")  # File exists, so update it
        commit_message = f"Update {file_name}"
    else:
        sha = None  # File doesn't exist, so create it
        commit_message = f"Add {file_name}"
    
    # Prepare data for upload
    data = {"message": commit_message, "content": encoded_content, "branch": "main"}
    if sha:
        data["sha"] = sha  # Include the sha to update the existing file
    
    # Upload file
    response = requests.put(file_url, json=data, headers=headers)
    return response.status_code in [200, 201]


if selected == 'Depot-Route Allocation':
    st.header("Inputs for Depot-Route Bus Allocation")
    required_file = 'depot_route_time_matrix'
    uploaded_file = st.file_uploader(f"Upload {required_file}", type=['xlsx'], key=required_file)

    if uploaded_file is not None:
        # Read the file content
        file_content = uploaded_file.read()
        file_name = "depot_route_time_matrix.xlsx"
        
        # Upload the file to GitHub
        upload_success = upload_file_to_github(file_name, file_content, UPLOAD_FOLDER, github_token)
        
        if upload_success:
            st.success(f"File '{file_name}' uploaded/updated successfully in GitHub!")
        else:
            st.error(f"Failed to upload '{file_name}' to GitHub.")

    # After file is uploaded, the "Run Depot Allocation" button is enabled
    if st.button("Run Depot Allocation"):
        file_path = f"{UPLOAD_FOLDER}/depot_route_time_matrix.xlsx"  # Path in GitHub

        # GitHub API URL for fetching the Excel file
        file_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{file_path}"

        # Prepare headers for the API request
        headers = {
            "Authorization": f"token {github_token}",
            "Content-Type": "application/json",
        }

        # Fetch the Excel file from the GitHub repository
        response = requests.get(file_url, headers=headers)
        
        if response.status_code == 200:
            file_content = response.json().get('content')
            decoded_content = base64.b64decode(file_content)  # Decode the base64 content

            # Load the Excel file into a pandas DataFrame
            df = pd.read_excel(BytesIO(decoded_content))
            st.write(df.head())  # Display the first few rows of the DataFrame

            # Process depot route and allocation logic
            buses_required = df.iloc[-1, 1:-1]  # Exclude 'Depot' and 'Capacity' columns
            buses_required.index = df.columns[1:-1]  # Set the route names as the index

            # Remove the last row (buses required) from the main data frame
            df = df.iloc[:-1, :]

            # Extract depot capacities (last column)
            depot_capacity_df = df[['Depot', 'Capacity']].set_index('Depot')

            # Extract route names (all columns except 'Depot' and 'Capacity')
            route_columns = [col for col in df.columns if col not in ['Depot', 'Capacity']]

            # Function to allocate buses
            def allocate_buses(route_list, buses_required):
                allocation = []

                for route in route_list:
                    buses_per_route = buses_required[route]
                    depots_for_route = df[['Depot', route, 'Capacity']].sort_values(route)

                    buses_allocated = 0
                    for index, depot in depots_for_route.iterrows():
                        depot_name = depot['Depot']
                        available_capacity = depot_capacity_df.loc[depot_name, 'Capacity']

                        if available_capacity > 0:
                            buses_to_allocate = min(available_capacity, buses_per_route - buses_allocated)

                            if buses_to_allocate > 0:
                                depot_capacity_df.loc[depot_name, 'Capacity'] -= buses_to_allocate
                                allocation.append({'Route': route, 'Depot': depot_name, 'Buses Allocated': buses_to_allocate})
                                buses_allocated += buses_to_allocate

                            if buses_allocated == buses_per_route:
                                break

                    if buses_allocated < buses_per_route:
                        st.warning(f"Warning: Could not allocate all buses for route {route}")

                return pd.DataFrame(allocation)

            # Perform bus allocation
            allocation_df = allocate_buses(route_columns, buses_required)

            # Save the result as an Excel file in memory
            output_buffer = BytesIO()
            allocation_df.to_excel(output_buffer, index=False)
            output_buffer.seek(0)

            # Display results in Streamlit
            st.write(allocation_df)

            # Provide a download button for the allocation results
            st.download_button(
                label="Download Depot-Route Allocation Results",
                data=output_buffer,
                file_name="Depot_Route_Bus_Allocation_Results.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.error(f"Error fetching the file from GitHub: {response.status_code}")
