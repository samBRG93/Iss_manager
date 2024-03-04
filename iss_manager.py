import os
from time import sleep
import matplotlib.pyplot as plt
import geopandas as gpd
import requests
from geopy.distance import geodesic
from dotenv import load_dotenv
from datetime import datetime

load_dotenv(os.path.join(os.path.dirname(__file__), '.env.devel.ini'), override=False, verbose=True)


class ISSManager:
    """
    Class to interact with the ISS API
    speed is in m/s
    period is in seconds
    """

    def __init__(self):
        try:
            self.__url = os.getenv('ISS_API_URL')
            self.__start_position = None
            self.__start_timestamp = None
        except Exception as e:
            raise "ISS_API_URL not found in environment variables" from e

    def sample_positions_calculate_speeds(self, period: int, n_periods: int) -> tuple[list[dict], float]:
        """
        Sample the position of the ISS over a period of time.
        This function will return a list of dictionaries containing the position of the ISS and the timestamp.
        This will be teh response for the question '2) Can you write an implementation (any language or pseudocode)
        of a simpler version of the program that only polls the APIs repeatedly to calculate the current speed of the
        international space station and prints it to standard output?'

        Even thought this may be simplified, it will still return the position of the ISS and the timestamp,
        as well as the speed. Furtheremore will be used to plot the path of the ISS on a map, that's why it is a public
        method.

        :param period: you can set the period of time in seconds to sample the position of the ISS
        :param n_periods: you can set the number of periods to sample the position of the ISS
        :return:  return a list of dictionaries containing the position of the ISS and the timestamp,
            as well as the speed plus the average speed
        """
        try:
            if n_periods <= 0:
                raise ValueError("n_periods must be a positive integer")
            if period <= 0:
                raise ValueError("period must be a positive integer")

            iss_tracking_data = []

            for i in range(n_periods):
                t0_data = self.get_data()
                if i == 0:
                    self.__start_position = t0_data['iss_position']
                    self.__start_timestamp = t0_data['timestamp']

                sleep(period)
                t1_data = self.get_data()
                t1_speed = self.__calculate_speed(t0_data, t1_data)

                iss_tracking_data.append({
                    'position': t1_data,
                    'timestamp': t1_data['timestamp'],
                    'speed': t1_speed
                })
                print(f"Speed of ISS: {t1_speed:.2f} m/s, at gps coords: {t1_data['iss_position']}")

            avg_speed = round(sum([x['speed'] for x in iss_tracking_data]) / n_periods, 2)
        except Exception as e:
            raise e

        print(f"Average speed of ISS: {avg_speed} m/s")
        return iss_tracking_data, avg_speed

    def plot_samples_on_globe(self, period: int, samples: int):
        """
        Execute the sample_position method and plot the path of the ISS on a map.
        :param period:
        :param samples:
        :return:
        """
        try:
            iss_infos, avg_speed = self.sample_positions_calculate_speeds(period, samples)
            coordinates = [(x['position']['iss_position']['latitude'], x['position']['iss_position']['longitude']) for x
                           in
                           iss_infos]
            timestamps = [x['timestamp'] for x in iss_infos]
            iss.__plot_iss_on_map(coordinates, timestamps, avg_speed, period)
        except Exception as e:
            raise e

    def get_data(self) -> dict:
        try:
            data = requests.get(self.__url).json()
            self.__raise_on_failure(data)

        except Exception as e:
            raise e

        return data

    @staticmethod
    def __raise_on_failure(data):
        try:
            if data['message'] != 'success':
                raise Exception('API did not return success')
        except KeyError as e:
            raise e

    @staticmethod
    def __calculate_speed(_data_t0: dict, _data_t1: dict) -> float:
        try:
            coords_t0 = (_data_t0['iss_position']['latitude'], _data_t0['iss_position']['longitude'])
            coords_t1 = (_data_t1['iss_position']['latitude'], _data_t1['iss_position']['longitude'])

            timestamp_t0 = _data_t0['timestamp']
            timestamp_t1 = _data_t1['timestamp']
            delta_time = timestamp_t1 - timestamp_t0

        except KeyError as e:
            raise e

        try:
            speed = geodesic(coords_t0, coords_t1).meters / delta_time
        except ZeroDivisionError as e:
            raise "Delta time is zero. Cannot divide by zero." from e

        return speed

    @staticmethod
    def __plot_iss_on_map(coordinates: list[tuple], timestamps: list[int], avg_speed: float, period: int):
        buffer = 25
        plt.figure(figsize=(10, 5))
        world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'), crs='EPSG:4326')
        ax = world.plot(figsize=(10, 5), color='lightgray', edgecolor='black')
        ax.set_facecolor('lightblue')

        gdf = gpd.GeoDataFrame(geometry=gpd.points_from_xy([coordinate[1] for coordinate in coordinates],
                                                           [coordinate[0] for coordinate in coordinates]),
                               crs='EPSG:4326')

        ax.set_xlim(float(min([coordinate[1] for coordinate in coordinates])) - buffer,
                    float(max([coordinate[1] for coordinate in coordinates])) + buffer)
        ax.set_ylim(float(min([coordinate[0] for coordinate in coordinates])) - buffer,
                    float(max([coordinate[0] for coordinate in coordinates])) + buffer)

        gdf.plot(ax=ax, marker='o', color='red', markersize=10)
        ax.plot(float(coordinates[-1][1]), float(coordinates[-1][0]), marker='o', color='blue', markersize=5)

        dates = [datetime.utcfromtimestamp(x).strftime('%H:%M:%S') for x in timestamps]
        plt.title(f"ISS Travel Path, time range: {dates[0]} to {dates[-1]}. Avg speed: {avg_speed} m/s. "
                  f"Period of: {period} seconds, {len(coordinates)} samples.")

        plt.show()


if __name__ == '__main__':
    iss = ISSManager()

    # this function will sample the position of the ISS over a period of time and a certain number of periods
    # It will print the speed and position of the ISS plus the average speed
    iss.sample_positions_calculate_speeds(period=1, n_periods=20)

    # this function will sample the position of the ISS over a period of time and plot the path of the ISS on a map
    # this function call the sample_positions_calculate_speeds method, you can run just this one if you want to
    # just see the map
    iss.plot_samples_on_globe(period=1, samples=20)
