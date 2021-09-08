# extract building of Rotterdam and write them into CityJSON file
# convert geojson data into cityJSON data

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


    # with open(r'./lists.txt', 'r') as f:
    #     # f = open(r'./lists.txt', 'a')
    #     line = f.readlines()
    #     # line = line.strip()
    # a = line[1].strip()
    gjson = fiona.open(r'D:\TUD\thesis\p4\car_parking\data\non_residential.geojson')  # 3d bag data
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
        oneb['attributes']['+groundHeight'] = int(f['properties']['ground-0.00'] or 0)
        oneb['attributes']['measuredHeight'] = int(f['properties']['roof-0.75'] or 0)
        oneb['attributes']['+function'] = f['properties']['function']
        oneb['attributes']['+org_car_parking_spaces'] = random.randint(0, 50)  # range from 0 to 10
        oneb['attributes']['+total_area'] = 0
        # calculation part
        # new attributes to store the results
        oneb['attributes']['+min_car_parking_spaces'] = 0
        # read attributes from other file
        # oneb['attributes']['+height_valid'] = int((j['properties']['height_valid']))
        # oneb['attributes']['+groundHeight'] = (j['properties']['ground-0.00'] or 0)
        # oneb['attributes']['measuredHeight'] = (j['properties']['roof-0.75'] or 0)



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

        room = fiona.open(r'D:\TUD\thesis\p4\car_parking\data\clip_bag_vbo_non_res.geojson')
        for r in room:
            if r['properties']['pand_identificatie'] == f['properties']['vbopand_identificatie']:
                oneb['attributes']['+total_area'] += r['properties']['oppervlakte']

        # #if oneb['attributes']['+residential_function']:
        # if oneb['attributes']['+total_area'] >= 600:
        #     room_list = []
        #     for k in room:
        #         if k['properties']['pand_identificatie'] == f['properties']['identificatie']:
        #             room_list.append(k['properties']['oppervlakte'])


        # calculate the parking spaces

        #
        if oneb['attributes']['+total_area'] > 600:
            #for office
            if oneb['attributes']['+function'] == 'Office':
                if f['properties']['zone'] == 'A':
                    oneb['attributes']['+min_car_parking_spaces'] = round(0.76 * oneb['attributes']['+total_area'] / 100)
                elif f['properties']['zone'] == 'B':
                    oneb['attributes']['+min_car_parking_spaces'] = round(1 * oneb['attributes']['+total_area'] / 100)
                else:
                    oneb['attributes']['+min_car_parking_spaces'] = round(1.2 * oneb['attributes']['+total_area'] / 100)

            # for industry
            if oneb['attributes']['+function'] == 'Industry':
                if f['properties']['zone'] == 'A':
                    oneb['attributes']['+min_car_parking_spaces'] = round(0.67 * oneb['attributes']['+total_area'] / 100)
                elif f['properties']['zone'] == 'B':
                    oneb['attributes']['+min_car_parking_spaces'] = round(1.2 * oneb['attributes']['+total_area'] / 100)
                else:
                    oneb['attributes']['+min_car_parking_spaces'] = round(2 * oneb['attributes']['+total_area'] / 100)

            # for retail
            if oneb['attributes']['+function'] == 'Retail':
                if f['properties']['zone'] == 'A':
                    oneb['attributes']['+min_car_parking_spaces'] = round(0.38 * oneb['attributes']['+total_area'] / 100)
                elif f['properties']['zone'] == 'B':
                    oneb['attributes']['+min_car_parking_spaces'] = round(2.5 * oneb['attributes']['+total_area'] / 100)
                else:
                    oneb['attributes']['+min_car_parking_spaces'] = round(2.5 * oneb['attributes']['+total_area'] / 100)

            # for Supermarket
            if oneb['attributes']['+function'] == 'Supermarket':
                if f['properties']['zone'] == 'A':
                    oneb['attributes']['+min_car_parking_spaces'] = round(0.38 * oneb['attributes']['+total_area'] / 100)
                elif f['properties']['zone'] == 'B':
                    oneb['attributes']['+min_car_parking_spaces'] = round(2.5 * oneb['attributes']['+total_area'] / 100)
                else:
                    oneb['attributes']['+min_car_parking_spaces'] = round(2.5 * oneb['attributes']['+total_area'] / 100)



        zmin.append(oneb['attributes']['+groundHeight'])
        zmax.append(oneb['attributes']['measuredHeight'])

        # -- insert the building as one city object
        cm['CityObjects'][f['properties']['ref_bag']] = oneb

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

    CityJSON(r"D:\TUD\thesis\p4\car_parking\data\car_parking_old_buildings.json")
    end = time.process_time()
    print("Done " + str(end - start))

    # to validate the structure of the CityJSON file type in the cmd: cjio buildings.json validate
    # to validate the geometry of the CityJSON file visit: http://geovalidation.bk.tudelft.nl/val3dity/
