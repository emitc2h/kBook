##########################################################
## versioned.py                                         ##
## author      : Michel Trottier-McDonald <mtm@cern.ch> ##
## date        : July 2014                              ##
## description : A base class to provide a versioning   ##
##               system                                 ##
##########################################################

## =======================================================
class Versioned:
	"""
	A base class to provide links between diferrent versions
	of the same navigable
	"""

	## -------------------------------------------------------
	def __init__(self, version=0, previous=None):
		"""
		Constructor
		"""

		self.version  = version
		self.previous = previous
		self.next     = None
		self.path     = ''


	## --------------------------------------------------------
	