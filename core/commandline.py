##########################################################
## commandline.py                                       ##
## author      : Michel Trottier-McDonald <mtm@cern.ch> ##
## date        : July 2014                              ##
## description : The command line interface             ##
##########################################################

import cmd, readline, sys, pickle
import logging as log
from book import Book

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
		Create a new chain
		"""

		## Interpret arguments
		arguments = arg.split(' ')
		if len(arguments) != 2:
			log.error('Must provide 2 arguments: type of chain and name')
			return

		chain_type = arguments[0]
		chain_name = arguments[1]

		if not chain_name.isalnum():
			log.error('Please provide a chain name that is alphanumeric (example: \'mychain456\').')
			return

		if not (chain_type=='prun' or chain_type=='pathena-algo' or chain_type=='pathena-trf'):
			log.error('Please provide of the the following chain types: \'prun\', \'pathena-algo\' or \'pathena-trf\'.')
			return

		self.book.create_chain(chain_name, chain_type)

	## -------------------------------------------------------
	def help_create(self):
		"""
		create documentation
		"""

		log.info('create <type> <name> : Create a new chain named name. Possible types are \'prun\', \'pathena-algo\', \'pathena-trf\'')




	## -------------------------------------------------------
	def do_ls(self, arg):
		"""
		list various things:
		    - chains
		    - jobs inside a chain
		    - submsissions inside a job
		"""

		if not self.book.location:
			self.book.sort_chains()
			log.info('chains:')
			log.info('-'*40)
			for i,chain in enumerate(self.book.chains):
				log.info('{0:<5} : {1:<20}'.format(i, chain.name))
			log.info('-'*40)

	## -------------------------------------------------------
	def help_ls(self):
		"""
		ls documentation
		"""

		log.info('ls <index> : lists the content of a specified container, the container being one of the following:')
		log,info('                 - the chains')
		log.info('                 - the jobs inside a chain')
		log.info('                 - the individual submissions inside a job')




	## -------------------------------------------------------
	def do_set(self, arg):
		"""
		sets a preference
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
	def help_set(self):
		"""
		setpref documentation
		"""

		log.info('set <pref_index> <new_pref_value> : Set a new value for a preference, referred to by index.')
		log.info('                                    Leave no argument  to list the current preferences and associated indices.')






	## -------------------------------------------------------
	def do_exit(self, arg):
		"""
		Exits kBook
		"""

		self.book.save_chains()
		self.book.save_preferences()

		log.info('Goodbye')
		sys.exit(1)

	## -------------------------------------------------------
	def help_exit(self):
		"""
		exit documentation
		"""

		log.info('exit : Exit kBook.')



	## -------------------------------------------------------
	def do_print(self, arg):
		"""
		prints the information contained in a specified data member of a chain
		"""

		arguments = arg.split(' ')
		index = int(arguments[0])
		member = arguments[1]

		log.info('{0} = {1}'.format(member, getattr(self.book.chains[index], member)))

