##########################################################
## job_prun.py                                          ##
## author      : Michel Trottier-McDonald <mtm@cern.ch> ##
## date        : July 2014                              ##
## description : specialization of the Job class for    ##
##               prun jobs                              ##
##########################################################

import os, shutil, glob
from job import Job

## -------------------------------------------------------
def gather(ask_for_path):
	"""
	Gather the information from the user to create the job
	"""

	## create dictionary
	job_specific = {}

	job_specific['job_type'] = 'prun'

	## Path to script to be executed
	job_specific['script_path'] = ask_for_path('create : prun : please provide path to the script to be executed')

	## Path to additional files to include
	use_more_files = raw_input('kBook : create : prun : Any additional files needed (you can use *)? (y/n) > ')

	additional_files = []
	if use_more_files == 'y':
		while(True):
			use_more_files = ask_for_path('create : prun : add file (type \'n\' if no more files)')
			if not os.path.basename(use_more_files) == 'n':
				additional_files.append(use_more_files)
			else:
				break
	job_specific['additional_files'] = additional_files

	## ROOT details
	use_root     = raw_input('kBook : create : prun : Use ROOT? (y/n) > ')
	root_version = ''

	if use_root == 'y':
		use_root = True
		root_version = raw_input('kBook : create : prun : which ROOT version? (leave empty for default: 5.34.18) > ')
		if not root_version: root_version = '5.34.18'

	job_specific['use_root'] = use_root
	job_specific['root_version'] = root_version

	## Specify the name of the output files
	job_specific['output'] = raw_input('kBook : create : prun : provide names of output files to be stored (comma-separated) > ')

	return job_specific



## =======================================================
class JobPrun(Job):
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

		self.script_path      = self.job_specific['script_path']
		self.script_name      = self.script_path.split('/')[-1]
		self.use_root         = self.job_specific['use_root']
		self.root_version     = self.job_specific['root_version']
		self.output           = self.job_specific['output']
		self.additional_files = self.job_specific['additional_files']

		self.type = 'prun'

		self.legend_string = 'index : type         : script_name          : status        : progress : version'
		self.ls_pattern    = ('{0:<5} : {1:<12} : {2:<20} : {3:<22} : {4:<8} : {5:<5}', 'index', 'type', 'script_name', 'status', 'completion', 'version')

		self.initialize()


	## --------------------------------------------------------
	def create_directory(self):
		"""
		copy the script over
		"""

		Job.create_directory(self)
		shutil.copyfile(self.script_path, os.path.join('.', self.script_name))

		if self.additional_files:

			files = []

			for additional_file in self.additional_files:
				for ff in  glob.glob(additional_file):
					file_name = os.path.basename(ff)
					files.append(file_name)
					shutil.copyfile(ff, './{0}'.format(file_name))

			self.panda_options += '--extFile={0}'.format(','.join(files))


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


































