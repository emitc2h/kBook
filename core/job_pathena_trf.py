##########################################################
## job_pathena_trf.py                                   ##
## author      : Michel Trottier-McDonald <mtm@cern.ch> ##
## date        : July 2014                              ##
## description : specialization of the Job class for    ##
##               transform jobs                         ##
##########################################################

import os, shutil, glob, subprocess
from job import Job

## -------------------------------------------------------
def gather(ask_for_path):
	"""
	Gather the information from the user to create the job
	"""

	## create dictionary
	job_specific = {}

	job_specific['job_type'] = 'pathena-trf'

	## Athena release
	job_specific['athena_release'] = raw_input('kBook : create : pathena-trf : which Athena release? > ')
	## Path to test area
	job_specific['testarea_path'] = ask_for_path('create : pathena-trf : please provide path to the test area (leave empty if none)')
	## transform type
	job_specific['transform_type'] = raw_input('kBook : create : pathena-trf : what transform type (Reco_tf or Generate_tf)? > ')
	## input dataset type
	job_specific['input_dataset_type'] = raw_input('kBook : create : pathena-trf : what is the type of the input? (AOD, NTUP_VTXLUMI, ETC.) > ')
	## output dataset type
	job_specific['output_dataset_type'] = raw_input('kBook : create : pathena-trf : what is the type of the desired output? (AOD, NTUP_VTXLUMI, ETC.) > ')
	## pre-execution commands
	job_specific['preexec'] = raw_input('kBook : create : pathena-trf : Any preExec code? (leave empty if none) > ')
	## pre-execution commands
	job_specific['postexec'] = raw_input('kBook : create : pathena-trf : Any postExec code? (leave empty if none) > ')

	return job_specific



## =======================================================
class JobPathenaTrf(Job):
	"""
	A class to contain a single job comfiguration, but to
	be used on many input datasets
	"""

	## -------------------------------------------------------
	def __init__(self, *args, **kwargs):
		"""
		Constructor
		"""

		Job.__init__(self, *args, **kwargs)

		self.athena_release      = job_specific['athena_release']

		self.testarea_path       = job_specific['testarea_path']
		self.transform_type      = job_specific['transform_type']

		self.input_dataset_type  = job_specific['input_dataset_type']
		self.output_dataset_type = job_specific['output_dataset_type']
		self.preexec             = job_specific['preexec']
		self.postexec            = job_specific['postexec']

		self.private += [
			'setup_athena'
		]

		self.type         = 'pathena-trf'

		self.legend_string = 'index : type         : output dataset type : status        : progress : version'
		self.ls_pattern    = ('{0:<5} : {1:<12} : {2:<19} : {3:<22} : {4:<8} : {5:<5}', 'index', 'type', 'output_dataset_type', 'status', 'completion', 'version')

		self.initialize()


	# ## --------------------------------------------------------
	# def create_directory(self):
	# 	"""
	# 	copy the testarea code over in a new directory, omitting the compiled files
	# 	"""

	# 	Job.create_directory(self)
	# 	if self.testarea_path:
			


	# ## --------------------------------------------------------
	# def construct_command(self):
	# 	"""
	# 	constructs a prun command
	# 	"""

	# 	self.command = 'pathena --trf="{transform_type}.py input{input_type}File=%IN output{output_type}File=%OUT.root autoConfiguration=everything maxEvents=-1" '.format(transform_type=self.transform_type, input_type=self.input_dataset_type, output_type=self.output_dataset_type)
	# 	if self.preexec:
	# 		self.command += 'preExec=\'{preexec}\' '.format(preexec=self.preexec)
	# 	if self.postexec:
	# 		self.command += 'postExec=\'{postexec}\' '.format(postexec=self.postexec)

	# 	self.command += '--inDS {input} --outDS {output}'


	## -------------------------------------------------------
	def generate_output_dataset_names(self):
		"""
		generate output dataset names for all submissions
		"""

		output_name_rules = self.parent.parent.preferences.output_name_rules.split(' ')

		for submission in self:

			dataset_string = submission.input_dataset
			for rule in output_name_rules:
				## Skip rules having to do with file types
				if self.input_dataset_type in rule or self.output_dataset_type in rule: continue
				strings = rule.split(':')
				input_string  = strings[0][1:-1]
				output_string = strings[-1][1:-1]
				dataset_string = dataset_string.replace(input_string, output_string)

			dataset_string = dataset_string.replace(self.input_dataset_type, self.output_dataset_type)

			outDS = 'user.{0}.{1}.{2}.{3}'.format(
				self.parent.parent.preferences.user,
				dataset_string,
				self.parent.name,
				'v{0}.{1}'.format(self.parent.version, self.version)
				)
			submission.output_dataset = outDS


	## -------------------------------------------------------
	def setup_athena(self):
		"""
		Setup Athena for job submission
		"""



