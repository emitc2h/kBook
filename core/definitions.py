##########################################################
## definitions.py                                       ##
## author      : Michel Trottier-McDonald <mtm@cern.ch> ##
## date        : July 2014                              ##
## description : A collection of useful definitions     ##
##                                                      ##
##########################################################

## =======================================================
special_indices = [
	'self',
	'all'
]

## =======================================================
job_types = [
	'prun',
	'taskid',
	'pathena-trf',
	'eventloop'
]

## =======================================================
kbook_status_list = [
	'not-submitted',
	'cancelled',
	'unfinished',
	'running',
	'finished',
	'error',
	'closed'
]

## =======================================================
eventloop_prun_options = {
	'--destSE'           : ('EL::Job::optGridDestSE', 'String'),
	'--site'             : ('EL::Job::optGridSite', 'String'),
	'--cloud'            : ('EL::Job::optGridCloud', 'String'),
	'--rootVer'          : ('EL::Job::optRootVer', 'String'),
	'--cmtConfig'        : ('EL::Job::optCmtConfig', 'String'),
	'--excludedSite'     : ('EL::Job::optGridExcludedSite', 'String'),
	'--nGBPerJob'        : ('EL::Job::optGridNGBPerJob', 'String'),
	'--memory'           : ('EL::Job::optGridMemory', 'String'),
	'--maxCpuCount '     : ('EL::Job::optGridMaxCpuCount', 'String'),
	'--nFiles'           : ('EL::Job::optGridNFiles', 'Double'),
	'--nFilesPerJob'     : ('EL::Job::optGridNFilesPerJob', 'Double'),
	'--nJobs'            : ('EL::Job::optGridNJobs', 'Double'),
	'--maxFileSize'      : ('EL::Job::optGridMaxFileSize', 'String'),
	'--maxNFilesPerJob'  : ('EL::Job::optGridMaxNFilesPerJob', 'String'),
	'--tmpDir'           : ('EL::Job::optTmpDir', 'String'),
	'--useChirpServer'   : ('EL::Job::optGridUseChirpServer', 'String'),
	'--express'          : ('EL::Job::optGridExpress', 'String'),
	'--noSubmit'         : ('EL::Job::optGridNoSubmit', 'String'),
	'--disableAutoRetry' : ('EL::Job::optGridDisableAutoRetry', 'String'),
	'--mergeOutput'      : ('EL::Job::optGridMergeOutput', 'String'),
}

## =======================================================
kbook_status = [
	'\033[00mnot submitted\033[0m',  ## 0
	'\033[35mcancelled\033[0m',     ## 1
	'\033[33munfinished\033[0m',    ## 2
	'\033[34mrunning\033[0m',       ## 3
	'\033[32mfinished\033[0m',      ## 4
	'\033[31merror\033[0m',         ## 5
	'\033[90mclosed\033[0m'         ## 6
]

## =======================================================
kbook_status_reversed = {
	'not-submitted' : 0,
	'cancelled'     : 1,
	'unfinished'    : 2,
	'running'       : 3,
	'finished'      : 4,
	'error'         : 5,
	'closed'        : 6
}

## =======================================================
kbook_status_from_panda = {
	'pending'     : 3,
	'defined'     : 3,
	'waiting'     : 3,
	'assigned'    : 3,
	'activated'   : 3,
	'sent'        : 3,
	'starting'    : 3,
	'running'     : 3,
	'holding'     : 3,
	'transfering' : 3,
	'merging'     : 3,
	'finished'    : 4,
	'failed'      : 2,
	'cancelled'   : 1
}

## =======================================================
kbook_status_from_jedi = {
	'registered'    : 3,
	'defined'       : 3,
	'assigning'     : 3,
	'ready'         : 3,
	'pending'       : 3,
	'scouting'      : 3,
	'scouted'       : 3,
	'running'       : 3,
	'prepared'      : 3,
	'done'          : 4,
	'failed'        : 2,
	'finished'      : 2,
	'aborting'      : 1,
	'aborted'       : 1,
	'finishing'     : 2,
	'topreprocess'  : 3,
	'preprocessing' : 3,
	'tobroken'      : 1,
	'broken'        : 1,
	'toretry'       : 3,
	'toincexec'     : 3,
	'rerefine'      : 3,
}