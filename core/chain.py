##########################################################
## chain.py                                             ##
## author      : Michel Trottier-McDonald <mtm@cern.ch> ##
## date        : July 2014                              ##
## description : A job container that makes a sequence  ##
##               of jobs, each using the output files   ##
##               of the previous job as new input files ##
##########################################################

import os, time
from job import Job

## =======================================================
class Chain:
	"""
	A class to contain a chain of jobs
	"""


	## -------------------------------------------------------
	def __init__(self, name, path, chain_type):
		"""
		Constructor
		"""

		self.name = name
		self.type = chain_type
		self.path = path
		self.creation_time = time.time()
		self.modified_time = time.time()
		self.jobs = []


	## --------------------------------------------------------
	def cd(self):
		"""
		Go to the chain's directory
		"""

		os.chdir(self.path)


	## --------------------------------------------------------
	def update(self):
		"""
		Update the chain's information
		"""

		self.modified_time = time.time()
