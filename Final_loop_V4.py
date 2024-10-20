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
import json


with open('user_input1.json', 'r') as f:
    data1 = json.load(f)
user_input1 = data1.get("user_input1", "No input found")
with open('user_input2.json', 'r') as f:
    data2 = json.load(f)
user_input2 = data2.get("user_input2", "No input found")
with open('user_input3.json', 'r') as f:
    data3 = json.load(f)
user_input3 = data3.get("user_input3", "No input found")
with open('user_input4.json', 'r') as f:
    data4 = json.load(f)
user_input4 = data4.get("user_input4", "No input found")


city_headway=str(user_input1)
city_peak_headway=str(user_input2)
Break_after_each_trip=user_input3
Lunch_break=str(user_input4)

df_314=pd.DataFrame(columns=["Route_number","Direction","New_start_time","Running_time","New_end_time","Break_time","Bus_No","Start_location","End_location","trip_number","Depot","Distance"])
df_315=pd.DataFrame(columns=["trip_id","arrival_time","departure_time","stop_id","stop_sequence"])
df_316=pd.DataFrame(columns=["route_id","service_id","trip_id","trip_headsign","shape_id"])
# df_317=pd.DataFrame(columns=["Depot","Route_number","Bus_No","trip_number","Start_location","End_location","New_start_time","New_end_time","Distance"])

route_inputs_path = os.path.join(UPLOAD_FOLDER, 'Route_inputs_sheet.xlsx')
df=pd.read_excel("Route_inputs_sheet.xlsx")



# df_st=pd.read_csv("stops_V3.csv")

for sk in range(len(df)):
    
#     df.head()

    df_st=pd.read_csv("stops_V3.csv")
    first_trip_start_time=str(df.iloc[sk]["First trip time"])
    new_first_trip_time=str(df.iloc[sk]["First trip time"])


    from datetime import datetime
    i1=datetime.strptime(city_headway,'%H:%M:%S')
    city_headway_seconds = i1.second + i1.minute*60 + i1.hour*3600
#     city_headway_seconds

    UP_RT=datetime.strptime(str(df.iloc[sk]["UP_trip_time"]),'%H:%M:%S').second + datetime.strptime(str(df.iloc[sk]["UP_trip_time"]),'%H:%M:%S').minute*60 + datetime.strptime(str(df.iloc[sk]["UP_trip_time"]),'%H:%M:%S').hour*3600
#     UP_RT

    P_UP_RT=datetime.strptime(str(df.iloc[sk]["Peak_hour_UP_trip_time"]),'%H:%M:%S').second + datetime.strptime(str(df.iloc[sk]["Peak_hour_UP_trip_time"]),'%H:%M:%S').minute*60 + datetime.strptime(str(df.iloc[sk]["Peak_hour_UP_trip_time"]),'%H:%M:%S').hour*3600
#     P_UP_RT

    small_break_seconds=datetime.strptime(Break_after_each_trip,'%H:%M:%S').second + datetime.strptime(Break_after_each_trip,'%H:%M:%S').minute*60 + datetime.strptime(Break_after_each_trip,'%H:%M:%S').hour*3600
#     small_break_seconds

    lunch_break_seconds=datetime.strptime(Lunch_break,'%H:%M:%S').second + datetime.strptime(Lunch_break,'%H:%M:%S').minute*60 + datetime.strptime(Lunch_break,'%H:%M:%S').hour*3600
#     lunch_break_seconds


    # In[112]:


    # from datetime import datetime
    df_1=pd.DataFrame({"Route_number":[str(df.iloc[sk]["Route Number"])]*int((1440)/datetime.strptime(city_headway,'%H:%M:%S').minute)
                       ,"Direction":["UP"]*int(1440/datetime.strptime(city_headway,'%H:%M:%S').minute)
                       ,"Start_time":[first_trip_start_time]*int(1440/datetime.strptime(city_headway,'%H:%M:%S').minute)
                       ,"Running_time":[str(df.iloc[sk]["UP_trip_time"])]*int(1440/datetime.strptime(city_headway,'%H:%M:%S').minute)
                       ,"End_time":np.arange(int(1440/datetime.strptime(city_headway,'%H:%M:%S').minute))})


    # In[113]:


    import datetime
    a=pd.to_datetime(df_1.iloc[0]["Start_time"]).date()
    time_00=datetime.datetime(year=a.year, month=a.month, day=a.day, hour=0, minute=0, second=0)
    y=pd.Timestamp(time_00)
    time_zero=y.timestamp()
#     time_zero


    # In[114]:


    new_start_time=[]
    import datetime
    for r in range(len(df_1)):
        if r==0:
            new_start_time.append(df_1.iloc[0]["Start_time"])
            continue
        else:
            l=(pd.to_datetime(df_1.iloc[0]["Start_time"]).timestamp()+city_headway_seconds*r)
            m=pd.to_datetime(datetime.datetime.utcfromtimestamp(l).strftime('%Y-%m-%d %H:%M:%S')).time()
            new_start_time.append(m)
    df_1["New_start_time"]=new_start_time
            


    # In[115]:


    import datetime
    s=pd.to_datetime(df_1['New_start_time'].astype("str"))
    s1=[]
    for k in range(len(s)):
        s1.append(s[k].timestamp())
    df_1["New_start_timestamp"]=s1


    # In[116]:


    new_end_timestamp=[]
    for k in range(len(df_1)):
        if (str(df_1.iloc[k]["New_start_time"])>="07:00:00" and str(df_1.iloc[k]["New_start_time"])<="11:00:00") or (str(df_1.iloc[k]["New_start_time"])>="16:00:00" and str(df_1.iloc[k]["New_start_time"])<="20:00:00"):
            new_end_timestamp.append(df_1.iloc[k]["New_start_timestamp"]+P_UP_RT)
            #print(new_end_timestamp)
        else:
             new_end_timestamp.append(df_1.iloc[k]["New_start_timestamp"]+UP_RT)
    df_1["New_end_timestamp"]=new_end_timestamp


    # In[117]:


    df_1["New_running_timestamp"]=df_1["New_end_timestamp"]-df_1["New_start_timestamp"]


    # In[118]:


    new_end_time=[]
    for i in range(len(df_1)):
        t=df_1["New_end_timestamp"][i]
        #print(t)
        a=datetime.datetime.utcfromtimestamp(t).strftime('%Y-%m-%d %H:%M:%S')
        b=pd.to_datetime(a)
        new_end_time.append(b.time())
    df_1['New_end_time']=new_end_time


    # In[119]:


    new_running_time=[]
    for i in range(len(df_1)):
        t=df_1["New_running_timestamp"][i]
        #print(t)
        a=datetime.datetime.utcfromtimestamp(t).strftime('%Y-%m-%d %H:%M:%S')
        b=pd.to_datetime(a)
        new_running_time.append(b.time())
    df_1['new running time']=new_running_time


    # In[120]:


#     df_1.head()


    # ## For different headway in peak hours

    # In[121]:


    from datetime import datetime
    i1=datetime.strptime(city_peak_headway,'%H:%M:%S')
    city_peak_headway_seconds = i1.second + i1.minute*60 + i1.hour*3600
#     city_peak_headway_seconds


    # In[122]:


    from datetime import datetime
    df_11=pd.DataFrame({"Route_number":[str(df.iloc[sk]["Route Number"])]*int((1440)/datetime.strptime(city_peak_headway,'%H:%M:%S').minute)
                       ,"Direction":["UP"]*int(1440/datetime.strptime(city_peak_headway,'%H:%M:%S').minute)
                       ,"Start_time":[first_trip_start_time]*int(1440/datetime.strptime(city_peak_headway,'%H:%M:%S').minute)
                       ,"Running_time":[str(df.iloc[sk]["UP_trip_time"])]*int(1440/datetime.strptime(city_peak_headway,'%H:%M:%S').minute)
                       ,"End_time":np.arange(int(1440/datetime.strptime(city_peak_headway,'%H:%M:%S').minute))})


    # In[123]:


    import datetime
    a=pd.to_datetime(df_11.iloc[0]["Start_time"]).date()
    time_00=datetime.datetime(year=a.year, month=a.month, day=a.day, hour=0, minute=0, second=0)
    y=pd.Timestamp(time_00)
    time_zero=y.timestamp()
#     time_zero


    # In[124]:


    new_start_time=[]
    import datetime
    for r in range(len(df_11)):
        if r==0:
            new_start_time.append(df_11.iloc[0]["Start_time"])
            continue
        else:
            l=(pd.to_datetime(df_11.iloc[0]["Start_time"]).timestamp()+city_peak_headway_seconds*r)
            m=pd.to_datetime(datetime.datetime.utcfromtimestamp(l).strftime('%Y-%m-%d %H:%M:%S')).time()
            new_start_time.append(m)
    df_11["New_start_time"]=new_start_time
            


    # In[125]:


    import datetime
    s=list(pd.to_datetime(df_11['New_start_time'].astype("str")))
    s11=[]
    for k in range(len(s)):
        s11.append(s[k].timestamp())
    df_11["New_start_timestamp"]=s11


    # In[126]:


    new_end_timestamp=[]
    for k in range(len(df_11)):
        if (str(df_11.iloc[k]["New_start_time"])>="07:00:00" and str(df_11.iloc[k]["New_start_time"])<="11:00:00") or (str(df_11.iloc[k]["New_start_time"])>="16:00:00" and str(df_11.iloc[k]["New_start_time"])<="20:00:00"):
            new_end_timestamp.append(df_11.iloc[k]["New_start_timestamp"]+P_UP_RT)
            #print(new_end_timestamp)
        else:
             new_end_timestamp.append(df_11.iloc[k]["New_start_timestamp"]+UP_RT)
    df_11["New_end_timestamp"]=new_end_timestamp


    # In[127]:


    df_11["New_running_timestamp"]=df_11["New_end_timestamp"]-df_11["New_start_timestamp"]


    # In[128]:


    new_end_time=[]
    for i in range(len(df_11)):
        t=df_11["New_end_timestamp"][i]
        #print(t)
        a=datetime.datetime.utcfromtimestamp(t).strftime('%Y-%m-%d %H:%M:%S')
        b=pd.to_datetime(a)
        new_end_time.append(b.time())
    df_11['New_end_time']=new_end_time


    # In[129]:


    new_running_time=[]
    for i in range(len(df_11)):
        t=df_11["New_running_timestamp"][i]
        #print(t)
        a=datetime.datetime.utcfromtimestamp(t).strftime('%Y-%m-%d %H:%M:%S')
        b=pd.to_datetime(a)
        new_running_time.append(b.time())
    df_11['new running time']=new_running_time


    # In[130]:


    df_11["New_start_time"]=df_11["New_start_time"].astype("str")

    df_12=df_11.loc[((df_11.New_start_time >='07:00:00' )& (df_11.New_start_time<= '11:00:00'))|
            ((df_11.New_start_time >='16:00:00' )& (df_11.New_start_time<= '20:00:00'))]

#     df_12.head()


    # In[131]:


    df_1["lab"]=[i+1 for i in range(len(df_1))]
#     df_1.head()


    # In[132]:


    df_1["New_start_time"]=df_1["New_start_time"].astype("str")
    df_13=df_1.loc[((df_1.New_start_time >='07:00:00' )& (df_1.New_start_time<= '11:00:00'))|
            ((df_1.New_start_time >='16:00:00' )& (df_1.New_start_time<= '20:00:00'))]


    # In[133]:


    el_lab=list(df_13["lab"].unique())
    #el_lab


    # In[134]:


    df_14=df_1[~df_1["lab"].isin(el_lab)]
    df_14 = df_14.drop('lab', axis=1)
#     df_14.head()


    # In[135]:


    df_15=pd.concat([df_12,df_14])
#     df_15.head()


    # ## Creating DOWN direction trips

    # In[136]:


    from datetime import datetime
    df_2=pd.DataFrame({"Route_number":[str(df.iloc[sk]["Route Number"])]*int(1440/datetime.strptime(city_headway,'%H:%M:%S').minute)
                       ,"Direction":["DOWN"]*int(1440/datetime.strptime(city_headway,'%H:%M:%S').minute)
                       ,"Start_time":[first_trip_start_time]*int(1440/datetime.strptime(city_headway,'%H:%M:%S').minute)
                       ,"Running_time":[str(df.iloc[sk]["UP_trip_time"])]*int(1440/datetime.strptime(city_headway,'%H:%M:%S').minute)
                       ,"End_time":np.arange(int(1440/datetime.strptime(city_headway,'%H:%M:%S').minute))})


    # In[137]:


    from datetime import datetime
    DOWN_RT=datetime.strptime(str(df.iloc[sk]["DOWN_trip_time"]),'%H:%M:%S').second + datetime.strptime(str(df.iloc[sk]["DOWN_trip_time"]),'%H:%M:%S').minute*60 + datetime.strptime(str(df.iloc[sk]["DOWN_trip_time"]),'%H:%M:%S').hour*3600
#     DOWN_RT

    P_DOWN_RT=datetime.strptime(str(df.iloc[sk]["Peak_hour_DOWN_trip_time"]),'%H:%M:%S').second + datetime.strptime(str(df.iloc[sk]["Peak_hour_DOWN_trip_time"]),'%H:%M:%S').minute*60 + datetime.strptime(str(df.iloc[sk]["Peak_hour_DOWN_trip_time"]),'%H:%M:%S').hour*3600
#     P_DOWN_RT


    # In[138]:


    new_start_time=[]
    import datetime
    for r in range(len(df_2)):
        if r==0:
            new_start_time.append(df_2.iloc[0]["Start_time"])
            continue
        else:
            l=(pd.to_datetime(df_2.iloc[0]["Start_time"]).timestamp()+city_headway_seconds*r)
            m=pd.to_datetime(datetime.datetime.utcfromtimestamp(l).strftime('%Y-%m-%d %H:%M:%S')).time()
            new_start_time.append(m)
    df_2["New_start_time"]=new_start_time
            


    # In[139]:


    import datetime
    s=pd.to_datetime(df_2['New_start_time'].astype("str"))
    s1=[]
    for k in range(len(s)):
        s1.append(s[k].timestamp())
    df_2["New_start_timestamp"]=s1


    # In[140]:


    new_end_timestamp=[]
    for k in range(len(df_2)):
        if (str(df_2.iloc[k]["New_start_time"])>="07:00:00" and str(df_2.iloc[k]["New_start_time"])<="11:00:00") or (str(df_2.iloc[k]["New_start_time"])>="16:00:00" and str(df_2.iloc[k]["New_start_time"])<="20:00:00"):
            new_end_timestamp.append(df_2.iloc[k]["New_start_timestamp"]+P_DOWN_RT)
            #print(new_end_timestamp)
        else:
             new_end_timestamp.append(df_2.iloc[k]["New_start_timestamp"]+DOWN_RT)
    df_2["New_end_timestamp"]=new_end_timestamp


    # In[141]:


    df_2["New_running_timestamp"]=df_2["New_end_timestamp"]-df_2["New_start_timestamp"]


    # In[142]:


    new_end_time=[]
    for i in range(len(df_2)):
        t=df_2["New_end_timestamp"][i]
        #print(t)
        a=datetime.datetime.utcfromtimestamp(t).strftime('%Y-%m-%d %H:%M:%S')
        b=pd.to_datetime(a)
        new_end_time.append(b.time())
    df_2['New_end_time']=new_end_time


    # In[143]:


    new_running_time=[]
    for i in range(len(df_2)):
        t=df_2["New_running_timestamp"][i]
        #print(t)
        a=datetime.datetime.utcfromtimestamp(t).strftime('%Y-%m-%d %H:%M:%S')
        b=pd.to_datetime(a)
        new_running_time.append(b.time())
    df_2['new running time']=new_running_time


    # In[144]:


#     #city_peak_headway="00:03:00"
#     from datetime import datetime
#     i1=datetime.strptime(city_peak_headway,'%H:%M:%S')
#     city_peak_headway_seconds = i1.second + i1.minute*60 + i1.hour*3600
#     city_peak_headway_seconds


    # In[145]:


    from datetime import datetime
    df_21=pd.DataFrame({"Route_number":[str(df.iloc[sk]["Route Number"])]*int((1440)/datetime.strptime(city_peak_headway,'%H:%M:%S').minute)
                       ,"Direction":["DOWN"]*int(1440/datetime.strptime(city_peak_headway,'%H:%M:%S').minute)
                       ,"Start_time":[first_trip_start_time]*int(1440/datetime.strptime(city_peak_headway,'%H:%M:%S').minute)
                       ,"Running_time":[str(df.iloc[sk]["UP_trip_time"])]*int(1440/datetime.strptime(city_peak_headway,'%H:%M:%S').minute)
                       ,"End_time":np.arange(int(1440/datetime.strptime(city_peak_headway,'%H:%M:%S').minute))})


    # In[146]:


    import datetime
    a=pd.to_datetime(df_21.iloc[0]["Start_time"]).date()
    time_00=datetime.datetime(year=a.year, month=a.month, day=a.day, hour=0, minute=0, second=0)
    y=pd.Timestamp(time_00)
    time_zero=y.timestamp()
#     time_zero


    # In[147]:


    new_start_time=[]
    import datetime
    for r in range(len(df_21)):
        if r==0:
            new_start_time.append(df_21.iloc[0]["Start_time"])
            continue
        else:
            l=(pd.to_datetime(df_21.iloc[0]["Start_time"]).timestamp()+city_peak_headway_seconds*r)
            m=pd.to_datetime(datetime.datetime.utcfromtimestamp(l).strftime('%Y-%m-%d %H:%M:%S')).time()
            new_start_time.append(m)
    df_21["New_start_time"]=new_start_time
            


    # In[148]:


    import datetime
    s=list(pd.to_datetime(df_21['New_start_time'].astype("str")))
    s11=[]
    for k in range(len(s)):
        s11.append(s[k].timestamp())
    df_21["New_start_timestamp"]=s11


    # In[149]:


    new_end_timestamp=[]
    for k in range(len(df_21)):
        if (str(df_21.iloc[k]["New_start_time"])>="07:00:00" and str(df_21.iloc[k]["New_start_time"])<="11:00:00") or (str(df_21.iloc[k]["New_start_time"])>="16:00:00" and str(df_21.iloc[k]["New_start_time"])<="20:00:00"):
            new_end_timestamp.append(df_21.iloc[k]["New_start_timestamp"]+P_UP_RT)
            #print(new_end_timestamp)
        else:
             new_end_timestamp.append(df_21.iloc[k]["New_start_timestamp"]+UP_RT)
    df_21["New_end_timestamp"]=new_end_timestamp


    # In[150]:


    df_21["New_running_timestamp"]=df_21["New_end_timestamp"]-df_21["New_start_timestamp"]


    # In[151]:


    new_end_time=[]
    for i in range(len(df_21)):
        t=df_21["New_end_timestamp"][i]
        #print(t)
        a=datetime.datetime.utcfromtimestamp(t).strftime('%Y-%m-%d %H:%M:%S')
        b=pd.to_datetime(a)
        new_end_time.append(b.time())
    df_21['New_end_time']=new_end_time


    # In[152]:


    new_running_time=[]
    for i in range(len(df_21)):
        t=df_21["New_running_timestamp"][i]
        #print(t)
        a=datetime.datetime.utcfromtimestamp(t).strftime('%Y-%m-%d %H:%M:%S')
        b=pd.to_datetime(a)
        new_running_time.append(b.time())
    df_21['new running time']=new_running_time


    # In[153]:


    df_21["New_start_time"]=df_21["New_start_time"].astype("str")

    df_22=df_21.loc[((df_21.New_start_time >='07:00:00' )& (df_21.New_start_time<= '11:00:00'))|
            ((df_21.New_start_time >='16:00:00' )& (df_21.New_start_time<= '20:00:00'))]

    # df_22.head()


    # In[154]:


    df_2["lab"]=[i+1 for i in range(len(df_2))]
    # df_2.head()


    # In[155]:


    df_2["New_start_time"]=df_2["New_start_time"].astype("str")


    # In[156]:


    df_23=df_1.loc[((df_2.New_start_time >='07:00:00' )& (df_2.New_start_time<= '11:00:00'))|
            ((df_2.New_start_time >='16:00:00' )& (df_2.New_start_time<= '20:00:00'))]


    # In[157]:


    el_lab=list(df_23["lab"].unique())
    #el_lab


    # In[158]:


    df_24=df_2[~df_2["lab"].isin(el_lab)]
    df_24 = df_24.drop('lab', axis=1)
    # df_24.head()


    # In[159]:


    df_25=pd.concat([df_22,df_24])
    # df_25


    # In[160]:


    #This will be final Form 3
    df_3=pd.concat([df_25,df_15]).sort_values(["New_start_timestamp"])


    # # Assignning  buses 

    # In[161]:


    No_of_total_buses=df.iloc[sk]['# buses running on route']
#     No_of_total_buses


    # In[162]:


    total_bus_numbers=[i+1 for i in range((No_of_total_buses))]


    # In[163]:


    Consistent_headway=int((DOWN_RT+UP_RT+2*small_break_seconds)/(No_of_total_buses))
#     Consistent_headway


    # In[164]:


    df_3["label"]=np.arange(1,len(df_3)+1)


    # In[165]:


    #made change here according to 2A
    cut=list(df_3[df_3["New_start_time"].astype("str")>=new_first_trip_time]["label"])[0]


    # In[166]:


#     cut


    # In[167]:


    sort_label=[]
    Sorted_start_timestamp=[]
    Sorted_end_timestamp=[]
    for i in range(len(df_3)):
        if df_3.iloc[i]["label"]<cut:
            sort_label.append(df_3.iloc[i]["label"]+len(df_3))
            Sorted_start_timestamp.append(df_3.iloc[i]["New_start_timestamp"]+24*3600)
            Sorted_end_timestamp.append(df_3.iloc[i]["New_end_timestamp"]+24*3600)
        else:
            sort_label.append(df_3.iloc[i]["label"])
            Sorted_start_timestamp.append(df_3.iloc[i]["New_start_timestamp"])
            Sorted_end_timestamp.append(df_3.iloc[i]["New_end_timestamp"])
    df_3["Sort_label"]=sort_label
    df_3["Sorted_start_timestamp"]=Sorted_start_timestamp
    df_3["Sorted_end_timestamp"]=Sorted_end_timestamp


    # In[168]:


    df_3=df_3.sort_values(["Sort_label"])


    # In[169]:


    df_3["New_start_time"]=df_3["New_start_time"].astype("str")
    df_3["New_end_time"]=df_3["New_end_time"].astype("str")


    # ### Assigning buses 

    # In[170]:


    df_31=df_3.loc[(df_3.New_start_time>=new_first_trip_time)& (df_3.New_end_time<"23:55:00")]


    # In[171]:


#     df_31


    # In[172]:


    No_of_total_buses=list(np.arange(1,No_of_total_buses+1))


    # In[173]:


    Bus_upper_limit_sec=[(16)*3600 for i in No_of_total_buses]


    # In[174]:


    num_bus_lower=0
    num_bus_upper=num_bus_lower+len(No_of_total_buses)
#     num_bus_upper


    # In[175]:


    lunch_break_after=4*3600


    # In[176]:


    done_trips=[]
    bus_and_trips=dict()
    done_count=0
    label_id={}
    for b in No_of_total_buses:
        df4=df_31[df_31["label"].isin(done_trips)==False]
        df4=df4.sort_values(["Sorted_start_timestamp","Direction"],ascending=[True, True])
        bus_and_trips[b]=[] 
        #print(len(bus_and_trips))
        if b==1:
            ltd=[df4.iloc[0]['label'],df4.iloc[0]['Sorted_start_timestamp'],df4.iloc[0]['Sorted_end_timestamp'],df4.iloc[0]["Direction"]]
            first_bus_start_timestamp=df4.iloc[0]["Sorted_start_timestamp"]
            fisrt_bus_direction=ltd[3]
            print(fisrt_bus_direction)

        else:
    #         ltd=[df4.iloc[1]['label'],df4.iloc[1]['Sorted_start_timestamp'],df4.iloc[1]['Sorted_end_timestamp'],df4.iloc[1]["Direction"]]
    #         first_bus_start_timestamp=df4.iloc[0]["Sorted_start_timestamp"]
    #         fisrt_bus_direction=ltd[3]
    #         print(fisrt_bus_direction)
            l=first_bus_start_timestamp+(b-1)*Consistent_headway
            for k in range(len(df4)):
                if df4.iloc[k]["Sorted_start_timestamp"]>=l:
                    ltd=[df4.iloc[k]['label'],df4.iloc[k]['Sorted_start_timestamp'],df4.iloc[k]['Sorted_end_timestamp'],df4.iloc[k]["Direction"]]
                    break
        start_timestamp=ltd[1]
        max_limit=start_timestamp+Bus_upper_limit_sec[b-1]
        CRT=0
        Long_break_cum_time=0

        for i in range(len(df4)):
            if df4.iloc[i]["Sorted_start_timestamp"] >= ltd[1] and len(bus_and_trips[b])==0 and df4.iloc[i]["Direction"]==fisrt_bus_direction :#and df4.iloc[i]["Sorted_end_timestamp"]<=max_limit:
                #print(df4.iloc[i]["label"])
                #print("Check1")
                bus_and_trips[b].append(ltd)
                done_trips.append(df4.iloc[i]["label"])
                ltd=[df4.iloc[i]['label'],df4.iloc[i]['Sorted_start_timestamp'],df4.iloc[i]['Sorted_end_timestamp'],df4.iloc[i]["Direction"]]
                done_count+=1
                label_id[df4.iloc[i]["label"]]=b
                CRT=df4.iloc[i]["Sorted_end_timestamp"]-start_timestamp
                Long_break_cum_time=Long_break_cum_time+df4.iloc[i]["New_running_timestamp"]+small_break_seconds
                #print(CRT)
            elif df4.iloc[i]["Sorted_start_timestamp"]>=ltd[2]+small_break_seconds and CRT<=Bus_upper_limit_sec[b-1] and Long_break_cum_time<lunch_break_after and df4.iloc[i]["Direction"]!=ltd[3] and df4.iloc[i]["Sorted_end_timestamp"]<=max_limit :
                #print("Check2")
                bus_and_trips[b].append(ltd)
                done_trips.append(df4.iloc[i]["label"])
                ltd=[df4.iloc[i]['label'],df4.iloc[i]['Sorted_start_timestamp'],df4.iloc[i]['Sorted_end_timestamp'],df4.iloc[i]["Direction"]]
                done_count+=1
                label_id[df4.iloc[i]["label"]]=b
                CRT=df4.iloc[i]["Sorted_end_timestamp"]-start_timestamp
                Long_break_cum_time=Long_break_cum_time+df4.iloc[i]["New_running_timestamp"]+small_break_seconds
                #print(b)
                #print(Long_break_time)
                #print(CRT)
            elif df4.iloc[i]["Sorted_start_timestamp"]>=ltd[2]+lunch_break_seconds and CRT<=Bus_upper_limit_sec[b-1] and Long_break_cum_time>=lunch_break_after and df4.iloc[i]["Direction"]!=ltd[3] and df4.iloc[i]["Sorted_end_timestamp"]<=max_limit:
                #print("Check3")
                Long_break_cum_time=0
                bus_and_trips[b].append(ltd)
                done_trips.append(df4.iloc[i]["label"])
                ltd=[df4.iloc[i]['label'],df4.iloc[i]['Sorted_start_timestamp'],df4.iloc[i]['Sorted_end_timestamp'],df4.iloc[i]["Direction"]]
                done_count+=1
                label_id[df4.iloc[i]["label"]]=b
                CRT=df4.iloc[i]["Sorted_end_timestamp"]-start_timestamp
                #Long_break_cum_time=0
                Long_break_cum_time=Long_break_cum_time+df4.iloc[i]["New_running_timestamp"]+small_break_seconds
                #print(CRT)


    # In[177]:


    f1=[]
    for i in range(len(df_31)):
        try:
            k=label_id[df_31.iloc[i]["label"]]
            f1.append(k)
        except:
            f1.append("Can not be completed with given number of buses and constraints")
    df_31["Bus_No"]=f1


    # In[178]:


    df_31=df_31.sort_values(["Bus_No","Sorted_start_timestamp"])


    # In[273]:


    #df_30=df_3[df_3["Bus_No"]!="Can not be completed with given number of buses and constraints"]
    
#     df_31["Shift Type"]="Day Shift"
    df_31["Depot"]="Depot "+str(sk+1)


    # In[274]:


#     df_31.head()


    # In[181]:


#     df_31["Bus_No"].unique()


    # In[ ]:





    # ### Checking for last return trips 

    # In[182]:


    remove_labels=[]
    for i in range(len(df_31)-1):
        if df_31.iloc[i]["Bus_No"]!=df_31.iloc[i+1]["Bus_No"]:
            if df_31.iloc[i]["Direction"]!="UP":
    #             print(df_31.iloc[i]["Bus_No"])
    #             print(df_31.iloc[i]["label"])
    #             print(i)
                df_31.iat[i,15] ="Can not be completed with given number of buses and constraints"
                remove_labels.append(df_31.iloc[i]["label"])
    done_trips=list(set(done_trips)-set(remove_labels))


    # In[183]:


    df_31=df_31[df_31["Bus_No"]!="Can not be completed with given number of buses and constraints"]


    # In[184]:


    trip_number=[]
    done_buses=[]
    for i in range(len(df_31)):
        if df_31.iloc[i]["Bus_No"] not in done_buses:
            k=1
            trip_number.append(k)
            done_buses.append(df_31.iloc[i]["Bus_No"])
        elif df_31.iloc[i]["Bus_No"] in done_buses:
            k=k+1
            trip_number.append(k)
    df_31["trip_number"]=trip_number


    # In[185]:


    start=[]
    end=[]
    for i in range(len(df_31)):
        if df_31.iloc[i]["Direction"]=="DOWN":
            start.append(df.iloc[sk]["Down_start_point_name"])
            end.append(df.iloc[sk]["Down_end_point_name"])
        else:
            start.append(df.iloc[sk]["Down_end_point_name"])
            end.append(df.iloc[sk]["Down_start_point_name"])
    df_31["Start_location"]=start
    df_31["End_location"]=end


    # In[186]:


#     df_31.head()


    # In[187]:


#     df_31.to_excel("p1_Check.xlsx",index=False)


    # In[ ]:





    # In[188]:


    bt=[]
    done_ids=[]
    for i in range(len(df_31)):
        if i==0:
            bt.append(0)
            done_ids.append(df_31.iloc[i]["Bus_No"])
            continue
        elif i==len(df_31)-1:
            bt.append(0)
        elif df_31.iloc[i]["Bus_No"] in done_ids:
            k=df_31.iloc[i]["Sorted_start_timestamp"]-df_31.iloc[i-1]["Sorted_end_timestamp"]
            bt.append(k)
    #         print("success")
        elif df_31.iloc[i]["Bus_No"] not in done_ids:
            done_ids.append(df_31.iloc[i]["Bus_No"])
            bt.append(0)
            


    # In[ ]:





    # In[189]:


#     len(df_31)


    # In[190]:


    df_31["break_time"]=bt


    # In[191]:


#     df_31.head()


    # In[192]:


    df_31["Break_time"]=pd.to_datetime(df_31["break_time"],unit="s").dt.strftime("%H:%M:%S")
    df_31["Running_time"]=pd.to_datetime(df_31["New_running_timestamp"],unit="s").dt.strftime("%H:%M:%S")


    # In[193]:


#     df_31.head()


    # In[194]:


    df_31["New_start_time"]=pd.to_datetime(df_31["New_start_timestamp"],unit="s").dt.strftime("%H:%M:%S")
    df_31["New_end_time"]=pd.to_datetime(df_31["New_end_timestamp"],unit="s").dt.strftime("%H:%M:%S")
    df_31["Distance"]=df.iloc[sk]["Distance"]

    # In[195]:
#     df_32_1=df_31[["Depot","Route_number","Bus_No","trip_number","Start_location","End_location","New_start_time","New_end_time","Distance"]]

#     df_31.head()


    # In[196]:


    df_31[["Route_number","Direction","New_start_time","Running_time","New_end_time","Break_time","Bus_No","Start_location","End_location","Distance"]]


    # In[ ]:





    # In[197]:


    df_313=df_31[["Route_number","Direction","New_start_time","Running_time","New_end_time","Break_time","Bus_No","Start_location","End_location","trip_number","Depot","Distance"]]
    df_314=pd.concat([df_314,df_313])




    df_314.to_excel("Route_wise_schedule.xlsx",index=False)
    
#     df_317=pd.concat([df_317,df_32_1])
    
    df_st=df_st[df_st["route"]==df.iloc[sk]["Route Number"]]
    df_st=df_st[["stop_name","stop_id","seq"]]
    df_st.rename(columns={'stop_id': 'id'}, inplace=True)
    
    stops=dict(zip(df_st["stop_name"],df_st["id"]))
#     done_ids=[]
#     k=0
#     for i in range(len(df_31)):
#         if df_31.iloc[i]["Bus_No"] not in done_ids:
#             k=0
#             done_ids.append(df_31.iloc[i]["Bus_No"])
#             trip_id.append("WD"+str(df_31.iloc[i]["Bus_No"]))
#             arr_time.append(df_31.iloc[i]["New_start_timestamp"])
#             dep_time.append(df_31.iloc[i]["New_start_timestamp"])
#             stop_id.append(stops[df_31.iloc[i]["Start_location"]])
#             stop_seq.append(k+1)
#             k=k+1
#             continue
#         else:
#             trip_id.append("WD"+str(df_31.iloc[i]["Bus_No"]))
#             arr_time.append(df_31.iloc[i-1]["Sorted_end_timestamp"])
#             dep_time.append(df_31.iloc[i]["Sorted_start_timestamp"])
#             stop_id.append(stops[df_31.iloc[i]["Start_location"]])
#             stop_seq.append(k+1)
#             k=k+1
            
    df41_d=df_31[df_31["Direction"]=="DOWN"]
    down_start_pivot=pd.pivot_table(df41_d, values='New_start_timestamp', index=['Start_location'],
                       columns=['New_start_time'], aggfunc="sum")
    
    first_row_list=down_start_pivot.iloc[0].tolist()
    rows_df=[]
    for i in range(len(stops)-1):
        new_row=[x+(i*70) for x in first_row_list]
        rows_df.append(new_row)
    df_123=pd.DataFrame(rows_df,columns=list(down_start_pivot.columns))
    down_end_pivot=pd.pivot_table(df41_d, values='New_end_timestamp', index=['End_location'],
                       columns=['New_start_time'], aggfunc="sum")
    
    
    df_123.loc[len(df_123)]=down_end_pivot.iloc[0].tolist()
    df_123["stops"]=list(df_st["stop_name"])
    df_123.set_index('stops', inplace=True)
    
    for col in df_123.columns:
        df_123["Time_"+col]=pd.to_datetime(df_123[col],unit='s').dt.strftime("%H:%M:%S")
    
    df_123=df_123[[col for col in df_123.columns if col.startswith("Time_")]]
    trip_id=[]
    arr_time=[]
    dep_time=[]
    stop_id=[]
    stop_seq=[]
    
    t=0
    for c in df_123.columns:
        #print(c)
        t=t+1
        for i in range(len(df_123)):
            if i==0:
                trip_id.append("WD"+df.iloc[sk]["Route Number"]+str(t))
                arr_time.append(df_123.iloc[i][c])
                #print("Okay")
                dep_time.append(df_123.iloc[i][c])
                stop_seq.append(i+1)
                stop_id.append(stops[df_123.index[i]])
            else:
                trip_id.append("WD"+df.iloc[sk]["Route Number"]+str(t))
                arr_time.append(df_123.iloc[i-1][c])
                dep_time.append(df_123.iloc[i][c])
                stop_seq.append(i+1)
                stop_id.append(stops[df_123.index[i]])
                
    df_stop_times_down=pd.DataFrame([trip_id,arr_time,dep_time,stop_id,stop_seq], index=['trip_id', 'arrival_time',"departure_time","stop_id","stop_sequence"]).T

    df41_u=df_31[df_31["Direction"]=="UP"]
    
    up_start_pivot=pd.pivot_table(df41_u, values='New_start_timestamp', index=['Start_location'],
                       columns=['New_start_time'], aggfunc="sum")
    
    first_row_list=up_start_pivot.iloc[0].tolist()
    
    rows_df=[]
    for i in range(len(stops)-1):
        new_row=[x+(i*70) for x in first_row_list]
        rows_df.append(new_row)
    df_124=pd.DataFrame(rows_df,columns=list(up_start_pivot.columns))
    
    up_end_pivot=pd.pivot_table(df41_u, values='New_end_timestamp', index=['End_location'],
                       columns=['New_start_time'], aggfunc="sum")
    
    
    df_124.loc[len(df_124)]=up_end_pivot.iloc[0].tolist()
    
    df_st_rev=df_st.sort_values(by="seq",ascending=False).reset_index(drop=True)
    df_st_rev2=df_st_rev
    
    df_st_rev2["seq2"]=[x+1 for x in range(len(df_st_rev2)) ]
    df_124["stops"]=df_st_rev2["stop_name"]
    
    df_124.set_index('stops', inplace=True)
    
    for col in df_124.columns:
        df_124["Time_"+col]=pd.to_datetime(df_124[col],unit='s').dt.strftime("%H:%M:%S")
        
    df_124=df_124[[col for col in df_124.columns if col.startswith("Time_")]]
    
    trip_id=[]
    arr_time=[]
    dep_time=[]
    stop_id=[]
    stop_seq=[]
    t=0
    for c in df_124.columns:
        #print(c)
        t=t+500
#         print(t)
        for i in range(len(df_124)):
            if i==0:
                trip_id.append("WD"+df.iloc[sk]["Route Number"]+str(t))
                arr_time.append(df_124.iloc[i][c])
                #print("Okay")
                dep_time.append(df_124.iloc[i][c])
                stop_seq.append(i+1)
                stop_id.append(stops[df_124.index[i]])
            else:
                trip_id.append("WD"+df.iloc[sk]["Route Number"]+str(t))
                arr_time.append(df_124.iloc[i-1][c])
                dep_time.append(df_124.iloc[i][c])
                stop_seq.append(i+1)
                stop_id.append(stops[df_124.index[i]])
                
    df_stop_times=pd.DataFrame([trip_id,arr_time,dep_time,stop_id,stop_seq], index=['trip_id', 'arrival_time',"departure_time","stop_id","stop_sequence"]).T           
    
    df_stop_times=pd.concat([df_stop_times_down,df_stop_times])
    df_315=pd.concat([df_315,df_stop_times])
    
    df_315.to_csv("stop_times.txt",index=False)

    df42=df_stop_times["trip_id"].unique()
    df42=pd.DataFrame(list(df_stop_times["trip_id"].unique()),columns=["trip_id"])
    df42["route_id"]=df.iloc[sk]["Route Number"]
    df42["service_id"]="WD"
    df42["trip_headsign"]="Rjkt"
    df42["shape_id"]="sh37"
    df42=df42[["route_id","service_id","trip_id","trip_headsign","shape_id"]]
    
    df_316=pd.concat([df_316,df42])
    df_316.to_csv("trips.txt",index=False)
    


# In[ ]:




