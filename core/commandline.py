##########################################################
## commandline.py                                       ##
## author      : Michel Trottier-McDonald <mtm@cern.ch> ##
## date        : July 2014                              ##
## description : The command line interface             ##
##########################################################

import cmd, readline, sys
import logging as log
from book import Book

## =======================================================
class CommandLine(cmd.Cmd):
	"""
	A class using the cmd module to provide a command line interface
	"""

	## -------------------------------------------------------
	def __init__(self):
		"""
		Constructeur
		"""

		cmd.Cmd.__init__(self)
		self.prompt = 'kBook > '
		self.book   = Book()


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

		print 'help : summons the main help menu'


	## -------------------------------------------------------
	def do_create(self, arg):
		"""
		Create a new chain
		"""

		print 'Creating a new chain with name "%s"' % arg


	## -------------------------------------------------------
	def help_create(self):
		"""
		create documentation
		"""

		print 'create <new_chain_name> : creates a new chain'


	## -------------------------------------------------------
	def do_exit(self, arg):
		"""
		Exits kBook
		"""

		print 'Goodbye'
		sys.exit(1)


	## -------------------------------------------------------
	def help_exit(self):
		"""
		exit documentation
		"""

		print 'exit : exits kBook'
