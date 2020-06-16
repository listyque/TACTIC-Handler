import unittest
from datetime import datetime

from timelapsed import Timelapsed


class TimeLapsedTest(unittest.TestCase):
	def test_will_return_VE_if_timestamp_is_out_of_range_with_safe_parameter_left_as_default_True_and_debug_parameter_left_as_default_False(self):
	  duration = Timelapsed.from_timestamp(324324234242424)
	  self.assertEqual(duration, 'V/E')

	def test_will_return_TE_if_timestamp_is_not_an_integer_with_safe_parameter_left_as_default_True_and_debug_parameter_left_as_default_False(self):
	  duration = Timelapsed.from_timestamp('sdfsdfsf4435435rete')
	  self.assertEqual(duration, 'T/E')

	def test_will_return_NA_if_timestamp_is_not_an_integer_with_safe_parameter_left_as_default_True_and_debug_parameter_is_set_to_True(self):
	  duration = Timelapsed.from_timestamp('sdfsdfsf4435435rete', debug=True)
	  self.assertEqual(duration, 'N/A')

	def test_will_return_NA_if_timestamp_is_out_of_range_with_safe_parameter_left_as_default_True_and_debug_parameter_is_set_to_True(self):
	  duration = Timelapsed.from_timestamp(324324234242424, debug=True)
	  self.assertEqual(duration, 'N/A')

	def test_will_raise_an_TypeError_if_timestamp_is_not_an_integer_with_safe_parameter_set_to_False(self):
		with self.assertRaises(TypeError):
			Timelapsed.from_timestamp('sdfsdfsf3434534erftg', safe=False)

	def test_will_raise_an_ValuError_if_timestamp_is_out_of_range_with_safe_parameter_set_to_False(self):
		with self.assertRaises(ValueError):
			Timelapsed.from_timestamp(12345678934243324, safe=False)

	def test_just_now_twitter_notation(self):
		duration = Timelapsed.from_timestamp(datetime.now().timestamp(), notation='twitter')
		self.assertEqual(duration, 'n')

	def test_just_now_mid_notation(self):
		duration = Timelapsed.from_timestamp(datetime.now().timestamp(), notation='mid')
		self.assertEqual(duration, 'now')

	def test_just_now_long_notation(self):
		duration = Timelapsed.from_timestamp(datetime.now().timestamp(), notation='lng')
		self.assertEqual(duration, 'just now')

	def test_1_minute_ago_default_notation(self):
		duration = Timelapsed.from_timestamp(datetime.now().timestamp() - 1000 * 60)
		self.assertEqual(duration, '1 minute ago')

	def test_1_minute_ago_twitter_notation(self):
		duration = Timelapsed.from_timestamp(datetime.now().timestamp() - 1000 * 60, notation='twitter')
		self.assertEqual(duration, '1m')

	def test_1_minute_ago_mid_notation(self):
		duration = Timelapsed.from_timestamp(datetime.now().timestamp() - 1000 * 60, notation='mid')
		self.assertEqual(duration, '1min')

	def test_1_minute_ago_long_notation(self):
		duration = Timelapsed.from_timestamp(datetime.now().timestamp() - 1000 * 60, notation='lng')
		self.assertEqual(duration, '1 minute ago')

	def test_17_minutes_ago_default_notation(self):
		duration = Timelapsed.from_timestamp(datetime.now().timestamp() - 17000 * 60)
		self.assertEqual(duration, '17 minutes ago')

	def test_17_minutes_ago_twitter_notation(self):
		duration = Timelapsed.from_timestamp(datetime.now().timestamp() - 17000 * 60, notation='twitter')
		self.assertEqual(duration, '17m')

	def test_17_minutes_ago_mid_notation(self):
		duration = Timelapsed.from_timestamp(datetime.now().timestamp() - 17000 * 60, notation='mid')
		self.assertEqual(duration, '17mins')

	def test_17_minutes_ago_long_notation(self):
		duration = Timelapsed.from_timestamp(datetime.now().timestamp() - 17000 * 60, notation='lng')
		self.assertEqual(duration, '17 minutes ago')

	def test_42_minutes_ago_default_notation(self):
		duration = Timelapsed.from_timestamp(datetime.now().timestamp() - 42000 * 60)
		self.assertEqual(duration, '42 minutes ago')

	def test_23_minutes_ago_default_notation(self):
		duration = Timelapsed.from_timestamp(datetime.now().timestamp() - 23000 * 60, notation='twitter')
		self.assertEqual(duration, '23m')

	def test_59_minutes_ago_default_notation(self):
		duration = Timelapsed.from_timestamp(datetime.now().timestamp() - 59000 * 60, notation='mid')
		self.assertEqual(duration, '59mins')

	def test_1_hour_ago_default_notation(self):
		duration = Timelapsed.from_timestamp(datetime.now().timestamp() - 1000 * 60 * 60)
		self.assertEqual(duration, '1 hour ago')

	def test_1_hour_ago_twitter_notation(self):
		duration = Timelapsed.from_timestamp(datetime.now().timestamp() - 1000 * 60 * 60, notation='twitter')
		self.assertEqual(duration, '1h')

	def test_1_hour_ago_mid_notation(self):
		duration = Timelapsed.from_timestamp(datetime.now().timestamp() - 1000 * 60 * 60, notation='mid')
		self.assertEqual(duration, '1hr')

	def test_1_hour_ago_lng_notation(self):
		duration = Timelapsed.from_timestamp(datetime.now().timestamp() - 1000 * 60 * 60, notation='lng')
		self.assertEqual(duration, '1 hour ago')

	def test_19_hours_ago_default_notation(self):
		duration = Timelapsed.from_timestamp(datetime.now().timestamp() - 19000 * 60 * 60)
		self.assertEqual(duration, '19 hours ago')

	def test_19_hours_ago_twitter_notation(self):
		duration = Timelapsed.from_timestamp(datetime.now().timestamp() - 19000 * 60 * 60, notation='twitter')
		self.assertEqual(duration, '19h')

	def test_19_hours_ago_mid_notation(self):
		duration = Timelapsed.from_timestamp(datetime.now().timestamp() - 19000 * 60 * 60, notation='mid')
		self.assertEqual(duration, '19hrs')

	def test_19_hours_ago_long_notation(self):
		duration = Timelapsed.from_timestamp(datetime.now().timestamp() - 19000 * 60 * 60, notation='lng')
		self.assertEqual(duration, '19 hours ago')

	def test_1_day_ago_default_notation(self):
		duration = Timelapsed.from_timestamp(datetime.now().timestamp() - 1000 * 60 * 60 * 24)
		self.assertEqual(duration, 'yesterday')

	def test_1_day_ago_twitter_notation(self):
		duration = Timelapsed.from_timestamp(datetime.now().timestamp() - 1000 * 60 * 60 * 24, notation='twitter')
		self.assertEqual(duration, '1d')

	def test_1_day_ago_mid_notation(self):
		duration = Timelapsed.from_timestamp(datetime.now().timestamp() - 1000 * 60 * 60 * 24, notation='mid')
		self.assertEqual(duration, '1dy')

	def test_1_day_ago_long_notation(self):
		duration = Timelapsed.from_timestamp(datetime.now().timestamp() - 1000 * 60 * 60 * 24, notation='lng')
		self.assertEqual(duration, 'yesterday')

	def test_1_day_ago_long_notation(self):
		duration = Timelapsed.from_timestamp(datetime.now().timestamp() - 1000 * 60 * 60 * 24, notation='lng')
		self.assertEqual(duration, 'yesterday')

	def test_6_days_ago_dafault_notation(self):
		duration = Timelapsed.from_timestamp(datetime.now().timestamp() - 6000 * 60 * 60 * 24)
		self.assertEqual(duration, '6 days ago')

	def test_6_days_ago_twitter_notation(self):
		duration = Timelapsed.from_timestamp(datetime.now().timestamp() - 6000 * 60 * 60 * 24, notation='twitter')
		self.assertEqual(duration, '6d')

	def test_6_days_ago_mid_notation(self):
		duration = Timelapsed.from_timestamp(datetime.now().timestamp() - 6000 * 60 * 60 * 24, notation='mid')
		self.assertEqual(duration, '6dys')

	def test_6_days_ago_long_notation(self):
		duration = Timelapsed.from_timestamp(datetime.now().timestamp() - 6000 * 60 * 60 * 24, notation='lng')
		self.assertEqual(duration, '6 days ago')

	def test_1_week_ago_default_notation(self):
		duration = Timelapsed.from_timestamp(datetime.now().timestamp() - 1000 * 60 * 60 * 24 * 7)
		self.assertEqual(duration, '1 week ago')

	def test_1_week_ago_twitter_notation(self):
		duration = Timelapsed.from_timestamp(datetime.now().timestamp() - 1000 * 60 * 60 * 24 * 7, notation='twitter')
		self.assertEqual(duration, '1w')

	def test_1_week_ago_mid_notation(self):
		duration = Timelapsed.from_timestamp(datetime.now().timestamp() - 1000 * 60 * 60 * 24 * 7, notation='mid')
		self.assertEqual(duration, '1wk')

	def test_1_week_ago_long_notation(self):
		duration = Timelapsed.from_timestamp(datetime.now().timestamp() - 1000 * 60 * 60 * 24 * 7, notation='lng')
		self.assertEqual(duration, '1 week ago')

	def test_3_weeks_ago_default_notation(self):
		duration = Timelapsed.from_timestamp(datetime.now().timestamp() - 3000 * 60 * 60 * 24 * 7)
		self.assertEqual(duration, '3 weeks ago')

	def test_3_weeks_ago_twitter_notation(self):
		duration = Timelapsed.from_timestamp(datetime.now().timestamp() - 3000 * 60 * 60 * 24 * 7, notation='twitter')
		self.assertEqual(duration, '3w')

	def test_3_weeks_ago_mid_notation(self):
		duration = Timelapsed.from_timestamp(datetime.now().timestamp() - 3000 * 60 * 60 * 24 * 7, notation='mid')
		self.assertEqual(duration, '3wks')

	def test_3_weeks_ago_long_notation(self):
		duration = Timelapsed.from_timestamp(datetime.now().timestamp() - 3000 * 60 * 60 * 24 * 7, notation='lng')
		self.assertEqual(duration, '3 weeks ago')

if __name__ == '__main__':
	unittest.main()
