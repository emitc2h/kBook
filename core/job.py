##########################################################
## job.py                                               ##
## author      : Michel Trottier-McDonald <mtm@cern.ch> ##
## date        : July 2014                              ##
## description : Job class, to house common arugments   ##
##               and config used on many input datasets ##
##########################################################

import os
from submission import Submission

## =======================================================
class Job:
	"""
	A class to contain a single job comfiguration, but to
	be used on many input datasets
	"""

	## -------------------------------------------------------
	def __init__(self, input_files):
		"""
		Constructor
		"""

		self.version          = 0
		self.panda_options    = ''
		self.status           = -1
		self.type             = ''
		self.submissions      = []
		self.path             = ''
		self.input_files_path = ''
		self.input_files      = []


	## -------------------------------------------------------
	def create_directory(self):
		"""
		creates the job directory that contains everything
		necessary to submit the job
		"""
		
