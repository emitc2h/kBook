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
from job_taskid import JobTaskID
from job_pathena_trf import JobPathenaTrf
from job_eventloop import JobEventLoop
from versioned import Versioned

## =======================================================
class Chain(Versioned):
	"""
	A class to contain a chain of jobs
	"""


	## -------------------------------------------------------
	def __init__(self, name, parent, panda_options, path, input_file_path, job_specific):
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
			'append_job'
		]

		self.level = 1

		self.legend_string = 'index : name                      : status        : version'
		self.ls_pattern    = ('{0:<5} : {1:<25} : {2:<22} : {3:<5}', 'index', 'name', 'status', 'version')

		self.create_job(input_file_path, job_specific)


	## --------------------------------------------------------
	def create_job(self, input_file_path, job_specific):
		"""
		Creates a job and append to the job list
		"""

		self.modified_time = time.time()

		new_job = None

		path = os.path.join(self.path, 'job0000_v0')

		job_type = job_specific['job_type']

		if job_type == 'prun':
			new_job = JobPrun('job0000', self, path, input_file_path, job_specific)

		if job_type == 'taskid':
			new_job = JobTaskID('job0000', self, path, input_file_path, job_specific)

		if job_type == 'pathena-trf':
			new_job = JobPathenaTrf('job0000', self, path, input_file_path, job_specific)

		if job_type == 'eventloop':
			new_job = JobEventLoop('job0000', self, path, input_file_path, job_specific)

		self.append(new_job)


	## ---------------------------------------------------------
	def append_job(self, job_specific):
		"""
		Appends a new job to the chain, using the output files
		of the previous job as the new input
		"""

		self.modified_time = time.time()


	## ---------------------------------------------------------
	def recreate(self):
		"""
		recreates the jobs
		"""

		del self[:]

		for job in self.previous:
			if job.hide < 0: continue
			new_job = None
			
			path            = os.path.join(self.path, 'job0000_v0')
			input_file_path = job.input_file_path
			job_specific    = job.job_specific

			if job.type == 'prun':
				new_job = JobPrun('job0000', self, path, input_file_path, job_specific)
	
			if job.type == 'taskid':
				new_job = JobTaskID('job0000', self, path, input_file_path, job_specific)
	
			if job.type == 'pathena-trf':
				new_job = JobPathenaTrf('job0000', self, path, input_file_path, job_specific)
	
			if job.type == 'eventloop':
				new_job = JobEventLoop('job0000', self, path, input_file_path, job_specific)

			self.append(new_job)
