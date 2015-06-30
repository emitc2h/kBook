##########################################################
## job_pathena_trf.py                                   ##
## author      : Michel Trottier-McDonald <mtm@cern.ch> ##
## date        : July 2014                              ##
## description : specialization of the Job class for    ##
##               transform jobs                         ##
##########################################################

import os, shutil, glob, subprocess, ConfigParser
import logging as log
from job import Job

## -------------------------------------------------------
def gather(ask_for_path):
	"""
	Gather the information from the user to create the job
	"""

	## create dictionary
	job_specific = {}

	job_specific['job_type'] = 'pathena-trf'

	## Path to test area
	job_specific['testarea_path']  = ask_for_path('create : pathena-trf : please provide path to the test area (leave empty if none)')
	job_specific['athena_release'] = ''
	job_specific['athena_other']   = ''

	if not job_specific['testarea_path']:
		## Athena release
		job_specific['athena_release'] = raw_input('kBook : create : pathena-trf : which Athena release? > ')

	## transform type
	job_specific['transform_type'] = raw_input('kBook : create : pathena-trf : what transform type (Reco_tf or Generate_tf)? > ')
	## input dataset type
	job_specific['input_dataset_type'] = raw_input('kBook : create : pathena-trf : what is the type of the input? (AOD, NTUP_VTXLUMI, ETC.) > ')
	## output dataset type
	job_specific['output_dataset_type'] = raw_input('kBook : create : pathena-trf : what is the type of the desired output? (AOD, NTUP_VTXLUMI, ETC.) > ')

	## pre-execution commands
	job_specific['preexec'] = []
	preexec_substep = ''
	while (not job_specific['preexec']) or preexec_substep:
		preexec_substep = raw_input('kBook : create : pathena-trf : Any preExec substeps? (leave empty if none or no more) > ')
		if preexec_substep:
			job_specific['preexec'].append(preexec_substep)
		else:
			break

	## post-execution commands
	job_specific['postexec'] = []
	postexec_substep = ''
	while (not job_specific['postexec']) or postexec_substep:
		postexec_substep = raw_input('kBook : create : pathena-trf : Any postExec substeps? (leave empty if none or no more) > ')
		if postexec_substep:
			job_specific['postexec'].append(postexec_substep)
		else:
			break

	## Additional transform options
	job_specific['transform_options'] = raw_input('kBook : create : pathena-trf : Additional {0} options? > '.format(job_specific['transform_type']))

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

		self.athena_release      = self.job_specific['athena_release']

		self.testarea_path       = self.job_specific['testarea_path']
		self.transform_type      = self.job_specific['transform_type']
		self.transform_options   = self.job_specific['transform_options']

		self.input_dataset_type  = self.job_specific['input_dataset_type']
		self.output_dataset_type = self.job_specific['output_dataset_type']
		self.preexec             = self.job_specific['preexec']
		self.postexec            = self.job_specific['postexec']

		self.private += [
			'setup_athena',
			'cleanup_config'
		]

		self.type         = 'pathena-trf'

		self.legend_string = 'index : type         : input  : output           : status        : progress : version'
		self.ls_pattern    = ('{0:<5} : {1:<12} : {2:<6} : {3:<16} : {4:<22} : {5:<8} : {6:<5}', 'index', 'type', 'input_dataset_type', 'output_dataset_type', 'status', 'completion', 'version')

		self.initialize()


	## --------------------------------------------------------
	def create_directory(self):
		"""
		copy the testarea code over in a new directory, omitting the compiled files
		"""

		Job.create_directory(self)

		if self.testarea_path:
			## Collect top directories
			testarea_toplevel_dirs = os.listdir(self.testarea_path)

			## First tests when encountering a new test area
			# 0) Check for .asetup.save
			if not '.asetup.save' in testarea_toplevel_dirs:
			    log.error('Athena has never been setup in this test area. Please do so and compile.')
			    return

			# 1) Has it been setup using setupWorkArea.py?
			if not 'WorkArea' in testarea_toplevel_dirs:
			    log.error('This probably won\'t work , as I can find no \'Workarea\' directory in the test area. Make sure it was setup using setupWorkArea.py')
			    return

			# 2) Has it been compiled and tested?
			if not 'InstallArea' in testarea_toplevel_dirs:
			    log.warning('Cannot find \'InstallArea\' directory in the test area. Has the test area been compiled and tested? Do you wish to proceed anyway?')

			## Create a parsable version of .asetup.save
			asetup_save = open(os.path.join(self.testarea_path, '.asetup.save'), 'r')
			asetup_save_lines = asetup_save.readlines()
			for i, line in enumerate(asetup_save_lines):
			    if ('[' in line and ']' in line) or ('=' in line): continue
			    asetup_save_lines[i] = '# ' + line
			asetup_save_ini = open(os.path.join(self.testarea_path, '.asetup.save.ini'), 'w')
			asetup_save_ini.writelines(asetup_save_lines)

			## Look up information in asetup.save.ini
			conf = ConfigParser.ConfigParser()
			try:
				conf.read(os.path.join(self.testarea_path, '.asetup.save.ini'))
			except ConfigParser.ParsingError:
				log.warning('Cannot parse \'.asetup.save.ini\' file, Attempting clean-up...')
				if not self.cleanup_config(conf):
					log.error('Could not clean-up \'.asetup.save.ini\'. Try manually editing the file.')
					return
				log.info('Clean-up complete.')
				conf.read(os.path.join(self.testarea_path, '.asetup.save.ini'))

			binary_dir_name = conf.get('summary', 'CMTCONFIG')
			self.athena_release  = conf.get('unassigned', 'unassigned')

			## Create the ignore patterns
			def ignore_patterns(path, names):
				return [binary_dir_name]

			def ignore_patterns_root(path, names):
				names_to_be_ignored = [binary_dir_name]
				for name in names:
					if '.root' in name:
						names_to_be_ignored.append(name)
				return names_to_be_ignored

    		## Copy the directories one by one, with tailored ignore factories
			for d in testarea_toplevel_dirs:
				if d == 'InstallArea': continue
				if d.startswith('.'): continue
				if not os.path.isdir(os.path.join(self.testarea_path, d)): continue
				if d == 'WorkArea':
					shutil.copytree(os.path.join(self.testarea_path, d), os.path.join(self.path, d), ignore=ignore_patterns_root)
				else:
					shutil.copytree(os.path.join(self.testarea_path, d), os.path.join(self.path, d), ignore=ignore_patterns)



	## -------------------------------------------------------
	def create_submissions(self, list_of_inputs):
		"""
		Alter the submission paths
		"""

		Job.create_submissions(self, list_of_inputs)

		for submission in self:
			submission.path = os.path.join(submission.path, 'WorkArea', 'run')


	## --------------------------------------------------------
	def construct_command(self):
		"""
		constructs a prun command
		"""

		self.command = 'pathena --trf="{transform_type}.py --input{input_type}File %IN --output{output_type}File %OUT.{output_type}.root --maxEvents -1 '.format(transform_type=self.transform_type, input_type=self.input_dataset_type, output_type=self.output_dataset_type)
		
		if self.transform_options:
			self.command += '{0} '.format(self.transform_options) 

		if self.preexec:
			for i, preexec_substep in enumerate(self.preexec):
				if i == 0:
					self.command += '--preExec \'{preexec_substep}\' '.format(preexec_substep=preexec_substep)
				else:
					self.command += '\'{preexec_substep}\' '.format(preexec_substep=preexec_substep)

		if self.postexec:
			for i, postexec_substep in enumerate(self.postexec):
				if i == 0:
					self.command += '--postExec \'{postexec_substep}\' '.format(postexec_substep=postexec_substep)
				else:
					self.command += '\'{postexec_substep}\' '.format(postexec_substep=postexec_substep)

		self.command += '" --inDS {input} --outDS {output}'


	## -------------------------------------------------------
	def generate_output_dataset_names(self):
		"""
		generate output dataset names for all submissions
		"""

		Job.generate_output_dataset_names(self, skip_datatype_rules=True)


	## ---------------------------------------------------------
	def start_shell(self, compile=True):
		"""
		Adding setup athena on top of shell setup
		"""

		if Job.start_shell(self):

			## Go to test area
			self.shell_command('cd {0}'.format(self.path))

			## Setup Athena
			self.shell_command('asetup {0},here'.format(self.athena_release))

			## Compile?
			if compile:
				self.shell_command('cd WorkArea/cmt')
				self.shell_command('cmt config; source setup.sh; cmt bro gmake')

			## Go to run directory
			self.shell_command('cd ../run')


	## ---------------------------------------------------------
	def cleanup_config(self, configparser):
		"""
		Clean-up the .asetup.save.ini file from parsing errors
		"""

		successful_parse = False

		while not successful_parse:
			try:
				configparser.read(os.path.join(self.testarea_path, '.asetup.save.ini'))
				successful_parse = True

			except ConfigParser.ParsingError as e:
				line_number = int(str(e).split('\n')[-1].split()[1].rstrip(']:'))
				f = open(os.path.join(self.testarea_path, '.asetup.save.ini'))
				f_lines = f.readlines()
				f.close()

				if 'CMTCONFIG' in f_lines[line_number-1] or 'unassigned' in f_lines[line_number-1]:
					log.error('    problematic line contains crucial information, cannot remove.')
					return False

				log.info('   removing line {0}: \'{1}\''.format(line_number, f_lines[line_number-1]))
				f = open(os.path.join(self.testarea_path, '.asetup.save.ini'), 'w')
				for line in f_lines:
					if line == f_lines[line_number-1]: continue
					f.write(line)
				f.close()

		return True



		
























