#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import numpy as np
import datetime as datetime
import os
import sys
import time
from datetime import datetime
import datetime
import matplotlib.pyplot as plt
import math


df_elec=pd.read_excel("electrification_parameters.xlsx")  
df_31=pd.read_excel("Route_wise_schedule.xlsx")
df_31["Bus_No"]=df_31["Route_number"]+"_"+df_31["Bus_No"].astype("str")

Dep=[]
Arrival=[]
for i in range(len(df_31)):
    k=str(df_31.iloc[i]["New_start_time"])
    hours,minutes,sec=map(int,k.split(':'))
    d=hours+minutes/60
    Dep.append(d)
    k=str(df_31.iloc[i]["New_end_time"])
    hours,minutes,sec=map(int,k.split(':'))
    d=hours+minutes/60
    Arrival.append(d)
df_31["Departure"]=Dep
df_31["Arrival"]=Arrival

df_31=df_31[["Depot","Bus_No","trip_number","Start_location","End_location","Departure","Arrival","Distance"]]

df_31.rename(columns={"Bus_No":"Route","trip_number":"Trip number","Start_location":"From","End_location":"To"},inplace=True)

df=df_31

gadbad = []
for r in list(df['Route'].unique()):
    temp = df[df['Route'] == r].sort_values(by = 'Trip number')
    for i in range(len(temp)-1):
        if temp.iloc[i]['Arrival'] > temp.iloc[i+1]['Departure']:
            gadbad.append(r)
            break
print(len(gadbad))
df = df[~df['Route'].isin(gadbad)]


df.sort_values(by = ['Route',"Trip number"]).reset_index(drop = True)

#Battery capacity KWh
B = df_elec.iloc[0][0]

#Reserve battery ratio = 20%
RBR = df_elec.iloc[0][1]/100

#Energy efficiency = 1.1 KWh per Km
EE = df_elec.iloc[0][2]

#Range = B(1 - RBR)/EE
R = (B*(1 - RBR))/EE  #Range in Kilometers


#KWh per Km
U = B/R

#Charging rate (KWh per Minute)
C =df_elec.iloc[0][3]

#Kilometer gain per minute of charging: (Km per Minute)
KPM = C/U


#Time required to charge the bus fully in hours
TOC = R/(KPM*60)

#Allowed waiting time including charging time in hours
W = df_elec.iloc[0][4]

#Cost per charger gun
CG = df_elec.iloc[0][5]

#Charging infrastructure fixed cost
FC = df_elec.iloc[0][6]

#Maximum charger allowed at a location
NC = df_elec.iloc[0][7]

#Charging rate of overnight chargers (KWh per Minute)
KPM_slow = df_elec.iloc[0][8]
U_slow = KPM_slow*B/R

#Allowable change in the schedule at any node
delta = df_elec.iloc[0][9]

#Charger capacity = 260 KW and At a stop Not more than 1 MW
#For depot --> 5.5 MW is allowed


Infeasible_Routes = list(df[df['Distance'] > R]['Route'].unique())
df = df[~df['Route'].isin(Infeasible_Routes)]
    
    
charger_status = {}        #Busy status of chargers during the day
Chargers = {}              #No. of chargers required at each stop

for i in list(set(df['From'].values)):
    if i not in charger_status:
        charger_status[i] = []
        Chargers[i] = 0
for i in list(set(df['To'].values)):
    if i not in charger_status:
        charger_status[i] = []
        Chargers[i] = 0
# Chargers

routes = list(df['Route'].unique())

depots = []
for depot in list(df['Depot'].unique()):
    depots.append(depot)
    Chargers[depot] = int(df_elec.iloc[0][10])
    charger_status[depot] = []
    for i in range(Chargers[depot]):
        charger_status[depot].append([True]*288)
        
        
routes_list = []
for i in routes:
    routes_list.append([float(df[df['Route'] == i]['Departure'].min()), i]) 
routes_list.sort()
    
Route_charging = pd.DataFrame(columns = ['Bus', 'Charged at', 'Charger_gun', 'Charge Start Time', 'Charging duration(Minutes)', 'Waiting'])  
    
Schedule_changes = pd.DataFrame(columns = ['Bus', 'Node', 'Arrival_time', 'Change in schedule(Mins)'])   
Charger_busy_status = {}    
Infeasible_Routes = []   
    
def to_time_units(time):
        hours = int(time)
        mins = math.ceil((time - hours)*60)
        return f"{hours}:{mins:02}"
        
def Priority(node):
        return max(len(df[df['From'] == node]), len(df[df['To'] == node]))
    
    
def find_charger(data):
        nodes = list(set(list(data['From'].unique()) + list(data['To'].unique())))
        for i in nodes:
            if(Chargers[i] != 0):
                return True
        return False
    
    
def to_decimal(time):
        lst = time.split(':')
        hour = int(lst[0])
        mins = math.floor(int(lst[1])/5)*5
        return hour + (mins/60)
    
def calc_avl_time2(data, tot_time_avl):
        node = data['Node']
        if Chargers[node] == 0:
            return 0
        start = math.ceil(data['Start']*12)
        end = math.ceil(data['End']*12)
        Range = data['Range_at_start']
        if node in depots:
            charging_rate = KPM_slow
            time_span = [True]*(288 - abs(end - start))
        else:
            charging_rate = KPM
            time_span = [True]*(end - start)
        
        #Calcualting available time for charging
        time_available = 0
        for charger_no in range(len(charger_status[node])):
            index = 0
            while index < len(time_span) and Range + ((tot_time_avl + 0)*charging_rate) < R:
                if start + index < 288:
                    time_stamp = start + index
                else:
                    time_stamp = start + index - 288
                if charger_status[node][charger_no][time_stamp] == True and time_span[index] == True:
                    time_available += 5
                    Range = min(Range + (5*charging_rate), R)
                    time_span[index] = False
                index += 1
        return time_available
    
def charge_existing(data_frame, min_charge, case):
        query = 'VIJAYAPURA-III Depot_30'
        flag = "None"
        max_time_availbale = -1000
        charge_index = -1
        potential_locs = []
        tot_time_avl = 0
        for i in range(data_frame.shape[0]):
            trip = data_frame.iloc[i]
            node = trip['Node']
            if node in depots:
                charging_rate = KPM_slow
            else:
                charging_rate = KPM
            
            if Chargers[node] != 0:
                ta1 = calc_avl_time2(trip, 0)
                
                if trip['charged_before'] == False and trip['Range_at_start'] + (ta1*charging_rate) >= trip['rem_dist']:
                    if trip['Route'] == query:
                        print("Time available for charging at only", node, ta1)
                    max_time_availbale = ta1
                    charge_index = i
                    flag = 'Full_trip'
                    break
                    
                else:
                    ta2 = 0
                    if trip['charged_before'] == False:
                        ta2 = calc_avl_time2(trip, tot_time_avl)
                        if trip['Route'] == query:
                            print('Time available for charging at more than one nodes.', [node, ta2])
                    potential_locs.append([i, tot_time_avl, ta2, 0])
                    tot_time_avl += ta2
                    flag = 'Partial_trip'
        
        if case == "New":
            additional_time = 0
            ta4 = 0
            for loc in potential_locs:
                ta4 += loc[2]
                if data_frame.iloc[loc[0]]['Schedule_changed'] == False:
    #                 change = min(math.ceil(((R - data_frame.iloc[loc[0]]['Range_at_start'])/charging_rate)/5)*5 - ta4, delta)
                    extra_charge = data_frame.iloc[loc[0]].copy()
                    extra_charge['Start'] = data_frame.iloc[loc[0]]['End']
                    extra_charge['End'] = extra_charge['Start'] + (delta/60)
    #                 display(extra_charge)
                    print(loc)
                    change = min(calc_avl_time2(extra_charge, loc[1] + loc[2]), delta)
                    additional_time += change
                    loc[3] = change
                if trip['Route'] == query:
                    print('Additional Time:', data_frame.iloc[loc[0]]['Node'], loc[2], loc[3])
        
        if flag == 'Full_trip':
            Charge(data_frame.iloc[charge_index], 0, 1e9)
            return (-1, flag, max_time_availbale)
        elif flag == 'Partial_trip' and tot_time_avl >= min_charge:
            temp_list = []
            ta3 = 0
            for loc in potential_locs:
                ta3 += loc[2]
                if data_frame.iloc[loc[0]]['Node'] in depots:
                    charging_rate = KPM_slow
                else:
                    charging_rate = KPM
                if loc[2] > 0:
                    temp_list.append((loc[0], loc[2]))
                    Charge(data_frame.iloc[loc[0]], loc[1], 1e9)
                if data_frame.iloc[loc[0]]['Range_at_start'] + (charging_rate*ta3) >= data_frame.iloc[loc[0]]['rem_dist']:
                    return (-1 , 'Full_trip', ta3)
                
            return (temp_list, flag, tot_time_avl)
        elif case == 'New' and flag == 'Partial_trip' and tot_time_avl + additional_time >= min_charge:
            temp_list = []
            ta5 = 0
            scedule_to_be_changed = math.ceil((min_charge - tot_time_avl)/5)*5
            if trip['Route'] == query:
                print('Total time available', tot_time_avl, 'schedule to be changed:', scedule_to_be_changed)
            for loc in potential_locs:
                if trip['Route'] == query:
                    print(data_frame.iloc[loc[0]]['Node'], loc[2], loc[3])
                if data_frame.iloc[loc[0]]['Schedule_changed'] == False:
                    if data_frame.iloc[loc[0]]['Node'] in depots:
                        charging_rate = KPM_slow
                    else:
                        charging_rate = KPM
                    
                    extra_charge = data_frame.iloc[loc[0]].copy()
                    extra_charge['Start'] = data_frame.iloc[loc[0]]['End']
                    extra_charge['End'] = extra_charge['Start'] + (delta/60)
                    extend = min(loc[3], scedule_to_be_changed, calc_avl_time2(extra_charge, loc[1] + loc[2]))
                    print("Time extended:", extend)
                    scedule_to_be_changed -= extend
                    ta5 += loc[2] + extend

                    if trip['Route'] == query:
                        print('Total charge till node:', data_frame.iloc[loc[0]]['Node'], ta5, '***')
                    temp_list.append((loc[0], loc[2], extend))
                    data_frame['Start'].iloc[loc[0]+1:] += extend/60
                    data_frame['End'].iloc[loc[0]+1:] += extend/60
                    if loc[2] > 0:
                        display(data_frame.iloc[loc[0]])
                        Charge(data_frame.iloc[loc[0]], loc[1], 1e9)
                    if extend > 0:
                        Charge(extra_charge, loc[1]+loc[2], extend)
    #                     print("***Le dekh le")
    #                     display(data_frame.iloc[loc[0]])
                        Schedule_changes.loc[len(Schedule_changes)] = [data_frame.iloc[loc[0]]['Route'], data_frame.iloc[loc[0]]['Node'], to_time_units(data_frame.iloc[loc[0]]['Start']), extend]
                    if data_frame.iloc[loc[0]]['Range_at_start'] + (charging_rate*ta5) >= data_frame.iloc[loc[0]]['rem_dist']:
                        return (temp_list , 'Full_trip', ta5)
            return (temp_list, 'Partial_with_changes', ta5)
        else:
            return (potential_locs,'NA', tot_time_avl)

        
def Charge(row, already_charged_time, max_time):
        query = 'VIJAYAPURA-III Depot_30'
        node = row['Node']
        start = math.ceil(row['Start']*12)
        end = math.floor(row['End']*12)
        if row['Route'] == query:
            print(row['Start'], row['End'], start, end)
        Range = row['Range_at_start'] + (already_charged_time*KPM)
        total_charge_time = 0
        
        if node in depots:
            charging_rate = KPM_slow
            time_span = [True]*(288 - abs(end - start))
        else:
            charging_rate = KPM
            time_span = [True]*(end-start)
        charge_time = 0
        for charger_no in range(len(charger_status[node])):
            charge_start = 100000
            index = 0
            while index < len(time_span) and Range + (0*charging_rate) < R and Range < row['rem_dist'] and total_charge_time < max_time:
                if start + index < 288:
                    time_stamp = start + index
                else:
                    time_stamp = start + index - 288
                if charger_status[node][charger_no][time_stamp] == True and time_span[index] == True:
                    charge_start = time_stamp if charge_start == 100000 else charge_start
                    charger_status[node][charger_no][time_stamp] = False
                    charge_time += 5
                    total_charge_time += 5
                    if row['Route'] == query:
                        print(time_stamp)
                    Range = min(Range + (5*charging_rate), R)
                    time_span[index] = False
                elif charge_time != 0:
                    Route_charging.loc[len(Route_charging)] = [row['Route'], node, charger_no + 1, \
                    to_time_units(charge_start/12), charge_time, math.ceil((((charge_start/12) - row['Start'])*60)/5)*5]
                    charge_time = 0
                    charge_start = 100000
                index += 1
            if charge_time != 0:
                Route_charging.loc[len(Route_charging)] = [row['Route'], node, charger_no + 1, \
                to_time_units(charge_start/12), charge_time, math.ceil((((charge_start/12) - row['Start'])*60)/5)*5]
                charge_time = 0
                charge_start = 100000
                

def reverse_the_charge(bus):
    query = 'VIJAYAPURA-III Depot_79'
    depot_charge_row = Route_charging[(Route_charging['Bus'] == bus)]
    depot_charge_row['Charge Start Time'] = depot_charge_row['Charge Start Time'].apply(to_decimal)
        
    for index in range(len(depot_charge_row)):
            
        initial = math.ceil(depot_charge_row.iloc[index]['Charge Start Time']*12)
        final = math.ceil((depot_charge_row.iloc[index]['Charge Start Time'] \
                       + (depot_charge_row.iloc[index]['Charging duration(Minutes)']/60))*12)
        if bus == query:
            print("Charge reversed",initial, final)
        for tstamp in range(initial, final+1):
            if tstamp >= 288:
                tstamp = tstamp - 288
            charger_status[depot_charge_row.iloc[index]['Charged at']][depot_charge_row.iloc[index]['Charger_gun'] - 1][tstamp] = True
    Route_charging.drop(list(depot_charge_row.index), inplace = True)
    Route_charging.reset_index(drop = True, inplace = True)

    
    
# query = 'VIJAYAPURA-III Depot_30'
query = 'Depot 3'
for element in routes_list:
        j = element[1]
        r = df[df['Route'] == j]
        r = r.sort_values(by='Departure')
        Range_at_start = 0
        if(r['Distance'].sum() < Range_at_start):
            continue
        rem_dist = r['Distance'].sum()
        
        vis_nodes = pd.DataFrame(columns = ['Route', 'Node', 'Priority', 'Range_at_start', 'rem_dist', 'Start', 'End', 'time_available', 'charged_before', 'Schedule_changed'])
        vis_nodes.loc[0] = [j, r.iloc[0]['Depot'], 0, Range_at_start, r['Distance'].sum(), r.iloc[len(r) - 1]['Arrival'], r.iloc[0]['Departure'], \
                            min(math.ceil(((R - Range_at_start)/KPM_slow)/5)*5, math.ceil(((r.iloc[0]['Departure'] - r.iloc[len(r) - 1]['Arrival'])*60)/5)*5), False, False]
        
        i = 0
        Schedule_changed_indexes = []
        while i < r.shape[0]:
            if i == 0:
                Schedule_changed = False
            if(i > 0):
                prev_trip = r.iloc[i-1]
            trip = r.iloc[i]
            if i != r.shape[0] - 1: 
                next_trip = r.iloc[i+1]
            start_node = trip["From"]
            end_node = trip["To"]
            print(start_node, Range_at_start)
            
            if Range_at_start < trip['Distance']:
                if i == 0:
                    charging_rate = KPM_slow
                else:
                    charging_rate = KPM
                time_req =  (trip['Distance'] - Range_at_start)/charging_rate
                existing = charge_existing(vis_nodes, time_req, 'Existing')
                if existing[1] == 'Full_trip':
                    if j == query:
                        print("**AA GAYA - 1**")
                    break
                elif existing[1] == 'Partial_trip':
                    if j == query:
                        print("**AA GAYA - 2**")
                    for temp in existing[0]:
                        vis_nodes['charged_before'].iloc[temp[0]] = True
                        vis_nodes['Range_at_start'].iloc[temp[0]:] += (charging_rate*temp[1])
                        vis_nodes["Range_at_start"] = np.where(vis_nodes["Range_at_start"] > R, R, vis_nodes["Range_at_start"])
                    Range_at_start = min(Range_at_start + (charging_rate*existing[2]), R) - trip['Distance']
                else:
                    if j == query:
                        print("***Condition-3***", 'Time required:', time_req)
                    temp_df = vis_nodes.sort_values(by = ['Priority', 'time_available'], ascending = [False, False])
                    temp_df = temp_df[temp_df['charged_before'] == False]
    #                 temp_df.drop_duplicates(subset="Priority", keep= 'first', inplace=True)
                    temp_df.reset_index(inplace = True)
                    new_charger_index = -1
                    vis_nodes_ind = -1
                    
                    print(j, len(temp_df), "***ThisOne")
                    for threshold in range(1, len(temp_df)+1):
                        print('threshold:', threshold)
                        new_chargers = 0
                        new_chargers_list = []
                        for index in range(len(temp_df)):
                            row = temp_df.iloc[index]
                            time_avl = row['time_available']
                            if j == query:
                                    print('Chargers available at node:', row['Node'], Chargers[row['Node']])
                            already_avl_time = calc_avl_time2(vis_nodes.iloc[int(row['index'])], 0)
                            if Chargers[row['Node']] < NC and time_avl >= time_req:
                                if j == query:
                                    print('Allocating new charger at', row['Node'])
                                new_charger_index = index
                                vis_nodes_ind = int(row['index'])
                                break

                            elif Chargers[row['Node']] < NC:
                                if j == query:
                                    print('Condition-1', row['Node'], Chargers[row['Node']])

                                if time_avl > already_avl_time:
                                    if j == query:
                                        print('Trying by giving a new charger at', row['Node'])
                                    Chargers[row['Node']] += 1
                                    charger_status[row['Node']].append([True]*288)
                                    new_chargers += 1
                                    new_chargers_list.append(index)
                                new_existing = charge_existing(vis_nodes, time_req, 'New')
                                if new_existing[1] == 'Full_trip':
                                    if new_existing[0] != -1:
                                        for temp in new_existing[0]:
                                            if temp[2] > 0:
                                                r['Departure'].iloc[temp[0]:] += temp[2]/60
                                                r['Arrival'].iloc[temp[0]:] += temp[2]/60
                                                vis_nodes['Schedule_changed'].iloc[temp[0]] = True
                                                Schedule_changed_indexes.append(temp[0])
                                            if temp[1] > 0:
                                                vis_nodes['charged_before'].iloc[temp[0]] = True
                                                
                                        Range_at_start = 0
                                        rem_dist = r['Distance'].sum()
                                        i = 0
                                        reverse_the_charge(j)
                                        for node_ind in new_chargers_list:
                                            if j == query:
                                                print('Charger removed from', temp_df.iloc[node_ind]['Node'])
                                            Chargers[temp_df.iloc[node_ind]['Node']] -= 1
                                            charger_status[temp_df.iloc[node_ind]['Node']].pop()
                                        vis_nodes.drop(list(vis_nodes.index), inplace = True)
                                        vis_nodes.reset_index(drop = True)
                                        vis_nodes.loc[0] = [j, r.iloc[0]['Depot'], 0, Range_at_start, r['Distance'].sum(), r.iloc[len(r) - 1]['Arrival'], r.iloc[0]['Departure'], \
                                                            min(math.ceil(((R - Range_at_start)/KPM_slow)/5)*5, math.ceil(((r.iloc[0]['Departure'] - r.iloc[len(r) - 1]['Arrival'])*60)/5)*5), False, False]
                                        Schedule_changed = True
                                        display(r)
                                        print("Hello world - 4")
                                        break
                                    new_charger_index = 'Done'
                                    break
                                elif new_existing[1] == 'Partial_trip':
                                    if j == query:
                                        print("Partial trip possible")
                                    for temp in new_existing[0]:
                                        vis_nodes['charged_before'].iloc[temp[0]] = True
                                        vis_nodes['Range_at_start'].iloc[temp[0]:] += (KPM*temp[1])
                                        vis_nodes["Range_at_start"] = np.where(vis_nodes["Range_at_start"] > R, R, vis_nodes["Range_at_start"])
                                    Range_at_start = min(Range_at_start + (KPM*new_existing[2]), R) - trip['Distance']
                                    new_charger_index = 'Not Done'
                                    break
                                elif new_existing[1] == 'Partial_with_changes':
                                    if j == query:
                                        print("Partial trip with Schedule changes possible")
                                    for temp in new_existing[0]:
                                        print(vis_nodes['Node'].iloc[temp[0]], vis_nodes['Start'].iloc[temp[0]], temp[2])
                                        if temp[2] > 0:
                                            r['Departure'].iloc[temp[0]:] += temp[2]/60
                                            r['Arrival'].iloc[temp[0]:] += temp[2]/60
                                            Schedule_changed_indexes.append(temp[0])
                                            print(Schedule_changed_indexes, "Dekhooo")
    #                                         vis_nodes['Schedule_changed'].iloc[temp[0]] = True
    #                                     if temp[1] > 0:
    #                                         vis_nodes['charged_before'].iloc[temp[0]] = True
    #                                     vis_nodes['Range_at_start'].iloc[temp[0]:] += (KPM*(temp[1] + temp[2]))
    #                                     vis_nodes["Range_at_start"] = np.where(vis_nodes["Range_at_start"] > R, R, vis_nodes["Range_at_start"])
    #                                 print(new_existing[2], '**Here')
                                    Range_at_start = 0
                                    rem_dist = r['Distance'].sum()
                                    i = 0
                                    display(Route_charging[Route_charging['Bus'] == query])
                                    reverse_the_charge(j)
    #                                 Schedule_changes.drop(list(Schedule_changes[Schedule_changes['Bus'] == j].index), inplace = True)
    #                                 Schedule_changes.reset_index(drop = True)
                                    for node_ind in new_chargers_list:
                                        if j == query:
                                            print('Charger removed from', temp_df.iloc[node_ind]['Node'])
                                        Chargers[temp_df.iloc[node_ind]['Node']] -= 1
                                        charger_status[temp_df.iloc[node_ind]['Node']].pop()
                                    vis_nodes.drop(list(vis_nodes.index), inplace = True)
                                    vis_nodes.reset_index(drop = True)
                                    vis_nodes.loc[0] = [j, r.iloc[0]['Depot'], 0, Range_at_start, r['Distance'].sum(), r.iloc[len(r) - 1]['Arrival'], r.iloc[0]['Departure'], \
                                                        min(math.ceil(((R - Range_at_start)/KPM_slow)/5)*5, math.ceil(((r.iloc[0]['Departure'] - r.iloc[len(r) - 1]['Arrival'])*60)/5)*5), False, False]
                                    Schedule_changed = True
                                    display(r)
                                    print("Hello world - 1")
                                    break
                                else:
                                    print("Threshold", threshold)
                                    print("new_chargers", new_chargers)
                                    if index == len(temp_df) - 1:
                                        for node_ind in new_chargers_list:
                                            if j == query:
                                                print('Charger removed from', temp_df.iloc[node_ind]['Node'])
                                            Chargers[temp_df.iloc[node_ind]['Node']] -= 1
                                            charger_status[temp_df.iloc[node_ind]['Node']].pop()
                                    elif time_avl > already_avl_time and new_chargers >= threshold:
                                        if j == query:
                                            print('Charger removed from', row['Node'])
                                        Chargers[row['Node']] -= 1
                                        charger_status[row['Node']].pop()
                                        new_chargers -= 1
                                        new_chargers_list.remove(index)
                    
                        if Schedule_changed == True:
                            print("Hello world - 2")
                            break
                                            
                        if new_charger_index != -1:
                            break

                    if(new_charger_index == 'Done'):
                        break
                    elif(new_charger_index == -1 and Schedule_changed == False):
                        if j == query:
                            print("Infeasible:", j)
                        Infeasible_Routes.append(j)
                        reverse_the_charge(j)
                        Schedule_changes.drop(list(Schedule_changes[Schedule_changes['Bus'] == j].index), inplace = True)
                        Schedule_changes.reset_index(drop = True)
                        break
                    elif new_charger_index != 'Not Done' and Schedule_changed == False:
                        charge_row = temp_df.iloc[new_charger_index]
                        if time_avl > already_avl_time:
                            charger_status[charge_row['Node']].append([True]*288)
                            Chargers[charge_row['Node']] += 1
                        start = math.ceil(charge_row['Start']*12)
                        end = math.ceil(charge_row['End']*12)
                        new_charge_time = 0
                        Range = charge_row['Range_at_start']
                        for ind in range(start, end):
                            if Range >= R or Range >= charge_row['rem_dist']:
                                break
                            Range = min(Range + (5*KPM), R)
                            if j == query:
                                print(ind)
                            charger_status[charge_row['Node']][-1][ind] = False
                            new_charge_time += 5

                        vis_nodes['Range_at_start'].iloc[vis_nodes_ind:] += (KPM*new_charge_time)
                        vis_nodes["Range_at_start"] = np.where(vis_nodes["Range_at_start"] > R, R, vis_nodes["Range_at_start"])
                        vis_nodes['charged_before'].iloc[vis_nodes_ind] = True
                        Route_charging.loc[len(Route_charging)] = [j, charge_row['Node'], len(charger_status[charge_row['Node']]), \
                        to_time_units(charge_row['Start']), new_charge_time, 0]
                        Range_at_start = min(Range_at_start + (KPM*new_charge_time), R) - trip['Distance']

                        if Range >= charge_row['rem_dist']:
                            break
                    
            else:
                Range_at_start -= trip['Distance']
            
            if Schedule_changed == True:
                print("Hello world - 3")
                continue
            
            rem_dist -= trip['Distance']
            
            if i < r.shape[0] - 1:
                vis_nodes.loc[len(vis_nodes)] = [j, end_node, Priority(end_node), Range_at_start, rem_dist, r.iloc[i]['Arrival'],\
                                             r.iloc[i+1]['Departure'], min(math.ceil(((R - Range_at_start)/KPM)/5)*5, math.ceil(((r.iloc[i+1]['Departure'] - r.iloc[i]['Arrival'])*60)/5)*5), False, False]
                if j == query:
                    print(r.iloc[i+1]['Departure'], r.iloc[i]['Arrival'])
                if (len(vis_nodes) - 1) in Schedule_changed_indexes:
                    print("Ha bhai kar diya", len(vis_nodes))
                    vis_nodes.at[len(vis_nodes)-1, 'Schedule_changed'] = True
            
            if j == query:
                display(vis_nodes)
            i += 1
        
        depot_charge_row = Route_charging[(Route_charging['Bus'] == j) & (Route_charging['Charged at'] == r.iloc[0]['Depot'])]
        
        depot_charge_row['Charge Start Time'] = depot_charge_row['Charge Start Time'].apply(to_decimal)
        temp_start = depot_charge_row[depot_charge_row['Charge Start Time'] >= vis_nodes['Start'].iloc[0]]['Charge Start Time'].min()
        if j == query:
            print(j, temp_start, r.iloc[len(r) - 1]['Arrival'], vis_nodes['Start'].iloc[0])
        if temp_start < r.iloc[len(r) - 1]['Arrival'] and \
            temp_start >= vis_nodes['Start'].iloc[0]:
            print("***", j, r.iloc[0]['Depot'])
            for index in range(len(depot_charge_row)):
                initial = math.ceil(depot_charge_row.iloc[index]['Charge Start Time']*12)
                final = math.ceil((depot_charge_row.iloc[index]['Charge Start Time'] \
                           + (depot_charge_row.iloc[index]['Charging duration(Minutes)']/60))*12)
                for tstamp in range(initial, final):
                    if tstamp >= 288:
                        tstamp = tstamp - 288
                    charger_status[r.iloc[0]['Depot']][depot_charge_row.iloc[index]['Charger_gun'] - 1][tstamp] = True

            Route_charging.drop(list(depot_charge_row.index), inplace = True)
            Route_charging.reset_index(drop = True, inplace = True)
            vis_nodes.loc[0] = [j, r.iloc[0]['Depot'], 0, 0, r['Distance'].sum(), r.iloc[len(r) - 1]['Arrival'], r.iloc[0]['Departure'], \
                            min(math.ceil((R/KPM_slow)/5)*5, math.ceil(((r.iloc[0]['Departure'] - r.iloc[len(r) - 1]['Arrival'])*60)/5)*5), False, False]
            Charge(vis_nodes.iloc[0], 0, 1e9)
            
num_charger_df = pd.DataFrame(columns = ["Location", "Number of Chargers"])
for i in Chargers:
    if(i not in depots and Chargers[i] != 0):
        num_charger_df.loc[len(num_charger_df)] = [i, Chargers[i]]
        
num_charger_df.to_excel("Location Wise No of Chargers.xlsx",index=False)
Route_charging=Route_charging[Route_charging["Charging duration(Minutes)"]>=20]
Route_charging2 = Route_charging.drop('Waiting')
Route_charging2.to_excel("Depot wise bus charging schedule.xlsx",index=False)


# In[2]:


num_charger_df


# In[3]:


Route_charging


# In[ ]:




