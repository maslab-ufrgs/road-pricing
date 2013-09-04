'''
Created on Feb 16, 2013

@author: anderson

'''

import sys
import random
from optparse import OptionParser
import xml.etree.ElementTree as ET

def generateBalancedStrategy():
    '''
    Returns the preference of a balanced strategy driver
    
    '''
    return 0.5

def generateHastyOrEconomic():
    '''
    Returns 1 or 0, randomly
    
    '''
    return random.choice([0,1]) 

def generate_with_uniform_dist():
    '''
    Returns a random number between 0 and 1
    
    '''
    return random.uniform(0, 1)

def generate_with_gaussian():
    '''
    Returns a number with gaussian distribution: mu = 0.5; stddev = 0.15
    
    '''
    n = random.gauss(0.5, 0.15)
    if n > 1: return 1
    if n < 0: return 0
    return n
    
#groups the preference generators    
pref_generators = {
    'balanced': generateBalancedStrategy,
    'time-money': generateHastyOrEconomic,
    'uniform': generate_with_uniform_dist,
    'gaussian': generate_with_gaussian
}

if __name__ == '__main__':
    parser = OptionParser()
        
    parser.add_option(
        '-o', '--output', type='str', default='out.drv',
         help = 'the .drv file to be generated'
    )
    
    parser.add_option(
        '-r', '--route-file',
        help='the .rou.xml file to be converted',
        type='str', default=None
    )
    
    parser.add_option(
        '-p', '--preference',
        help='the preference generator for the drivers (balanced, time-money, uniform, gaussian)',
        type=str, default='balanced'
    )
    
    (options, args) = parser.parse_args(sys.argv)
    
    tree = ET.parse(options.route_file)
    outfile = open(options.output, 'w')
    
    #header
    outfile.write('#id orig dest depart pref\n')
    
    for element in tree.getroot():
            
        edges = element[0].get('edges').split(" ")
    
        outfile.write( 
            '%s %s %s %s %f\n' % 
            (element.get('id'), edges[0], edges[-1], 
             element.get('depart'), pref_generators[options.preference]())
        )
        
    outfile.close()
    print "Output file '%s' generated" % options.output


