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

		self.legend_string = 'index : name                 : type         : script_name    : version'
		self.ls_pattern    = ('{0:<5} : {1:<20} : {2:<12} : {3:<20} : {4:<5}', 'index', 'name', 'type', 'script_name', 'version')


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

		for submission in self:
			outDS = 'user.{0}.{1}.{2}.{3}'.format(
				self.parent.parent.preferences.user,
				submission.input_dataset.replace('/', '').replace('user.mtm.', ''),

				self.script_name.replace('.py', ''),
				'v{0}'.format(self.version)
				)
			submission.output_dataset = outDS




