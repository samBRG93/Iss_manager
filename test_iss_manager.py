from unittest import TestCase
from iss_manager import ISSManager
import requests
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env.devel.ini'), override=False, verbose=True)


class TestIssOpenApi(TestCase):
    def test_api_url(self):
        url = os.getenv('ISS_API_URL')
        self.assertTrue(url.startswith('http://') or url.startswith('https://'))

    def test_malformed_response(self):
        response = requests.get(os.getenv('ISS_API_URL'))
        self.assertTrue(response.headers['Content-Type'] == 'application/json')

    def test_response_code(self):
        response = requests.get(os.getenv('ISS_API_URL'))
        self.assertEqual(200, response.status_code)

    def test_message(self):
        response = requests.get(os.getenv('ISS_API_URL'))
        self.assertEqual('success', response.json()['message'])

    def test_timestamp(self):
        response = requests.get(os.getenv('ISS_API_URL'))
        self.assertIsNotNone(response.json()['timestamp'])

    def test_iss_position(self):
        response = requests.get(os.getenv('ISS_API_URL'))
        self.assertIsNotNone(response.json()['iss_position'])

    def test_latitude(self):
        response = requests.get(os.getenv('ISS_API_URL'))
        self.assertIsNotNone(response.json()['iss_position']['latitude'])

    def test_longitude(self):
        response = requests.get('http://api.open-notify.org/iss-now.json')
        self.assertIsNotNone(response.json()['iss_position']['longitude'])


class TestIssManager(TestCase):
    def test_latitude_ranges(self):
        """
        Latitude: Approximately +51.6 degrees to -51.6 degrees.
        This represents the maximum inclination of the ISS's orbit from the equator.
        The ISS can come within about 51.6 degrees of the North Pole and 51.6 degrees of the South Pole during its orbit.
        """
        iss_manager = ISSManager()
        iss_tracking_data, avg_speed = iss_manager.sample_positions_calculate_speeds(period=1, n_periods=20)
        for sample in iss_tracking_data:
            self.assertTrue(-51.6 <= float(sample['position']['iss_position']['latitude']) <= 51.6)

    def test_longitude_ranges(self):
        """
        Longitude: Because the ISS orbits the Earth in a relatively low Earth orbit (LEO),
        it covers almost all longitudes over time. The ISS completes an orbit roughly every 90 minutes, so it can
        traverse the entire longitude range from approximately -180 degrees to +180 degrees over a period of time.
        :return:
        """
        iss_manager = ISSManager()
        iss_tracking_data, avg_speed = iss_manager.sample_positions_calculate_speeds(period=1, n_periods=20)
        for sample in iss_tracking_data:
            self.assertTrue(-180 <= float(sample['position']['iss_position']['longitude']) <= 180)

    def test_speed_ranges(self):
        """
        It travels at about 17,500 miles (28,000 km) per hour, which gives the crew 16 sunrises and sunsets every day.
        Which is about  7777.78 m/s or 28000 km/h. Since we calculate the avg speed in m/s we expect the avg speed to be
        around 7777.78 m/s. we accept a 10% error.
        :return:
        """

        iss_manager = ISSManager()
        iss_tracking_data, avg_speed = iss_manager.sample_positions_calculate_speeds(period=1, n_periods=20)
        self.assertAlmostEqual(avg_speed, 7777.78, delta=777.78)

    def test_speed_dont_change_to_much_between_samples(self):
        """
        The speed of the ISS should not change to much between samples
        """
        iss_manager = ISSManager()
        iss_tracking_data, avg_speed = iss_manager.sample_positions_calculate_speeds(period=1, n_periods=2)
        for i in range(1, len(iss_tracking_data)):
            delta = (abs(iss_tracking_data[i]['speed'] - iss_tracking_data[i - 1]['speed']) /
                     iss_tracking_data[i - 1]['speed'] * 100)
            self.assertTrue(delta < 10)

    def test_sample_position_periods_empty(self):
        n_periods = 0
        iss_manager = ISSManager()
        with self.assertRaises(ValueError):
            _, _ = iss_manager.sample_positions_calculate_speeds(period=1, n_periods=n_periods)

    def test_sample_position_period_empty(self):
        n_periods = 1
        iss_manager = ISSManager()
        with self.assertRaises(ValueError):
            _, _ = iss_manager.sample_positions_calculate_speeds(period=0, n_periods=n_periods)

    def test_sample_position_corner(self):
        n_periods = 1
        iss_manager = ISSManager()
        iss_tracking_data, avg_speed = iss_manager.sample_positions_calculate_speeds(period=1, n_periods=n_periods)

        self.assertEqual(len(iss_tracking_data), n_periods)

    def test_sample_length_generic(self):
        n_periods = 2
        iss_manager = ISSManager()
        iss_tracking_data, avg_speed = iss_manager.sample_positions_calculate_speeds(period=1, n_periods=n_periods)

        self.assertEqual(len(iss_tracking_data), n_periods)

    def test_speed(self):
        n_periods = 20
        iss_manager = ISSManager()

        iss_tracking_data, avg_speed = iss_manager.sample_positions_calculate_speeds(period=1, n_periods=n_periods)
        try:
            _speed_test = 0
            for sample in iss_tracking_data:
                _speed_test += sample['speed']
            _speed_test = _speed_test / len(iss_tracking_data)
            _speed_test = round(_speed_test, 2)
        except Exception as e:
            raise e

        self.assertAlmostEqual(avg_speed, _speed_test)
