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
		self.current_panda_job_id = []
		self.past_panda_job_ids   = []
		self.finished_processes   = 0
		self.total_processes      = 0
		self.status               = 0
		self.private += [
			'compile_panda_options',
			'parse_panda_status'
		]

		self.level = 3

		self.legend_string = 'index : name                 : status               : input dataset'
		self.ls_pattern    = ('{0:<5} : {1:<20} : {2:<20} : {3:<50}', 'index', 'name', 'status', 'input_dataset')


	## -------------------------------------------------------
	def ls(self, locator=''):
		"""
		prints out information about the submission
		"""

		log.info('-'*60)
		log.info('input dataset    : {0}'.format(self.input_dataset))
		log.info('output dataset   : {0}'.format(self.output_dataset))
		log.info('status           : {0}'.format(definitions.kbook_status[self.status]))
		log.info('finished jobs    : {0}/{1}'.format(self.finished_processes, self.total_processes))
		log.info('current panda ID : {0}'.format(self.current_panda_job_id))
		log.info('command          : {0} {1}'.format(self.command.format(input=self.input_dataset, output=self.output_dataset), self.compile_panda_options()))


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

		self.update()

		if self.status == 3:
			log.info('already submitted, currently running.')
			return

		if self.status == 4:	
			log.info('already submitted, finished.')
			return

		os.chdir(self.path)

		## Finish constructing the command
		command = '{0} {1}'.format(self.command.format(input=self.input_dataset, output=self.output_dataset), self.compile_panda_options())

		log.info('='*40)
		log.info('Submitting ...')
		log.info('-'*40)
		log.info(command)

		p = Popen(args=command, stdout=PIPE, shell=True)
		p.wait()
		pout, perr = p.communicate()

		already_done = False
		JobID_found_one = False

		pout_lines = pout.split('\n')
		for line in pout_lines:
			if 'JobID' in line:
				new_panda_job_id = int(line.split(':')[-1])
				if self.status == 0:
					if not JobID_found_one:
						self.current_panda_job_id = [new_panda_job_id]
						JobID_found_one = True
					else:
						self.current_panda_job_id.append(new_panda_job_id)
				else:
					if not JobID_found_one:
						self.past_panda_job_ids.append(self.current_panda_job_id)
						self.current_panda_job_id = [new_panda_job_id]
						JobID_found_one = True
					else:
						self.current_panda_job_id.append(new_panda_job_id)


		if 'Done. No jobs to be submitted' in pout:
			already_done = True
			self.status = 4

		log.info(pout)
		if not (perr is None):
			log.error(perr)

		if (perr is None) and (not 'ERROR' in pout) and (not already_done):
			self.status = 3


	## --------------------------------------------------------
	def update(self):
		"""
		Calls the grid to update the status of the submission
		"""

		if not self.current_panda_job_id:
			log.warning('{0}Not submitted yet, no panda job ID.'.format('    '*self.level))
			return

		log.debug('{0}updating {1} ...'.format('    '*self.level, self.name))

		panda_jobs = {}

		for job_id in self.current_panda_job_id:
			status, pandaIDstatus = Client.getPandIDsWithJobID(job_id, verbose=False)
			if status > 0:
				log.error('Cannot update, panda job ID may be corrupted or proxy may be void.')
				return
			panda_jobs.update(pandaIDstatus)

		self.parse_panda_status(panda_jobs)


	## ---------------------------------------------------------
	def parse_panda_status(self, panda_jobs):
		"""
		parses the panda dictionary and produces the job status and other useful pieces of information
		"""

		minimum_status = 5
		finished = 0
		total    = 0
		for job in panda_jobs.itervalues():
			total += 1
			status = definitions.kbook_status_from_panda[job[0]]
			if status == 4: finished += 1
			if status < minimum_status:
				minimum_status = status

		self.status             = minimum_status
		self.total_processes    = total
		self.finished_processes = finished













