'''
Created on Jun 18, 2013

@author: anderson

Contains the constants to be used for plotting

'''


REDUCED_FIG_SIZE = (8,5)
TALL_FIG_SIZE = (8,8)
LONG_FIG_SIZE = (15,5)

#names of the probability distributions \Pi
PI_A05 = '$\Pi$ = sempre 0.5'
PI_EXT = '$\Pi$ = extremos'
PI_UNI = '$\Pi$ = uniforme'
PI_NRM = '$\Pi$ = normal'

DIST_NAMES = {
    'a05': PI_A05, 
    'tm': PI_EXT,
    'uni': PI_UNI,
    'gsn': PI_NRM 
}

#for global plots
DIST_MARKERS = {
    'a05': '^-', 
    'tm': 's-',
    'uni': 'o-',
    'gsn': 'd-' 
}

DIST_COLORS = {
   'a05': 'b', 
    'tm': 'r',
    'uni': 'g',
    'gsn': 'c' 
}

#ranges of the drivers' preference
DRV_GRP = {
    'a05': ['$\\rho=0.5$'],
    'tm':  ['$\\rho=0.0$', '$\\rho=1.0$'],
    'uni': ['$\\rho \leq 0.25$', '$0.25 < \\rho \leq 0.50$', '$0.50 < \\rho \leq 0.75$', '$\\rho > 0.75$' ],
    'gsn': ['$\\rho \leq 0.35$', '$0.35 < \\rho \leq 0.50$', '$0.50 < \\rho \leq 0.65$', '$\\rho > 0.65$' ]
}

RHO_MARKERS = {
   'a05': ['o-'],
   'tm':  ['d-', '^-' ],
   'uni': ['d-','s-', 'o-', '^-'],
   'gsn': ['d-','s-', 'o-', '^-'],
}

MARKER_INTERVAL = 20
MARKER_SIZE = 13

TITLE_SIZE = 22
AXIS_FONTSIZE = 20
TICK_FONTSIZE = 20
LGND_FONTSIZE = 18

BOTTOM_MARGIN = 0.14



