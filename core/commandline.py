##########################################################
## commandline.py                                       ##
## author      : Michel Trottier-McDonald <mtm@cern.ch> ##
## date        : July 2014                              ##
## description : The command line interface             ##
##########################################################

import cmd, readline, os, sys, pickle, glob
import logging as log
from book import Book

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
		self.book   = Book('book', preferences)




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

		input_file_path = self.ask_for_path('create : please provide path to list of input datasets')

		## job type specific input
		script_path   = ''
		use_root      = False
		root_version  = ''
		output        = ''
		panda_options = ''

		if job_type == 'prun':
			script_path = self.ask_for_path('create : prun : please provide path to the script to be executed')
			use_root    = raw_input('kBook : create : prun : Use ROOT? (y/n) > ')
			if use_root == 'y':
				use_root = True
				root_version = raw_input('kBook : create : prun : which ROOT version? (leave empty for default: 5.34.18) > ')
				if not root_version: root_version = '5.34.18'
			output = raw_input('kBook : create : prun : provide names of output files to be stored (comma-separated) > ')
			panda_options = raw_input('kBook : create : prun : any additional panda options? > ')


		self.book.create_chain(
			chain_name,
			job_type,
			input_file_path,
			panda_options,
			script_path=script_path,
			use_root=use_root,
			root_version=root_version,
			output=output
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

		self.book.location = self.book.location.cd(arg)



	## -------------------------------------------------------
	def do_get(self, arg):
		"""
		get <index> <attribute> : Print the specified attribute of the object of the given index.
                                  Leave the attribute empty to print all attributes.
                                  Use <index> = \'self\' to refer to the current object.
                                  Use <index> ] \'all\' to refer to all objects at once in the current object.
		"""

		arguments = arg.split(' ')
		index = ''
		attribute = ''
		if len(arguments) < 1:
			log.error('provide at least an index.')
			return
		elif len(arguments) > 2:
			log.error('too many arguments. provide at most an index and an attribute.')
			return
		elif len(arguments) == 1:
			index = arguments[0]
		else:
			index = arguments[0]
			attribute = arguments[1]

		self.book.location.get(index, attribute)


	## -------------------------------------------------------
	def do_set(self, arg):
		"""
		set <index> <attribute> <value> : Set the specified attribute of the object of the given index to value.
                                          Leave the attribute empty to print all attributes.
                                          Use <index> = \'self\' to refer to the current object.
                                          Use <index> = \'all\' to refer to all objects at once in the current object.
		"""

		arguments = arg.split(' ')
		index = ''
		attribute = ''
		value = ''
		if len(arguments) < 3:
			log.error('provide an index, an attribute and a value.')
			return
		elif len(arguments) > 3:
			index = arguments[0]
			attribute = arguments[1]
			value = ' '.join(arguments[2:])
		else:
			index = arguments[0]
			attribute = arguments[1]
			value = arguments[2]

		self.book.location.set(index, attribute, value)



	## -------------------------------------------------------
	def do_submit(self, arg):
		"""
		submit <index> : submit a chain, job or submission
		"""

		self.book.location.submit(arg)


	## -------------------------------------------------------
	def do_retrieve(self, arg):
		"""
		retrieve <index> <onefile> : retrieve datasets from the grid
		                             set onefile to True/False if only 1 or all the files of the datasets are to be retrieved
		"""

		arguments = arg.split(' ')
		locator = ''
		one_file = True
		if len(arguments) == 1:
			locator = arguments[0]
		elif len(arguments) == 2:
			locator = arguments[0]
			if arguments[1] == 'True':
				one_file = True
			elif arguments[1] == 'False':
				one_file = False
			else:
				log.error('does not understand <onefile> argument, provide \'True\' or \'False\'.')
				return

		self.book.location.retrieve(locator, one_file)




	## -------------------------------------------------------
	def do_pref(self, arg):
		"""
		pref <pref_index> <new_pref_value> : Set a new value for a preference, referred to by index.
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
			self.book.preferences.update()





	## -------------------------------------------------------
	def do_exit(self, arg):
		"""
		exit <saving> : Exit kBook. saving = \'nosave\' to avoid saving the session.
		"""

		if not arg == 'nosave':
			self.book.save_chains()
			self.book.save_preferences()

		log.info('Goodbye')
		sys.exit(1)





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






