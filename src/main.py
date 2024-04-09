import googlemaps
from datetime import datetime
import pandas as pd
import responses
import requests
from pytz import timezone


import re

CLEANR = re.compile('<.*?>')

# for cleaning purpose
def cleanhtml(raw_html):
    cleantext = re.sub(CLEANR, '', raw_html)
    return cleantext

# import CSV, request google distances API and export the resulting data
class GoogleDistanceCalc:
    def set_up(self):
        """
        Set up the google map API
        :return: googlemaps object with assigned client
        """
        self.client = googlemaps.Client(key='REPLACE WITH API KEY')

    def read_from_csv(self, file):
        """
        Parse the CSV file and collect addresses of departure and arrival

        :param file: file to read from
        :return: dictionary of address of departure and arrival
        """
        temp_dict = {}
        data = pd.read_csv(file)
        origins = data['Origin Address'].tolist()
        dests = data["Destination Address"].tolist()
        for i in range(len(origins)):
            if not isinstance(origins[i], str):
                splitted = origins[i].split(sep=',')
                origins[i] = (float(splitted[0]), float(splitted[1]))
        for i in range(len(dests)):
            if not isinstance(dests[i], str):
                splitted = dests[i].split(sep=',')
                dests[i] = (float(splitted[0]), float(splitted[1]))
        temp_dict["origins"] = origins
        temp_dict["destinations"] = dests
        return temp_dict

    def retrieve_matrix(self, data, file_name):
        """
        Request Google Distances API to collected relevant information such as
        traveling duration and routes then export the information to CSV file

        :param data: dictionary of addresses (generated from read_from_csv)
        :param file_name: file name to export
        :return: None
        """
        requested_time_IST = []
        durations = []
        durations_in_traffic = []
        distance = []
        routes = []
        start_address = []
        end_address = []

        # collect information from the origin address
        for i in range(len(data['origins'])):
            ind_time = datetime.now(timezone("Asia/Kolkata")).strftime('%Y-%m-%d %H:%M:%S.%f')
            requested_time_IST.append(ind_time)

            # request travelling information from origins to destinations
            directions = self.client.directions(origin=data["origins"][i], destination=data["destinations"][i], mode='driving', departure_time=datetime.now())
            directions = directions[0]
            inner_lst = []

            # parsing the html outcome to readable data
            for j in range(len(directions['legs'][0]['steps'])):
                inner_lst.append(cleanhtml(directions['legs'][0]['steps'][j]["html_instructions"]))
            routes.append(inner_lst)
            durations.append(str(round(directions['legs'][0]['duration']['value'] / 60, 3)) + " minutes")
            durations_in_traffic.append(str(round(directions['legs'][0]['duration_in_traffic']['value'] / 60, 3)) + " minutes")
            distance.append(str(round(directions['legs'][0]['distance']['value'] / 1000, 3)) + " km")
            start_address.append(directions['legs'][0]['start_address'])
            end_address.append(directions['legs'][0]['end_address'])

        # export to CSV file
        df_builder = {'requested time': requested_time_IST, 'origin': start_address, 'destination': end_address,
                      'duration': durations, 'duration_in_traffic': durations_in_traffic, 'distance': distance, 'routes': routes}
        df = pd.DataFrame(data=df_builder)
        df.to_csv(file_name)


if __name__ == "__main__":
    distance_cal = GoogleDistanceCalc()
    distance_cal.set_up()
    data = distance_cal.read_from_csv('example_data.csv')
    distance_cal.retrieve_matrix(data, 'result.csv')

