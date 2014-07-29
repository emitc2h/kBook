##########################################################
## job.py                                               ##
## author      : Michel Trottier-McDonald <mtm@cern.ch> ##
## date        : July 2014                              ##
## description : Job class, to house common arugments   ##
##               and config used on many input datasets ##
##########################################################

import os
import logging as log
from submission import Submission

## =======================================================
class Job:
	"""
	A class to contain a single job comfiguration, but to
	be used on many input datasets
	"""

	## -------------------------------------------------------
	def __init__(self, input_file_path):
		"""
		Constructor
		"""

		self.version          = 0
		self.panda_options    = ''
		self.status           = 'not submitted'
		self.type             = ''
		self.submissions      = []
		self.path             = ''
		self.input_file_path  = input_file_path

		self.read_input_file()


	## -------------------------------------------------------
	def read_input_file(self):
		"""
		opens the input file and create the submissions
		"""

		f = open(self.input_file_path)
		lines = f.readlines()
		for line in lines:
			self.submissions.append(Submission(line.rstrip('\n')))


	## --------------------------------------------------------
	def cd(self, locator):
		"""
		go to a submission
		"""

		try:
			index = int(locator)
		except ValueError:
			log.error('Please provide a submission index')
			return False

		try:
			return self.submissions[index]
		except IndexError:
			log.error('The index provided must from 0 to {0}'.format(len(self.submissions)-1))
			return False


	## --------------------------------------------------------
	def ls(self, locator=''):
		"""
		lists the jobs in the chain
		"""

		if not locator:
			log.info('Submissions:')
			log.info('-'*40)
			log.info('index : status         : input dataset')
			log.info('- '*20)
			for i, submission in enumerate(self.submissions):
				log.info('{0:<5} : {1:<14} : {2:<20}'.format(i, submission.status, submission.input_dataset))
	
			log.info('-'*40)
		else:
			try:
				index = int(locator)
			except ValueError:
				log.error('Please provide a submission index')
				return
	
			try:
				self.submissions[index].ls() 
			except IndexError:
				log.error('The index provided must from 0 to {0}'.format(len(self.jobs)-1))



	## -------------------------------------------------------
	def create_directory(self):
		"""
		creates the job directory that contains everything
		necessary to submit the job
		"""
		
