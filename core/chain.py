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
			'append_job'
		]

		self.level = 1

		self.legend_string = 'index : name                      : status        : version'
		self.ls_pattern    = ('{0:<5} : {1:<25} : {2:<22} : {3:<5}', 'index', 'name', 'status', 'version')

		self.create_job(input_file_path, initial_job_type, **kwargs)


	## --------------------------------------------------------
	def create_job(self, input_file_path, job_type, **kwargs):
		"""
		Creates a job and append to the job list
		"""

		self.modified_time = time.time()

		new_job = None

		path = os.path.join(self.path, 'job0000_v0')

		if job_type == 'prun':
			script_path      = kwargs['script_path']
			use_root         = kwargs['use_root']
			root_version     = kwargs['root_version']
			output           = kwargs['output']
			additional_files = kwargs['additional_files']

			new_job = JobPrun(
				script_path,
				use_root,
				root_version,
				output,
				additional_files,
				'job0000',
				self,
				path,
				input_file_path
				)

		if job_type == 'taskid':
			new_job = JobTaskID(
				'job0000',
				self,
				path,
				input_file_path
				)

		if job_type == 'pathena-trf':

			athena_release      = kwargs['athena_release']
			testarea_path       = kwargs['testarea_path']
			transform_type      = kwargs['transform_type']
			input_dataset_type  = kwargs['input_dataset_type']
			output_dataset_type = kwargs['output_dataset_type']
			preexec             = kwargs['preexec']
			postexec            = kwargs['postexec']

			new_job = JobPathenaTrf(
				athena_release,
				testarea_path,
				transform_type,
				input_dataset_type,
				output_dataset_type,
				preexec,
				postexec,
				'job0000',
				self,
				path,
				input_file_path
				)

		self.append(new_job)



	## ---------------------------------------------------------
	def append_job(self, job_type, **kwargs):
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

		self.creation_time = time.time()
		self.modified_time = time.time()
		self.status        = 0
		self.comment       = ''

		for job in self.previous:
			if job.hide < 0: continue
			new_job = None
			if job.type == 'prun':
				new_job = JobPrun(
					job.script_path,
					job.use_root,
					job.root_version,
					job.output,
					job.additional_files,
					job.name,
					job.parent.get_latest(),
					os.path.join(self.path, '{0}_v0'.format(job.name)),
					job.input_file_path
					)

			self.append(new_job)
