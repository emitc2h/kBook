##########################################################
## submission.py                                        ##
## author      : Michel Trottier-McDonald <mtm@cern.ch> ##
## date        : July 2014                              ##
## description : Submission class, to hold a single     ##
##               submission                             ##
##########################################################

import os
import logging as log
from subprocess import Popen, PIPE
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
		self.command              = command
		self.input_dataset        = input_dataset
		self.output_dataset       = ''
		self.jedi_task_dict       = {'jediTaskID' : None}
		self.past_jedi_task_dicts = []
		self.finished_processes   = 0
		self.total_processes      = 0
		self.status               = 0
		self.private += [
			'compile_panda_options',
			'parse_panda_status'
		]

		self.level = 3

		self.legend_string = 'index : name                 : status        : progress     : input dataset'
		self.ls_pattern    = ('{0:<5} : {1:<20} : {2:<22} : {3:>5}/{4:<5}  : {5:<50}', 'index', 'name', 'status', 'finished_processes', 'total_processes', 'input_dataset')


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

		log.info('='*40)
		log.info('Checking submission status ...')
		self.update()

		if self.status == 3:
			log.info('    already submitted, currently running.')
			return

		if self.status == 4:	
			log.info('    already submitted, finished.')
			return

		os.chdir(self.path)

		## Finish constructing the command
		command = '{0} {1}'.format(self.command.format(input=self.input_dataset, output=self.output_dataset), self.compile_panda_options())

		log.info('Submitting ...')
		log.info('-'*40)
		log.info(command)

		p = Popen(args=command, stdout=PIPE, stderr=PIPE, shell=True)
		p.wait()
		pout, perr = p.communicate()
		pout += '\n' + perr

		already_done = False

		pout_lines = pout.split('\n')
		for line in pout_lines:
			if 'jediTaskID' in line:
				new_panda_job_id = -1
				line_elements = line.split(' ')
				for line_element in line_elements:
					if 'jediTaskID' in line_element:
						new_panda_job_id = int(line_element.split('=')[-1])
				if self.status == 0:
					if self.jedi_task_dict is None:
						self.jedi_task_dict = {}
					self.jedi_task_dict['jediTaskID'] = new_panda_job_id
				else:
					self.past_jedi_task_dicts.append(self.jedi_task_dict)
					self.jedi_task_dict = {}
					self.jedi_task_dict['jediTaskID'] = new_panda_job_id


		if 'Done. No jobs to be submitted' in pout:
			already_done = True
			self.status = 4

		log.info(pout)

		if ('succeeded. new' in pout) and (not already_done):
			self.status = 3

		self.update()


	## --------------------------------------------------------
	def retry(self, locator=''):
		"""
		Calls the grid to retry the submission
		"""

		if not status == 2: return
		Client.retryTask(self.jedi_task_dict['jediTaskID'], True)


	## --------------------------------------------------------
	def kill(self, locator=''):
		"""
		Calls the grid to kill the submission
		"""

		if status == 3:
			Client.killTask(self.jedi_task_dict['jediTaskID'], True)


	## --------------------------------------------------------
	def update(self, locator=''):
		"""
		Calls the grid to update the status of the submission
		"""

		if self.hide == -1: return
		if self.status == 6: return

		if not self.jedi_task_dict:
			log.warning('{0}Not submitted yet, no jedi task ID.'.format('    '*self.level))
			return

		log.debug('{0}updating {1} ...'.format('    '*self.level, self.name))

		status, new_jedi_task_dict = Client.getJediTaskDetails(self.jedi_task_dict, True, True)
		if not new_jedi_task_dict is None:
			self.jedi_task_dict = new_jedi_task_dict

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

		except KeyError:
			pass

		try:
			self.status = definitions.kbook_status_from_jedi[self.jedi_task_dict['status']]
		except KeyError:
			log.error('Status is not defined yet.')













