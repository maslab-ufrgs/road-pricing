'''
Created on Mar 5, 2013

@author: anderson
'''

import csv
import sys
from optparse import OptionParser

def plot_driver_data(files, col, sep=','):
    
    all_data = {}
    
    for key in files:
        if files[key]:
            all_data[key] = [row for row in csv.reader(open('incfile'), delimiter=sep)]
            x_data = [i[0] for i in all_data[key][1:]]
            
    
    
    
if __name__ == '__main__':
    parser = OptionParser()
            
    parser.add_option(
        '-o', '--output-prefix', type=str, default='drvdata',
        dest = 'output',
        help = 'the prefix of the output files to be generated'
    )
    
    parser.add_option(
        '-g', '--greedy-file',
        help='the path to the file with the driver results of greedy prc policy',
        type=str
    )
    
    parser.add_option(
        '-i', '--incremental-file',
        help='the path to the file with the driver results of incremental prc policy',
        type=str
    )
    
    parser.add_option(
        '-q', '--qlearning-file',
        help='the path to the file with the driver results of q-learning prc policy',
        type=str
    )
    
    parser.add_option(
        '-o', '--oldq-file',
        help='the path to the file with the driver results of old-q prc policy',
        type=str
    )
    
    parser.add_option(
        '-f', '--fixedpricing-file',
        help='the path to the file with the driver results of fixed prc policy',
        type=str
    )
    
    parser.add_option(
        '-s', '--separator',
        help='the separator for the output file',
        type=str, default=','
    )
    
    parser.add_option(
        '-c', '--column',
        help='the number of the column to plot the data (1,2,3) = (z,tt,exp) respectively',
        type=int, default=1
    )
    
    (options, args) = parser.parse_args(sys.argv)

    files = {}
    files['greedy'] = options.greedy_file if options.greedy_file else None
    files['incremental'] = options.incremental_file if options.incremental_file else None 
    files['qlearning'] = options.qlearning_file if options.qlearning_file else None
    files['oldq'] = options.oldq_file if options.oldq_file else None
    files['fixed'] = options.fixedpricing_file if options.fixedpricing_file else None
    
    plot_driver_data(files, options.column, options.separator)
 