##########################################################
## commandline.py                                       ##
## author      : Michel Trottier-McDonald <mtm@cern.ch> ##
## date        : July 2014                              ##
## description : The command line interface             ##
##########################################################

import cmd, readline, os, sys, pickle, glob
import logging as log
from book import Book
from chain import Chain

## =======================================================
## Define the two types of completers
def path_completer(text, state): return (glob.glob(text+'*')+[None])[state]
path_delimiters     = ' \t\n;'
readline.parse_and_bind('tab: complete')

## =======================================================
class CommandLine(cmd.Cmd):
	"""
	A class using the cmd module to provide a command line interface
	"""

	## -------------------------------------------------------
	def __init__(self, preferences):
		"""
		Constructeur
		"""

		cmd.Cmd.__init__(self)
		self.prompt = 'kBook > '
		self.book   = Book(preferences)




	## --------------------------------------------------------
	def run(self):
		"""
		runs the user interface
		"""

		log.info('Begin interactive session (type \'help\' for assistance)')
		self.cmdloop()



	## -------------------------------------------------------
	def help_help(self):
		"""
		help documentation
		"""

		log.info('help : Summon the main help menu.')



	## -------------------------------------------------------
	def do_create(self, arg):
		"""
		create <type> <name> : Create a new chain named name. Possible types are \'prun\', \'pathena-algo\', \'pathena-trf\'
		"""

		## Interpret arguments
		arguments = arg.split(' ')
		if len(arguments) != 2:
			log.error('Must provide 2 arguments: type of chain and name')
			return

		job_type   = arguments[0]
		chain_name = arguments[1]

		if not chain_name.isalnum():
			log.error('Please provide a chain name that is alphanumeric (example: \'mychain456\').')
			return

		if not (job_type=='prun' or job_type=='pathena-algo' or job_type=='pathena-trf'):
			log.error('Please provide of the the following chain types: \'prun\', \'pathena-algo\' or \'pathena-trf\'.')
			return

		input_files_path = self.ask_for_path('create : please provide path to list of input datasets')

		## job type specific input
		script_path = ''
		if job_type == 'prun':
			script_path = self.ask_for_path('create : prun : please provide path to the script to be executed')

		self.book.create_chain(
			chain_name,
			job_type,
			input_files_path,
			script_path=script_path
			)




	## -------------------------------------------------------
	def do_ls(self, arg):
		"""
		ls <index> : lists the content of a specified container, the container being one of the following:
		                 - the chains
		                 - the jobs inside a chain
		                 - the individual submissions inside a job
		"""

		self.book.location.ls(arg)




	## -------------------------------------------------------
	def do_cd(self, arg):
		"""
		cd <index> : navigate the chains, jobs and submission.
		             Type \'cd ..\' to go back
		"""

		if arg == '..':
			if len(self.book.parent_locations) > 0:
				self.book.location = self.book.parent_locations[-1]
				self.book.parent_locations.pop()
			else:
				log.error('Already at top level.')
		else:
			new_location = self.book.location.cd(arg)
			if new_location:
				self.book.parent_locations.append(self.book.location)
				self.book.location = new_location




	## -------------------------------------------------------
	def do_set(self, arg):
		"""
		set <pref_index> <new_pref_value> : Set a new value for a preference, referred to by index.
		                                    Leave no argument  to list the current preferences and associated indices.
		"""

		## Print list of preferences if not arguments are passed
		if not arg:
			for i, pref in enumerate(self.book.preferences.list):
				log.info('{0:<5} : {1:<20} : {2}'.format(i, pref, self.book.preferences[pref]))
		else:
			arguments  = arg.split(' ')

			## Check that an index is provided
			try:
				pref_index = int(arguments[0])
			except ValueError:
				log.error('Provided \'{0}\' as a preference index, needs integer value from 0 to {1}'.format(arguments[0], self.book.preferences.n-1))
				return

			## Check that the index is within range
			if not 0 <= pref_index < self.book.preferences.n:
				log.error('Must provide a preference index from 0 to {0}'.format(self.book.preferences.n-1))
				return

			pref       = self.book.preferences.list[pref_index]
			value      = ' '.join(arguments[1:])

			## Some value interpretation, booleans and numerals
			if   value == 'False':	  value = False
			elif value == 'True' :    value = True
			else:
				try:
					value = int(value)
				except ValueError:
					try:
						value = float(value)
					except ValueError:
						pass

			log.info('Set value of {0} to {1}'.format(pref, value))
			self.book.preferences[pref] = value





	## -------------------------------------------------------
	def do_exit(self, arg):
		"""
		exit : Exit kBook.
		"""

		self.book.save_chains()
		self.book.save_preferences()

		log.info('Goodbye')
		sys.exit(1)





	## -------------------------------------------------------
	def do_print(self, arg):
		"""
		print <index> <attribute> : prints the attribute of chain/job/submission with given index.
		"""

		arguments = arg.split(' ')

		## Make sure the index provided is an integer
		try:
			index = int(arguments[0])
		except ValueError:
			log.error('Provided \'{0}\' as a chain index, needs integer value from 0 to {1}'.format(arguments[0], len(self.book.chains)-1))
			return

		## Check that the index is within range
		if not 0 <= index < len(self.book.chains):
			log.error('Must provide a chain index from 0 to {0}'.format(len(self.book.chains)-1))
			return

		## Make sure a second argument is provided
		try:
			member = arguments[1]
		except IndexError:
			log.error('Must provide a chain attribute to look at. Possible attributes are:')
			test_chain = Chain('', '', '', '')
			for att in dir(test_chain):
				if not '__' in att:
					log.info('    {0}'.format(att))
			log.info('')
			return

		## Make sure the second argument provided is an actual attribute of the chain class
		try:
			log.info('{0} = {1}'.format(member, getattr(self.book.chains[index], member)))
		except AttributeError:
			log.error('Chains have no attributes named {0}. Possible attributes are:'.format(member))
			test_chain = Chain('', '', '', '')
			for att in dir(test_chain):
				if not '__' in att:
					log.info('    {0}'.format(att))
			log.info('')
			return





	## -------------------------------------------------------
	def ask_for_path(self, prompt):
		"""
		ask user to provide a path, with path autocomplete capabilities
		"""

		cwd = os.getcwd()
		os.chdir(self.book.cwd)

		## Retrieve the default completer and delimiters
		default_completer  = readline.get_completer()
		default_delimiters = readline.get_completer_delims()

		## Switch to path completer
		readline.set_completer_delims(path_delimiters)
		readline.set_completer(path_completer)

		path_is_good = False

		while not path_is_good:
			try:
				path = raw_input('kBook : {0} > '.format(prompt))
				absolute_path = os.path.abspath(path)
				path_is_good = True
			except OSError:
				log.error('Path is no valid. Please provide a valid path to an existing file.')

		## Switch back to default completer
		readline.set_completer_delims(default_delimiters)
		readline.set_completer(default_completer)

		os.chdir(cwd)

		return absolute_path






