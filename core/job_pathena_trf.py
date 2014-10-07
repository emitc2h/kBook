##########################################################
## job_pathena_trf.py                                   ##
## author      : Michel Trottier-McDonald <mtm@cern.ch> ##
## date        : July 2014                              ##
## description : specialization of the Job class for    ##
##               transform jobs                         ##
##########################################################

import os, shutil, glob, subprocess
from job import Job

## =======================================================
class JobPathenaTrf(Job):
	"""
	A class to contain a single job comfiguration, but to
	be used on many input datasets
	"""


	## -------------------------------------------------------
	def __init__(self, athena_release, testarea_path, transform_type, input_dataset_type, output_dataset_type, preexec, postexec, *args, **kwargs):
		"""
		Constructor
		"""

		self.athena_release      = athena_release

		self.testarea_path       = testarea_path
		self.transform_type      = transform_type

		self.input_dataset_type  = input_dataset_type
		self.output_dataset_type = output_dataset_type
		self.preexec             = preexec
		self.postexec            = postexec

		Job.__init__(self, *args, **kwargs)

		self.private += [
			'setup_athena'
		]

		self.type         = 'pathena-trf'

		self.legend_string = 'index : type         : output dataset type : status        : progress : version'
		self.ls_pattern    = ('{0:<5} : {1:<12} : {2:<19} : {3:<22} : {4:<8} : {5:<5}', 'index', 'type', 'output_dataset_type', 'status', 'completion', 'version')


	## --------------------------------------------------------
	def create_directory(self):
		"""
		copy the script over
		"""

		Job.create_directory(self)
		if self.testarea_path:
			os.symlink(self.testarea_path, 'TestArea')
		else:
			self.testarea_path = self.path


	## --------------------------------------------------------
	def construct_command(self):
		"""
		constructs a prun command
		"""

		self.command = 'pathena --trf="{transform_type}.py input{input_type}File=%IN output{output_type}File=%OUT.root autoConfiguration=everything maxEvents=-1" '.format(transform_type=self.transform_type, input_type=self.input_dataset_type, output_type=self.output_dataset_type)
		if self.preexec:
			self.command += 'preExec=\'{preexec}\' '.format(preexec=self.preexec)
		if self.postexec:
			self.command += 'postExec=\'{postexec}\' '.format(postexec=self.postexec)

		self.command += '--inDS {input} --outDS {output}'


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

		os.system('AtlasProdRelease={athena_release},slc5,testarea={testarea_path}; export AtlasSetup=/afs/cern.ch/atlas/software/dist/AtlasSetup; source $AtlasSetup/scripts/asetup.sh $AtlasProdRelease'.format(athena_release=self.athena_release, testarea_path=self.testarea_path))



