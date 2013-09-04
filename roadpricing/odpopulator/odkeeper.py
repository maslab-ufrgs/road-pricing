'''
Created on Jan 12, 2013

@author: anderson
'''
import traci, sumolib
import os, sys
from optparse import OptionParser

sys.path.append('..')
import odpopulator

#looks up on ../lib to import Guilherme's implementation of Dijkstra algorithm
path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'lib'))
if not path in sys.path: sys.path.append(path)
import search

class ODKeeper(object):
    '''
    Keeps the load in the road network by replacing vehicles who leave
    with new ones, respecting the proportions defined in an OD matrix
    '''


    def __init__(self, road_net, od_matrix, num_veh = 900, max_per_action = 0, aux_prefix = 'aux',  
                 exclude_prefix = None):
        '''
        Initializes the od-keeper
        
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
        
        '''
        self._road_net = road_net
        self._od_matrix = od_matrix
        self._num_veh = num_veh
        self._max_per_action = max_per_action
        self._aux_prefix = aux_prefix
        self._exclude_prefix = exclude_prefix
        self._insertions = 0
    
    def act(self):
        '''
        Must be called at each timestep. Stores the drivers that departed for 
        writing them later in an output file
        
        '''
        
        thisTs = traci.simulation.getCurrentTime() / 1000

        #does nothing if we have more vehicles than the desired number
        if len(traci.vehicle.getIDList()) > self._num_veh:
            return
        
        for vehId in traci.simulation.getArrivedIDList():
            
            if self._exclude_prefix is not None and self._exclude_prefix in vehId:
                continue

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
            
            vehId = str(thisTs) + '-' + vehId
            traci.route.add(vehId, edges)
            traci.vehicle.add(vehId, vehId, traci.vehicle.DEPART_NOW, 5.10, 0)
            
            #print '%s\t%s\t%d' % (orig.getID(), dest.getID(), traci.simulation.getCurrentTime() / 1000)
        
            #print ['%.2f' % traci.edge.getLastStepOccupancy(e) for e in edges], traci.simulation.getCurrentTime() / 1000


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
#    optParser.add_option("-r", "--route-file", dest="routefile",
#                         help="route file to be generated")
    optParser.add_option("-d", "--driver-number", type="int", dest="numveh",
                         default=1000, help="desired number of drivers to keep")
    optParser.add_option("-b", "--begin", type="int", default=0, help="begin time")
    optParser.add_option("-e", "--end", type="int", default=7200, help="end time")
    optParser.add_option("-p", "--port", type="int", default=8813, help="TraCI port")
    optParser.add_option("-x", "--exclude", type="string", default=None, dest='exclude',
                         help="Exclude replacing drivers whose ID have the given value")
    #optParser.add_option("-s", "--seed", type="int", help="random seed")
    
    (options, args) = optParser.parse_args()
#    if not options.netfile or not options.routefile:
#        optParser.print_help()
#        sys.exit()
    
    net = sumolib.net.readNet(options.netfile)
    
    traci.init(options.port)
    
    drivers = {} #stores drivers information when they depart
    
    if options.begin > 0:
        print 'Skipping %d timesteps.' % options.begin
        traci.simulationStep(options.begin * 1000)
        
#        for drvid in traci.simulation.getDepartedIDList():
#            drivers[drvid] = {
#               'depart': traci.simulation.getCurrentTime() / 1000,
#               'route': traci.vehicle.getRoute(drvid)
#            }
    
    print 'From ts %d to %d, will replace vehicles' % (options.begin, options.end)
    
    #creates the odloader and initializes it with the drivers already recorded
    od_matrix = odpopulator.generate_odmatrix(options.tazfile, options.odmfile)
    loadkeeper = ODKeeper(net, od_matrix, options.numveh, options.max_per_ts, 'aux', options.exclude)
    
    for i in range(options.begin, options.end):
        traci.simulationStep()
        loadkeeper.act()
    
    print 'Now, simulating until all drivers leave the network'
    while (True): #simulates the remaining steps till the end
        traci.simulationStep()
        if len(traci.vehicle.getIDList()) == 0:
            break
        
    traci.close()
    
    print 'DONE.'
        
            