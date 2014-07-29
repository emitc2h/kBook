##########################################################
## chain.py                                             ##
## author      : Michel Trottier-McDonald <mtm@cern.ch> ##
## date        : July 2014                              ##
## description : A job container that makes a sequence  ##
##               of jobs, each using the output files   ##
##               of the previous job as new input files ##
##########################################################

import os, time
import logging as log
from job_prun import JobPrun

## =======================================================
class Chain:
	"""
	A class to contain a chain of jobs
	"""


	## -------------------------------------------------------
	def __init__(self, preferences, name, path, initial_job_type, input_file_path, **kwargs):
		"""
		Constructor
		"""

		self.preferences = preferences
		self.name = name
		self.path = path
		self.creation_time = time.time()
		self.modified_time = time.time()
		self.jobs = []

		self.create_job(input_file_path, initial_job_type, **kwargs)




	## --------------------------------------------------------
	def cd(self, locator):
		"""
		Go to a job
		"""

		try:
			index = int(locator)
		except ValueError:
			log.error('Please provide a job index')
			return False

		try:
			return self.jobs[index]
		except IndexError:
			log.error('The index provided must from 0 to {0}'.format(len(self.jobs)-1))
			return False

		


	## --------------------------------------------------------
	def ls(self, locator=''):
		"""
		lists the jobs in the chain
		"""

		if not locator:
			log.info('Jobs:')
			log.info('-'*40)
			log.info('index : status         : job type')
			log.info('- '*20)
			for i, job in enumerate(self.jobs):
				log.info('{0:<5} : {1:<14} : {2:<20}'.format(i, job.status, job.type))
	
			log.info('-'*40)
		else:
			try:
				index = int(locator)
			except ValueError:
				log.error('Please provide a job index')
				return
	
			try:
				self.jobs[index].ls() 
			except IndexError:
				log.error('The index provided must from 0 to {0}'.format(len(self.jobs)-1))




	## --------------------------------------------------------
	def update(self):
		"""
		Update the chain's information
		"""


	## --------------------------------------------------------
	def submit(self, locator=''):
		"""
		Submit jobs
		"""

		self.modified_time = time.time()
		if not locator:
			for job in self.jobs:
				job.submit()
		else:
			try:
				index = int(locator)
			except ValueError:
				log.error('Please provide a job index')
				return
	
			try:
				self.jobs[index].submit() 
			except IndexError:
				log.error('The index provided must from 0 to {0}'.format(len(self.jobs)-1))


	## --------------------------------------------------------
	def create_job(self, input_file_path, job_type, **kwargs):
		"""
		Creates a job and append to the job list
		"""

		self.modified_time = time.time()
		if job_type == 'prun':
			script_path  = kwargs['script_path']
			use_root     = kwargs['use_root']
			root_version = kwargs['root_version']
			output       = kwargs['output']
			path         = os.path.join(self.path, 'job0000')

			new_jobprun = JobPrun(
				script_path,
				use_root,
				root_version,
				output,
				self.preferences,
				path,
				input_file_path
				)

			self.jobs.append(new_jobprun)


	## ---------------------------------------------------------
	def append_job(self, job_type):
		"""
		Appends a new job to the chain, using the output files
		of the previous job as the new input
		"""

		self.modified_time = time.time()
