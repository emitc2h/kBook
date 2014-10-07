##########################################################
## definitions.py                                       ##
## author      : Michel Trottier-McDonald <mtm@cern.ch> ##
## date        : July 2014                              ##
## description : A collection of useful definitions     ##
##                                                      ##
##########################################################

## =======================================================
job_types = [
	'prun',
	'taskid',
	'pathena-trf'
]

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