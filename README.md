# kBook
kBook is a python-based LHC Grid utility for ATLAS users designed to operate in the Tier3SW environment. Its purpose is to facilitate organization, submission and bookkeeping of data-processing jobs on the grid. It's close to being finalized and has all the major features implemented. However, it needs to be thoroughly tested, polished and documented. If you do try kBook, let me know of any bug you encounter. Thanks for participating in the testing!

## It's a command-line tool that
* Focuses the user on the pieces of information required to submit a job on the grid as opposed to the details of the syntax of the command-line panda tools,
* Allows you to submit and organize jobs on large numbers of input datasets,
* Provides you with a detailed report of the completion status of your jobs,
* Exploits crontabs to automatically follow-up, submit and retry jobs,
* Backs up all the necessary files and code to submit particular jobs in a common, organized space,
* Provides a smart versioning system that allows you to effortlessly update and relaunch your jobs,
* Organizes jobs in chains, where the output of one job is used as input for the next, which permits reprocessing all the way back to RAW data to the final results in a single command.

## Quickstart on lxplus/PDSF
* In your home directory:
  * git clone git@github.com:emitc2h/kBook.git kBook
  * cd kBook/
  * setupATLAS
  * lsetup panda rucio root
  * chmod a+x kBook.py
  * ./kBook.py
  * try typing 'help' and explore the possibilities!

All it really need to work is the Tier3SW environment.

## Documentation
* [Overview](https://github.com/emitc2h/kBook/wiki/Overview)
