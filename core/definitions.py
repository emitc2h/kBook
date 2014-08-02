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
	'finished'       ## 4
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
	'finished'    : 4,
	'failed'      : 2,
	'cancelled'   : 1
}