'''
drivers module

Provides functions to parse files specifying drivers' attributes.
Also provides classes and functions related to drivers representation

Created on 12/11/2012

@author: artavares

'''
import sumolib
import traci
import sys
import os
import xml.etree.ElementTree as ET

#looks up on ../lib to import Guilherme's implementation of Dijkstra algorithm
path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lib', 'search'))
if not path in sys.path: sys.path.append(path)

from search import dijkstra

def parse_drivers(filename, road_net):
    '''
    Returns a list with the drivers from the file.
    
    :param filename: the path to the drivers' file
    :type filename: string
    return: a list with drivers
    :rtype: list
    
    '''
    
    lines = open(filename,'r').readlines()
    drivers = []
    for l in lines:
        if l[0] != '#': 
            attributes = l.split(' ')
            drivers.append(Driver(
                attributes[0], #id
                road_net,
                road_net.getEdge(attributes[1]), #origin
                road_net.getEdge(attributes[2]), #destination
                int(attributes[3]), #depart
                float(attributes[4]) #preference
            ))
                           
    return drivers


def update_kb(drivers, net_mgmt, route_info_file):
    '''
    Updates the drivers knowledge base
    using the information from route_info_file
    
    '''
    #pre-parse the file, disregarding the commented lines =/
    f = open(route_info_file)
    lines = f.readlines()
    f.close()
    #del lines[3]
    while not lines[0].startswith("<routes>"):
        del lines[0]
    
    f = open(route_info_file,'w')
    for l in lines:
        f.write(l)
    f.close()
    #finish pre-parsing =/
    
    tree = ET.parse(route_info_file)
    drivers_dict = dict((d.driver_id, d) for d in drivers)
    last_arrival = 0 #for glitch-fixing
    for vehicle in tree.getroot():
        
        d = drivers_dict[vehicle.get('id')]
        
        tstart = float(vehicle.get('depart'))
        d._time_when_departed = tstart
        d._time_when_arrived = float(vehicle.get('arrival')) if vehicle.get('arrival') != '' else last_arrival
        last_arrival = d._time_when_arrived
        edges = vehicle[0].get('edges').split(' ')
        exit_times = vehicle[0].get('exitTimes').split(' ')
        
        d._route = edges
        
        for i in range(len(edges)):
            spent_time = float(exit_times[i]) - tstart
            edge_price = net_mgmt.manager_of_link(edges[i]).price
            
            d.set_known_travel_time(edges[i], spent_time) 
            d.set_known_price(edges[i],  edge_price)
            d._trip_expenses += edge_price
            
            tstart = float(exit_times[i])


def _save_attr_to_file(self, net, drivers, filename, getter):
        '''
        Saves one attribute of the drivers regarding the road network to a file in the format:
        drv\road,road1,road2,...
        drv1,val1-1,val1-2,...
        drv2,val2-1,val2-2,...
        
        '''
        outfile = open(filename, 'w')
        
        #writes the file header
        outfile.write('drv_id\\road_id,' + ','.join([e.getID() for e in net.getEdges()]) + '\n')
        
        #writes the file data
        for d in drivers:
            outfile.write(d.driver_id + ',')
            outfile.write(','.join([str(getter(d,e.getID())) for e in net.getEdges()]) + '\n')
        outfile.close()
        
def _load_data(self, drivers, filename, setter):
        '''
        Loads data of drivers regarding the road network from a file in the format:
        drv\road,road1,road2,...
        drv1,50,60,...
        drv2,55,67,...
        
        '''
        #makes a dict {id: driver,...} from the list of drivers
        drvdict = dict((d.getId(), d) for d in drivers)
        
        indata = open(filename).readlines()
        #edges ids are in the first row, from 2nd col onwards 
        edges = indata[0].strip().split(',')[1:]
        for line in indata[1:]:
            #removes the new line and splits the csv into a list
            line_spl = line.strip().split(',')
            
            #drv id is in 1st col and edge data are from 2nd col onwards in each line
            drv_id = line_spl[0]
            edg_data = line_spl[1:]
            
            #writes the edge data into each edge of driver knowledge base
            for i in range(len(edges)):
                setter(drvdict[drv_id], edges[i], float(edg_data[i]))
            

def _open_file(file_or_filename):
    '''
    Checks if given parameter is a file or a filename and returns an 
    actual file if a filename is given
    :param file_or_filename: the variable to be checked
    :type file_or_filename: file|string
    return: file object
    :rtype: file
    '''
    
    #if is string, returns the file with the given filename
    if isinstance(file_or_filename,str):
        return open(file_or_filename, 'w')
    
    #if not, assumes that it is a file object and returns it
    return file_or_filename

class KBLoader(object):
    def __init__(self, prc_file, tt_file):
        '''
        Initializes knowledge base loader
        
        :param prc_file: the file object or the string with the file name to load prices
        :type prc_file: file|string
        :param tt_file: the file object or the string with the file name to load travel times
        :type tt_file: file|string
        
        '''
        self._prc_file = prc_file
        self._tt_file = tt_file
        
        self._timestep = -1
        self._iteration = -1
        
    def load(self, drivers):
        '''
        Loads knowledge base of drivers
        :param drivers: the list of drivers
        :type drivers: list
        
        '''
        #creates a dict from the list
        self._drivers = {}
        
        for d in drivers:
            self._drivers[d.driver_id] = d
            
        self._load_prices()
        self._load_travel_times()
        
        return drivers
    
    def _load_prices(self):
        self._prc_file = _open_file(self._prc_file)
        self._load_content(self._prc_file, 'set_known_price')
    
    def _load_travel_times(self):
        self._load_content(_open_file(self._tt_file), 'set_known_travel_time')
    
    def _load_content(self, the_file, attribute):
        '''
        Reads the given attribute and stores it in the drivers
        :param the_file: file to read from
        :type the_file: file
        :param attribute: the name of driver's attribute that will loaded
        :type attribute: string
        
        '''
        
        lines = the_file.readlines()
        
        #first line is the iteration and second is the timestep
        file_it = int(lines[0])
        file_ts = int(lines[1])
        
        if self._iteration > -1 and self._iteration != file_it:
            print 'WARNING: iteration from current file is different from the previously stored.'
        if self._timestep > -1 and self._timestep != file_ts:
            print 'WARNING: timestep from current file is different from the previously stored.'
        
        #reads the header (3rd line of file - contains edge IDs)
        #rstrip removes the trailing \n which was causing errors
        edg_ids = lines[2].rstrip().split(',') 
        
        #4th line onwards are the driver's data
        for line in lines[3:]:
            line_array = line.split(',')
            
            #finds which driver should have the data loaded
            d = self._drivers[line_array[0]] #1st column is drv ID
            method = getattr(d, attribute)
            for i in range(1,len(line_array)): #skips 1st col
                method(edg_ids[i], line_array[i]) #loads the data
            


class KBSaver(object):
    
    def __init__(self, drivers, road_net, prc_file, tt_file):
        '''
        Initializes knowledge base saver
        
        :param drivers: the list of drivers
        :type drivers: list
        :param road_net: the road network
        :type road_net: sumolib.net.Net
        :param prc_file: the file object or the string with the file name to save prices
        :type prc_file: file|string
        :param tt_file: the file object or the string with the file name to save travel times
        :type tt_file: file|string
        
        '''
        self._drivers = drivers
        self._road_net = road_net
        self._prc_file = prc_file
        self._tt_file = tt_file
    
    def save(self, iteration, timestep):
        '''
        Saves known prices and travel times
        
        :param iteration: the number of the iteration when save was called
        :type iteration: int
        :param timestep: the number of the timestep when save was called
        :type timestep: int
        
        '''
        self._save_prices(iteration, timestep)
        self._save_travel_times(iteration, timestep)
    
    def _save_prices(self, iteration, timestep):
        '''
        Saves known prices
        
        :param iteration: the number of the iteration when save was called
        :type iteration: int
        :param timestep: the number of the timestep when save was called
        :type timestep: int
        
        '''
        
        #checks if prices file is an actual file or the filename (opens a file in this case)
        self._prc_file = _open_file(self._prc_file)
        self._write_header(self._prc_file, iteration, timestep)
        self._write_content(self._prc_file, 'known_price')
        
    def _save_travel_times(self, iteration, timestep):
        '''
        Saves known travel times
        
        :param iteration: the number of the iteration when save was called
        :type iteration: int
        :param timestep: the number of the timestep when save was called
        :type timestep: int
        
        '''
        
        self._tt_file = _open_file(self._tt_file)
        self._write_header(self._tt_file, iteration, timestep)
        self._write_content(self._tt_file, 'known_travel_time')
        
    
    def _write_header(self, the_file, iteration, timestep):
        '''
        Writes iteration, timestep and IDs of edges in the given file
        :param iteration: 
        :type iteration: int
        :param timestep: 
        :type timestep: int
        
        '''
        
        #writes iteration in first and timestep in second line    
        the_file.write("%d\n%d\n" % (iteration, timestep))
        
        line_array = ['drv_id\edg_id']
        for e in self._road_net.getEdges():
            line_array.append(e.getID())
        
        the_file.write(','.join(line_array) + '\n')
        
    def _write_content(self, the_file, attribute):
        '''
        Writes the given attribute, for all drivers and edges
        :param the_file: file to write into
        :type the_file: file
        :param attribute: the name of driver's attribute that will be written
        :type attribute: string
        
        '''
        
        for d in self._drivers:
            method = getattr(d, attribute)
            line_array = [d.driver_id] 
            for e in self._road_net.getEdges():
                line_array.append(str(method(e)))
            
            the_file.write(','.join(line_array) + '\n')
                 
        
    

class Driver(object):
    '''
    Represents a driver
    
    '''
    
    DEPART_POS = 5.10 #in this position, vehicle starts in edge's beginning
    NOT_ARRIVED = -1
    NOT_DEPARTED = -1

    _route = []
    
    _trip_number = -1

    def __init__(self, drv_id, road_network, origin, destination, depart=0,
                 preference=1, prc_init=None, tt_init=None):
        '''
        Initializes properties and the knowledge bases
        
        :param drv_id: driver identifier
        :type drv_id: string
        :param road_network: road network object
        :type road_network: sumolib.net.Net
        :param origin: driver's origin edge
        :type origin: sumolib.net.Edge
        :param destination: driver's destination edge
        :type destination: sumolib.net.Edge
        :param depart: driver's departure time
        :type depart: int
        :param preference: driver's preference coefficient (weigths travel time vs. price)
        :type preference: float
        :param prc_init: driver's price initialization function
        :type prc_init: function
        :param tt_init: driver's travel time initialization function
        :type tt_init: function
        
        '''
        self._driver_id = drv_id
        self._origin = origin
        self._destination = destination
        self._road_network = road_network
        self._depart_time = depart
        
        self._trip_expenses = 0 #credits spent in one trip
        self._total_expenses = 0 #credits spent in all trips
        
        self._knownprices = {}
        self._knownTT = {}
       
        self._length_of_traversed_edges = 0
        self._last_timestep_edge_id = None
        self._current_edge_id = None
        
        #self._arrived = False
        self._time_when_departed = self.NOT_DEPARTED
        self._time_when_arrived = self.NOT_ARRIVED
        self._time_spent_on_last_edge = 0
        self._entry_time = 0
        
        if preference < 0 or preference > 1:
            raise ValueError('Driver\'s preference must be on the interval [0:1]')
        self._preference = preference
        
        #uses default price initialization if none was provided
        for edge in self._road_network.getEdges():
            #initializes known prices and travel times. 
            #uses default initialization if no init function was given
            
            if prc_init is not None:
                self._knownprices[edge.getID()] = prc_init(edge.getID())
            else:
                self._knownprices[edge.getID()] = 50 #half of max price
                
            if tt_init is not None:
                self._knownTT[edge.getID()] = tt_init(edge.getID())
            else:
                self._knownTT[edge.getID()] = float(edge.getLength()) / edge.getSpeed() 
                #initializes with free-flow travel time 
                #casts first term to float to prevent integer division
            
        
    @property
    def driver_id(self):
        return self._driver_id
    
    @property
    def origin(self):
        return self._origin
    
    @property
    def destination(self):
        return self._destination
    
    @property
    def preference(self):
        return self._preference
    
    @property
    def route(self):
        return self._route
    
    @property
    def trip_number(self):
        return self._trip_number
    
    @property
    def depart_time(self):
        return self._depart_time
    
    @property 
    def arrived(self):
        return self._time_when_arrived != self.NOT_ARRIVED
    
    @property
    def departed(self):
        return self._time_when_departed != self.NOT_DEPARTED
    
    @property 
    def average_speed(self):
        '''
        Returns the driver's speed in m/s
        
        '''
        return float(self.traversed_distance) / self.travel_time
    
    @property
    def traversed_distance(self):
        '''
        Returns the distance, in meters, that this driver traversed so far.
        When the trip is finished it reports the sum of lengths of all traversed edges
        assuming that it is removed at the end of an edge
        
        '''
        
        traversed_distance = self._length_of_traversed_edges 
        
        if not self.arrived:
            traversed_distance += traci.vehicle.getLanePosition(self._driver_id)
        
        return traversed_distance
    
    @property
    def travel_time(self):
        '''
        Returns the time, in SUMO time units, that this driver spent on trip
        
        '''
        
        if not self.departed:
            return self.NOT_DEPARTED
        
        the_time = self._time_when_arrived if self.arrived else traci.simulation.getCurrentTime()
        
        #/1000 commented to unbug with the new approach
        return (the_time - self._time_when_departed) #/ 1000.0 
    
    @property
    def norm_travel_time(self, factor = 100):
        '''
        Returns the normalized travel time that this driver spent on trip
        i.e.: the sum of normalized travel times for each link in driver's route
        must be used only after driver has finished its trip
        Normalized time is scaled by a factor (default=100)
        
        '''
        if not self.departed:
            return self.NOT_DEPARTED
        
        if not self.arrived:
            return self.NOT_ARRIVED
        
        return sum([self.norm_known_travel_time(edg, factor) for edg in self.route])
            
    @property
    def trip_expenses(self):
        return self._trip_expenses
    
    @property
    def perceived_trip_cost(self):
        '''
        Returns the cost this driver perceives for the trip.
        It is related to the spent travel time, credits 
        expenditure and driver preference
        
        '''
        
        return self._preference * self.travel_time +\
             (1 - self._preference) * self.trip_expenses
    
    @property
    def current_edge_id(self):
        return self._current_edge_id
    
    @property
    def total_expenses(self):
        return self._total_expenses
    
    def pay_credits(self, ammount):
        '''
        Stores the ammount in the driver expenses
        
        '''
        self._trip_expenses += ammount 
        self._total_expenses += ammount
                
    
    def has_changed_link(self):
        '''
        Returns true if driver has moved to a new link in the current timestep
        
        '''
        return self._current_edge_id != self._last_timestep_edge_id
    
    def on_depart(self):
        '''
        Action to be performed when vehicle enters the simulation
        
        '''
        self._time_when_departed = traci.simulation.getCurrentTime()
        traci.vehicle.setColor(self.driver_id, [255, 0, int(255 * self.preference), 0])
        #print '%s: departed' % self._driver_id
        
        
    def on_arrive(self):
        '''
        Action to be performed when driver finishes its trip. Updates traversed
        distance, travel time and flags vehicle with trip finished
        
        '''
        self._arrived = True
        self._time_when_arrived = traci.simulation.getCurrentTime()
        self._current_edge_id = None
        
        #updates known travel time of last edge
        self._time_spent_on_last_edge = traci.simulation.getCurrentTime() - self._entry_time 
        
        #updates traversed distance and knowledge base if last edge is valid (avoids errors at departure)
        self._length_of_traversed_edges += traci.lane.getLength(self._last_timestep_edge_id + '_0')
            
        self.set_known_travel_time(self._last_timestep_edge_id, 
                                       self._time_spent_on_last_edge / 1000)
         
        #print '%s: arrived' % self._driver_id
        
    def on_timestep(self):
        '''
        Must be called every timestep. Updates driver status.
        
        '''
        
        #updates the edge occupied by the vehicle in last timestep
        self._last_timestep_edge_id = self._current_edge_id
        
        #do nothing if has not yet departed or has already arrived
        if not self.departed or self.arrived:
            return
        
        if self.arrived:
            print 'ARRIVED!', traci.vehicle.getRoadID(self.driver_id)
        
        #updates edge of vehicle in the current timestep
        self._current_edge_id = traci.vehicle.getRoadID(self.driver_id)
        
        
        #check if vehicle has changed its edge...
        if self.has_changed_link():# self._current_edge_id != self._last_timestep_edge_id:
                
            #calculates travel time spent on last edge
            self._time_spent_on_last_edge = traci.simulation.getCurrentTime() - self._entry_time
            
            #stores entry time in curr. edge
            self._entry_time = traci.simulation.getCurrentTime()
            
            #updates traversed distance and knowledge base if last edge is valid (avoids errors at departure)
            if self._last_timestep_edge_id is not None:
                self._length_of_traversed_edges += traci.lane.getLength(self._last_timestep_edge_id + '_0')
                
                self.set_known_travel_time(self._last_timestep_edge_id, 
                                           self._time_spent_on_last_edge / 1000)
                
                # print 'LTE:', self._last_timestep_edge_id, 'TSOLE:', self._time_spent_on_last_edge, '/ KTT-e2:', self.known_travel_time('e2'), '/ ET:', self._entry_time 
            
                #stores price in knowledge base
                pass #ACTUALLY, SYSTEM MAKES DRIVER PAY CREDITS
                
    def get_edge_ID(self, edge_or_id):
        """
        Checks if given parameter is edge or the actual ID 
        and returns the actual ID
        :param edge_or_id: edge object or string
        :type edge: sumolib.net.Edge|string
        :return: the edge ID
        :rtype: string
        
        """
        
        #if is string, assumes that it contains the ID and returns it
        if isinstance(edge_or_id, str):
            return edge_or_id
        
        #else, assumes that it is an Edge and returns the ID
        return edge_or_id.getID()
    
    def known_price(self, edge):
        '''
        Returns the known price of the given edge
        :param edge: the given edge (or its id)
        :type edge: sumolib.net.Edge|str
        :return: the known price
        :rtype: int
        
        '''
        return self._knownprices[self.get_edge_ID(edge)]
    
    def known_travel_time(self, edge):
        '''
        Returns the known travel time of the given edge
        :param edge: the given edge (or its id)
        :type edge: sumolib.net.Edge|str
        :return: the known travel time
        :rtype: float
        
        '''
        return self._knownTT[self.get_edge_ID(edge)]
    
    def norm_known_travel_time(self, edge, factor=100):
        '''
        Returns the known travel time of the given edge
        normalized by 3*fftt
        :param edge: the given edge (or its id)
        :type edge: sumolib.net.Edge|str
        :return: the known travel time
        :rtype: float
        
        '''
        eid = self.get_edge_ID(edge)
        edg = self._road_network.getEdge(eid)
        
        max_time = (3.0 * edg.getLength()) / edg.getSpeed()
            
        return factor * self._knownTT[eid] / max_time
    
    def set_known_travel_time(self, edge_or_id, travel_time):
        '''
        Changes the known travel time for a given edge
        :param edge: the given edge (or string with the id)
        :type edge: sumolib.net.Edge|string
        :param travel_time: the travel time to be stored
        :type travel_time: float
        :return: this driver (self)
        :rtype: Driver
        
        '''
        
        self._knownTT[self.get_edge_ID(edge_or_id)] = float(travel_time)
        return self
    
    
    def set_known_price(self, edge_or_id, price):
        '''
        Changes the known price for a given edge
        :param edge: the given edge (or string with the id)
        :type edge: sumolib.net.Edge|string
        :param price: the price to be stored
        :type price: int
        :return: this driver (self)
        :rtype: Driver
        
        '''
        self._knownprices[self.get_edge_ID(edge_or_id)] = int(price)
        return self
        
    def edge_cost(self, edge):
        '''
        Returns the cost for traversing the given edge. The cost is 
        a function of the preference coefficient and the known
        cost and travel time
        :param edge: the given edge
        :type edge: sumolib.net.Edge
        :return: the cost
        :rtype: float
        
        '''
        return self._preference * self.norm_known_travel_time(edge) +\
               (1 - self._preference) * self.known_price(edge)
    
    def reset(self):
        '''
        Resets driver status data.
        To be called when a new iteration starts
        
        '''
        #resets attributes
        self._arrived = False
        
        self._length_of_traversed_edges = 0
        self._last_timestep_edge_id = None
        self._current_edge_id = None
        
        self._time_when_departed = self.NOT_DEPARTED
        self._time_when_arrived = self.NOT_ARRIVED
        self._time_spent_on_last_edge = 0
        self._entry_time = 0
        
        self._trip_expenses = 0    
    
    def prepare_next_trip(self, depart_offset=0):
        '''
        Increments the trip counter, calculates a new route and
        registers it via traci
        :param depart_offset: offset to add in departure time
        :type depart_offset: int
        :return: this driver (self)
        :rtype: Driver
        
        '''
        
        self._trip_number += 1
        the_route = dijkstra(self._road_network,
                             self._origin, 
                             self._destination,
                             lambda edge: self.edge_cost(edge))
        self._route = [edg.getID().encode('utf-8') for edg in the_route]
        trip_ID = self._driver_id #+ '_' + str(self._trip_number)
        traci.route.add(trip_ID, self._route)
        #traci.vehicle.setRoute(d.getId(), edges)
        traci.vehicle.add(
            trip_ID, trip_ID, self._depart_time + depart_offset, 
            self.DEPART_POS, 0
        )
        
        #print '%s: trip prepared' % self._driver_id
        return self
    

    
