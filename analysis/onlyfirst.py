'''
Created on 06/03/2013

@author: artavares

'''
import xml.etree.ElementTree as ET
import sys
import os
import csv
from optparse import OptionParser

def load_csv_data(outputpath, filename, separator = ','):
    csv_file = open(os.path.join(outputpath, filename))
    return [row for row in csv.reader(csv_file, delimiter=separator)]

def main():
    
    (options, args) = parse_args()
    
    if not options.iterations:
        print 'parameter -i/--iterations required.'
        exit()
    
    sep = options.separator.decode('string-escape')
    eprefix = options.expresults_prefix
    
    print 'Loading travel time data...'
    tt_data = load_csv_data(options.path_to_input, eprefix + '_tt.csv')
    #print len(tt_data), len(tt_data[0])
    
    print 'Loading credits expenditure data...'
    xps_data = load_csv_data(options.path_to_input, eprefix + '_xps.csv')
    
    print 'Loading z data...'
    z_data = load_csv_data(options.path_to_input, eprefix + '_z.csv')
    
    header_offset = 2 #how many lines the header of tt, exp and z data has
    
    #drvdata = collections.defaultdict(dict)
    
    categories = sorted([float(c) for c in options.categories.split(',')])
    
    metrics = ['z', 'tt', 'xps', 'count']
    
    outfiles = dict((m, open(os.path.join(
        options.path_to_input,
        options.output + '_%s.fdvs' % m), 'w'
    )) for m in metrics)
    
    for metric in outfiles:
        outfiles[metric].write(
            (
                sep.join(['%s'] * (len(categories)+1) ) % 
                tuple(['#it'] + categories)
            ) + '\n' 
        ) 
    
    #this is the difference between this script and drvcategories.
    #here, we only analyse the drivers that completed the first trip
    #we want to see how they perform even when other drivers enter the simulation on the other days
    full_trips = full_trips_in_window(options.begin, options.finish, os.path.join(
       options.path_to_input, 
       '%s_%d.xml' % (options.tripinfo_prefix, 1)
    ))
    
    for i in range(options.iterations):
        print 'Generating data for iteration', i+1
        
        drvdata = dict((categ, {'z':0, 'tt':0, 'xps':0, 'count':0}) for categ in categories)
        
        #parses the i-th routeinfo file
        rinfo_tree = ET.parse(os.path.join(
           options.path_to_input, 
           '%s_%d.xml' % (options.tripinfo_prefix, i + 1)
        )) 
        
        vehnum = 0
        for vdata in rinfo_tree.getroot():
            
            #finds the column with veh_id in the data files (all must have columns in the same order!)
            col = tt_data[0].index(vdata.get('id'))
            #ignores vehicles w/ trips outside the time window
            if (not vdata.get('id') in full_trips): 
                continue
            
            pref = float(tt_data[1][col])
            
            #find which category the driver's preference belongs to
            for categ in categories:
                if pref <= categ:
                    #print 'hit', categ
                    drvdata[categ]['z'] = new_average(drvdata[categ]['z'], z_data[header_offset + i][col], vehnum)
                    drvdata[categ]['tt'] = new_average(drvdata[categ]['tt'], tt_data[header_offset + i][col], vehnum)
                    drvdata[categ]['xps'] = new_average(drvdata[categ]['xps'], xps_data[header_offset + i][col], vehnum)
                    drvdata[categ]['count'] += 1
                    break
                    
            vehnum += 1
            
        #drvdata[categ]['count'] = vehnum
        
        #outputs one line
        for metric,outfile in outfiles.iteritems():
            outfile.write(
                (
                    sep.join(['%s'] * (len(categories)+1) ) % 
                    tuple([i+1] + [drvdata[c][metric] for c in categories])
                ) + '\n' 
            ) 
            
    for o in outfiles.values():
        o.close()        
    
    print "Output files '%s_*.fdvs' written." % os.path.join(options.path_to_input,options.output)
    
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
        '-c', '--categories',
        help='comma-separated list with the categories of preferences to average the driver data (e.g.: 0.33,0.66,1.0)',
        type=str, default='0.33,0.66,1.0'
    )
    
    parser.add_option(
        '-t', '--tripinfo-prefix',
        help='the prefix for the tripinfoinfo files: [prefix]_i.xml, where i is the iteration',
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
    
    
    