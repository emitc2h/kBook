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

		Versioned.__init__(self, name, parent, '')

		self.name = name
		self.path = path
		self.creation_time = time.time()
		self.modified_time = time.time()
		self.private += [
			'create_job',
			'append_job',
			'panda_options',
		]

		self.level = 1

		self.legend_string = 'index : name                      : status        : progress : version : last modified             '
		self.ls_pattern    = ('{0:<5} : {1:<25} : {2:<22} : {3:<8} : {4:<7} : {5:<15}', 'index', 'name', 'status', 'completion', 'version', 'modified_time')

		self.create_job(input_file_path, job_specific, panda_options)




	## --------------------------------------------------------
	def create_job(self, input_file_path, job_specific, panda_options):
		"""
		Creates a job and append to the job list
		"""

		self.modified_time = time.time()

		new_job = None

		path = os.path.join(self.path, 'job0000_v0')

		job_type = job_specific['job_type']
		job_specific['panda_options'] = panda_options

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

		new_job = None

		## Make the new job name and path
		new_job_name = 'job{0}'.format(str(len(self)).zfill(4))
		path = os.path.join(self.path, '{0}_v0'.format(new_job_name))

		## Collect outputs of the previous job in the chain
		inputs = [submission for submission in self[-1].get_latest()]
		job_specific['datasets'] = inputs
		input_file_path = None

		## Steer job creation by  job type
		job_type = job_specific['job_type']

		if job_type == 'prun':
			new_job = JobPrun(new_job_name, self, path, input_file_path, job_specific)

		if job_type == 'taskid':
			new_job = JobTaskID(new_job_name, self, path, input_file_path, job_specific)

		if job_type == 'pathena-trf':
			new_job = JobPathenaTrf(new_job_name, self, path, input_file_path, job_specific)

		if job_type == 'eventloop':
			new_job = JobEventLoop(new_job_name, self, path, input_file_path, job_specific)

		new_job.index = len(self)
		self.append(new_job)


	## ---------------------------------------------------------
	def recreate(self):
		"""
		recreates the jobs
		"""

		os.mkdir(self.path)

		del self[:]

		for i, job in enumerate(self.previous):
			if job.hide < 0: continue

			if i == 0:
				self.create_job(job.input_file_path, job.job_specific, job.panda_options)
			else:
				self.append_job(job.panda_options, job.job_specific)
			

