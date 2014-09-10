##########################################################
## preferences.py                                       ##
## author      : Michel Trottier-McDonald <mtm@cern.ch> ##
## date        : July 2014                              ##
## description : A class store the various prefenrences ##
##               that need to be restored  every sess.  ##
##########################################################

## =======================================================
class Preferences(dict):
	"""
	A class to store various preferences for kBook
	"""

	## -------------------------------------------------------
	def __init__(self):
		"""
		Constructor
		"""

		## AFS user name
		self['user']           = ''

		## Default PANDA options
		self['panda-options']  = ''

		## logging services
		self['write-log-file']    = True
		self['log-file-level']    = 'DEBUG'
		self['dated-log-file']    = False
		self['update-on-start']   = False

		## Output file name preferences
		self['output-name-rules'] = '"user.{0}.":"" "/":""'

		## Record keys in list
		self.list = sorted(self.keys())
		self.n    = len(self.list)


	## -------------------------------------------------------
	def update(self):
		"""
		update data member values from dictionary
		"""

		if '{0}' in self['output-name-rules'] and not self['user'] == '':
			self['output-name-rules'] = self['output-name-rules'].format(self['user'])

		for key, value in self.iteritems():
			setattr(self, key.replace('-', '_'), value)


	## -------------------------------------------------------
	def print_all(self):
		"""
		A function to quickly display the preferences
		"""

		for key, value in self.iteritems():
			print '{0:<20} : {1}'.format(key, value)