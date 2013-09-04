'''
Created on May 17, 2013

@author: anderson

'''
import sumolib
import sys
import xml.etree.ElementTree as ET

from optparse import OptionParser
from drvcategories import full_trips_in_window,new_average


def normalize(net_file_name, routeinfo_prefix, num_iterations, factor, first, last, separator, ofname):
    
    road_net = sumolib.net.readNet(net_file_name)
    
    ofile = open(ofname,'w')
    ofile.write('#it%sntt\n' % separator)
    
    for it in range(num_iterations):
        print 'Generating data for iteration', it+1
        
        #parses the i-th routeinfo file
        rinfo_tree = ET.parse(
           '%s_%d.xml' % (routeinfo_prefix, it + 1)
        ) 
        
        full_trips = full_trips_in_window(first, last,
           '%s_%d.xml' % (routeinfo_prefix, it+1)
        )
        
        drv_average = 0
        num_veh = 0
        last_arrival = 0
        for vdata in rinfo_tree.getroot():
            if (not vdata.get('id') in full_trips): 
                continue
            
            tstart = float(vdata.get('depart'))
            time_when_arrived = float(vdata.get('arrival')) if vdata.get('arrival') != '' else last_arrival
            last_arrival = time_when_arrived
            
            edges = vdata[0].get('edges').split(' ')
            exit_times = vdata[0].get('exitTimes').split(' ')
            
            #route = edges
            
            normalized_time = 0
            for i in range(len(edges)):
                
                spent_time = float(exit_times[i]) - tstart
                
                max_time = (3.0 * road_net.getEdge(edges[i]).getLength()) / road_net.getEdge(edges[i]).getSpeed()
                
                #normalized_time = new_average(normalized_time, spent_time / max_time, i)
                normalized_time += spent_time / max_time
                
                tstart = float(exit_times[i])
            
            #driver normalized tt = sum_{i \in R} mean-norm-tt_i * |R|
             
                
            #adjust the overall average
            drv_average = new_average(drv_average, normalized_time, num_veh)
            num_veh += 1
            
        #prints the results for the i-th iteration
        print '%d%s%f' % ((it+1), separator, drv_average * factor) 
        ofile.write('%d%s%f\n' % ((it+1), separator, drv_average * factor))
    
def parse_args():
    
    parser = OptionParser()
            
    parser.add_option(
        '-o', '--output-prefix', type=str, default='normtt.csv',
        dest = 'output',
        help = 'the output file to be generated'
    )
    
    parser.add_option(
        '-n', '--netfile',
        help='the path to the road network file',
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
        '-r', '--routeinfo-prefix',
        help='the prefix for the routeinfo files: [prefix]_i.xml, where i is the iteration',
        type=str, default='routeinfo'
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
    
    parser.add_option(
        '--factor',
        help='the factor to multiply the normalized travel time (to scale accordingly to max road price',
        type=int, default=100
    )
    
    
    return parser.parse_args(sys.argv)


if __name__ == '__main__':
    (options, args) = parse_args()
    normalize(
        options.netfile, options.routeinfo_prefix, options.iterations, options.factor,
        options.begin, options.finish, options.separator, options.output
    )
    

