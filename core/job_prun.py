##########################################################
## job_prun.py                                          ##
## author      : Michel Trottier-McDonald <mtm@cern.ch> ##
## date        : July 2014                              ##
## description : specialization of the Job class for    ##
##               prun jobs                              ##
##########################################################

import os, shutil
from job import Job

## =======================================================
class JobPrun(Job):
	"""
	A class to contain a single job comfiguration, but to
	be used on many input datasets
	"""


	## -------------------------------------------------------
	def __init__(self, script_path, use_root, root_version, output, *args, **kwargs):
		"""
		Constructor
		"""

		self.script_path  = script_path
		self.script_name  = script_path.split('/')[-1]
		self.use_root     = use_root
		self.root_version = root_version
		self.output       = output

		Job.__init__(self, *args, **kwargs)

		self.type         = 'prun'

		self.legend_string = 'index : type         : script_name          : status         : version'
		self.ls_pattern    = ('{0:<5} : {1:<12} : {2:<20} : {3:<23} : {4:<5}', 'index', 'type', 'script_name', 'status', 'version')


	## --------------------------------------------------------
	def create_directory(self):
		"""
		copy the script over
		"""

		Job.create_directory(self)
		shutil.copyfile(self.script_path, './{0}'.format(self.script_name))


	## --------------------------------------------------------
	def construct_command(self):
		"""
		constructs a prun command
		"""

		self.command = 'prun --exec="python {script} %IN" '.format(script=self.script_name)
		if self.use_root:
			self.command += '--rootVer {root} '.format(root=self.root_version)
		self.command += '--outputs {output} '.format(output=self.output)
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
				strings = rule.split(':')
				input_string  = strings[0][1:-1]
				output_string = strings[-1][1:-1]
				dataset_string = dataset_string.replace(input_string, output_string)

			outDS = 'user.{0}.{1}.{2}.{3}'.format(
				self.parent.parent.preferences.user,
				dataset_string,
				self.parent.name,
				'v{0}.{1}'.format(self.parent.version, self.version)
				)
			submission.output_dataset = outDS




