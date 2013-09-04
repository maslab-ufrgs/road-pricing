'''
Created on 22/02/2013

@author: artavares
'''
import xml.etree.ElementTree as ET
import sys
import os
import csv
from optparse import OptionParser
import collections

def load_csv_data(outputpath, filename, separator = ','):
    csv_file = open(os.path.join(outputpath, filename))
    return [row for row in csv.reader(csv_file, delimiter=separator)]

def main():
    
    (options, args) = parse_args()
    
    if not options.iterations:
        print 'parameter -i/--iterations required.'
        exit()
    
    eprefix = options.expresults_prefix
    
    print 'Loading travel time data...'
    tt_data = load_csv_data(options.path_to_input, eprefix + '_tt.csv')
    #print len(tt_data), len(tt_data[0])
    
    print 'Loading credits expenditure data...'
    xps_data = load_csv_data(options.path_to_input, eprefix + '_xps.csv')
    
    print 'Loading z data...'
    z_data = load_csv_data(options.path_to_input, eprefix + '_z.csv')
    
    
    header_offset = 2 #how many lines the header of tt, exp and z data has
    
    full_trips = full_trips_in_window(options.begin, options.finish, os.path.join(
           options.path_to_input, 
           '%s_1.xml' % options.routeinfo_prefix
    ))
    #print len(full_trips)
    drvdata = collections.defaultdict(dict)
    
    for i in range(options.iterations):
        print 'Generating data for iteration', i+1
        
        #parses the i-th routeinfo file
        rinfo_tree = ET.parse(os.path.join(
           options.path_to_input, 
           '%s_%d.xml' % (options.routeinfo_prefix, i + 1)
        )) 
        
        vehnum = 0
        for vdata in rinfo_tree.getroot():
            
            #finds the column with veh_id in the data files (all must have columns in the same order!)
            col = tt_data[0].index(vdata.get('id'))
            #ignores vehicles w/ trips outside the time window
            if (not vdata.get('id') in full_trips): 
                continue
            
            pref = tt_data[1][col]
            
            
            if not pref in drvdata:
                drvdata[pref] = dict((i,{'tt':0,'xps':0,'z':0}) for i in range(options.iterations))
                
            #print drvdata[pref]#,drvdata[pref][i]['tt']
                
            drvdata[pref][i]['tt'] = new_average(drvdata[pref][i]['tt'], tt_data[header_offset + i][col], vehnum) 
            drvdata[pref][i]['xps'] = new_average(drvdata[pref][i]['xps'], xps_data[header_offset + i][col], vehnum)
            drvdata[pref][i]['z'] = new_average(drvdata[pref][i]['z'], z_data[header_offset + i][col], vehnum)
            
            vehnum += 1
#    for i in range(options.iterations):
#        drvdata['0.5'][i]['tt'] = sum([float(t) for t in drvdata['0.5'][i]['tt']]) / len(drvdata['0.5'][i]['tt'])
#        print 'avg...', drvdata['0.5'][i]['tt']    
    #print [pref for pref in drvdata]
    outfiles = dict((pref, open(os.path.join(
        options.path_to_input,
        options.output + '_%s.drv' % pref), 'w'
    )) for pref in drvdata)
    
    
    #print outfiles, [p for p in drvdata]
    
    for pref in outfiles:
        outfiles[pref].write(
             '#Begin: %d, end: %d, num_drivers: %d\n' % (options.begin, options.finish, len(full_trips)))
        outfiles[pref].write((options.separator.join(['%s'] * 4) % ('#it','z','tt','exp\n')).decode('string-escape'))
        
        for i in range(options.iterations):
        
            outfiles[pref].write((
                (options.separator.join(['%s'] * 4) + '\n') % (
                    i+1, 
                    drvdata[pref][i]['z'],
                    drvdata[pref][i]['tt'],
                    drvdata[pref][i]['xps'],
                )).decode('string-escape')
            )
                          
        outfiles[pref].close()        
    
    print "Output files '%s_x.drv' written." % os.path.join(options.path_to_input,options.output)
    
def new_average(old_avg, new_value, stepnum):
    #if old_avg == {}:
    #    return new_value
    #old_avg = float(old_avg)
    #print new_value, old_avg, stepnum
    return ( (float(new_value) - float(old_avg)) / (stepnum + 1)) + old_avg
    
def full_trips_in_window(begin, finish, routeinfo_file):
    '''
    Returns a list with the ID of the drivers that
    made a full trip between begin and finish
    
    '''
    rinfo_tree = ET.parse(routeinfo_file)
    
    fulltrips = []
    
    #handles edge case:
    if finish == 0:
        finish = sys.maxint
    
    for vdata in rinfo_tree.getroot():
        try:
            if float(vdata.get('depart')) >= begin and float(vdata.get('arrival')) <= finish:
                fulltrips.append(vdata.get('id'))
        except ValueError:
            print 'Warning: %s has no depart or arrival in %s, skipping...' % (vdata.get('id'), routeinfo_file)
    
    return fulltrips 
    
def parse_args():
    
    parser = OptionParser()
            
    parser.add_option(
        '-o', '--output-prefix', type=str, default='drvdata',
        dest = 'output',
        help = 'the prefix of the output files to be generated'
    )
    
    parser.add_option(
        '-p', '--path-to-input',
        help='the path to the directory where the input files are',
        default='.', type=str,
    )
    
    parser.add_option(
        '-b', '--begin',
        help='the start time of the time window',
        type=int, default=0
    )
    
    parser.add_option(
        '-f', '--finish',
        help='the finish time of the time window, 0=unlimited',
        type=int, default=0
    )
    
    parser.add_option(
        '-g', '--group-by',
        help='filter drivers who have the preference value',
        type=int, default=0
    )
    
    parser.add_option(
        '-r', '--routeinfo-prefix',
        help='the prefix for the routeinfo files: [prefix]_i.xml, where i is the iteration',
        type=str, default='routeinfo'
    )
    
    parser.add_option(
        '-e', '--expresults-prefix',
        help='the prefix for the experiment result files: [prefix]_type.csv, where type will be tt, xps or z',
        type=str, default='exp'
    )
    
    parser.add_option(
        '-i', '--iterations',
        help='the number of iterations to be read from inputs',
        type=int
    )
    
    parser.add_option(
        '-s', '--separator',
        help='the separator for the output file',
        type=str, default=','
    )
    
    return parser.parse_args(sys.argv)

if __name__ == '__main__':
    main()
    
    
    