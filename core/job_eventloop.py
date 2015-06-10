##########################################################
## job_prun.py                                          ##
## author      : Michel Trottier-McDonald <mtm@cern.ch> ##
## date        : July 2014                              ##
## description : specialization of the Job class for    ##
##               prun jobs                              ##
##########################################################

import os, shutil, glob
from job import Job
from submission import Submission
import definitions

## -------------------------------------------------------
def copy_symlink(src, dst):
	"""
	Copy a symlink
	"""
	if os.path.islink(src):
		linkto = os.readlink(src)
		os.symlink(linkto, dst)
	else:
		shutil.copy(src,dst)

## -------------------------------------------------------
def gather(ask_for_path):
	"""
	Gather the information from the user to create the job
	"""

	## create dictionary
	job_specific = {}

	job_specific['job_type'] = 'eventloop'

	## Path to test area
	job_specific['rootcore_path']  = ask_for_path('create : eventloop : please provide path to the rootcore area')

	## Path to script to be executed
	job_specific['script_path'] = ask_for_path('create : eventloop : please provide path to the prototype script to be executed')

	## Path to additional files to include
	use_more_files = raw_input('kBook : create : eventloop : Any additional files needed (you can use *)? (y/n) > ')

	additional_files = []
	if use_more_files == 'y':
		while(True):
			use_more_files = ask_for_path('create : eventloop : add file (type \'n\' if no more files)')
			if not os.path.basename(use_more_files) == 'n':
				additional_files.append(use_more_files)
			else:
				break
	job_specific['additional_files'] = additional_files

	return job_specific



## =======================================================
class JobEventLoop(Job):
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

		self.rootcore_path    = self.job_specific['rootcore_path']
		self.script_path      = self.job_specific['script_path']
		self.script_name      = self.script_path.split('/')[-1]
		self.additional_files = self.job_specific['additional_files']
		self.run_directory    = os.path.join(self.path, 'Run')

		self.private += [
			'setup_rootcore',
			'generate_grid_scripts',
			'compile_panda_options'
		]

		self.type = 'eventloop'

		self.legend_string = 'index : type         : script_name          : status        : progress : version'
		self.ls_pattern    = ('{0:<5} : {1:<12} : {2:<20} : {3:<22} : {4:<8} : {5:<5}', 'index', 'type', 'script_name', 'status', 'completion', 'version')

		self.initialize()
		self.generate_grid_scripts()


	## --------------------------------------------------------
	def create_directory(self):
		"""
		copy the script over
		"""

		Job.create_directory(self)

		## Collect top RootCore area directories
		rootcore_toplevel_dirs = os.listdir(self.rootcore_path)

		## Copy all directories except the run directory
		for d in rootcore_toplevel_dirs:
			if d.lower() == 'run': continue
			d_fullpath = os.path.join(self.rootcore_path, d)
			if os.path.islink(d_fullpath):
				continue
			elif os.path.isdir(d_fullpath):
				shutil.copytree(d_fullpath, os.path.join(self.path, d), symlinks=True)
			else:
				shutil.copy(d_fullpath, os.path.join(self.path, d))

		## Create a run directory
		os.mkdir(self.run_directory)

		## Copy the prototype script in the run directory
		shutil.copyfile(self.script_path, os.path.join(self.run_directory, self.script_name))

		## Create the .RootCoreBin symlink
		os.symlink(os.path.join(self.path, 'RootCoreBin'), os.path.join(self.path, '.RootCoreBin'))


	## -------------------------------------------------------
	def create_submissions(self, list_of_inputs):
		"""
		Alter the submission paths
		"""

		Job.create_submissions(self, list_of_inputs)

		for submission in self:
			submission.path = self.run_directory


	## --------------------------------------------------------
	def construct_command(self):
		"""
		constructs a prun command
		"""

		self.command = 'root -l -b -q \'$ROOTCOREDIR/scripts/load_packages.C\' \'{submission}.cxx("{submission}")\''


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

			version_tag = 'v{0}.{1}'.format(self.parent.version, self.version)
			if version_tag in dataset_string:
				dataset_string = dataset_string.replace('.' + version_tag, '')

			if self.parent.name in dataset_string:
				dataset_string = dataset_string.replace('.' + self.parent.name, '')

			outDS = 'user.{0}.{1}.{2}.{3}'.format(
				self.parent.parent.preferences.user,
				dataset_string,
				self.parent.name,
				version_tag,
				)
			submission.output_dataset = outDS


	## --------------------------------------------------------
	def compile_panda_options(self):
		"""
		Gather all the panda options from upstream in the hierarchy
		"""

		current_navigable = self
		panda_options = []

		while not current_navigable is None:
			if current_navigable.panda_options:
				panda_options += current_navigable.panda_options.split(' ')
			current_navigable = current_navigable.parent

		panda_options += self.parent.parent.preferences.panda_options.split(' ')

		return panda_options


	## -------------------------------------------------------
	def generate_grid_scripts(self):
		"""
		Generates the grid scripts based on the prototype script provided
		"""

		## Save current directory and go to run directory
		cwd = os.getcwd()
		os.chdir(self.run_directory)

		## Prepare prototype script
		f_prototype = open('prototype.cxx', 'w')
		f_script    = open(self.script_path, 'r')

		sample_handler_name = ''
		driver_name = ''
		function_name = ''

		## Construct prototype script
		for line in f_script.readlines():

			## Replace existing curly braces to preserve them
			if '{' in line: line = line.replace('{', 'curly_brace_left')
			if '}' in line: line = line.replace('}', 'curly_brace_right')

			## strip away unimportant lines
			if line.lstrip(' \t').startswith('//'): continue
			if not line.strip(): continue

			## Change the name of the void function
			if 'void' in line:
				line_items = line.split()
				function_name = line_items[line_items.index('void') + 1]
				function_name = function_name[:function_name.find('(')]

				line = line.replace(function_name, '{submission}')

			## Remove lines about local path
			if 'gSystem->ExpandPathName' in line: continue
			if 'SH::DiskListLocal' in line: continue
			if 'SH::scanDir' in line: continue

			## Replace the Direct Driver by a Prun Driver
			if 'EL::DirectDriver' in line:
				line = line.replace('EL::DirectDriver', 'EL::PrunDriver')
				line_items = line.split()
				driver_name = line_items[line_items.index('EL::PrunDriver') + 1]
				driver_name = driver_name[:driver_name.find(';')]
				f_prototype.write(line)

				## Write panda options
				for option in self.compile_panda_options():
					option_elements = option.split('=')

					key = option_elements[0]
					value = option_elements[-1]

					if key == value: value = 1

					try:
						option_enum = definitions.eventloop_prun_options[key][0]
						value_type = definitions.eventloop_prun_options[key][1]
					except KeyError:
						continue

					if value_type == 'String':
						value = '"{0}"'.format(value)
					f_prototype.write('  {0}.options()->set{1}({2}, {3});\n'.format(driver_name, value_type, option_enum, value))

				## Specify output dataset name
				f_prototype.write('  {0}.options()->setString("nc_outputSampleName", '.format(driver_name) + '"{output}");\n')

				continue

			## Use submitOnly instead of submit for the driver
			if '{0}.submit('.format(driver_name) in line:
				line = line.replace('{0}.submit'.format(driver_name), '{0}.submitOnly'.format(driver_name))
				f_prototype.write(line)

				## Arrange to print jediTaskID
				f_prototype.write('\n  SH::SampleHandler sh_end;\n')
				f_prototype.write('  sh_end.load("{submission}/input");\n')
				f_prototype.write('  for (int i = 0; i < sh_end.size(); ++i)\n')
				f_prototype.write('  curly_brace_left\n')
		  		f_prototype.write('    std::cout << sh_end[i]->name() << " : jediTaskID=" << (int)sh_end[i]->getMetaDouble("nc_jediTaskID") << std::endl;\n')
				f_prototype.write('  curly_brace_right\n')

				continue

			f_prototype.write(line)

			## Add new grid sample input line after the samplehandler declaration
			if 'SH::SampleHandler' in line:
				line_items = line.split()
				sample_handler_name = line_items[line_items.index('SH::SampleHandler') + 1]
				sample_handler_name = sample_handler_name[:sample_handler_name.find(';')]
				f_prototype.write('  SH::addGrid({0}, '.format(sample_handler_name) + '"{input}");\n')

				continue

		f_prototype.close()
		f_script.close()

		prototype = open('prototype.cxx', 'r').read()

		for submission in self:
			submission_script = open('{0}.cxx'.format(submission.name), 'w')
			submission_script_content = prototype.format(submission=submission.name, input=submission.input_dataset, output=submission.output_dataset)
			submission_script_content = submission_script_content.replace('curly_brace_left', '{')
			submission_script_content = submission_script_content.replace('curly_brace_right', '}')
			submission_script.write(submission_script_content)
			submission_script.close()

		os.chdir(cwd)


	## --------------------------------------------------------
	def recreate(self):
		"""
		recreates the submissions
		"""

		Job.recreate(self)
		self.generate_grid_scripts()


	## ---------------------------------------------------------
	def start_shell(self, compile=True):
		"""
		Adding setup athena on top of shell setup
		"""

		if Job.start_shell(self):

			## Go to test area
			self.shell_command('cd {0}'.format(self.path))

			## Setup Athena
			self.shell_command('rcSetup')

			## Compile?
			if compile:
				self.shell_command('rc find_packages')
				self.shell_command('rc compile')

			## Go to run directory
			self.shell_command('cd Run')






