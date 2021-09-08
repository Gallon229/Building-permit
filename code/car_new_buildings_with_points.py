# extract building of Rotterdam and write them into CityJSON file
# convert geojson data into cityJSON data

import pandas as pd
import geopandas as gpd
import shapely

shapely.speedups.disable()

import fiona
import shapely
import shapely.geometry as sg
import json
import pprint
import numpy as np
import scipy
from laspy.file import File
import time
from osgeo import ogr
import random

import geos


def CityJSON(output):
    # -- create a simple CityJSON file
    cm = {}
    cm["type"] = "CityJSON"
    cm["version"] = "1.0"
    cm["extensions"] = {}
    cm["extensions"]['Urban_planning_extensions'] = {}
    cm["extensions"]['Urban_planning_extensions']['url'] = "file://D:/TUD/thesis/fixed_file/test_schema.json"
    cm["extensions"]['Urban_planning_extensions']['version'] = "1.0"
    cm["CityObjects"] = {}
    cm["vertices"] = []

    merged_buffer = gpd.read_file(r"D:\TUD\thesis\p4\tranportation buffer\buffer results\merged_buffer.geojson")
    new_buildings = gpd.read_file(r"D:\TUD\thesis\p4\car_parking\data\new_buildings_with_points.geojson")
    sjoined_listings = gpd.sjoin(new_buildings, merged_buffer, op="within")

    grouped = sjoined_listings.groupby("id").agg({'discount_factor': ['min']})
    pd.DataFrame(grouped)
    discount_list = grouped.values.tolist()

    # with open(r'./lists.txt', 'r') as f:
    #     # f = open(r'./lists.txt', 'a')
    #     line = f.readlines()
    #     # line = line.strip()
    # a = line[1].strip()
    gjson = fiona.open(r'D:\TUD\thesis\p4\car_parking\data\new_buildings_with_points.geojson')  # 3d bag data
    # gjson = fiona.open(r'D:\TUD\thesis\data\for program\3d_bag_building_test.geojson')  # 3d bag data
    # hjson = fiona.open(r'D:\TUD\thesis\data\for program\building_test.geojson')  # building_test--bag datasets

    ##########################################################
    # read every feature in the geojson file, each feature contain its properties and geometry

    zmin = []
    zmax = []
    for f in gjson:
        print('have')
        s = sg.shape(f['geometry'])
        oneb = {}
        oneb['type'] = 'Building'
        oneb['toplevel'] = True
        oneb['attributes'] = {}
            # print('have')
            # s = sg.shape(f['geometry'])
            # oneb = {}
            # oneb['type'] = 'Building'
            # oneb['toplevel'] = True
            # oneb['attributes'] = {}
        oneb['attributes']['+height_valid'] = 1
        oneb['attributes']['+non_residential'] = random.randint(0, 2)
        oneb['attributes']['+groundHeight'] = 0
        storeys = random.randint(1, 20)
        oneb['attributes']['measuredHeight'] = storeys * 3.5
        # oneb['attributes']['+org_bicycle_parking_spaces'] = random.randint(0, 10)  # range from 0 to 10
        # here we don't need to multiply with a coefficient
        oneb['attributes']['+total_area'] = f['properties']['footprint_area'] * storeys * 3.5
        idd = f['properties']['id']
        discount_factor = discount_list[idd - 1][0]
        oneb['attributes']['+discount_factor'] = discount_factor
        # calculation part
        # new attributes to store the results
        oneb['attributes']['+min_bicycle_parking_spaces'] = 0
        oneb['attributes']['+min_car_parking_spaces'] = 0
        #residential buildings
        if oneb['attributes']['+non_residential'] == 0:
            oneb['attributes']['+total_area'] = oneb['attributes']['+total_area'] * 0.7
            oneb['attributes']['+function1'] = 'Residential'

            room_list = []
            room_list.append(f['properties']['point1_area'])
            room_list.append(f['properties']['point2_area'])
            N_40 = len([i for i in room_list if i < 40])
            N_40_65 = len([i for i in room_list if 40 <= i < 65])
            N_65_85 = len([i for i in room_list if 65 <= i < 85])
            N_85 = len([i for i in room_list if i >= 85])
            N_85_120 = len([i for i in room_list if 85 <= i < 120])
            N_120 = len([i for i in room_list if i >= 120])
            oneb['attributes']['+min_bicycle_parking_spaces'] = round((
                N_40 * 2 + N_40_65 * 3 + N_65_85 * 4 + N_85 * 5) * storeys)
            del room_list[:]

            if oneb['attributes']['+total_area'] > 300:
                if f['properties']['zone'] == 'A':
                    oneb['attributes']['+min_car_parking_spaces'] = round((
                N_40 * 0.1 + N_40_65 * 0.4 + N_65_85 * 0.6 + N_85_120 * 1 + N_120 * 1.2) * storeys)
                elif f['properties']['zone'] == 'B':
                    oneb['attributes']['+min_car_parking_spaces'] = round((
                N_40 * 0.1 + N_40_65 * 0.5 + N_65_85 * 0.8 + N_85_120 * 1 + N_120 * 1.2) * storeys)
                else:
                    oneb['attributes']['+min_car_parking_spaces'] = round((N_40 * 0.1 + N_40_65 * 0.6 + N_65_85 * 1.4 + N_85_120 * 1.6 + N_120 * 1.8) * storeys)

        # one function buildings
        elif oneb['attributes']['+non_residential'] == 1:
            oneb['attributes']['+total_area'] = oneb['attributes']['+total_area'] * 0.7
            function1 = ['Office', 'Industry', 'Retail', 'Supermarket', 'Gym', 'Museum', 'Cinema', 'catering I',
                        'catering III', 'catering IV', 'universities', 'Hospital']
            oneb['attributes']['+function1'] = random.choice(function1)
            if oneb['attributes']['+total_area'] > 600:
                # for office
                if oneb['attributes']['+function1'] == 'Office':
                    oneb['attributes']['+min_bicycle_parking_spaces'] = round(
                            1.7 * oneb['attributes']['+total_area'] / 100)
                    if f['properties']['zone'] == 'A':
                        oneb['attributes']['+min_car_parking_spaces'] = round(
                            0.76 * oneb['attributes']['+total_area'] / 100)
                    elif f['properties']['zone'] == 'B':
                        oneb['attributes']['+min_car_parking_spaces'] = round(
                            1 * oneb['attributes']['+total_area'] / 100)
                    else:
                        oneb['attributes']['+min_car_parking_spaces'] = round(
                            1.2 * oneb['attributes']['+total_area'] / 100)

                # for industry
                if oneb['attributes']['+function1'] == 'Industry':
                    oneb['attributes']['+min_bicycle_parking_spaces'] = round(
                        1 * oneb['attributes']['+total_area'] / 100)
                    if f['properties']['zone'] == 'A':
                        oneb['attributes']['+min_car_parking_spaces'] = round(
                            0.67 * oneb['attributes']['+total_area'] / 100)
                    elif f['properties']['zone'] == 'B':
                        oneb['attributes']['+min_car_parking_spaces'] = round(
                            1.2 * oneb['attributes']['+total_area'] / 100)
                    else:
                        oneb['attributes']['+min_car_parking_spaces'] = round(
                            2 * oneb['attributes']['+total_area'] / 100)

                # for retail
                if oneb['attributes']['+function1'] == 'Retail':
                    oneb['attributes']['+min_bicycle_parking_spaces'] = round(
                        2.7 * oneb['attributes']['+total_area'] / 100)
                    if f['properties']['zone'] == 'A':
                        oneb['attributes']['+min_car_parking_spaces'] = round(
                            0.38 * oneb['attributes']['+total_area'] / 100)
                    elif f['properties']['zone'] == 'B':
                        oneb['attributes']['+min_car_parking_spaces'] = round(
                            2.5 * oneb['attributes']['+total_area'] / 100)
                    else:
                        oneb['attributes']['+min_car_parking_spaces'] = round(
                            2.5 * oneb['attributes']['+total_area'] / 100)

                # for Supermarket
                if oneb['attributes']['+function1'] == 'Supermarket':
                    oneb['attributes']['+min_bicycle_parking_spaces'] = round(
                        2.9 * oneb['attributes']['+total_area'] / 100)
                    if f['properties']['zone'] == 'A':
                        oneb['attributes']['+min_car_parking_spaces'] = round(
                            0.38 * oneb['attributes']['+total_area'] / 100)
                    elif f['properties']['zone'] == 'B':
                        oneb['attributes']['+min_car_parking_spaces'] = round(
                            2.5 * oneb['attributes']['+total_area'] / 100)
                    else:
                        oneb['attributes']['+min_car_parking_spaces'] = round(
                            2.5 * oneb['attributes']['+total_area'] / 100)

                # for gym
                if oneb['attributes']['+function1'] == 'Gym':
                    oneb['attributes']['+min_bicycle_parking_spaces'] = round(
                        2.5 * oneb['attributes']['+total_area'] / 100)
                    if f['properties']['zone'] == 'A':
                        oneb['attributes']['+min_car_parking_spaces'] = round(
                            0.08 * oneb['attributes']['+total_area'] / 100)
                    elif f['properties']['zone'] == 'B':
                        oneb['attributes']['+min_car_parking_spaces'] = round(
                            1.7 * oneb['attributes']['+total_area'] / 100)
                    else:
                        oneb['attributes']['+min_car_parking_spaces'] = round(
                            2 * oneb['attributes']['+total_area'] / 100)

                # for Museum
                if oneb['attributes']['+function1'] == 'Museum':
                    oneb['attributes']['+min_bicycle_parking_spaces'] = round(
                        0.9 * oneb['attributes']['+total_area'] / 100)
                    if f['properties']['zone'] == 'A':
                        oneb['attributes']['+min_car_parking_spaces'] = round(
                            0.02 * oneb['attributes']['+total_area'] / 100)
                    elif f['properties']['zone'] == 'B':
                        oneb['attributes']['+min_car_parking_spaces'] = round(
                            0.4 * oneb['attributes']['+total_area'] / 100)
                    else:
                        oneb['attributes']['+min_car_parking_spaces'] = round(
                            0.7 * oneb['attributes']['+total_area'] / 100)

                # for Cinema
                if oneb['attributes']['+function1'] == 'Cinema':
                    oneb['attributes']['+min_bicycle_parking_spaces'] = round(
                        7.8 * oneb['attributes']['+total_area'] / 100)
                    if f['properties']['zone'] == 'A':
                        oneb['attributes']['+min_car_parking_spaces'] = round(
                            0.01 * oneb['attributes']['+total_area'] / 100)
                    elif f['properties']['zone'] == 'B':
                        oneb['attributes']['+min_car_parking_spaces'] = round(
                            0.1 * oneb['attributes']['+total_area'] / 100)
                    else:
                        oneb['attributes']['+min_car_parking_spaces'] = round(
                            0.2 * oneb['attributes']['+total_area'] / 100)

                # for catering I
                if oneb['attributes']['+function1'] == 'catering I':
                    oneb['attributes']['+min_bicycle_parking_spaces'] = round(
                        9 * oneb['attributes']['+total_area'] / 100)
                    if f['properties']['zone'] == 'A':
                        oneb['attributes']['+min_car_parking_spaces'] = round(
                            0.4 * oneb['attributes']['+total_area'] / 100)
                    elif f['properties']['zone'] == 'B':
                        oneb['attributes']['+min_car_parking_spaces'] = round(
                            4 * oneb['attributes']['+total_area'] / 100)
                    else:
                        oneb['attributes']['+min_car_parking_spaces'] = round(
                            6 * oneb['attributes']['+total_area'] / 100)

                # for catering III
                if oneb['attributes']['+function1'] == 'catering III':
                    oneb['attributes']['+min_bicycle_parking_spaces'] = round(
                        18 * oneb['attributes']['+total_area'] / 100)
                    if f['properties']['zone'] == 'A':
                        oneb['attributes']['+min_car_parking_spaces'] = round(
                            0.4 * oneb['attributes']['+total_area'] / 100)
                    elif f['properties']['zone'] == 'B':
                        oneb['attributes']['+min_car_parking_spaces'] = round(
                            4 * oneb['attributes']['+total_area'] / 100)
                    else:
                        oneb['attributes']['+min_car_parking_spaces'] = round(
                            6 * oneb['attributes']['+total_area'] / 100)

                # for catering IV
                if oneb['attributes']['+function1'] == 'catering IV':
                    oneb['attributes']['+min_bicycle_parking_spaces'] = round(
                        18 * oneb['attributes']['+total_area'] / 100)
                    if f['properties']['zone'] == 'A':
                        oneb['attributes']['+min_car_parking_spaces'] = round(
                            1.6 * oneb['attributes']['+total_area'] / 100)
                    elif f['properties']['zone'] == 'B':
                        oneb['attributes']['+min_car_parking_spaces'] = round(
                            8 * oneb['attributes']['+total_area'] / 100)
                    else:
                        oneb['attributes']['+min_car_parking_spaces'] = round(
                            12 * oneb['attributes']['+total_area'] / 100)

                # for universities
                if oneb['attributes']['+function1'] == 'universities':
                    oneb['attributes']['+min_bicycle_parking_spaces'] = round(
                        13 * oneb['attributes']['+total_area'] / 100)
                    if f['properties']['zone'] == 'A':
                        oneb['attributes']['+min_car_parking_spaces'] = round(
                            0.5 * oneb['attributes']['+total_area'] / 100)
                    elif f['properties']['zone'] == 'B':
                        oneb['attributes']['+min_car_parking_spaces'] = round(
                            2 * oneb['attributes']['+total_area'] / 100)
                    else:
                        oneb['attributes']['+min_car_parking_spaces'] = round(
                            3 * oneb['attributes']['+total_area'] / 100)

                # for Hospital
                if oneb['attributes']['+function1'] == 'Hospital':
                    oneb['attributes']['+min_bicycle_parking_spaces'] = round(
                        0.9 * oneb['attributes']['+total_area'] / 100)
                    if f['properties']['zone'] == 'A':
                        oneb['attributes']['+min_car_parking_spaces'] = round(
                            1.1 * oneb['attributes']['+total_area'] / 100)
                    elif f['properties']['zone'] == 'B':
                        oneb['attributes']['+min_car_parking_spaces'] = round(
                            1.3 * oneb['attributes']['+total_area'] / 100)
                    else:
                        oneb['attributes']['+min_car_parking_spaces'] = round(
                            1.5 * oneb['attributes']['+total_area'] / 100)


        else:
            # create function list and give random function attributes
            # 12 example functions here
            function = ['Office', 'Industry', 'Retail', 'Supermarket', 'Gym', 'Museum', 'Cinema', 'catering I', 'catering III', 'catering IV', 'universities', 'Hospital']
            f_list = random.sample(function, 2)
            oneb['attributes']['+function1'] = f_list[0]
            oneb['attributes']['+function2'] = f_list[1]
            # oneb['attributes']['+function1'] = random.choice(function)
            #oneb['attributes']['+org_bicycle_parking_spaces'] = random.randint(0, 10)  # range from 0 to 10
            # here we don't need to multiply with a coefficient
            area1 = oneb['attributes']['+total_area'] * 0.3
            area2 = oneb['attributes']['+total_area'] * 0.4
            usage_area = area1 + area2
            oneb['attributes']['+discount_factor'] = 0.0
            # calculation part
            # new attributes to store the results
            oneb['attributes']['+min_car_parking_spaces'] = 0
            # read attributes from other file
            # oneb['attributes']['+height_valid'] = int((j['properties']['height_valid']))
            # oneb['attributes']['+groundHeight'] = (j['properties']['ground-0.00'] or 0)
            # oneb['attributes']['measuredHeight'] = (j['properties']['roof-0.75'] or 0)

            # calculate the parking spaces
            # Exemption for building area below 600 square meters
            spaces_1 = 0
            spaces_2 = 0

            if usage_area > 600:
                # for office
                if oneb['attributes']['+function1'] == 'Office':
                    bi1 = round(1.7 * area1 / 100)
                    if f['properties']['zone'] == 'A':
                        spaces_1 = round(0.76 * area1 / 100)
                    elif f['properties']['zone'] == 'B':
                        spaces_1 = round(1 * area1 / 100)
                    else:
                        spaces_1 = round(1.2 * area1 / 100)

                # for industry
                if oneb['attributes']['+function1'] == 'Industry':
                    bi1 = round(1 * area1 / 100)
                    if f['properties']['zone'] == 'A':
                        spaces_1 = round(0.67 * area1 / 100)
                    elif f['properties']['zone'] == 'B':
                        spaces_1 = round(1.2 * area1 / 100)
                    else:
                        spaces_1 = round(2 * area1 / 100)

                # for retail
                if oneb['attributes']['+function1'] == 'Retail':
                    bi1 = round(2.7 * area1 / 100)
                    if f['properties']['zone'] == 'A':
                        spaces_1 = round(0.38 * area1 / 100)
                    elif f['properties']['zone'] == 'B':
                        spaces_1 = round(2.5 * area1 / 100)
                    else:
                        spaces_1 = round(2.5 * area1 / 100)

                # for Supermarket
                if oneb['attributes']['+function1'] == 'Supermarket':
                    bi1 = round(2.9 * area1 / 100)
                    if f['properties']['zone'] == 'A':
                        spaces_1 = round(0.38 * area1 / 100)
                    elif f['properties']['zone'] == 'B':
                        spaces_1 = round(2.5 * area1 / 100)
                    else:
                        spaces_1 = round(2.5 * area1 / 100)

                # for gym
                if oneb['attributes']['+function1'] == 'Gym':
                    bi1 = round(2.5 * area1 / 100)
                    if f['properties']['zone'] == 'A':
                        spaces_1 = round(0.08 * area1 / 100)
                    elif f['properties']['zone'] == 'B':
                        spaces_1 = round(1.7 * area1 / 100)
                    else:
                        spaces_1 = round(2 * area1 / 100)

                # for Museum
                if oneb['attributes']['+function1'] == 'Museum':
                    bi1 = round(0.9 * area1 / 100)
                    if f['properties']['zone'] == 'A':
                        spaces_1 = round(0.02 * area1 / 100)
                    elif f['properties']['zone'] == 'B':
                        spaces_1 = round(0.4 * area1 / 100)
                    else:
                        spaces_1 = round(0.7 * area1 / 100)

                # for Cinema
                if oneb['attributes']['+function1'] == 'Cinema':
                    bi1 = round(7.8 * area1 / 100)
                    if f['properties']['zone'] == 'A':
                        spaces_1 = round(0.01 * area1 / 100)
                    elif f['properties']['zone'] == 'B':
                        spaces_1 = round(0.1 * area1 / 100)
                    else:
                        spaces_1 = round(0.2 * area1 / 100)

                # for catering I
                if oneb['attributes']['+function1'] == 'catering I':
                    bi1 = round(9 * area1 / 100)
                    if f['properties']['zone'] == 'A':
                        spaces_1 = round(0.4 * area1 / 100)
                    elif f['properties']['zone'] == 'B':
                        spaces_1 = round(4 * area1 / 100)
                    else:
                        spaces_1 = round(6 * area1 / 100)

                # for catering III
                if oneb['attributes']['+function1'] == 'catering III':
                    bi1 = round(18 * area1 / 100)
                    if f['properties']['zone'] == 'A':
                        spaces_1 = round(0.4 * area1 / 100)
                    elif f['properties']['zone'] == 'B':
                        spaces_1 = round(4 * area1 / 100)
                    else:
                        spaces_1 = round(6 * area1 / 100)

                # for catering IV
                if oneb['attributes']['+function1'] == 'catering IV':
                    bi1 = round(18 * area1 / 100)
                    if f['properties']['zone'] == 'A':
                        spaces_1 = round(1.6 * area1 / 100)
                    elif f['properties']['zone'] == 'B':
                        spaces_1 = round(8 * area1 / 100)
                    else:
                        spaces_1 = round(12 * area1 / 100)

                # for universities
                if oneb['attributes']['+function1'] == 'universities':
                    bi1 = round(13 * area1 / 100)
                    if f['properties']['zone'] == 'A':
                        spaces_1 = round(0.5 * area1 / 100)
                    elif f['properties']['zone'] == 'B':
                        spaces_1 = round(2 * area1 / 100)
                    else:
                        spaces_1 = round(3 * area1 / 100)

                # for Hospital
                if oneb['attributes']['+function1'] == 'Hospital':
                    bi1 = round(0.9 * area1 / 100)
                    if f['properties']['zone'] == 'A':
                        spaces_1 = round(1.1 * area1 / 100)
                    elif f['properties']['zone'] == 'B':
                        spaces_1 = round(1.3 * area1 / 100)
                    else:
                        spaces_1 = round(1.5 * area1 / 100)

                # for function2
                if oneb['attributes']['+function2'] == 'Office':
                    bi2 = round(1.7 * area2 / 100)
                    if f['properties']['zone'] == 'A':
                        spaces_2 = round(0.76 * area2 / 100)
                    elif f['properties']['zone'] == 'B':
                        spaces_2 = round(1 * area2 / 100)
                    else:
                        spaces_2 = round(1.2 * area2 / 100)

                # for industry
                if oneb['attributes']['+function2'] == 'Industry':
                    bi2 = round(1 * area2 / 100)
                    if f['properties']['zone'] == 'A':
                        spaces_2 = round(0.67 * area2 / 100)
                    elif f['properties']['zone'] == 'B':
                        spaces_2 = round(1.2 * area2 / 100)
                    else:
                        spaces_2 = round(2 * area2 / 100)

                # for retail
                if oneb['attributes']['+function2'] == 'Retail':
                    bi2 = round(2.7 * area2 / 100)
                    if f['properties']['zone'] == 'A':
                        spaces_2 = round(0.38 * area2 / 100)
                    elif f['properties']['zone'] == 'B':
                        spaces_2 = round(2.5 * area2 / 100)
                    else:
                        spaces_2 = round(2.5 * area2 / 100)

                # for Supermarket
                if oneb['attributes']['+function2'] == 'Supermarket':
                    bi2 = round(2.9 * area2 / 100)
                    if f['properties']['zone'] == 'A':
                        spaces_2 = round(0.38 * area2 / 100)
                    elif f['properties']['zone'] == 'B':
                        spaces_2 = round(2.5 * area2 / 100)
                    else:
                        spaces_2 = round(2.5 * area2 / 100)

                # for gym
                if oneb['attributes']['+function2'] == 'Gym':
                    bi2 = round(2.5 * area2 / 100)
                    if f['properties']['zone'] == 'A':
                        spaces_2 = round(0.08 * area2 / 100)
                    elif f['properties']['zone'] == 'B':
                        spaces_2 = round(1.7 * area2 / 100)
                    else:
                        spaces_2 = round(2 * area2 / 100)

                # for Museum
                if oneb['attributes']['+function2'] == 'Museum':
                    bi2 = round(0.9 * area2 / 100)
                    if f['properties']['zone'] == 'A':
                        spaces_2 = round(0.02 * area2 / 100)
                    elif f['properties']['zone'] == 'B':
                        spaces_2 = round(0.4 * area2 / 100)
                    else:
                        spaces_2 = round(0.7 * area2 / 100)

                # for Cinema
                if oneb['attributes']['+function2'] == 'Cinema':
                    bi2 = round(7.8 * area2 / 100)
                    if f['properties']['zone'] == 'A':
                        spaces_2 = round(0.01 * area2 / 100)
                    elif f['properties']['zone'] == 'B':
                        spaces_2 = round(0.1 * area2 / 100)
                    else:
                        spaces_2 = round(0.2 * area2 / 100)

                # for catering I
                if oneb['attributes']['+function2'] == 'catering I':
                    bi2 = round(9 * area2 / 100)
                    if f['properties']['zone'] == 'A':
                        spaces_2 = round(0.4 * area2 / 100)
                    elif f['properties']['zone'] == 'B':
                        spaces_2 = round(4 * area2 / 100)
                    else:
                        spaces_2 = round(6 * area2 / 100)

                # for catering III
                if oneb['attributes']['+function2'] == 'catering III':
                    bi2 = round(18 * area2 / 100)
                    if f['properties']['zone'] == 'A':
                        spaces_2 = round(0.4 * area2 / 100)
                    elif f['properties']['zone'] == 'B':
                        spaces_2 = round(4 * area2 / 100)
                    else:
                        spaces_2 = round(6 * area2 / 100)

                # for catering IV
                if oneb['attributes']['+function2'] == 'catering IV':
                    bi2 = round(18 * area2 / 100)
                    if f['properties']['zone'] == 'A':
                        spaces_2 = round(1.6 * area2 / 100)
                    elif f['properties']['zone'] == 'B':
                        spaces_2 = round(8 * area2 / 100)
                    else:
                        spaces_2 = round(12 * area2 / 100)

                # for universities
                if oneb['attributes']['+function2'] == 'universities':
                    bi2 = round(13 * area2 / 100)
                    if f['properties']['zone'] == 'A':
                        spaces_2 = round(0.5 * area2 / 100)
                    elif f['properties']['zone'] == 'B':
                        spaces_2 = round(2 * area2 / 100)
                    else:
                        spaces_2 = round(3 * area2 / 100)

                # for Hospital
                if oneb['attributes']['+function2'] == 'Hospital':
                    bi2 = round(0.9 * area2 / 100)
                    if f['properties']['zone'] == 'A':
                        spaces_2 = round(1.1 * area2 / 100)
                    elif f['properties']['zone'] == 'B':
                        spaces_2 = round(1.3 * area2 / 100)
                    else:
                        spaces_2 = round(1.5 * area2 / 100)

            oneb['attributes']['+min_bicycle_parking_spaces'] = bi1 +bi2
            oneb['attributes']['+min_car_parking_spaces'] = spaces_1 + spaces_2

        oneb['attributes']['+min_bicycle_parking_spaces'] = round(oneb['attributes']['+min_bicycle_parking_spaces'] * discount_factor)
        oneb['attributes']['+min_car_parking_spaces'] = round(oneb['attributes']['+min_car_parking_spaces'] * discount_factor)

        oneb['geometry'] = []  # -- a cityobject can have >1
        ##########################################################
        g = {}  # -- the geometry
        g['type'] = 'MultiSurface'
        g['lod'] = 1.2
        g['boundaries'] = []
        g['semantics'] = {}

        thecoordinates = list(s.exterior.coords)  # get coordinates from polygon
        thecoordinates.pop(-1)

        b1 = []
        b2 = []
        b3 = []
        ##########################################################
        # to record
        g['semantics']['surfaces'] = [{"type": "GroundSurface"}, {"type": "WallSurface"},
                                      {"type": "RoofSurface"}]
        g['semantics']['values'] = [0, 2]
        counter_1 = len(cm['vertices'])
        ##########################################################
        for pt in thecoordinates:
            cm['vertices'].append([pt[0], pt[1], oneb['attributes']['+groundHeight']])
            b1.append(len(cm['vertices']) - 1)  # groundsurface height of 0

        for pt in thecoordinates:
            cm['vertices'].append([pt[0], pt[1], oneb['attributes']['measuredHeight']])
            b2.append(len(cm['vertices']) - 1)  # roofsurface

        counter_2 = len(cm['vertices']) - counter_1
        for i in range(int(counter_2 / 2)):
            if i == int((counter_2 / 2) - 1):
                b3.append([counter_1 + i, int(counter_1 + counter_2 / 2), int(counter_1 + (counter_2 / 2) + i)])
                b3.append([counter_1 + i, counter_1, int(counter_1 + counter_2 / 2)])
                break
            b3.append(
                [counter_1 + i, int(counter_1 + (counter_2 / 2) + 1 + i), int(counter_1 + (counter_2 / 2) + i)])
            b3.append([counter_1 + i, int(counter_1 + 1 + i), int(counter_1 + (counter_2 / 2) + 1 + i)])
        # wall surface, create triangles, connect two planes

        g['semantics']['values'].extend([1] * counter_2)
        ##########################################################
        g['boundaries'] = [[b1], [b2]]
        for i in b3:
            g['boundaries'].append([i])

        oneb['geometry'].append(g)

        # room = fiona.open(r'D:\TUD\thesis\data\for program\room_test.geojson')
        # for r in room:
        #     if r['properties']['pand_identificatie'] == f['properties']['identificatie']:
        #         oneb['attributes']['+total_area'] += r['properties']['oppervlakte']
        #
        # #if oneb['attributes']['+residential_function']:
        # if oneb['attributes']['+total_area'] >= 300:
        #     room_list = []
        #     for k in room:
        #         if k['properties']['pand_identificatie'] == f['properties']['identificatie']:
        #             room_list.append(k['properties']['oppervlakte'])]


        zmin.append(oneb['attributes']['+groundHeight'])
        zmax.append(oneb['attributes']['measuredHeight'])

        # -- insert the building as one city object
        cm['CityObjects'][f['properties']['id']] = oneb

        # cm["metadata"] = {"geographicalExtent": [
        #     min(xx), min(yy), min(zmin),
        #     max(xx), max(yy), max(zmax)],
        #     "referenceSystem": "urn:ogc:def:crs:EPSG::28992"}

    cm["metadata"] = {"geographicalExtent": [int(55500.0008102336141746), int(428647.4457731072907336), int(min(zmin)),
                                             int(101032.5938219273375580) + 1, int(447000.0042785919504240) + 1,
                                             int(max(zmax))], "referenceSystem": "urn:ogc:def:crs:EPSG::28992"}

    # -- save CityJSON to a file out.json
    json_str = json.dumps(cm, indent=2)
    fout = open(output, "w")
    fout.write(json_str)

    return


if __name__ == '__main__':
    start = time.process_time()

    CityJSON(r"D:\TUD\thesis\p4\car_parking\car_parking_new_buildings_with_points.json")
    end = time.process_time()
    print("Done " + str(end - start))

    # to validate the structure of the CityJSON file type in the cmd: cjio buildings.json validate
    # to validate the geometry of the CityJSON file visit: http://geovalidation.bk.tudelft.nl/val3dity/
