##########################################################
## definitions.py                                       ##
## author      : Michel Trottier-McDonald <mtm@cern.ch> ##
## date        : July 2014                              ##
## description : A collection of useful definitions     ##
##                                                      ##
##########################################################

## =======================================================
kbook_status = [
	'not submitted', ## 0
	'cancelled',     ## 1
	'unfinished',    ## 2
	'running',       ## 3
	'finished',      ## 4
	'error'          ## 5
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
	'finished'      : 4,
	'aborting'      : 1,
	'aborted'       : 1,
	'finishing'     : 4,
	'topreprocess'  : 3,
	'preprocessing' : 3,
	'tobroken'      : 1,
	'broken'        : 1,
	'toretry'       : 3,
	'toincexec'     : 3,
	'rerefine'      : 3,
}