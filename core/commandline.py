##########################################################
## commandline.py                                       ##
## author      : Michel Trottier-McDonald <mtm@cern.ch> ##
## date        : July 2014                              ##
## description : The command line interface             ##
##########################################################

from cmd import Cmd
import readline, os, sys, pickle, glob, shutil, stat, getpass, time
from subprocess import Popen, PIPE
import logging as log
from book import Book
import definitions

## =======================================================
## Define the two types of completers

# - - - - - - - - - - - - - - - - - - - - - - - -
def path_completer(text, state):
	complete_candidates = glob.glob(text+'*')
	complete_candidates_dir = []
	for candidate in complete_candidates:
		if os.path.isdir(candidate): complete_candidates_dir.append('{0}{1}'.format(candidate, os.path.sep))
		else: complete_candidates_dir.append(candidate)

	return (complete_candidates_dir+[None])[state]

# - - - - - - - - - - - - - - - - - - - - - - - -
def panda_completer(text, state):
	if not text:
		completions = definitions.eventloop_prun_options.keys()
	else:
		completions = [item for item in definitions.eventloop_prun_options.keys() if item.startswith(text)]

	return (completions+[None])[state]

path_delimiters     = ' \t\n;'
panda_delimiters    = ' ='

readline.parse_and_bind('tab: complete')

## =======================================================
class CommandLine(Cmd):
	"""
	A class using the cmd module to provide a command line interface
	"""

	## -------------------------------------------------------
	def __init__(self, preferences, test_unclosed_book=True):
		"""
		Constructor
		"""

		## Record kBook directory path
		self.path = os.getcwd()

		## Greetings
		log.info('='*40)
		log.info('Welcome to kBook 2.0.0!')
		log.info('-'*40)

		## Initialize command line
		Cmd.__init__(self)
		self.prompt = 'kBook > '

		## Make sure .book exists
		try:
			os.mkdir('.book')
		except OSError:
			pass

		## Look for unclosed sessions
		self.session_start = time.time()

		potential_books = os.listdir('.book')
		main_book_present     = False
		unclosed_book_present = False
		unclosed_book         = ''

		for pb in potential_books:
			if pb == 'book.kbk': main_book_present = True
			if 'book.kbk.' in pb:
				unclosed_book_present = True
				unclosed_book = pb

		if unclosed_book_present:
			## Deal with unclosed book
			log.warning('Unclosed kBook session detected:')

			if test_unclosed_book:
				answer = raw_input('kBook : Attempt to recover? (y/n) > ')
			else:
				answer = 'y'

			if answer == 'y':
				try:
					book_file = open(os.path.join('.book', unclosed_book))
					self.book = pickle.load(book_file)
					book_file.close()
				except EOFError:
					if main_book_present:
						log.error('kBook session unrecoverable, loading last correctly saved session.')
						book_file = open(os.path.join('.book', 'book.kbk'))
						self.book = pickle.load(book_file)
						book_file.close()
					else:
						log.error('kBook session unrecoverable, creating new book ...')
						self.book = Book('book', preferences)
			else:
				if main_book_present:
					log.error('kBook session unrecoverable, loading last correctly saved session.')
					book_file = open(os.path.join('.book', 'book.kbk'))
					self.book = pickle.load(book_file)
					book_file.close()
				else:
					log.error('kBook session unrecoverable, creating new book ...')
					self.book = Book('book', preferences)


		elif main_book_present:
			## Make a copy of book.kbk
			shutil.copyfile('.book/book.kbk', '.book/book.kbk.{0}'.format(self.session_start))
			try:
				book_file = open('.book/book.kbk.{0}'.format(self.session_start))
				self.book = pickle.load(book_file)
				book_file.close()
			except EOFError:
				log.error('kBook session unrecoverable, creating new one.')
				self.book = Book('book', preferences)

		else:
			log.info('Creating book...')
			self.book = Book('book', preferences)

		self.proxy_is_expired = self.book.prepare(preferences)
		self.book.rebuild_hierarchy()


	## --------------------------------------------------------
	def run(self):
		"""
		runs the user interface
		"""

		log.info('Begin interactive session (type \'help\' for assistance)')
		self.cmdloop()


	## -------------------------------------------------------
	def execute_and_exit(self, arg):
		"""
		execute commands and quit (script mode)
		"""

		if self.proxy_is_expired:
			log.info('')
			log.info('Proxy is expired, cleaning the crontab ...')
			self.book.clean_crontab()
			log.info('Exiting.')
			return

		self.book.use_color = False
		log.info('kBook running in script mode ...')
		self.onecmd(arg)
		self.book.use_color = True
		self.do_exit('')


	## -------------------------------------------------------
	def onecmd(self, arg):
		"""
		Overrides onecmd to enable parsing of multiple commands separated by semi-colons
		"""

		if ';' in arg and not 'track' in arg:
			commands = arg.split(';')
			for command in commands:
				Cmd.onecmd(self, command)
		else:
			Cmd.onecmd(self, arg)


	## -------------------------------------------------------
	def help_help(self):
		"""
		help documentation
		"""

		log.info('help : Summon the main help menu.')


	## -------------------------------------------------------
	def do_create(self, arg):
		"""
		create <type> <name> : Create a new chain named name. Possible types are \'prun\', \'eventloop\', \'pathena-trf\', \'taskid\', etc.
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

		if not (job_type in definitions.job_types):
			job_types_string = ''
			for i, jt in enumerate(definitions.job_types):
				if i < len(definitions.job_types) -1:
					job_types_string += ' \'{0}\','.format(jt)
				else:
					job_types_string += ' or \'{0}\'.'.format(jt)
			log.error('Please provide of the the following chain types:{0}'.format(job_types_string))
			return

		if job_type == 'taskid':
			input_file_path = self.ask_for_path('create : please provide path to the file containing the JEDI task IDs')
		else:
			input_file_path = self.ask_for_path('create : please provide path to list of input datasets')


		## job type specific input
		_temp = __import__('job_{0}'.format(job_type.replace('-', '_')), globals(), locals(), ['gather'], -1)
		job_specific = _temp.gather(self.ask_for_path)

		## Specify additional panda options
		panda_options = self.ask_for_panda_options()

		self.book.create_chain(chain_name, input_file_path, panda_options, job_specific)

		self.save_book()


	## -------------------------------------------------------
	def complete_create(self, text, line, begidx, endidx):
		"""
		Autocomplete for the create types
		"""

		if not text:
			completions = definitions.job_types
		else:
			completions = [item for item in definitions.job_types if item.startswith(text)]

		return completions


	## -------------------------------------------------------
	def do_append(self, arg):
		"""
		append <index> <type> : Append a new job to an existing chain of index <index> and of type <type>. Possible types are \'prun\', \'eventloop\', \'pathena-trf\', \'taskid\', etc.
		"""

		## Interpret arguments, and argument testing
		arguments = arg.split(' ')
		if len(arguments) != 2:
			log.error('Must provide 2 arguments: <index> <type>')
			return

		## Make sure the index is an integer
		try:
			index = int(arguments[0])
		except ValueError:
			log.error('First argument is not a valid index')
			return

		## Make sure the index is in the right range
		if not (0 <= index < len(self.book)):
			log.error('First argument is not a valid index')
			return

		## Collect job type argument
		job_type = arguments[1]

		## Make sure the job_type provided is of a known type
		if not (job_type in definitions.job_types):
			job_types_string = ''
			for i, jt in enumerate(definitions.job_types):
				if i < len(definitions.job_types) -1:
					job_types_string += ' \'{0}\','.format(jt)
				else:
					job_types_string += ' or \'{0}\'.'.format(jt)
			log.error('Please provide of the the following chain types:{0}'.format(job_types_string))
			return

		## It doesn't make sense to chain taskids
		if job_type == 'taskid' or self.book[index][-1].type == 'taskid':
			log.error('Cannot chain jobs of type \'taskid\'')
			return

		## job type specific input
		_temp = __import__('job_{0}'.format(job_type.replace('-', '_')), globals(), locals(), ['gather'], -1)
		job_specific = _temp.gather(self.ask_for_path)

		## Ask for extension
		extensions = self.book[index][-1].generate_output_dataset_extensions()
		log.info('append : Select which output dataset extension you wish to use as input : ')
		for i, extension in enumerate(extensions):
			log.info('append : {0} : {1}'.format(i, extension))

		try:
			extension_index = int(raw_input('kBook : append : specify the index of the extension you want (select other if not available) : '))
		except ValueError:
			log.error('index provided is not an integer.')
			return

		if extension_index == len(extensions) - 1:
			extension = raw_input('kBook : append : specify the extension : ')
			job_specific['extension'] = extension
		else:
			job_specific['extension'] = extensions[extension_index]

		## Additional panda options
		panda_options = self.ask_for_panda_options('append')

		## Actually append to the chain
		self.book.append_to_chain(self.book[index], panda_options, job_specific)

		self.save_book()


	## -------------------------------------------------------
	def complete_append(self, text, line, begidx, endidx):
		"""
		Autocomplete for the create types
		"""

		try:
			position = line.split(' ').index(text)
		except ValueError:
			position = -1

		if position == 1:
			return []

		if position == 2:
			if not text:
				completions = definitions.job_types
			else:
				completions = [item for item in definitions.job_types if item.startswith(text)]

		return completions


	## -------------------------------------------------------
	def do_ls(self, arg):
		"""
		ls <index> : lists the content of a specified container, the container being one of the following:
		                 - the chains
		                 - the jobs inside a chain
		                 - the individual submissions inside a job
		"""

		locator = ''
		option  = ''

		arguments = arg.split(' ')

		if len(arguments) > 0:
			locator = arguments[0]
		if len(arguments) > 1:
			option  = arguments[1]

		self.book.location.ls(locator, option)


	## -------------------------------------------------------
	def complete_ls(self, text, line, begidx, endidx):
		"""
		autocomplete for ls
		"""

		## Get argument position
		try:
			position = line.split(' ').index(text)
		except ValueError:
			position = -1

		if position == 1:
			arguments = definitions.kbook_status_list + definitions.special_indices

		if position == 2:
			arguments = ['hidden']

		if not text:
			completions = arguments
		else:
			completions = [item for item in arguments if item.startswith(text)]
	
		return completions


	## -------------------------------------------------------
	def do_cd(self, arg):
		"""
		cd <index> : navigate the chains, jobs and submission.
		             Type \'cd ..\' to go back
		"""

		index, self.book.location = self.book.location.navigate(arg)[0]


	## -------------------------------------------------------
	def do_get(self, arg):
		"""
		get <index> <attribute> : Print the specified attribute of the object of the given index.
                                  Leave the attribute empty to print all attributes.
                                  Use <index> = \'self\' to refer to the current object.
                                  Use <index> = \'all\' to refer to all objects at once in the current object.
		"""

		arguments = arg.split(' ')

		if len(arguments) == 1:
			argument = arguments[0]
			self.book.location.get(argument)
		elif len(arguments) == 2:
			index     = arguments[0]
			attribute = arguments[1]
			self.book.location.get(index, attribute)
		else:
			log.error('Too many arguments, type \'help get\'')


	## -------------------------------------------------------
	def complete_get(self, text, line, begidx, endidx):
		"""
		Autocomplete for the get arguments
		"""

		completions = []

		## Get argument position
		try:
			position = line.split(' ').index(text)
		except ValueError:
			position = -1

		if position == 0:
			return []

		if position == 1:
			if not text:
				completions = (definitions.special_indices + definitions.kbook_status_list)
			else:
				completions = [item for item in (definitions.special_indices + definitions.kbook_status_list) if item.startswith(text)]

		if position == 2:
			index = line.split(' ')[1]
			if index == 'self':
				list_of_attributes = self.book.location.list_of_attributes()
			elif index == 'all' or index in definitions.kbook_status_list:
				list_of_attributes = self.book.location[0].list_of_attributes()
			else:
				list_of_attributes = self.book.location[int(index)].list_of_attributes()

			if not text:
				completions = list_of_attributes
			else:
				completions = [item for item in list_of_attributes if item.startswith(text)]

		return completions


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
		if len(arguments) < 2:
			log.error('provide an index, an attribute and a value.')
			return
		elif len(arguments) == 2:
			index     = arguments[0]
			attribute = arguments[1]
		elif len(arguments) > 3:
			index     = arguments[0]
			attribute = arguments[1]
			value     = ' '.join(arguments[2:])
		else:
			index     = arguments[0]
			attribute = arguments[1]
			value     = arguments[2]

		self.book.location.set(index, attribute, value)


	## -------------------------------------------------------
	def complete_set(self, text, line, begidx, endidx):
		"""
		Same completion rules as get
		"""

		return self.complete_get(text, line, begidx, endidx)


	## -------------------------------------------------------
	def do_close(self, arg):
		"""
		close <index> : closes a chain, job or submission for further updates
		"""

		self.book.location.close(arg)


	## -------------------------------------------------------
	def complete_close(self, text, line, begidx, endidx):
		"""
		autocomplete index to statuses
		"""

		return self.complete_status(text, line, begidx, endidx)


	## -------------------------------------------------------
	def do_open(self, arg):
		"""
		open <index> : reopens a chain, job or submission for further updates
		"""

		self.book.location.open(arg)
		self.book.location.update(arg)


	## -------------------------------------------------------
	def complete_open(self, text, line, begidx, endidx):
		"""
		autocomplete index to statuses
		"""

		return self.complete_status(text, line, begidx, endidx)


	## -------------------------------------------------------
	def do_submit(self, arg):
		"""
		submit <index> : submit a chain, job or submission
		"""

		self.book.location.submit(arg)
		self.save_book()


	## -------------------------------------------------------
	def complete_submit(self, text, line, begidx, endidx):
		"""
		autocomplete index to statuses
		"""

		return self.complete_status(text, line, begidx, endidx)


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
			navigables = self.book.location.navigate(arg)
			for i, child in navigables:
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
	def complete_copy(self, text, line, begidx, endidx):
		"""
		autocomplete index to statuses
		"""

		return self.complete_status(text, line, begidx, endidx)


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
			navigables = self.book.location.navigate(arg)
			for i, child in navigables:
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

		current_is_versioned   = False
		children_are_versioned = False

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
			navigables = self.book.location.navigate(locator)
			for i, child in navigables:
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
		self.save_book()


	## -------------------------------------------------------
	def complete_update(self, text, line, begidx, endidx):
		"""
		autocomplete index to statuses
		"""

		return self.complete_status(text, line, begidx, endidx)


	## -------------------------------------------------------
	def do_retry(self, arg):
		"""
		retry <index> : retries unfinished submissions under the given index
		"""

		self.book.location.retry(arg)


	## -------------------------------------------------------
	def complete_retry(self, text, line, begidx, endidx):
		"""
		autocomplete index to statuses
		"""

		return self.omplete_status(text, line, begidx, endidx)


	## -------------------------------------------------------
	def do_kill(self, arg):
		"""
		kill <index> : kills all running submissions under the given index
		"""

		self.book.location.kill(arg)


	## -------------------------------------------------------
	def complete_kill(self, text, line, begidx, endidx):
		"""
		autocomplete index to statuses
		"""

		return self.complete_status(text, line, begidx, endidx)


	## -------------------------------------------------------
	def do_download(self, arg):
		"""
		downlaod <index> <status> : generates a dq2-get shell script in the kbook download directory only including submissions
		                            with the specified status (leave empty for all)
		"""

		os.chdir(self.book.download_path)

		parts = arg.split(' ')
		locator = parts[0]

		if len(parts) == 1:
			status = None
		elif len(parts) == 2:
			status = parts[1]

		## Get the navigable
		navigables = self.book.location.navigate(locator)
		for i, navigable in navigables:
			if navigable.hide < 0: continue
			if i < 0:
				log.error('{0} does not exist'.format(locator))
				return
	
			if hasattr(navigable, 'version'):
				script_dir_name = '{0}.v{1}'.format(navigable.name, navigable.version)
			else:
				script_dir_name = '{0}'.format(navigable.name)
	
			try:
				os.mkdir(script_dir_name)
			except OSError:
				log.warning('download directory {0} already exists.'.format(script_dir_name))
	
			os.chdir(os.path.join(self.book.download_path, script_dir_name))
	

			if status is None:
				script_name = '{0}.sh'.format(script_dir_name)
			else:
				script_name = '{0}-{1}.sh'.format(script_dir_name, status)

			script = open(script_name, 'w')
			script.write('#!/bin/bash\n\n')
	
			job, output_datasets = navigable.generate_list('output_dataset', status=status)
			for output_dataset_list in output_datasets:
				for output_dataset in output_dataset_list.split(','):
					if output_dataset:
						if job.type == 'prun':
							script.write('dq2-get {0}_{1}/\n'.format(output_dataset, job.output))
						if job.type == 'taskid':
							script.write('dq2-get {0}\n'.format(output_dataset))
	
			script.close()
			script_path = os.path.join(self.book.download_path, script_dir_name, script_name)
			permissions = os.stat(script_path)
			os.chmod(script_path, permissions.st_mode | stat.S_IEXEC)
	
			log.info('Created dq2-get script at {0}'.format(script_path))

			os.chdir(self.book.download_path)
	
		os.chdir(self.book.path)


	## -------------------------------------------------------
	def complete_dq2get(self, text, line, begidx, endidx):
		"""
		autocomplete for dq2get
		"""

		## Get argument position
		try:
			position = line.split(' ').index(text)
		except ValueError:
			position = -1

		if position <= 1:
			return []

		if position == 2:
			if not text:
				completions = definitions.kbook_status_list
			else:
				completions = [item for item in definitions.kbook_status_list if item.startswith(text)]

		return completions


	## -------------------------------------------------------
	def do_delete(self, arg):
		"""
		delete <index> : deletes object of the given index
		"""

		indices_to_pop = []

		navigables = self.book.location.navigate(arg)
		for i, navigable in navigables:
			if i < 0:
				log.error('No entry with index {0}'.format(arg))
				return
	
			if navigable.parent is None:
				log.error('Cannot delete book, {0} has no parent.'.format(navigable.name))
				return
	
			if hasattr(navigable, 'version'):
				if not navigable.previous is None:
					navigable.previous.hide = 1
					navigable.previous.current = True
					navigable.previous.next = None
	
			if not navigable.level == 3:
				try:
					shutil.rmtree(navigable.path)
				except OSError:
					pass

			indices_to_pop.append(i)
	
		for i in reversed(indices_to_pop):
			navigable = self.book.location.pop(i)
			del navigable
	

	## -------------------------------------------------------
	def complete_delete(self, text, line, begidx, endidx):
		"""
		autocomplete index to statuses
		"""

		return self.complete_status(text, line, begidx, endidx)


	## -------------------------------------------------------
	def do_track(self, arg):
		"""
		track <commands> : Use acrontab to automatically update and retry tasks monitored in kBook
		                   commands are additional commands to be run periodically
		                   use 'cancel' as an argument to cancel the current tracking (if any)
		"""

		if arg == 'cancel':
			log.info('Cleaning the crontab ...')
			self.book.clean_crontab()
			return

		## Generate a proxy of the necessary duration
		hours = raw_input('kBook : track : How many hours do you wish to track for? (max=96) ')
		try:
			if not (0 < int(hours) <= 96):
				log.info('Number of hours ({0}) not allowed, aborting'.format(hours))
				return
		except ValueError:
			log.info('Number of hours provided ({0}) is not an integer, aborting'.format(hours))
			return

		password_attempts   = 0

		log.info('track : Enter your grid password (no more than 2 attempts are allowed) :')
		while True:

			pw = getpass.getpass()

			p = Popen(args='voms-proxy-init -voms atlas -valid {0}:0 -pwstdin'.format(hours), stdout=PIPE, stderr=PIPE, stdin=PIPE, shell=True)
			p.stdin.write(pw)

			pout, perr = p.communicate()

			for line in pout.split('\n'):
				log.info('    {0}'.format(line))

			pout += '\n' + perr

			if 'Remote VOMS server contacted succesfully.' in pout:
				break

			password_attempts += 1
			if password_attempts > 1:
				log.info('Too many password attempts, aborting.')
				return

		## Prepare the crontab
		self.book.add_to_crontab(arg)


	## -------------------------------------------------------
	def complete_track(self, text, line, begidx, endidx):
		"""
		autocomplete index to statuses
		"""


		if not text:
			completions = ['cancel']
		else:
			completions = [item for item in ['cancel'] if item.startswith(text)]

		return completions


	## -------------------------------------------------------
	def do_add(self, arg):
		"""
		add <index> : Adds new input datasets to an existing job. It will query for the path to a new input file.
		"""

		input_file_path = self.ask_for_path('Please provide the path to the input file containing the list of new inputs.')

		navigables = self.book.location.navigate(arg)
		for i, navigable in navigables:
			if i < 0:
				log.error('No entry with index {0}'.format(arg))
				return

			if not navigable.level == 2:
				log.warning('{0} is not a job'.format(navigable.name))
				continue

			navigable.create_submissions(navigable.read_input_file(input_file_path))


	## -------------------------------------------------------
	def do_graph(self, arg):
		"""
		graph <index> : Creates a graph of the completion of the job vs. time, puts it in the kBook directory
		"""

		navigables = self.book.location.navigate(arg)
		for i, navigable in navigables:
			if i < 0:
				log.error('No entry with index {0}'.format(arg))
				return

			navigable.make_completion_graph(self.path)


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
		exit <saving> : Exit kBook.
		"""

		self.save_book()

		os.chdir(self.book.path)
		shutil.copyfile('book.kbk.{0}'.format(self.session_start), 'book.kbk')
		for f in glob.glob('book.kbk.*'):
			os.remove(f)

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


	## -------------------------------------------------------
	def ask_for_panda_options(self, command='create'):
		"""
		ask user to provide a path, with path autocomplete capabilities
		"""

		## Retrieve the default completer and delimiters
		default_completer  = readline.get_completer()
		default_delimiters = readline.get_completer_delims()

		## Switch to path completer
		readline.set_completer_delims(panda_delimiters)
		readline.set_completer(panda_completer)


		panda_options = raw_input('kBook : {0} : any additional panda options? > '.format(command))

		## Switch back to default completer
		readline.set_completer_delims(default_delimiters)
		readline.set_completer(default_completer)

		return panda_options


	## -------------------------------------------------------
	def complete_status(self, text, line, begidx, endidx):
		"""
		autocomplete index to statuses
		"""

		## Get argument position
		try:
			position = line.split(' ').index(text)
		except ValueError:
			position = -1

		if position == 1:
			if not text:
				completions = definitions.kbook_status_list
			else:
				completions = [item for item in definitions.kbook_status_list if item.startswith(text)]

		return completions


	## ---------------------------------------------------------
	def save_book(self):
		"""
		Save the book
		"""

		self.book.save_preferences()
		os.chdir(self.book.path)
		book_file = open('book.kbk.{0}'.format(self.session_start), 'w')
		pickle.dump(self.book, book_file, pickle.HIGHEST_PROTOCOL)
		book_file.close()





