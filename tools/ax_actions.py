
# "actions" - commands that execute a command for the application

# 
#--------------------------------------------------------------------------
# simple job class - list of parameters and an ID string. 
#
# Sub-classes a dictionary (dict), and stores parameters in the dictionary. 
# Parameters can also be accessed as attributes. 

class AxJob(dict):

	def __init__(self, action_id:str, indict=None):

		if indict is None:
			indict = {}

		self.action_id = action_id

		# super
		dict.__init__(self, indict)

		# flag
		self.__initialized = True

	def __getattr__(self, item):

		try:
			return self.__getitem__(item)
		except KeyError:
			raise AttributeError(item)

	def __setattr__(self, item, value):

		if '_AxJob__initialized' not in  self.__dict__:  # this test allows attributes to be set in the __init__ method
			return dict.__setattr__(self, item, value)

		else:
			self.__setitem__(item, value)

	#def __str__(self):
	#	return "\"" + self.action_id + "\" :" + str(self._args)

#--------------------------------------------------------------------------
# Base action class - defines method
class AxAction(object):

	def __init__(self, action_id:str) -> None:
		object.__init__(self)
		self.action_id = action_id

	def run_job(self, job:AxJob) -> int:
		return 1 # error