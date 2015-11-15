import time


class Task(object):

	def __init__(self, id, type, time_start=None, time_end=None):
		self.id = id
		self.type = type

		if time_start:
			self.time_start = time_start
		else:
			self.time_start = time.time()

		if time_end:
			self.time_end = time_end
		else:
			self.time_end = time.time()

		self.execute_time = self.calc_time()

	def calc_time(self):
		res = self.time_end - self.time_start
		return res