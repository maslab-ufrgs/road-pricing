'''
This script can be used standalone or imported in another script.

As a standalone, it connects to a SUMO simulation and inserts vehicles
at every timestep until the road network load reaches the desired level.
User can specify how long the load should be controlled.

Each vehicle is inserted according to a given OD matrix.

When imported, the user can use the ODKeeper methods to control the load
and insert vehicles in the road network

This script requires the search module available at maslab-googlecode

Created on Jan 3, 2013

@author: anderson

'''
import os, sys
import random
import traci
import sumolib
from optparse import OptionParser
sys.path.append('..')
import odpopulator

#looks up on ../lib to import Guilherme's implementation of Dijkstra algorithm
path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'lib','search'))
if not path in sys.path: sys.path.append(path)
import search

class ODLoader(object):
    '''
    Vehicle loader that keeps the proportions defined in an OD matrix
    
    '''


    def __init__(self, road_net, od_matrix, num_veh = 900, max_per_action = 0, aux_prefix = 'aux',  
                 exclude_prefix = None, output = None):
        '''
        Initializes the od-loader
        
        :param road_net: the road network 
        :type road_net: sumolib.net.Net
        :param od_matrix: the OD matrix loaded with districts and trip information
        :type od_matrix: odmatrix.ODMatrix
        :param num_veh: the number of vehicles to be kept in the network
        :type num_veh: int
        :param max_per_action: the max. number of insertions per action of the controller
        :type max_per_action: int
        :param aux_prefix: the prefix of the vehicles created by the ODLoader
        :type aux_prefix: str
        :param exclude_prefix: the prefix of the vehicle ID's to be discounted while checking the total
        :type exclude_prefix: str
        :param output: the file to write the generated demand
        :type output: str
        
        '''
        self._road_net = road_net
        self._od_matrix = od_matrix
        self._num_veh = num_veh
        self._max_per_action = max_per_action
        self._aux_prefix = aux_prefix
        self._exclude_prefix = exclude_prefix
        self._output = output
        
        self._insertions = 0
        self._started_trips = []
        self._count_complete_trips = -1
        self._complete_trips = 0
        
        self._steady_duration = 0
        self._steady_timesteps = -1
        
        self._complete_trips_per_ts = []
        
        self._launched_vehicles = {}
        
    def set_steady_duration(self, duration):
        '''
        Sets how many timesteps the loader will keep the 
        number of vehicles in the desired number
        
        '''
        self._steady_duration = duration
        
    def is_steady_duration_finished(self):
        '''
        Returns whether the duration of the network in steady
        state has finished
        
        '''
        return self._steady_timesteps >= self._steady_duration
        
    def act(self):
        '''
        Must be called every timestep (or in regular intervals of time)
        to ensure that the load on the network will be steady
        
        '''
        
        if self.is_steady_duration_finished():
            print 'Warning: steady duration of network has finished'
            return
        
        #saves data of vehicles that just departed
        thisTs = traci.simulation.getCurrentTime() / 1000
        for drvid in traci.simulation.getDepartedIDList():
            if self._exclude_prefix is not None and self._exclude_prefix in drvid:
                continue
            
            self._launched_vehicles[drvid] = {
               'depart': thisTs,
               'route': traci.vehicle.getRoute(drvid)
            }
            
        #counts the vehicles without the exclude prefix that are in the network
        num_veh = 0
        for veh_id in traci.vehicle.getIDList():
            if self._exclude_prefix is None or self._exclude_prefix not in veh_id:
                num_veh += 1
        
        inserted_this_ts = 0
        
        if self._count_complete_trips == -1 and num_veh >= self._num_veh:
            self._count_complete_trips = traci.simulation.getCurrentTime() / 1000
            self._steady_timesteps = 0
            
        if self._count_complete_trips > 0:
            self._started_trips += traci.simulation.getDepartedIDList()
            self._steady_timesteps += 1
            
            for arvd in traci.simulation.getArrivedIDList():
                if arvd in self._started_trips:
                    self._started_trips.remove(arvd)
                    self._complete_trips += 1
                    
            self._complete_trips_per_ts.append(
               ((traci.simulation.getCurrentTime() / 1000), self._complete_trips)
            )
                    
        #inserts vehicles until the maximum number is reached
        #or the maximum insertions per timestep is reached
        while num_veh < self._num_veh:
            
            if self._max_per_action != 0 and inserted_this_ts >= self._max_per_action:
                break
            
            (orig_taz, dest_taz) = self._od_matrix.select_od_taz()
            orig_edg = self._road_net.getEdge(orig_taz.select_source()['id'])
            dest_edg = self._road_net.getEdge(dest_taz.select_sink()['id']) 
            
            theRoute = search.dijkstra(
                self._road_net, 
                orig_edg, 
                dest_edg, None, True
            )
            #tries again if dest is not reachable from orig
            if theRoute is None:
                continue
            
            edges = [edge.getID().encode('utf-8') for edge in theRoute]
            
            veh_id = self._aux_prefix + str(self._insertions)
            traci.route.add(veh_id, edges)
            traci.vehicle.add(veh_id, veh_id, 
                              traci.vehicle.DEPART_NOW, 5.10, 13)
            
            self._insertions += 1
            inserted_this_ts += 1
            num_veh += 1
            
    def writeOutput(self):
        '''
        Writes the stored drivers into an output file
        
        '''
        #print 'Writing output...'
        
        if self._output is None:
            print 'Error: no valid file to write.'
            return
        
        #sort drivers by departure time
        drvKeys = sorted(self._launched_vehicles, key=lambda x: (self._launched_vehicles[x]['depart'], x))
        #try:
        outfile = open(self._output, 'w')
            
        outfile.write('<routes>\n')
            
        for key in drvKeys:
            outfile.write('    <vehicle id="%s" depart="%d">\n' % (key, self._launched_vehicles[key]['depart']))
            outfile.write('        <route edges="%s" />\n' % ' '.join(self._launched_vehicles[key]['route']))
            outfile.write('    </vehicle>\n')
            
        outfile.write('</routes>')

class UniformLoader(ODLoader):
    '''
    Simple vehicle loader that assumes an uniform distribution
    of origins and destinations among the edges (no need to pass
    an od matrix with such distribution)
    
    '''
    
    def act(self):
        thisTs = traci.simulation.getCurrentTime() / 1000
        num_veh = 0
        for veh_id in traci.vehicle.getIDList():
            if self._exclude_prefix is None or self._exclude_prefix not in veh_id:
                num_veh += 1
        
        inserted_this_ts = 0
        
        if self._count_complete_trips == -1 and num_veh >= self._num_veh:
            self._count_complete_trips = traci.simulation.getCurrentTime() / 1000
            self._steady_timesteps = 0
            
        if self._count_complete_trips > 0:
            self._started_trips += traci.simulation.getDepartedIDList()
            self._steady_timesteps += 1
        
        for drvid in traci.simulation.getDepartedIDList():
            if self._exclude_prefix is not None and self._exclude_prefix in drvid:
                continue
            
            self._launched_vehicles[drvid] = {
               'depart': thisTs,
               'route': traci.vehicle.getRoute(drvid)
            }
        
        #inserts vehicles until the maximum number is reached
        #or the maximum insertions per timestep is reached
        while num_veh < self._num_veh:
            
            if self._max_per_action != 0 and inserted_this_ts >= self._max_per_action:
                break
            
            congestedRoute = True
            numTries = 0
            while (congestedRoute and numTries < 100): #try to distribute load
            
                #(orig_taz, dest_taz) = self._od_matrix.select_od_taz()
                orig_edg = random.choice(self._road_net._edges) 
                dest_edg = random.choice(self._road_net._edges) 
                
                theRoute = search.dijkstra(
                    self._road_net, 
                    orig_edg, 
                    dest_edg, None, True
                )
                #tries again if dest is not reachable from orig
                if theRoute is None:
                    continue
                
                edges = [edge.getID().encode('utf-8') for edge in theRoute]
                
                congestedRoute = False
                for e in edges:
                    if traci.edge.getLastStepOccupancy(e) > 0.7:
                        congestedRoute = True
                        break #the inner loop
                
                numTries += 1
                
            veh_id = self._aux_prefix + str(self._insertions)
            traci.route.add(veh_id, edges)
            traci.vehicle.add(veh_id, veh_id, 
                              traci.vehicle.DEPART_NOW, 0, 13)
            
            self._insertions += 1
            inserted_this_ts += 1
            num_veh += 1
                
if __name__ == "__main__":
    optParser = OptionParser()
    
    optParser.add_option("-n", "--net-file", dest="netfile",
                            help="road network file (mandatory)")
    optParser.add_option("-t", "--taz-file", dest="tazfile",
                            help="traffic assignment zones definition file (mandatory)")
    optParser.add_option("-m", "--odm-file", dest="odmfile",
                            help="OD matrix trips definition file (mandatory)")
    optParser.add_option("-l", "--limit-per-ts", type='int', dest="max_per_ts", default=0,
                            help="Limit the number of vehicles to be inserted at each timestep")
    optParser.add_option("-o", "--output", type='str', default=None,
                         help="route file to be generated with the data of drivers inserted by odloader")
    optParser.add_option("-d", "--driver-number", type="int", dest="numveh",
                         default=1000, help="desired number of drivers to keep")
    optParser.add_option("-b", "--begin", type="int", default=0, help="begin time")
    optParser.add_option("-e", "--end", type="int", default=7200, help="end time")
    optParser.add_option("--duration", type="int", default=0, help="duration of control")
    optParser.add_option("-p", "--port", type="int", default=8813, help="TraCI port")
    optParser.add_option("-x", "--exclude", type="string", default=None, dest='exclude',
                         help="Exclude replacing drivers whose ID have the given value")
    optParser.add_option('-u', '--uniform', action='store_true', default=False,
                         help = 'use uniform OD distribution instead of OD files')
    #optParser.add_option("-s", "--seed", type="int", help="random seed")
    optParser.add_option("-s", "--steady-output", type="string", dest="steadyout",
                         help="the file where the timestep vs #full trips with steady network will be written")
    
    (options, args) = optParser.parse_args()
    
    net = sumolib.net.readNet(options.netfile)
    
    traci.init(options.port)
    
    drivers = {} #stores drivers information when they depart
    
    if options.begin > 0:
        print 'Skipping %d timesteps.' % options.begin
        traci.simulationStep(options.begin * 1000)
        
    print 'From ts %d to %d, will replace vehicles' % (options.begin, options.end)
    
    #creates the odloader and initializes it with the drivers already recorded
    if options.uniform:
        loadkeeper = UniformLoader(
           net, None, options.numveh, options.max_per_ts, 'aux', options.exclude, options.output
        )
    else:
        od_matrix = odpopulator.generate_odmatrix(options.tazfile, options.odmfile)
        loadkeeper = ODLoader(
            net, od_matrix, options.numveh, 
            options.max_per_ts, 'aux', options.exclude, options.output
        )
    if options.duration:
        loadkeeper.set_steady_duration(options.duration)
    
    for i in range(options.begin, options.end):
        traci.simulationStep()
        
        if loadkeeper.is_steady_duration_finished():
            break
        
        loadkeeper.act()
    
    print 'OD Loader counted %d complete trips during peak demand which started at %d' %\
     (loadkeeper._complete_trips, loadkeeper._count_complete_trips)
    
    print 'Writing timesteps vs. fulltrips...'
    outstream = open(options.steadyout, 'w') if options.steadyout else sys.stdout
    
    for i in loadkeeper._complete_trips_per_ts:
        outstream.write("%d %d\n" % (i[0], i[1]))
        
    if options.output is not None:
        print 'Writing output route file...'
        loadkeeper.writeOutput()
        
    print 'Now, simulating until all drivers leave the network'
    while (True): #simulates the remaining steps till the end
        traci.simulationStep()
        if len(traci.vehicle.getIDList()) == 0:
            break
        
    traci.close()
    
    print 'DONE.'
        
    