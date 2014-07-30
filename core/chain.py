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
from navigable import Navigable

## =======================================================
class Chain(Navigable):
	"""
	A class to contain a chain of jobs
	"""


	## -------------------------------------------------------
	def __init__(self, name, parent, path, initial_job_type, input_file_path, **kwargs):
		"""
		Constructor
		"""

		Navigable.__init__(self, name, parent)

		self.name = name
		self.path = path
		self.creation_time = time.time()
		self.modified_time = time.time()
		self.private += [
			'submit',
			'update',
			'create_job',
			'append_job'
		]

		self.create_job(input_file_path, initial_job_type, **kwargs)



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
			for job in self:
				job.submit()
		else:
			try:
				index = int(locator)
			except ValueError:
				log.error('Please provide a job index')
				return
	
			try:
				self[index].submit() 
			except IndexError:
				log.error('The index provided must from 0 to {0}'.format(len(self)-1))


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
				'job0000',
				self,
				path,
				input_file_path
				)

			self.append(new_jobprun)


	## ---------------------------------------------------------
	def append_job(self, job_type):
		"""
		Appends a new job to the chain, using the output files
		of the previous job as the new input
		"""

		self.modified_time = time.time()
