import pandas as pd
import numpy as np
import datetime as datetime
import os
import sys
import time
from datetime import datetime, timedelta

# import datetime
import matplotlib.pyplot as plt
import zipfile
import csv
import utm
import math

if not hasattr(np, "float"):
    np.float = float
import osmnx as ox
import random
import numpy as np
import networkx as nx
import geopandas as gpd
from shapely.geometry import Point, Polygon, LineString
import ast
import json

current_dir = os.path.dirname(os.path.abspath(__file__))

GTFS = [
    "trips.txt",
    "stop_times.txt",
    "stops.txt",
    "calendar.txt",
    "calendar_dates.txt",
]


def accessed_stops(
    input_lat, input_lon, transfers, start_time, weekday, max_travel_mins, max_walk_mins
):
    if weekday == "Monday":
        weekday = "monday"
    elif weekday == "Tuesday":
        weekday = "tuesday"
    elif weekday == "Wednesday":
        weekday = "wednesday"
    elif weekday == "Thursday":
        weekday = "thursday"
    elif weekday == "Friday":
        weekday = "friday"
    elif weekday == "Saturday":
        weekday = "saturday"
    elif weekday == "Sunday":
        weekday = "sunday"

    transfer_dist = 100  # Meters

    utm_inputs = utm.from_latlon(input_lat, input_lon)
    utm_lat = utm_inputs[1]
    utm_lon = utm_inputs[0]
    closest_stop = {"stop_id": "stop_id", "distance": math.inf}

    # Empty dataframes for GTFS data.
    stops_df = pd.DataFrame()
    calendar_df = pd.DataFrame()
    calendar_dates_df = pd.DataFrame()
    trips_df = pd.read_csv(
        os.path.join(current_dir, "GTFS", "trips.txt"),
    )
    stop_times_df = pd.read_csv(
        os.path.join(current_dir, "GTFS", "stop_times.txt"),
    )
    file_stops_df = pd.read_csv(
        os.path.join(current_dir, "GTFS", "stops.txt"),
        dtype={"stop_id": "str", "stop_lat": "float", "stop_lon": "float"},
    )

    file_stops_df["file"] = str(os.path.join(current_dir, "GTFS", "stops.txt"))
    stops_df = pd.concat([stops_df, file_stops_df], ignore_index=True)
    file_calendar_df = pd.read_csv(
        os.path.join(current_dir, "GTFS", "calendar.txt"),
        dtype={
            "service_id": "str",
            "monday": "str",
            "tuesday": "str",
            "wednesday": "str",
            "thursday": "str",
            "friday": "str",
            "saturday": "str",
            "sunday": "str",
            "start_date": "int64",
            "end_date": "int64",
        },
        delimiter=",",
    )

    file_calendar_df["file"] = str(os.path.join(current_dir, "GTFS", "calendar.txt"))
    calendar_df = pd.concat([calendar_df, file_calendar_df], ignore_index=True)
    file_calendar_dates_df = pd.read_csv(
        os.path.join(current_dir, "GTFS", "calendar_dates.txt"),
        dtype={"service_id": "str", "date": "int64", "exception_type": "str"},
        delimiter=",",
    )

    calendar_df_list = []
    service_list = list(set(file_calendar_dates_df["service_id"].tolist()))
    for service in service_list:
        new_row = {
            "service_id": service,
            "monday": "0",
            "tuesday": "0",
            "wednesday": "0",
            "thursday": "0",
            "friday": "0",
            "saturday": "0",
            "sunday": "0",
            "start_date": 0,
            "end_date": 0,
        }
        calendar_df_list.append(new_row)

    file_calendar_df = pd.DataFrame.from_dict(calendar_df_list, orient="columns")

    date_day_dict = {
        "0": "monday",
        "1": "tuesday",
        "2": "wednesday",
        "3": "thursday",
        "4": "friday",
        "5": "saturday",
        "6": "sunday",
    }

    for index, row in file_calendar_dates_df.iterrows():
        service_id = row["service_id"]
        date = row["date"]
        date_formatted = datetime.strptime(str(date), "%Y%m%d")
        date_day_num = str(datetime.weekday(date_formatted))
        date_day = date_day_dict[date_day_num]
        file_calendar_df.loc[file_calendar_df["service_id"] == service_id, date_day] = (
            "1"
        )
        file_calendar_df.loc[
            file_calendar_df["service_id"] == service_id, "start_date"
        ] = date
        file_calendar_df.loc[
            file_calendar_df["service_id"] == service_id, "end_date"
        ] = date

    file_calendar_df["file"] = str(os.path.join(current_dir, "GTFS", "calendar.txt"))
    calendar_df = pd.concat([calendar_df, file_calendar_df], ignore_index=True)
    GTFS_file_list = list(set(calendar_df["file"].tolist()))

    if len(GTFS_file_list) > 1:
        calendar_df_2 = calendar_df
        file_counter = 0
        first_start = ""
        day_diff = ""

        for file in GTFS_file_list:
            file_counter += 1
            if file_counter == 1:
                first_start = calendar_df[calendar_df["file"] == file][
                    "start_date"
                ].min()
            else:
                file_start = calendar_df[calendar_df["file"] == file][
                    "start_date"
                ].min()
                first_start_formatted = datetime.strptime(str(first_start), "%Y%m%d")
                file_start_formatted = datetime.strptime(str(file_start), "%Y%m%d")
                day_diff = first_start_formatted - file_start_formatted

                for index, row in calendar_df.iterrows():
                    if row["file"] == file:
                        start_date_new = (
                            datetime.strptime(str(row["start_date"]), "%Y%m%d")
                            + day_diff
                        )
                        calendar_df_2.loc[index, "start_date"] = int(
                            start_date_new.strftime("%Y%m%d")
                        )
                        end_date_new = (
                            datetime.strptime(str(row["end_date"]), "%Y%m%d") + day_diff
                        )
                        calendar_df_2.loc[index, "end_date"] = int(
                            end_date_new.strftime("%Y%m%d")
                        )

        calendar_df = calendar_df_2

        # calendar_dates_df_2 = calendar_dates_df

    # THIS SECTION DETERMINES IF NEW IDS ARE REQUIRED, THEN MAKES THEM.
    # List of all stop IDs.
    stop_ids = stops_df["stop_id"].tolist()

    # Set of unique stop IDs.
    unique_ids = set(stop_ids)

    # Checks to see if there are duplicat IDs. If so, new IDs are created.
    new_ids = False
    if len(stop_ids) > len(unique_ids):

        new_ids = True

        # Sets up the dictionary of IDs.
        stop_id_unique = {}
        master_set = set()
        for file in GTFS:
            key = str(file)
            stop_id_unique[key] = {}
            for file in GTFS:
                file_ids = stops_df[stops_df["file"] == str(file)]["stop_id"].tolist()
            for id in file_ids:
                new_id = str(random.randint(100000, 999999))
                while new_id in master_set:
                    new_id = str(random.randint(100000, 999999))
                master_set.add(new_id)
                stop_id_unique[str(file)][id] = new_id

        # Replaces the old stop IDs with the new, random stop IDs in the stops dataframe.
        for index, row in stops_df.iterrows():
            file = row["file"]
            old_id = row["stop_id"]
            stops_df.loc[index, "stop_id"] = stop_id_unique[file][old_id]

    # PROCESSES THE STOPS DATAFRAME.
    # Gets the column names as a list.
    stops_df_columns = stops_df.columns.tolist()

    stops_dict = {}
    stop_name_dict = {}
    for index, row in stops_df.iterrows():
        stop_id = row["stop_id"]
        stop_lat = row["stop_lat"]
        stop_lon = row["stop_lon"]
        stop_name = row["stop_name"]
        if "location_type" in stops_df_columns:
            location_type = row["location_type"]
            if location_type == 0 or str(location_type) == "nan":
                stops_dict[stop_id] = {
                    "stop_name": stop_name,
                    "stop_lat": stop_lat,
                    "stop_lon": stop_lon,
                    "stop_times": [],
                }
                stop_name_dict[stop_name] = []

                stop_utm = utm.from_latlon(stop_lat, stop_lon)
                stop_lat_utm = stop_utm[1]
                stop_lon_utm = stop_utm[0]

                distance = ox.distance.euclidean(
                    utm_lat, utm_lon, stop_lat_utm, stop_lon_utm
                )
                if distance < closest_stop["distance"]:
                    closest_stop["stop_id"] = stop_id
                    closest_stop["distance"] = distance

        else:
            stops_dict[stop_id] = {
                "stop_name": stop_name,
                "stop_lat": stop_lat,
                "stop_lon": stop_lon,
                "stop_times": [],
            }
            stop_name_dict[stop_name] = []

            stop_utm = utm.from_latlon(stop_lat, stop_lon)
            stop_lat_utm = stop_utm[1]
            stop_lon_utm = stop_utm[0]

            distance = ox.distance.euclidean(
                utm_lat, utm_lon, stop_lat_utm, stop_lon_utm
            )
            if distance < closest_stop["distance"]:
                closest_stop["stop_id"] = stop_id
                closest_stop["distance"] = distance

    for index, row in stops_df.iterrows():
        if "location_type" in stops_df_columns:
            location_type = row["location_type"]
            if location_type == 0 or str(location_type) == "nan":
                stop_id = row["stop_id"]
                stop_name = row["stop_name"]
                stop_name_dict[stop_name].append(stop_id)

        else:
            stop_id = row["stop_id"]
            stop_name = row["stop_name"]
            stop_name_dict[stop_name].append(stop_id)

    # Creates a dictionary of stop names with the middle point for each collection of stops associated with that name.
    names_list = list(stop_name_dict.keys())
    simple_stops = {}
    for name in names_list:
        lats = []
        lons = []
        for stop in stop_name_dict[name]:
            stop_lat = stops_dict[stop]["stop_lat"]
            stop_lon = stops_dict[stop]["stop_lon"]
            lats.append(stop_lat)
            lons.append(stop_lon)
        lat_max = max(lats)
        lat_min = min(lats)
        lon_max = max(lons)
        lon_min = min(lons)
        lat_mid = lat_min + ((lat_max - lat_min) / 2)
        lon_mid = lon_min + ((lon_max - lon_min) / 2)
        simple_stops[name] = {"lat_mid": lat_mid, "lon_mid": lon_mid}

    start_point = closest_stop["stop_id"]

    # Loops through the stops, adds the utm coordinates to the dataframe.
    for index, row in stops_df.iterrows():
        stop_lat = row["stop_lat"]
        stop_lon = row["stop_lon"]
        stop_utm = utm.from_latlon(stop_lat, stop_lon)
        utm_lat = stop_utm[1]
        utm_lon = stop_utm[0]
        stops_df.loc[index, "utm_lat"] = utm_lat
        stops_df.loc[index, "utm_lon"] = utm_lon

    # Loops thorugh the stops, for each stop, it calculates all distances to all other stops, adds the close ones to a dictionary.
    transfer_dict = {}
    for index, row in stops_df.iterrows():
        origin_id = row["stop_id"]
        origin_utm_lat = row["utm_lat"]
        origin_utm_lon = row["utm_lon"]
        stops_df["distance"] = (
            abs(origin_utm_lat - stops_df["utm_lat"]) ** 2
            + abs(origin_utm_lon - stops_df["utm_lon"]) ** 2
        ) ** 0.5
        if "location_type" in stops_df_columns:
            if row["location_type"] == 0:
                transfer_nodes = stops_df[
                    (stops_df["distance"] <= transfer_dist)
                    & (stops_df["location_type"] == 0)
                ]["stop_id"].values
            elif str(row["location_type"]) == "nan":
                transfer_nodes = stops_df[
                    (stops_df["distance"] <= transfer_dist)
                    & (stops_df["location_type"].isnull())
                ]["stop_id"].values
            else:
                continue
        else:
            transfer_nodes = stops_df[stops_df["distance"] <= transfer_dist][
                "stop_id"
            ].values
        transfer_dict[origin_id] = transfer_nodes

    # THIS SECTION IDENTIFIES THE PREVIOUS DAY TO THE INPUT DAY.
    # Converts the start and end times to the number of minutes past midnight.
    orig_start_time_mins = (int(start_time[:2]) * 60) + int(start_time[3:])
    orig_end_time_mins = orig_start_time_mins + max_travel_mins

    # If the end time is after midnight, the end time is adjusted so that it starts counting at zero from midnight.
    if orig_end_time_mins >= 24 * 60:
        orig_end_time_mins = orig_end_time_mins - (24 * 60)

    # Determines the preceding day to the input day.
    if weekday == "monday":
        previous_day = "sunday"
    elif weekday == "tuesday":
        previous_day = "monday"
    elif weekday == "wednesday":
        previous_day = "tuesday"
    elif weekday == "thursday":
        previous_day = "wednesday"
    elif weekday == "friday":
        previous_day = "thursday"
    elif weekday == "saturday":
        previous_day = "friday"
    elif weekday == "sunday":
        previous_day = "saturday"

    # THIS SECTION PROCESSES THE CALENDAR DATAFRAME.
    first_date = calendar_df["start_date"].min()
    # first_date = 30000101
    # for index, row in calendar_df.iterrows():
    #     service_id = row['service_id']
    #     start_date = row['start_date']
    #     if start_date < first_date:
    #         first_date = start_date

    first_date = str(int(first_date))
    first_year = int(first_date[:4])
    first_month = int(first_date[4:6])
    first_day = int(first_date[6:])

    first_date_obj = datetime(first_year, first_month, first_day)
    start_weekday = datetime.weekday(first_date_obj)

    if start_weekday == 0:
        first_monday = first_date_obj
    elif start_weekday != 0:
        first_monday = first_date_obj + timedelta(days=7 - start_weekday)

    # Dictionary of weekdays and the corresponding first dates in the GTFS dataset that.
    date_dict = {}

    monday = int(first_monday.strftime("%Y%m%d"))
    date_dict["monday"] = monday
    tuesday = int((first_monday + timedelta(days=1)).strftime("%Y%m%d"))
    date_dict["tuesday"] = tuesday
    wednesday = int((first_monday + timedelta(days=2)).strftime("%Y%m%d"))
    date_dict["wednesday"] = wednesday
    thursday = int((first_monday + timedelta(days=3)).strftime("%Y%m%d"))
    date_dict["thursday"] = thursday
    friday = int((first_monday + timedelta(days=4)).strftime("%Y%m%d"))
    date_dict["friday"] = friday
    saturday = int((first_monday + timedelta(days=5)).strftime("%Y%m%d"))
    date_dict["saturday"] = saturday
    sunday = int((first_monday + timedelta(days=6)).strftime("%Y%m%d"))
    date_dict["sunday"] = sunday

    service_set = set()
    calendar_dict = {}
    for index, row in calendar_df.iterrows():
        service_id = row["service_id"]
        weekdays = list(date_dict.keys())
        weekday_dict = {}
        for day in weekdays:
            weekday_dict[date_dict[day]] = "0"
        calendar_dict[service_id] = weekday_dict
        service_set.add(service_id)

    for index, row in calendar_df.iterrows():
        service_id = row["service_id"]
        start_date = row["start_date"]
        end_date = row["end_date"]
        if date_dict["monday"] >= start_date and date_dict["monday"] <= end_date:
            calendar_dict[service_id][date_dict["monday"]] = row["monday"]
        if date_dict["tuesday"] >= start_date and date_dict["tuesday"] <= end_date:
            calendar_dict[service_id][date_dict["tuesday"]] = row["tuesday"]
        if date_dict["wednesday"] >= start_date and date_dict["wednesday"] <= end_date:
            calendar_dict[service_id][date_dict["wednesday"]] = row["wednesday"]
        if date_dict["thursday"] >= start_date and date_dict["thursday"] <= end_date:
            calendar_dict[service_id][date_dict["thursday"]] = row["thursday"]
        if date_dict["friday"] >= start_date and date_dict["friday"] <= end_date:
            calendar_dict[service_id][date_dict["friday"]] = row["friday"]
        if date_dict["saturday"] >= start_date and date_dict["saturday"] <= end_date:
            calendar_dict[service_id][date_dict["saturday"]] = row["saturday"]
        if date_dict["sunday"] >= start_date and date_dict["sunday"] <= end_date:
            calendar_dict[service_id][date_dict["sunday"]] = row["sunday"]

    # THIS SECTION PROCESSES THE CALENDAR_DATES DATAFRAME.
    for index, row in calendar_dates_df.iterrows():
        service_id = row["service_id"]
        date = row["date"]
        exception_type = row["exception_type"]
        if service_id not in service_set:
            weekday_dict = {}
            for day in weekdays:
                weekday_dict[date_dict[day]] = "0"
            calendar_dict[service_id] = weekday_dict
        if date >= date_dict["monday"] and date <= date_dict["sunday"]:
            if exception_type == "1":
                calendar_dict[service_id][date] = "1"
            elif exception_type == "2":
                calendar_dict[service_id][date] = "0"

    # THIS SECTION PROCESSES THE TRIPS DATAFRAME.
    trips_dict = {}
    for index, row in trips_df.iterrows():
        trip_id = row["trip_id"]
        service_id = row["service_id"]
        trips_dict[trip_id] = {"service_id": service_id}

    # start_name = stops_dict[start_point]['stop_name']
    # start_points = stop_name_dict[start_name]

    # Identifies the start points that are within an acceptable distance of the closest stop.
    start_points = transfer_dict[start_point]

    # THIS SECTION PROCESSES THE STOP_TIMES DATAFRAME.
    # Gets the column names as a list.
    stop_times_df_columns = stop_times_df.columns.tolist()

    # Removes unnecessary data from the dataframe.
    acceptable_columns = [
        "trip_id",
        "arrival_time",
        "departure_time",
        "stop_id",
        "stop_sequence",
        "file",
    ]
    for col_name in stop_times_df_columns:
        if col_name not in acceptable_columns:
            del stop_times_df[col_name]

    # Creates a list of unique trip IDs. This will be used to create the stop_times_dict.
    trip_ids = set(stop_times_df["trip_id"].tolist())

    # Creates a new dictionary with trip IDs as the key, then a list of stop times associated with the trip as the value.
    stop_times_dict = {}
    for trip_id in trip_ids:
        stop_times_dict[trip_id] = []

    # Converts the stop_times dataframe into a list of dictionaries. It's faster to loop through.
    stop_times = stop_times_df.to_dict(orient="records")

    for stop_time in stop_times:

        # Reaplaces the old stop_ids with the new stop_ids, if they were replaced.
        if new_ids == True:
            file = stop_time["file"]
            old_id = stop_time["stop_id"]
            stop_id = stop_id_unique[file][old_id]
        else:
            stop_id = stop_time["stop_id"]

        trip_id = stop_time["trip_id"]
        arrival_time = stop_time["arrival_time"]
        departure_time = stop_time["departure_time"]
        stop_sequence = stop_time["stop_sequence"]

        # Adds the stop times to the trips-based stop time dictionary.
        stop_times_dict[trip_id].append(
            {
                "stop_id": stop_id,
                "arrival_time": arrival_time,
                "departure_time": departure_time,
                "stop_sequence": stop_sequence,
            }
        )
        # Adds the stop times to the stops dictionary.
        stops_dict[stop_id]["stop_times"].append(
            {
                "trip_id": trip_id,
                "arrival_time": arrival_time,
                "departure_time": departure_time,
                "stop_sequence": stop_sequence,
            }
        )

    # Adjusts the start_points list so that it is consistent to the output of the analysis.
    start_points_new = []
    for point in start_points:
        stop_lat = stops_dict[point]["stop_lat"]
        stop_lon = stops_dict[point]["stop_lon"]
        start_points_new.append(
            {
                "stop_id": point,
                "ttm_r": max_travel_mins,
                "stop_lat": stop_lat,
                "stop_lon": stop_lon,
            }
        )

    start_points = start_points_new

    # THE FOLLOWING SECTION IS THE MAIN ANALYSIS. EVERYTHING BEFORE WAS PREPARING THE GTFS DATA.
    reached_stops_set = set()
    ttm_r_dict = {}

    while len(start_points) > 0:

        potential_trips = []

        # The first part of this function loops through all of the stop times associated with each starting point, and determines if the trip associated with that stop_time is valid.
        for point in start_points:

            point_id = point["stop_id"]
            travel_budget = point["ttm_r"]
            used_time = max_travel_mins - travel_budget
            start_time_mins = orig_start_time_mins + used_time
            end_time_mins = orig_start_time_mins + travel_budget
            if end_time_mins >= 24 * 60:
                end_time_mins = end_time_mins - (24 * 60)

            for stop_time in stops_dict[point_id]["stop_times"]:

                depart_change = "n"

                trip_id = stop_time["trip_id"]
                service_id = trips_dict[trip_id]["service_id"]

                # Adjusts the departure time, if later than 23:59.
                departure_time = stop_time["departure_time"]

                if departure_time[1:2] == ":":
                    departure_hour = int(departure_time[:1])
                    departure_mins = int(departure_time[2:4])
                else:
                    departure_hour = int(departure_time[:2])
                    departure_mins = int(departure_time[3:5])

                if departure_hour >= 24:
                    depart_change = "y"
                    new_departure_hour = str(departure_hour - 24)
                    if len(new_departure_hour) < 2:
                        new_departure_hour = "0" + new_departure_hour
                    departure_time_mins = (
                        int(new_departure_hour) * 60
                    ) + departure_mins
                else:
                    departure_time_mins = (departure_hour * 60) + departure_mins

                # Adjusts the arrival time, if later than 23:59.
                arrival_time = stop_time["arrival_time"]

                if arrival_time[1:2] == ":":
                    arrival_hour = int(arrival_time[:1])
                    arrival_mins = int(arrival_time[2:4])
                else:
                    arrival_hour = int(arrival_time[:2])
                    arrival_mins = int(arrival_time[3:5])

                if arrival_hour >= 24:
                    new_arrival_hour = str(arrival_hour - 24)
                    if len(new_arrival_hour) < 2:
                        new_arrival_hour = "0" + new_arrival_hour
                    arrival_time_mins = (int(new_arrival_hour) * 60) + arrival_mins
                else:
                    arrival_time_mins = (arrival_hour * 60) + arrival_mins

                # Checks to see if the departure and arrival times are valid with the time constraints.
                if (
                    departure_time_mins >= start_time_mins
                    and arrival_time_mins <= end_time_mins
                ):
                    if depart_change == "n":
                        if calendar_dict[service_id][date_dict[weekday]] == "1":
                            remaining_budget = travel_budget - (
                                departure_time_mins - start_time_mins
                            )
                            potential_trips.append(
                                {
                                    "trip_id": trip_id,
                                    "remaining_budget": remaining_budget,
                                }
                            )
                    elif depart_change == "y":
                        if calendar_dict[service_id][date_dict[previous_day]] == "1":
                            if departure_time_mins - start_time_mins >= 0:
                                remaining_budget = travel_budget - (
                                    departure_time_mins - start_time_mins
                                )
                            else:
                                remaining_budget = travel_budget - (
                                    (departure_time_mins + (24 * 60)) - start_time_mins
                                )
                            potential_trips.append(
                                {
                                    "trip_id": trip_id,
                                    "remaining_budget": remaining_budget,
                                }
                            )

        # This part of the function loops through the previously identified trips, then determines if the stop_times associated with those trips are valid.
        reached_stops = {}
        for trip in potential_trips:
            trip_id = trip["trip_id"]
            remaining_budget = trip["remaining_budget"]
            for stop_time in stop_times_dict[trip_id]:

                board_time_mins = start_time_mins + (travel_budget - remaining_budget)
                if board_time_mins >= 24 * 60:
                    board_time_mins = board_time_mins - (24 * 60)

                departure_time = stop_time["departure_time"]
                departure_hour = int(departure_time[:2])
                if departure_hour >= 24:
                    new_departure_hour = str(departure_hour - 24)
                    if len(new_departure_hour) < 2:
                        new_departure_hour = "0" + new_departure_hour
                    departure_time_mins = (int(new_departure_hour) * 60) + int(
                        departure_time[3:5]
                    )
                else:
                    departure_time_mins = (departure_hour * 60) + int(
                        departure_time[3:5]
                    )

                arrival_time = stop_time["arrival_time"]
                arrival_hour = int(arrival_time[:2])
                if arrival_hour >= 24:
                    new_arrival_hour = str(arrival_hour - 24)
                    if len(new_arrival_hour) < 2:
                        new_arrival_hour = "0" + new_arrival_hour
                    arrival_time_mins = (int(new_arrival_hour) * 60) + int(
                        arrival_time[3:5]
                    )
                else:
                    arrival_time_mins = (arrival_hour * 60) + int(arrival_time[3:5])

                if (
                    departure_time_mins >= board_time_mins
                    and arrival_time_mins <= end_time_mins
                ):
                    stops_set = set(reached_stops.keys())
                    remain_travel_time = end_time_mins - arrival_time_mins
                    if stop_time["stop_id"] in stops_set:
                        if reached_stops[stop_time["stop_id"]] < remain_travel_time:
                            reached_stops[stop_time["stop_id"]] = remain_travel_time
                    else:
                        reached_stops[stop_time["stop_id"]] = remain_travel_time

                    # adds the remaining time to a list with all remaining times associated with this stop name.
                    reach_name = stops_dict[stop_time["stop_id"]]["stop_name"]
                    if reach_name not in set(ttm_r_dict.keys()):
                        ttm_r_dict[reach_name] = []
                        ttm_r_dict[reach_name].append(remain_travel_time)
                    else:
                        ttm_r_dict[reach_name].append(remain_travel_time)

        # Loops through the previously identified stop times and adds them to the list for the next loop.
        start_points = []
        reached_stops_list = list(reached_stops.keys())
        for stop in reached_stops_list:
            stop_name = stops_dict[stop]["stop_name"]
            stop_lat = stops_dict[stop]["stop_lat"]
            stop_lon = stops_dict[stop]["stop_lon"]
            remain_travel_time = reached_stops[stop]

            if stop not in reached_stops_set:
                reached_stops_set.add(stop)
                # reached_stops_dict_list.append({'stop_id':stop, 'ttm_r':remain_travel_time, 'stop_lat':stop_lat, 'stop_lon':stop_lon})
                start_points.append(
                    {
                        "stop_id": stop,
                        "ttm_r": remain_travel_time,
                        "stop_lat": stop_lat,
                        "stop_lon": stop_lon,
                    }
                )

            if transfers == True:
                transfer_stops = transfer_dict[stop]
                # transfer_stops = stop_name_dict[stop_name]
                for transfer in transfer_stops:

                    if transfer not in reached_stops_set:

                        reached_stops_set.add(transfer)
                        # reached_stops_dict_list.append({'stop_id':transfer, 'ttm_r':remain_travel_time, 'stop_lat':stops_dict[transfer]['stop_lat'], 'stop_lon':stops_dict[transfer]['stop_lon']})
                        start_points.append(
                            {
                                "stop_id": transfer,
                                "ttm_r": remain_travel_time,
                                "stop_lat": stops_dict[transfer]["stop_lat"],
                                "stop_lon": stops_dict[transfer]["stop_lon"],
                            }
                        )

                        stop_name = stops_dict[transfer]["stop_name"]
                        if stop_name not in set(ttm_r_dict.keys()):
                            ttm_r_dict[stop_name] = []
                            ttm_r_dict[stop_name].append(remain_travel_time)
                        else:
                            ttm_r_dict[stop_name].append(remain_travel_time)

    # THIS SECTION SIMPLIFIES THE OUTPUT OF THE MAIN WHILE LOOP.
    # Creates a more simplified version of the accessible stops. This has one point for each cluster of stops with the same stop name.
    simple_dict_list = []
    reached_names = set()
    for stop in reached_stops_set:
        stop_name = stops_dict[stop]["stop_name"]
        ttm_r = max(ttm_r_dict[stop_name])
        if stop_name not in reached_names:
            lat_mid = simple_stops[stop_name]["lat_mid"]
            lon_mid = simple_stops[stop_name]["lon_mid"]
            if ttm_r < max_walk_mins:
                walk_mins = ttm_r
            elif ttm_r >= max_walk_mins:
                walk_mins = max_walk_mins
            simple_dict_list.append(
                {
                    "stop_name": stop_name,
                    "walk_mins": walk_mins,
                    "stop_lat": lat_mid,
                    "stop_lon": lon_mid,
                }
            )
            reached_names.add(stop_name)

    return simple_dict_list


# ISOCHRONE DEVELOPMENT


def get_network(input_lat, input_lon, distances):
    max_distance = max(distances)

    # # Buffer settings
    # edge_buff = 50
    # node_buff = 50
    # infill = True

    # # Determines the UTM zone and crs code for the input coordinates.
    # utm_crs = {}
    # epsg_dict = {}
    # zone_numbers = list(range(1, 60))
    # zone_letters = ['N','S']
    #
    # for number in zone_numbers:
    #     epsg_end = zone_numbers.index(number) + 1
    #     for letter in zone_letters:
    #         zone = str(number) + letter
    #         if letter == 'N':
    #             epsg_number = str(32600 + epsg_end)
    #         elif letter == 'S':
    #             epsg_number = str(32700 + epsg_end)
    #         epsg_dict[zone] = 'epsg:' + epsg_number
    # number = str(math.ceil(input_lon / 6) + 30)
    #
    # if input_lat >= 0:
    #     letter = 'N'
    # elif input_lat < 0:
    #     letter = 'S'
    #
    # zone = number + letter
    # epsg = epsg_dict[zone]
    #
    # utm_crs['zone'] = zone
    # utm_crs['epsg'] = epsg

    # # Converts point latitude and longitude from decimal degrees to utm meters.
    # point_utm = utm.from_latlon(input_lat, input_lon)
    #
    # point_lat = point_utm[1]
    # point_lon = point_utm[0]

    # Downloads a network originating from the point.
    G = ox.graph_from_point(
        (input_lat, input_lon), dist=max_distance + 100, network_type="walk"
    )

    return G


def process_network(G, input_lat, input_lon):

    # Converts point latitude and longitude from decimal degrees to utm meters.
    point_utm = utm.from_latlon(input_lat, input_lon)

    point_lat = point_utm[1]
    point_lon = point_utm[0]

    # Determines the UTM zone and crs code for the input coordinates.
    utm_crs = {}
    epsg_dict = {}
    zone_numbers = list(range(1, 60))
    zone_letters = ["N", "S"]

    for number in zone_numbers:
        epsg_end = zone_numbers.index(number) + 1
        for letter in zone_letters:
            zone = str(number) + letter
            if letter == "N":
                epsg_number = str(32600 + epsg_end)
            elif letter == "S":
                epsg_number = str(32700 + epsg_end)
            epsg_dict[zone] = "epsg:" + epsg_number
    number = str(math.ceil(input_lon / 6) + 30)

    if input_lat >= 0:
        letter = "N"
    elif input_lat < 0:
        letter = "S"

    zone = number + letter
    epsg = epsg_dict[zone]

    utm_crs["zone"] = zone
    utm_crs["epsg"] = epsg

    # Projects the network into utm.
    G_projected = ox.project_graph(G, to_crs=utm_crs["epsg"])

    node_ids = set()
    G_exploded = nx.MultiGraph()
    G_exploded.graph["crs"] = G_projected.graph["crs"]

    # Adds the ID to each node.
    id_list = ast.literal_eval(str(list(G_projected.nodes())))
    for id in id_list:
        G_projected.nodes[id]["id"] = id

    # Explodes the graph and creates a new one.
    for edge in G_projected.edges():
        edge_u = edge[0]
        edge_v = edge[1]
        edge_attributes = dict(G_projected[edge_u][edge_v])
        edge_attribute_keys = set(list(edge_attributes[0].keys()))

        # Adds simple line segments to the new exploded graph.
        if "geometry" not in edge_attribute_keys:

            u_id = edge_u
            u_x = G_projected.nodes[u_id]["x"]
            u_y = G_projected.nodes[u_id]["y"]
            G_exploded.add_node(u_id)
            G_exploded.nodes[u_id]["x"] = u_x
            G_exploded.nodes[u_id]["y"] = u_y
            node_ids.add(u_id)

            v_id = edge_v
            v_x = G_projected.nodes[v_id]["x"]
            v_y = G_projected.nodes[v_id]["y"]
            G_exploded.add_node(v_id)
            G_exploded.nodes[v_id]["x"] = v_x
            G_exploded.nodes[v_id]["y"] = v_y
            node_ids.add(v_id)

            length = ox.distance.euclidean(u_y, u_x, v_y, v_x)
            G_exploded.add_edge(u_id, v_id, length=length)

        # Explodes more complicated line segments and adds them to the new exploded graph.
        else:
            node_linestring = edge_attributes[0]["geometry"]
            nodes = list(node_linestring.coords)
            u_start = G_projected.nodes[edge_u]["id"]
            for node in nodes[:-1]:
                # Creates the first line segment if it's the first node.
                if nodes.index(node) == 0:

                    u_id = u_start
                    u_x = G_projected.nodes[edge_u]["x"]
                    u_y = G_projected.nodes[edge_u]["y"]
                    G_exploded.add_node(u_id)
                    G_exploded.nodes[u_id]["x"] = u_x
                    G_exploded.nodes[u_id]["y"] = u_y
                    node_ids.add(u_id)

                    v_id = random.randint(100000, 999999)
                    v_x = nodes[nodes.index(node) + 1][0]
                    v_y = nodes[nodes.index(node) + 1][1]
                    if v_id not in node_ids:
                        G_exploded.add_node(v_id)
                        G_exploded.nodes[v_id]["x"] = v_x
                        G_exploded.nodes[v_id]["y"] = v_y
                    else:
                        while v_id in node_ids:
                            v_id = random.randint(100000, 999999)
                        G_exploded.add_node(v_id)
                        G_exploded.nodes[v_id]["x"] = v_x
                        G_exploded.nodes[v_id]["y"] = v_y
                    node_ids.add(v_id)
                    u_start = v_id

                    length = ox.distance.euclidean(u_y, u_x, v_y, v_x)
                    G_exploded.add_edge(u_id, v_id, length=length)

                # Creates the middle line segments if the node is after the first or before the second-to-last.
                elif nodes.index(node) >= 1 and nodes.index(node) < len(nodes) - 2:

                    u_id = u_start
                    u_x = node[0]
                    u_y = node[1]

                    v_id = random.randint(100000, 999999)
                    v_x = nodes[nodes.index(node) + 1][0]
                    v_y = nodes[nodes.index(node) + 1][1]
                    if v_id not in node_ids:
                        G_exploded.add_node(v_id)
                        G_exploded.nodes[v_id]["x"] = v_x
                        G_exploded.nodes[v_id]["y"] = v_y
                    else:
                        while v_id in node_ids:
                            v_id = random.randint(100000, 999999)
                        G_exploded.add_node(v_id)
                        G_exploded.nodes[v_id]["x"] = v_x
                        G_exploded.nodes[v_id]["y"] = v_y
                    node_ids.add(v_id)
                    u_start = v_id

                    length = ox.distance.euclidean(u_y, u_x, v_y, v_x)
                    G_exploded.add_edge(u_id, v_id, length=length)

                # Creates the last line segment if it's the second-to-last node.
                elif nodes.index(node) == len(nodes) - 2:

                    u_id = u_start
                    u_x = node[0]
                    u_y = node[1]

                    v_id = G_projected.nodes[edge_v]["id"]
                    v_x = G_projected.nodes[edge_v]["x"]
                    v_y = G_projected.nodes[edge_v]["y"]
                    G_exploded.add_node(v_id)
                    G_exploded.nodes[v_id]["x"] = v_x
                    G_exploded.nodes[v_id]["y"] = v_y
                    node_ids.add(v_id)

                    length = ox.distance.euclidean(u_y, u_x, v_y, v_x)
                    G_exploded.add_edge(u_id, v_id, length=length)

    # Identifies the nearest edge to the point.
    nearest_edge = ox.nearest_edges(G_exploded, point_utm[0], point_utm[1])

    # Nearest edge u and v values.
    u = nearest_edge[0]
    v = nearest_edge[1]

    # Inserts a new snap node into the exploded graph.
    line_segments = []
    u_lat = G_exploded.nodes[u]["y"]
    u_lon = G_exploded.nodes[u]["x"]
    v_lat = G_exploded.nodes[v]["y"]
    v_lon = G_exploded.nodes[v]["x"]
    line = {"nodes": [[u_lon, u_lat], [v_lon, v_lat]]}
    line_segments.append(line)

    # Identifies the intersect coordinates.
    intersect_lat = ""
    intersect_lon = ""

    min_snap_dist = math.inf
    for segment in line_segments:

        node_1 = segment["nodes"][0]
        node_1_lat = node_1[1]
        node_1_lon = node_1[0]
        node_2 = segment["nodes"][1]
        node_2_lat = node_2[1]
        node_2_lon = node_2[0]

        rise = node_2_lat - node_1_lat
        run = node_2_lon - node_1_lon

        if rise == 0 and run == 0:
            continue

        slope = rise / run
        line_angle = math.degrees(math.atan(slope))

        inverse_slope = (run / rise) * -1

        node_1_lon_diff = point_lon - node_1_lon
        node_2_lon_diff = point_lon - node_2_lon

        if inverse_slope > 0:
            if node_1_lon > node_2_lon:
                min_lat = (node_1_lon_diff * inverse_slope) + node_1_lat
                max_lat = (node_2_lon_diff * inverse_slope) + node_2_lat
            elif node_1_lon < node_2_lon:
                max_lat = (node_1_lon_diff * inverse_slope) + node_1_lat
                min_lat = (node_2_lon_diff * inverse_slope) + node_2_lat
        elif inverse_slope < 0:
            if node_1_lon > node_2_lon:
                max_lat = (node_1_lon_diff * inverse_slope) + node_1_lat
                min_lat = (node_2_lon_diff * inverse_slope) + node_2_lat
            elif node_1_lon < node_2_lon:
                min_lat = (node_1_lon_diff * inverse_slope) + node_1_lat
                max_lat = (node_2_lon_diff * inverse_slope) + node_2_lat

        if point_lat >= min_lat and point_lat <= max_lat:

            rise = node_2_lat - node_1_lat
            run = node_2_lon - node_1_lon
            slope = rise / run
            line_angle = math.degrees(math.atan(slope))

            node_1_dist = math.sqrt(
                abs(node_1_lat - point_lat) ** 2 + abs(node_1_lon - point_lon) ** 2
            )
            node_1_angle = math.degrees(
                math.atan((node_1_lat - point_lat) / (node_1_lon - point_lon))
            )

            if node_1_angle > 0 and line_angle > 0:
                if line_angle > node_1_angle:
                    alpha_angle = line_angle - node_1_angle
                elif line_angle < node_1_angle:
                    alpha_angle = node_1_angle - line_angle
            elif node_1_angle > 0 and line_angle < 0:
                alpha_angle = 180 - (abs(line_angle) + abs(node_1_angle))
            elif node_1_angle < 0 and line_angle > 0:
                alpha_angle = 180 - (abs(line_angle) + abs(node_1_angle))
            elif node_1_angle < 0 and line_angle < 0:
                if abs(line_angle) > abs(node_1_angle):
                    alpha_angle = abs(line_angle) - abs(node_1_angle)
                elif abs(line_angle) < abs(node_1_angle):
                    alpha_angle = abs(node_1_angle) - abs(line_angle)

            snap_dist = math.sin(math.radians(alpha_angle)) * node_1_dist

            beta_angle = 90 - alpha_angle

            line_seg_length = abs(math.sin(math.radians(beta_angle)) * node_1_dist)

            if snap_dist < min_snap_dist:
                min_snap_dist = snap_dist

                intersect_run = (
                    math.sin(math.radians(90 - abs(line_angle))) * line_seg_length
                )
                intersect_rise = (
                    math.sin(math.radians(abs(line_angle))) * line_seg_length
                )

                if slope > 0:
                    if node_1_lat > node_2_lat:
                        intersect_lat = node_1_lat - intersect_rise
                        intersect_lon = node_1_lon - intersect_run
                    elif node_1_lat < node_2_lat:
                        intersect_lat = node_1_lat + intersect_rise
                        intersect_lon = node_1_lon + intersect_run
                elif slope < 0:
                    if node_1_lat > node_2_lat:
                        intersect_lat = node_1_lat - intersect_rise
                        intersect_lon = node_1_lon + intersect_run
                    elif node_1_lat < node_2_lat:
                        intersect_lat = node_1_lat + intersect_rise
                        intersect_lon = node_1_lon - intersect_run

        elif point_lat < min_lat or point_lat > max_lat:
            node_1_dist = math.sqrt(
                abs(node_1_lat - point_lat) ** 2 + abs(node_1_lon - point_lon) ** 2
            )
            node_2_dist = math.sqrt(
                abs(node_2_lat - point_lat) ** 2 + abs(node_2_lon - point_lon) ** 2
            )

            if node_1_dist < node_2_dist:
                snap_dist = node_1_dist
                snap_lat = node_1_lat
                snap_lon = node_1_lon
            elif node_1_dist > node_2_dist:
                snap_dist = node_2_dist
                snap_lat = node_2_lat
                snap_lon = node_2_lon

            if snap_dist < min_snap_dist:
                min_snap_dist = snap_dist
                intersect_lat = snap_lat
                intersect_lon = snap_lon

    # Adds the snap node to the list of nodes.
    G_exploded.add_node("snap_node")
    G_exploded.nodes["snap_node"]["y"] = intersect_lat
    G_exploded.nodes["snap_node"]["x"] = intersect_lon

    # Adds the new edges instead.
    G_exploded.add_edge(u, "snap_node")
    G_exploded.add_edge("snap_node", v)

    # Calculates the length between u and the snap_node, then adds that length to the new edge in the graph.
    y1 = G_exploded.nodes[u]["y"]
    x1 = G_exploded.nodes[u]["x"]
    y2 = G_exploded.nodes["snap_node"]["y"]
    x2 = G_exploded.nodes["snap_node"]["x"]
    length = ox.distance.euclidean(y1, x1, y2, x2)
    # G_exploded[u]['snap_node'][0]['length'] = length

    # Adds the new edges instead.
    G_exploded.add_edge(u, "snap_node", length=length)

    # Calculates the length between the snap_node and v, then adds that length to the new edge in the graph.
    y1 = G_exploded.nodes["snap_node"]["y"]
    x1 = G_exploded.nodes["snap_node"]["x"]
    y2 = G_exploded.nodes[v]["y"]
    x2 = G_exploded.nodes[v]["x"]
    length = ox.distance.euclidean(y1, x1, y2, x2)
    # G_exploded['snap_node'][v][0]['length'] = length

    # Adds the new edges instead.
    G_exploded.add_edge("snap_node", v, length=length)

    # Removes the original closest edge from the graph.
    G_exploded.remove_edge(u, v)
    # G_exploded.remove_edge(v, u)

    # Adds an ID value to all of the nodes in the exploded grah.
    node_list = ast.literal_eval(str(list(G_exploded.nodes())))
    for node in node_list:
        G_exploded.nodes[node]["id"] = node

    return G_exploded


def calculate_isochrones(input_lat, input_lon, G_exploded, attributes, distances):

    # Buffer settings
    edge_buff = 50
    node_buff = 50
    infill = True

    # Determines the UTM zone and crs code for the input coordinates.
    utm_crs = {}
    epsg_dict = {}
    zone_numbers = list(range(1, 60))
    zone_letters = ["N", "S"]

    for number in zone_numbers:
        epsg_end = zone_numbers.index(number) + 1
        for letter in zone_letters:
            zone = str(number) + letter
            if letter == "N":
                epsg_number = str(32600 + epsg_end)
            elif letter == "S":
                epsg_number = str(32700 + epsg_end)
            epsg_dict[zone] = "epsg:" + epsg_number
    number = str(math.ceil(input_lon / 6) + 30)

    if input_lat >= 0:
        letter = "N"
    elif input_lat < 0:
        letter = "S"

    zone = number + letter
    epsg = epsg_dict[zone]

    utm_crs["zone"] = zone
    utm_crs["epsg"] = epsg

    polygons = []
    # for point in points:
    for distance in sorted(distances, reverse=True):

        travel_budget = distance - edge_buff

        # input_lat = point['lat']
        # input_lon = point['lon']
        hub_id = attributes["id"]

        point_utm = utm.from_latlon(input_lat, input_lon)

        hub_lat = point_utm[1]
        hub_lon = point_utm[0]

        start_node = G_exploded.nodes["snap_node"]

        node_lat = start_node["y"]
        node_lon = start_node["x"]

        a = abs(hub_lat - node_lat)
        b = abs(hub_lon - node_lon)
        min_dist = math.sqrt(a**2 + b**2)

        remaining_budget = travel_budget - min_dist
        trunk_nodes = [{"t_node": start_node, "r_budget": remaining_budget}]
        accessed_nodes = set()

        # Creates an isochrone graph using the exploded graph.
        iso_graph = nx.MultiDiGraph()
        iso_graph.graph["crs"] = G_exploded.graph["crs"]

        end_nodes = 0
        while len(trunk_nodes) > 0:
            new_trunk_nodes = []
            for t_node in trunk_nodes:

                t_node_lat = t_node["t_node"]["y"]
                t_node_lon = t_node["t_node"]["x"]
                r_budget = t_node["r_budget"]
                branch_nodes = list(
                    nx.all_neighbors(G_exploded, t_node["t_node"]["id"])
                )

                for b_node in branch_nodes:

                    b_node_lat = G_exploded.nodes[b_node]["y"]
                    b_node_lon = G_exploded.nodes[b_node]["x"]

                    if b_node in accessed_nodes:
                        continue

                    c = math.sqrt(
                        abs(t_node_lat - b_node_lat) ** 2
                        + abs(t_node_lon - b_node_lon) ** 2
                    )

                    if r_budget - c > 0:
                        b_budget = r_budget - c
                        t_dict = {
                            "t_node": G_exploded.nodes[b_node],
                            "r_budget": b_budget,
                        }
                        new_trunk_nodes.append(t_dict)
                        accessed_nodes.add(b_node)

                        u = t_node["t_node"]["id"]
                        v = b_node

                        iso_graph.add_node(u)
                        iso_graph.nodes[u]["y"] = t_node_lat
                        iso_graph.nodes[u]["x"] = t_node_lon

                        iso_graph.add_node(v)
                        iso_graph.nodes[v]["y"] = b_node_lat
                        iso_graph.nodes[v]["x"] = b_node_lon

                        iso_graph.add_edge(u, v)
                        iso_graph.add_edge(v, u)

                    elif r_budget - c < 0:
                        remainder = r_budget - c

                        # The following section is new. 20240406

                        rise = b_node_lat - t_node_lat
                        run = b_node_lon - t_node_lon

                        if rise == 0 and run == 0:
                            continue

                        slope = rise / run

                        # if b_node_lon - t_node_lon != 0:
                        #     slope = (b_node_lat - t_node_lat) / (b_node_lon - t_node_lon)
                        # else:
                        #     slope = 0

                        # The above section is new. 20240406

                        # slope = (b_node_lat - t_node_lat) / (b_node_lon - t_node_lon)
                        line_angle = math.degrees(math.atan(slope))

                        intersect_run = (
                            math.sin(math.radians(90 - abs(line_angle))) * remainder
                        )
                        intersect_rise = (
                            math.sin(math.radians(abs(line_angle))) * remainder
                        )

                        if slope > 0:
                            if t_node_lat > b_node_lat:
                                intersect_lat = t_node_lat + intersect_rise
                                intersect_lon = t_node_lon + intersect_run
                            elif t_node_lat < b_node_lat:
                                intersect_lat = t_node_lat - intersect_rise
                                intersect_lon = t_node_lon - intersect_run
                        elif slope < 0:
                            if t_node_lat > b_node_lat:
                                intersect_lat = t_node_lat + intersect_rise
                                intersect_lon = t_node_lon - intersect_run
                            elif t_node_lat < b_node_lat:
                                intersect_lat = t_node_lat - intersect_rise
                                intersect_lon = t_node_lon + intersect_run

                        end_nodes += 1
                        node_name = "new_node_" + str(end_nodes)
                        accessed_nodes.add(node_name)
                        iso_graph.add_node(node_name)
                        iso_graph.nodes[node_name]["y"] = intersect_lat
                        iso_graph.nodes[node_name]["x"] = intersect_lon
                        iso_graph.nodes[node_name]["id"] = node_name

                        u = t_node["t_node"]["id"]
                        v = node_name

                        iso_graph.add_node(u)
                        iso_graph.nodes[u]["y"] = t_node_lat
                        iso_graph.nodes[u]["x"] = t_node_lon

                        iso_graph.add_node(v)
                        iso_graph.nodes[v]["y"] = intersect_lat
                        iso_graph.nodes[v]["x"] = intersect_lon

                        iso_graph.add_edge(u, v)
                        iso_graph.add_edge(v, u)

            trunk_nodes = new_trunk_nodes

        G_exploded_edges = list(G_exploded.edges())
        for edge in G_exploded_edges:
            u = edge[0]
            v = edge[1]
            if (
                iso_graph.has_edge(u, v) == False
                and iso_graph.has_node(u) == True
                and iso_graph.has_node(v) == True
            ):
                iso_graph.add_edge(u, v)

        node_points = [
            Point((data["x"], data["y"])) for node, data in iso_graph.nodes(data=True)
        ]
        nodes_gdf = gpd.GeoDataFrame({"id": iso_graph.nodes()}, geometry=node_points)
        nodes_gdf = nodes_gdf.set_index("id")

        edge_lines = []
        for n_fr, n_to in iso_graph.edges():
            f = nodes_gdf.loc[n_fr].geometry
            t = nodes_gdf.loc[n_to].geometry
            edge_lines.append(LineString([f, t]))

        n = nodes_gdf.buffer(node_buff).geometry
        e = gpd.GeoSeries(edge_lines).buffer(edge_buff).geometry
        all_gs = list(n) + list(e)
        new_iso = gpd.GeoSeries(all_gs).unary_union
        if infill == True:
            new_iso = Polygon(new_iso.exterior)
        # attributes = {'id':hub_id, 'walk_mins':trip_time}
        polygons.append({"polygon": new_iso, "attributes": attributes})

    # Converts the isochrone polygons from the utm crs to wgs84.
    polygons_wgs84 = []
    for isochrone in polygons:
        geometry = isochrone["polygon"]
        attributes = isochrone["attributes"]
        isochrone_wgs84 = ox.projection.project_geometry(
            geometry, crs=utm_crs["epsg"], to_crs="epsg:4326"
        )
        polygons_wgs84.append({"polygon": isochrone_wgs84[0], "attributes": attributes})

    iso_poly_json_all = {
        "type": "FeatureCollection",
        "features": [],
        "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:EPSG::4326"}},
    }

    for iso_poly in polygons_wgs84:
        geometry = iso_poly["polygon"]
        attributes = iso_poly["attributes"]
        attribute_keys = list(attributes.keys())
        iso_poly_json = gpd.GeoSeries([geometry]).to_json()
        iso_poly_dict = ast.literal_eval(iso_poly_json)
        for key in attribute_keys:
            iso_poly_dict["features"][0]["properties"][key] = attributes[key]
        iso_poly_json_all["features"].append(iso_poly_dict["features"][0])

    return {"json": iso_poly_json_all, "shapes": polygons_wgs84}
