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
from versioned import Versioned

## =======================================================
class Chain(Versioned):
	"""
	A class to contain a chain of jobs
	"""


	## -------------------------------------------------------
	def __init__(self, name, parent, panda_options, path, initial_job_type, input_file_path, **kwargs):
		"""
		Constructor
		"""

		Versioned.__init__(self, name, parent, panda_options)

		self.name = name
		self.path = path
		self.creation_time = time.time()
		self.modified_time = time.time()
		self.private += [
			'create_job',
			'append_job',
			'previous',
			'next',
			'copy'
		]

		self.create_job(input_file_path, initial_job_type, **kwargs)


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
			path         = os.path.join(self.path, 'job0000_v0')

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


	## ---------------------------------------------------------
	def retrieve(self, locator='', one_file=True):
		"""
		Does nothing for a chain
		"""

		log.error('Cannot retrieve output datasets from chain : {0}'.format(self.name))


	## ---------------------------------------------------------
	def recreate(self):
		"""
		recreates the chain, and the underlying jobs
		"""
