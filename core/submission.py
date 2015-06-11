##########################################################
## submission.py                                        ##
## author      : Michel Trottier-McDonald <mtm@cern.ch> ##
## date        : July 2014                              ##
## description : Submission class, to hold a single     ##
##               submission                             ##
##########################################################

import os, time, sys
import logging as log
from navigable import Navigable
from pandatools import Client, PdbUtils
import definitions

## =======================================================
class Submission(Navigable):
	"""
	A class to handle the submission of a single grid
	command
	"""

	## -------------------------------------------------------
	def __init__(self, name, parent, input_dataset, command, path):
		"""
		Constructor
		"""

		Navigable.__init__(self, name, parent, '')

		self.path                 = path
		self.parent_submission    = None
		self.command              = command
		self.input_dataset        = input_dataset
		self.output_dataset       = ''
		self.jedi_task_dict       = {'jediTaskID' : None}
		self.past_jedi_task_dicts = []
		self.finished_processes   = 0
		self.total_processes      = 0
		self.completion           = '0.0%'
		self.status               = definitions.NOT_SUBMITTED
		self.retry_count          = 0
		self.retry_count_max      = 10
		self.url                  = ''
		self.private += [
			'compile_panda_options',
			'parse_panda_status',
			'generate_output_dataset_extensions'
		]

		self.level = 3

		self.legend_string = 'index : status         : progress : input dataset'
		self.ls_pattern    = ('{0:<5} : {1:<23} : {2:<8} : {3:<50}', 'index', 'status', 'completion', 'input_dataset')


	## -------------------------------------------------------
	def info(self):
		"""
		prints out information about the submission
		"""

		log.info('-'*60)
		log.info('input dataset        : {0}'.format(self.input_dataset))
		log.info('output dataset       : {0}'.format(self.output_dataset))
		log.info('status               : {0}'.format(definitions.kbook_status[self.status]))
		log.info('finished jobs        : {0}/{1}'.format(self.finished_processes, self.total_processes))
		log.info('current jedi task ID : {0}'.format(self.jedi_task_dict['jediTaskID']))
		log.info('command              : {0} {1}'.format(self.command.format(input=self.input_dataset, output=self.output_dataset), self.compile_panda_options()))
		log.info('')


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

		panda_options += self.parent.parent.parent.preferences.panda_options.split(' ')

		return ' '.join(panda_options)


	## --------------------------------------------------------
	def submit(self, locator=''):
		"""
		submits the one submission
		"""

		## Check the status of the source job, if there is one
		if not self.parent_submission is None:
			if not self.parent_submission.is_finished():
				log.info('Parent submission is not finished, skipping.')
				return

		log.info('='*40)
		log.info('Checking submission status ...')
		self.update()

		if self.is_running():
			log.info('    already submitted, currently running.')
			return

		if self.is_finished():	
			log.info('    already submitted, finished.')
			return

		## Start the shell
		self.parent.start_shell()

		if self.parent.type == 'eventloop':
			command = self.command.format(submission=self.name)
		else:
			command = '{0} {1}'.format(self.command.format(input=self.input_dataset, output=self.output_dataset), self.compile_panda_options())

		log.info('Submitting ...')
		log.info('-'*40)

		self.parent.shell_command('cd {0}'.format(self.path), silent=True)
		pout = self.parent.shell_command(command, silent=True)

		already_done = False

		pout_lines = pout.split('\n')
		for line in pout_lines:
			log.info(line)
			if 'jediTaskID' in line:
				new_panda_job_id = -1
				line_elements = line.split(' ')
				for line_element in line_elements:
					if 'jediTaskID' in line_element:
						new_panda_job_id = int(line_element.split('=')[-1])
				if self.is_not_submitted():
					if self.jedi_task_dict is None:
						self.jedi_task_dict = {}
					self.jedi_task_dict['jediTaskID'] = new_panda_job_id
					self.url = 'http://bigpanda.cern.ch/jobs/?display_limit=100&jeditaskid={0}'.format(new_panda_job_id)
				else:
					self.past_jedi_task_dicts.append(self.jedi_task_dict)
					self.jedi_task_dict = {}
					self.jedi_task_dict['jediTaskID'] = new_panda_job_id
					self.url = 'http://bigpanda.cern.ch/jobs/?display_limit=100&jeditaskid={0}'.format(new_panda_job_id)

		log.info('Monitoring URL: {0}'.format(self.url))

		if 'Done. No jobs to be submitted' in pout:
			already_done = True
			self.status = definitions.FINISHED

		if ('succeeded. new' in pout) and (not already_done):
			self.status = definitions.RUNNING

		self.modified_time = time.time()


	## --------------------------------------------------------
	def retry(self, locator=''):
		"""
		Calls the grid to retry the submission
		"""

		if not self.is_unfinished(): return
		if self.retry_count >= self.retry_count_max: return

		log.info('{0}retrying {1} ...'.format('    '*self.level, self.name))
		Client.retryTask(self.jedi_task_dict['jediTaskID'], False)

		self.status = definitions.RUNNING
		self.retry_count += 1

		self.modified_time = time.time()


	## --------------------------------------------------------
	def kill(self, locator=''):
		"""
		Calls the grid to kill the submission
		"""

		log.info('{0}killing {1} ...'.format('    '*self.level, self.name))
		Client.killTask(self.jedi_task_dict['jediTaskID'], False)
		self.status = definitions.CANCELLED

		self.modified_time = time.time()


	## --------------------------------------------------------
	def update(self, locator='', indepth=False):
		"""
		Calls the grid to update the status of the submission
		"""

		if self.is_hidden(): return
		if self.is_finished(): return
		if self.is_closed(): return

		if not self.jedi_task_dict:
			log.warning('{0}Not submitted yet, no jedi task ID.'.format('    '*self.level))
			return

		log.info('{0}updating {1} ...'.format('    '*self.level, self.name))

		status, new_jedi_task_dict = Client.getJediTaskDetails(self.jedi_task_dict, True, True)
		if not new_jedi_task_dict is None:
			self.jedi_task_dict = new_jedi_task_dict
			self.url = 'http://bigpanda.cern.ch/jobs/?display_limit=100&jeditaskid={0}'.format(self.jedi_task_dict['jediTaskID'])

		try:
			statistics = self.jedi_task_dict['statistics']
			statuses = statistics.split(',')
			done  = 0
			total = 0
			for s in statuses:
				label  = s.split('*')[0]
				number = int(s.split('*')[-1])
				if label == 'finished':
					done += number
				total += number

			self.finished_processes = done
			self.total_processes    = total
			if not self.total_processes == 0:
				self.completion = '{0:.1%}'.format(float(self.finished_processes)/float(self.total_processes))

		except KeyError:
			pass
		except ValueError:
			pass

		if indepth:
			try:
				output_datasets = self.jedi_task_dict['outDS']
				output_datasets = output_datasets.split(',')
				if len(output_datasets) > 2:
					log.error('More than 2 output datasets registered, which one to pick?')
					for outDS in output_datasets:
						log.error('    {0}'.format(outDS))
					return

				for outDS in output_datasets:
					if '.log' in outDS: continue
					self.output_dataset = outDS
			except KeyError:
				pass


		try:
			self.status = definitions.kbook_status_from_jedi[self.jedi_task_dict['status']]
		except KeyError:
			log.error('Status is not defined yet.')

		self.modified_time = time.time()


	## --------------------------------------------------------
	def generate_output_dataset_extensions(self):
		"""
		returns a list of extensions for output datasets
		"""

		extensions = []

		output_datasets = []
		try:
			output_datasets = self.jedi_task_dict['outDS'].split(',')
		except KeyError:
			pass

		for output_dataset in output_datasets:
			output_dataset.strip(' \n\t')
			if self.output_dataset in output_dataset:
				extension = output_dataset[len(self.output_dataset):-1]
				extensions.append(extension)

		return extensions + ['other']


	## --------------------------------------------------------
	def __repr__(self):
		"""
		Customize printout
		"""

		return '{0}/{1}/{2}'.format(self.parent.parent.name, self.parent.name, self.name)













