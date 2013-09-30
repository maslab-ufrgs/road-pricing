'''
Created on 12/11/2012

@author: artavares
'''
import unittest
import os
import sys
import traci
import StringIO
from sumomockup.roadnetpatch import MyEdge, MyRoadNetwork
import sumomockup.tracipatch as tracipatch

#TODO remove this by installing the module in PYTHONPATH
sys.path.append(os.path.join('..','roadpricing'))

from drivers import Driver, parse_drivers, KBSaver, KBLoader

class Test(unittest.TestCase):
    
    def setUp(self):
        '''
        Activates the monkey patches for traci methods
        
        '''
        
        traci.route.add = my_traci_route_add
        traci.vehicle.add = my_traci_vehicle_add
        
        #netpatch = 
        patch = tracipatch.TraCIReplacement(MyRoadNetwork())
        patch.perform_patch()

    def test_driver_creation_with_wrong_pref(self):
        '''
        Makes sure that an error is thrown when creating a 
        driver with preference < 0 or > 1
        
        '''
        with self.assertRaises(ValueError):
            d = Driver('id', MyRoadNetwork(), None, None, 0, -0.1)
            
        with self.assertRaises(ValueError):
            d = Driver('id', MyRoadNetwork(), None, None, 0, 1.1)
            
    def test_KB_std_init(self):
        '''
        Tests the standard initialization of known price and 
        travel time for the drivers
        
        '''
        road_net =  MyRoadNetwork()
        d = Driver('id', road_net, None, None)
        
        for e in road_net.getEdges():
            self.assertEqual(10, d.known_travel_time(e))
            self.assertEqual(50, d.known_price(e))
            
    def test_KB_custom_init(self):
        '''
        Tests customized initialization of known price and
        travel time of the drivers. Creates a simple function
        that returns a fixed value and compares if this value
        was inserted into driver's knowledge base (KB)
        
        '''
        road_net =  MyRoadNetwork()
        
        tt_func = lambda(edg): 99
        prc_func = lambda(edg): 11
        
        d = Driver('id', road_net, None, None, 0, 1, prc_func, tt_func)
        
        for e in road_net.getEdges():
            self.assertEqual(99, d.known_travel_time(e))
            self.assertEqual(11, d.known_price(e))
            
            
    def test_get_edge_ID(self):
        '''
        Tests if get_edge_ID() returns the edge ID 
        both when the edge and the actual ID are provided
        
        '''
        road_net =  MyRoadNetwork()
        d = Driver('id', road_net, None, None, 0)
        e1 = road_net.getEdge('e1')
        
        self.assertEquals('e1', d.get_edge_ID('e1'))
        self.assertEquals('e1', d.get_edge_ID(e1))
        
        
        
    def test_set_KB(self):
        '''
        Tests whether the function for setting the driver's
        known price or travel time are working
        
        '''
        road_net =  MyRoadNetwork()
        d = Driver('id', road_net, None, None)
        
        e1 = road_net.getEdge('e1')
        
        d.set_known_travel_time(e1, 55.55)
        d.set_known_price(e1, 49)
        
        self.assertEquals(55.55, d.known_travel_time(e1))
        self.assertEquals(49, d.known_price(e1))
        
            
    def test_edge_costs(self):
        '''
        Tests the calculation of costs performed by driver.
        Cost is a function of travel time and known price, 
        adjusted by the preference coefficient
        
        '''
        road_net =  MyRoadNetwork()
        d = Driver('id', road_net, None, None)
        
        #in MyRoadNetwork, length is 100 and speed is 10 for all edges
        #drivers init price as 50
        #with pref = 1, drivers care about travel time
        for e in road_net.getEdges():
            self.assertEqual(10, d.edge_cost(e))
        
        #with pref = 1, drivers care about credit expenditure    
        d._preference = 0
        for e in road_net.getEdges():
            self.assertEqual(50, d.edge_cost(e))
            
    def test_perceived_trip_costs(self):
        '''
        Tests whether the driver returns the correct cost it perceives for 
        a trip
        
        '''
        road_net =  MyRoadNetwork()
        d = Driver('id', road_net, None, None)
        
        #sets arbitrary values for trip expenses and depart/arrive times
        d._trip_expenses = 50
        d._time_when_departed = 0
        d._time_when_arrived = 20000
        
        #sets preference to 1 (consider travel time) and tests perceived cost
        d._preference = 1
        self.assertEqual(20, d.perceived_trip_cost)
        
        #sets preference to 0 (expenditure) and tests perceived cost
        d._preference = 0
        self.assertEqual(50, d.perceived_trip_cost)
        
            
    def test_route_calculation(self):
        '''
        Tests driver route calculation by calling prepare_next_trip
        then comparing the generated route
        
        '''
        
        road_net = MyRoadNetwork()
        edges = road_net.getEdges()
        #driver has origin = e1 and destination = e4
        d = Driver('id', road_net, edges[0], edges[-1])
        
        d.prepare_next_trip()
        
        self.assertEqual(['e1','e2','e4'], d.route)
        
    def test_driver_doesnt_query_traci_position_after_arrival(self):
        '''
        Tests whether driver is querying traci position after arrival.
        
        A simple road network is created, driver is inserted in it, 
        traverses first edge for 10 timesteps, then it is removed
        and its traversed_distance is queried to trigger the error
        
        '''
        
        road_net = MyRoadNetwork()
        edges = road_net.getEdges()
        
        #creates traci surrogate and patches the actual traci
        newtraci = tracipatch.TraCIReplacement(road_net)
        newtraci.perform_patch()
        
        d = Driver('v1', road_net, edges[0], edges[-1])
        d.prepare_next_trip()
        
        newtraci.set_edge_for_vehicle('e1', 'v1')
        newtraci.set_edge_length('e1', 100)
        d.on_depart()
        
        for i in range(0, 10):
            traci.simulationStep()
            d.on_timestep()
            
        
        newtraci.remove_vehicle(d.driver_id)
        d.on_arrive()
        
        try:
            self.assertEqual(100, d.traversed_distance)
        except KeyError:
            self.fail('Vehicle is querying for its position after being removed from simulation!')
    
        
    def test_on_timestep(self):
        '''
        Tests if driver is updating status correctly. This is a big test.
        
        This test simulates the driver traversing edges e1, e2 and e4 of MyRoadNetwork.
        Each edge is set to have 100 meters
        Driver speed is simulated as 10 m/s
        Each edge should be traversed in 10 seconds
        
        This tests checks how driver stores known travel time and updates its internal
        representation when starting trips, changing edges and finishing trips
        
        TraCIReplacement class is used to perform the required TraCI tasks
        
        '''
        road_net = MyRoadNetwork()
        edges = road_net.getEdges()
        
        #creates traci surrogate and patches the actual traci
        newtraci = tracipatch.TraCIReplacement(road_net)
        newtraci.perform_patch()
        
        #sets length of 100m to all edges:
        for e in edges:
            newtraci.set_edge_length(e.getID(), 100)
            
            
        '''
        driver has origin = e1 and destination = e4;
        default values are used for preference and price initialization;
        depart time is set as 100 and known travel times are initialized as 20.
        '''
        d = Driver('v1', road_net, edges[0], edges[-1], 100, 1, None, lambda x: 20)
        d.prepare_next_trip()
        
        #ensures that initial edge status of driver are null
        self.assertEquals(None, d._last_timestep_edge_id)
        self.assertEquals(None, d._current_edge_id)
        
        #performs 99 timesteps before driver starts its trip
        traci.simulationStep(99000)
        
        #tests travel time (not initialized, should be -1)
        self.assertEquals(-1, d.travel_time)
        
        #inserts driver in simulation at timestep #100 in edge e1
        traci.simulationStep()
        d.on_depart()
        newtraci.set_edge_for_vehicle('e1', 'v1')
        d.on_timestep()
        self.assertEquals(0, d.travel_time)
        
        #makes driver traverse e1 for 9 timesteps, in 10th it changes to e2
        for i in range(0,9):
            traci.simulationStep()
            
            d.on_timestep()
            self.assertEquals('e1', d._current_edge_id)
            newtraci.set_lane_position('v1', 10*(i + 1))
            
        #changes edge of v1 to e2, checks if spent travel time and distance are correct
        newtraci.set_edge_for_vehicle('e2', 'v1')
        newtraci.set_lane_position('v1', 0)
        traci.simulationStep() #d's travel time is 10 sec. now
        d.on_timestep()
        self.assertEquals('e1', d._last_timestep_edge_id)
        self.assertEquals('e2', d._current_edge_id)
        self.assertEquals(10000, d._time_spent_on_last_edge)
        self.assertEquals(110000, d._entry_time) #d enters e2 at timestep 110000 (110 sec)
        self.assertEquals(100, d._length_of_traversed_edges)
        self.assertEquals(10, d.known_travel_time('e1'))
        
        
        
        #makes sure that we are in timestep 110000 (100 at start + 10 on trip)*1000 -- traci time unit
        self.assertEqual(110000, newtraci.ticks())
        
            
        #tests if driver stored the traversed distance & travel time
        #also checks if it is calculating speed properly 
        self.assertEquals(10, d.travel_time)
        self.assertEquals(100, d.traversed_distance)
        self.assertEquals(10, d.average_speed)
        
        #steps again, set new position for v1 and checks variables
        traci.simulationStep() #d's travel time is 11 now
        newtraci.set_lane_position('v1', 10)
        d.on_timestep()
        self.assertEquals('e2', d._last_timestep_edge_id)
        self.assertEquals('e2', d._current_edge_id)
        self.assertEquals(11, d.travel_time)
        self.assertEquals(100, d._length_of_traversed_edges)
        self.assertEquals(110, d.traversed_distance)
        self.assertEquals(10, d.average_speed)
        
        #steps 8 timesteps more, spending a total of 9 in e2
        for i in range(0,8):
            traci.simulationStep()
            d.on_timestep()
            
        #now, steps again and the vehicle reaches e4
        newtraci.set_edge_for_vehicle('e4', 'v1')
        traci.simulationStep()
        d.on_timestep()
        newtraci.set_lane_position('v1', 0)    
            
        #makes sure that we are in timestep 120000 (100 at start + 20 on trip)*1000 -- traci time unit
        self.assertEqual(120000, newtraci.ticks())
        
        #d's travel time is 20 at this point    
        
        #tests if statistics about e2 were updated
        self.assertEquals('e2', d._last_timestep_edge_id)
        self.assertEquals(10000, d._time_spent_on_last_edge)
        self.assertEquals(10, d.known_travel_time('e2'))
        
        #spends 9 timesteps in e4
        for i in range(0,9):
            traci.simulationStep()
            d.on_timestep()
            newtraci.set_lane_position('v1', 10*(i + 1))
            
        #as e4 is not finished yet, length of traversed edges must contain e1 and e2
        self.assertEquals(200, d._length_of_traversed_edges)
        
        #traversed distance must be 290 (200 of traversed edges + 90 traversed in e4)
        self.assertEqual(290, d.traversed_distance)
            
        
        #do the last timestep; finishes d's trip and checks stats
        traci.simulationStep()
        newtraci.remove_vehicle(d.driver_id)
        d.on_arrive()
        
            
        #makes sure that 30 timesteps were run (starting at #100)
        self.assertEqual(130000, newtraci.ticks())
            
        #d's travel time is 30 now
        self.assertEqual(30, d.travel_time)
        
        #checks if d has stored information about e4:
        self.assertEquals(10, d.known_travel_time('e4'))
        
        #checks if the non-travelled edge has known tt unchanged
        self.assertEquals(20, d.known_travel_time('e3'))
        
        #d's travel time is 30 at this point
        
        #checks final values
        self.assertEqual(300, d.traversed_distance)
        self.assertEquals(300, d._length_of_traversed_edges)
        self.assertEqual(30, d.travel_time)
        self.assertEqual(10, d.average_speed)
        self.assertEqual(None, d._current_edge_id)
        
        #perform 100 more timesteps (driver statistics should not change)
        for i in range(0, 100):
            traci.simulationStep()
            try:
                d.on_timestep()
            except KeyError:
                self.fail('Vehicle is querying for its road ID after being removed from simulation!')
        
        #checks if final values haven't changed
        self.assertEqual(300, d.traversed_distance)
        self.assertEqual(30, d.travel_time)
        self.assertEqual(10, d.average_speed)
        self.assertEqual(None, d._current_edge_id)
        
        self.assertEquals(10, d.known_travel_time('e1'))
        self.assertEquals(10, d.known_travel_time('e2'))
        self.assertEquals(10, d.known_travel_time('e4'))
        
        #TODO update with pricing calculation
        
    def test_parse_drivers(self):
        '''
        Tests the driver parser by checking the drivers created by the 
        parser from a known input file.
        
        content of test file is:
        id1 orig1 dest1 0 0.5
        id2 orig2 dest2 5 1
        
        '''
        
        road_net =  MyRoadNetwork()

        drivers = parse_drivers('input.test', road_net)
        self.assertEquals('id1', drivers[0].driver_id)
        self.assertEquals(road_net.getEdge('e1'), drivers[0].origin)
        self.assertEquals(road_net.getEdge('e3'), drivers[0].destination)
        self.assertEquals(0, drivers[0].depart_time)
        self.assertEquals(0.5, drivers[0].preference)
        
        self.assertEquals('id2', drivers[1].driver_id)
        self.assertEquals(road_net.getEdge('e2'), drivers[1].origin)
        self.assertEquals(road_net.getEdge('e4'), drivers[1].destination)
        self.assertEquals(5, drivers[1].depart_time)
        self.assertEquals(1, drivers[1].preference)
        
        
    def test_kb_saver(self):
        '''
        Tests the saving of the knowledge base. Creates two drivers,
        saves their knowledge bases and then checks the contents of 
        the saved files. File is mocked by StringIO
        
        '''
        
        road_net = MyRoadNetwork()
        edges = road_net.getEdges()
        #driver has origin = e1 and destination = e4
        d1 = Driver('id1', road_net, edges[0], edges[-1])
        d2 = Driver('id2', road_net, edges[0], edges[-1])
        
        #creates list with the 2 drivers
        drivers = [d1, d2]
        
        prc_file = StringIO.StringIO()
        tt_file = StringIO.StringIO()
        kb_saver = KBSaver(drivers, road_net, prc_file, tt_file)
        
        #with the given road network and KB initalization, these are the expected files:
        expected_prc_file = '1\n10\ndrv_id\\edg_id,e1,e2,e3,e4\nid1,50,50,50,50\nid2,50,50,50,50\n'
        expected_tt_file = '1\n10\ndrv_id\\edg_id,e1,e2,e3,e4\nid1,10.0,10.0,10.0,10.0\nid2,10.0,10.0,10.0,10.0\n'
        
        kb_saver.save(1,10)
        
        self.assertEqual(expected_prc_file, prc_file.getvalue())
        self.assertEqual(expected_tt_file, tt_file.getvalue())
        
    def test_kb_loader(self):
        '''
        Tests knowledge base loading. Call KBLoader with a known file
        then checks the information loaded into drivers 
        File is mocked by StringIO
        
        '''
        
        #with the given road network and KB initalization, these are the expected files:
        prc_file_content = '1\n10\ndrv_id\\edg_id,e1,e2,e3,e4\nid1,40,50,50,50\nid2,50,50,50,30\n'
        tt_file_content = '1\n10\ndrv_id\\edg_id,e1,e2,e3,e4\nid1,10.0,20.0,10.0,10.0\nid2,10.0,10.0,20.0,10.0\n'
        
        drivers = [
                   Driver('id1', MyRoadNetwork(), None, None),
                   Driver('id2', MyRoadNetwork(), None, None)
                   ]
        
        prc_file = StringIO.StringIO(prc_file_content)
        tt_file = StringIO.StringIO(tt_file_content)
        
        kb_loader = KBLoader(prc_file, tt_file)
        loaded_drivers = kb_loader.load(drivers)
        
        driver1 = loaded_drivers[0]
        driver2 = loaded_drivers[1]
        
        #assertions for driver 1
        self.assertEqual('id1', driver1.driver_id)
        self.assertEqual(40, driver1.known_price('e1'))
        self.assertEqual(50, driver1.known_price('e2'))
        self.assertEqual(50, driver1.known_price('e3'))
        self.assertEqual(50, driver1.known_price('e4'))
        
        self.assertEqual(10.0, driver1.known_travel_time('e1'))
        self.assertEqual(20.0, driver1.known_travel_time('e2'))
        self.assertEqual(10.0, driver1.known_travel_time('e3'))
        self.assertEqual(10.0, driver1.known_travel_time('e4'))
        
        #assertions for driver 2
        self.assertEqual('id2', driver2.driver_id)
        self.assertEqual(50, driver2.known_price('e1'))
        self.assertEqual(50, driver2.known_price('e2'))
        self.assertEqual(50, driver2.known_price('e3'))
        self.assertEqual(30, driver2.known_price('e4'))
        
        self.assertEqual(10.0, driver2.known_travel_time('e1'))
        self.assertEqual(10.0, driver2.known_travel_time('e2'))
        self.assertEqual(20.0, driver2.known_travel_time('e3'))
        self.assertEqual(10.0, driver2.known_travel_time('e4'))
        
        

#----- Monkeypatches from now on ------#
        
def my_traci_vehicle_add(vehID, routeID, depart_time, depart_pos, lane):
    '''
    Mocks traci.vehicle.add. Only prints a message with the given parameters
    
    '''
    
    
    print "Vehicle %s with routeID %s will depart at time %s in position %s of lane %s" %\
    (vehID, routeID, depart_time, depart_pos, lane)
    
    
    
    
def my_traci_route_add(routeID, edges):
    '''
    Mocks traci.route.add. Only prints a message with the given parameters
    
    '''
    
    print "Adding route with ID=%s containing edges: %s" %\
    (routeID, ','.join(edges))    
            

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testDrivers']
    unittest.main()
    
    