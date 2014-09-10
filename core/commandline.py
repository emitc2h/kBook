##########################################################
## commandline.py                                       ##
## author      : Michel Trottier-McDonald <mtm@cern.ch> ##
## date        : July 2014                              ##
## description : The command line interface             ##
##########################################################

import cmd, readline, os, sys, pickle, glob, shutil
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
		Constructor
		"""

		log.info('='*40)
		log.info('Welcome to kBook 2.0.0!')
		log.info('-'*40)

		cmd.Cmd.__init__(self)
		self.prompt = 'kBook > '
		try:
			book_file = open('.book/book.kbk')
			self.book = pickle.load(book_file)
			book_file.close()
		except IOError:
			log.info('Creating book...')
			try:
				os.mkdir('.book')
			except OSError:
				pass

			self.book   = Book('book', preferences)

		self.book.prepare(preferences)
		self.book.rebuild_hierarchy()


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

		if not chain_name.replace('_', '').replace('-', '').isalnum():
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

		self.save_book()


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
		self.save_book()


	## -------------------------------------------------------
	def do_copy(self, arg):
		"""
		copy <index> : copies a chain or a job, incrementing the version number and hiding the original.
		               enters copy mode, in which the copied object can be modified before being recreated
		"""

		current_is_versioned = False
		children_are_versioned   = False

		try:
			v = self.book.location.version
			current_is_versioned = True
		except AttributeError:
			pass

		try:
			if len(self.book.location) > 0:
				v = self.book.location[0].version
				children_are_versioned = True
		except AttributeError:
			pass

		if (not arg) and current_is_versioned:
			spawn = self.book.location.copy()
			if not spawn is None:
				self.book.location.parent.append(spawn)
				self.book.location = spawn
				self.book.location.recreate()
		elif arg and children_are_versioned:
			i, child = self.book.location.locate(arg)
			if i < 0:
				log.error('{0} does not exist in {1}'.format(arg, self.book.location.name))
				return
			spawn = child.copy()
			if not spawn is None:
				self.book.location.append(spawn)
				spawn.recreate()
		else:
			log.error('Cannot copy object.')

		self.save_book()


		## -------------------------------------------------------
	def do_versions(self, arg):
		"""
		versions <index> : copies a chain or a job, incrementing the version number and hiding the original
		"""

		current_is_versioned = False
		children_are_versioned   = False

		try:
			v = self.book.location.version
			current_is_versioned = True
		except AttributeError:
			pass

		try:
			if len(self.book.location) > 0:
				v = self.book.location[0].version
				children_are_versioned = True
		except AttributeError:
			pass

		if (not arg) and current_is_versioned:
			self.book.location.show_versions()
		elif arg and children_are_versioned:
			i, child = self.book.location.locate(arg)
			if i < 0:
				log.error('{0} does not exist in {1}'.format(arg, self.book.location.name))
				return
			child.show_versions()
		else:
			log.error('Object is not versioned.')


	## -------------------------------------------------------
	def do_switch(self, arg):
		"""
		switch <index> <version> : switch object to given version
		"""

		arguments = arg.split(' ')
		if len(arguments) == 1:
			locator = 'self'
			try:
				version = int(arguments[0])
			except ValueError:
				log.error('<version> must be an integer')
				return

		elif len(arguments) == 2:
			locator = arguments[0]
			try:
				version = int(arguments[1])
			except ValueError:
				log.error('<version> must be an integer')
				return

		else:
			log.error('wrong arguments.')
			return


		current_is_versioned = False
		children_are_versioned   = False

		try:
			v = self.book.location.version
			current_is_versioned = True
		except AttributeError:
			pass

		try:
			if len(self.book.location) > 0:
				v = self.book.location[0].version
				children_are_versioned = True
		except AttributeError:
			pass

		if locator == 'self' and current_is_versioned:
			self.book.location = self.book.location.get_version(version)
		elif locator and children_are_versioned:
			i, child = self.book.location.locate(locator)
			if i < 0:
				log.error('{0} does not exist in {1}'.format(arg, self.book.location.name))
				return
			new_child = child.get_version(version)
		else:
			log.error('Object is not versioned.')


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
	def do_update(self, arg):
		"""
		update <index> : updates the object of the given index
		"""

		self.book.location.update(arg)


	## -------------------------------------------------------
	def do_dq2get(self, arg):
		"""
		dq2get <index> : generates a dq2-get shell script in the kbook directory
		"""

		os.chdir(self.book.download_path)

		if not arg:
			if hasattr(self.book.location, 'version'):
				script_name = '{0}.v{1}'.format(self.book.location.name, self.book.location.version)
			else:
				script_name = '{0}'.format(self.book.location.name)

			try:
				os.mkdir(script_name)
			except OSError:
				log.error('download directory {0} already exists.'.format(script_name))
				return

			os.chdir(os.path.join(self.book.download_path, script_name))

			script = open('{0}.sh'.format(script_name), 'w')

			output_datasets = self.book.location.generate_list('output_dataset')
			for output_dataset in output_datasets:
				script.write('dq2-get {0}_{1}/\n'.format(output_dataset, 'histograms.root'))

			script.close()

		os.chdir(self.book.path)


	## -------------------------------------------------------
	def do_delete(self, arg):
		"""
		delete <index> : deletes object of the given index
		"""

		try:
			navigable = self.book.location[int(arg)]
		except IndexError:
			log.error('No entry with index {0}'.format(arg))
			return

		if hasattr(navigable, 'version'):
			if not navigable.previous is None:
				navigable.previous.hide = 1
				navigable.previous.current = True
				navigable.previous.next = None

		if not hasattr(navigable, 'command'):
			try:
				shutil.rmtree(navigable.path)
			except OSError:
				pass
		self.book.location.remove(navigable)
		del navigable


	## -------------------------------------------------------
	def do_save(self, arg):
		"""
		save : save the book
		"""

		log.info('Saving ...')
		self.save_book()


	## -------------------------------------------------------
	def do_exit(self, arg):
		"""
		exit <saving> : Exit kBook. saving = \'nosave\' to avoid saving the session.
		"""

		if not arg == 'nosave':
			self.save_book()

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


	## ---------------------------------------------------------
	def save_book(self):
		"""
		Save the book
		"""

		self.book.save_preferences()
		os.chdir(self.book.path)
		book_file = open('book.kbk', 'w')
		pickle.dump(self.book, book_file, pickle.HIGHEST_PROTOCOL)
		book_file.close()





