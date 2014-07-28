##########################################################
## chain.py                                             ##
## author      : Michel Trottier-McDonald <mtm@cern.ch> ##
## date        : July 2014                              ##
## description : A job container that makes a sequence  ##
##               of jobs, each using the output files   ##
##               of the previous job as new input files ##
##########################################################

import os, time
from job_prun import JobPrun

## =======================================================
class Chain:
	"""
	A class to contain a chain of jobs
	"""


	## -------------------------------------------------------
	def __init__(self, name, path, initial_job_type, input_files, **kwargs):
		"""
		Constructor
		"""

		self.name = name
		self.path = path
		self.creation_time = time.time()
		self.modified_time = time.time()
		self.jobs = []

		self.create_job(input_files, initial_job_type, **kwargs)




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


	## --------------------------------------------------------
	def submit(self):
		"""
		Submit the last job in the chain
		"""

		self.modified_time = time.time()


	## --------------------------------------------------------
	def create_job(self, input_files, job_type, **kwargs):
		"""
		Creates a job and append to the job list
		"""

		self.modified_time = time.time()
		if job_type == 'prun':
			script_path = kwargs['script_path']
			new_jobprun = JobPrun(script_path, input_files)
			self.jobs.append(new_jobprun)


	## ---------------------------------------------------------
	def append_job(self, job_type):
		"""
		Appends a new job to the chain, using the output files
		of the previous job as the new input
		"""

		self.modified_time = time.time()
