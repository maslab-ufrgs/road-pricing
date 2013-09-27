'''
DEPRECATED

Provides a class that inserts vehicles in the simulation until the load reaches
the desired level.

It requires the search module available at maslab-googlecode

'''
import random
import traci
import sys, os

#looks up on ../lib to import Guilherme's implementation of Dijkstra algorithm
path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lib', 'search'))
if not path in sys.path: sys.path.append(path)

import search

class DynamicLoadController(object):
    '''
    Inserts vehicles in the simulation until the 
    maximum allowed number of auxiliary vehicles is reached.
    New vehicles are inserted with random OD pairs.
    
    '''
    
    def __init__(self, road_network, max_drivers, 
                 aux_id_prefix = 'aux', exclude_prefix = None):
        '''
        Initializes the auxiliary load controller class
        
        :param road_network: the road network 
        :type road_network: sumolib.net.Net
        :param max_drivers: the maximum allowed number of auxiliary drivers 
        :type max_drivers: int
        :param aux_id_prefix: 
        :type aux_id_prefix: str
        :param exclude_prefix: exclude these drivers from being controlled
        :type exclude_prefix: string 

        '''
        
        self._road_net = road_network
        self._max_drv = max_drivers
        self._exclude_prefix = exclude_prefix
        self._aux_id_prefix = aux_id_prefix
        
        self._num_drv = 0
        self._insertions = 0
        
    def act(self):
        '''
        Must be called every timestep. Inserts vehicles in the simulation
        until the maximum allowed # of auxiliary vehicles is reached. 
        New vehicles are inserted with random OD pairs
        
        '''
        
        #checks how many vehicles are in the simulation
        num_veh = 0
        for veh_id in traci.vehicle.getIDList():
            if self._exclude_prefix is None or self._exclude_prefix not in veh_id:
                num_veh += 1
        
        #inserts vehicles until the maximum number is reached
        while num_veh < self._max_drv:
            
            
            #tries to insert a vehicle in a non-congested route for 100 times
            #if non-congested route is not found, inserts a vehicle in the last tried route
            congestedRoute = True
            numTries = 0
             
            while (congestedRoute and numTries < 100): 
                #if numTries > 0:
                #    print 'Congested! Retries: ', numTries
                orig = random.choice(self._road_net.getEdges()) 
                dest = random.choice(self._road_net.getEdges())
                
                #print '%.2f\t%.2f' % (origOcc, destOcc)
                
                theRoute = search.dijkstra(
                    self._road_net, 
                    orig, 
                    dest, None, True
                )
                #tries again if dest is not reachable from orig
                if theRoute is None:
                    continue
                
                #checks if any edge of the found route is congested 
                edges = [edge.getID().encode('utf-8') for edge in theRoute]
                
                congestedRoute = False
                for e in edges:
                    if traci.edge.getLastStepOccupancy(e) > 0.8:
                        congestedRoute = True
                        break #the inner loop
                
                numTries += 1
            
            veh_id = self._aux_id_prefix + str(self._insertions)
            traci.route.add(veh_id, edges)
            traci.vehicle.add(veh_id, veh_id, 
                              traci.vehicle.DEPART_NOW, 5.10, 0)
            self._insertions += 1
            num_veh += 1
            
        
        