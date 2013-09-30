'''
Created on Nov 17, 2012

@author: anderson
'''
import sys
import os
import unittest
import traci
from sumomockup.roadnetpatch import MyRoadNetwork, MyEdge

#TODO remove this by installing the module in PYTHONPATH
sys.path.append(os.path.join('..','roadpricing'))
from netmanagement import LinkManager, NetworkManager, GreedyLinkManager,\
    IncrementalLinkManager

class Test(unittest.TestCase):
    

    def test_std_mgr_creation_and_prc_update(self):
        road_net = MyRoadNetwork()
        
        self._net_mgr = NetworkManager(road_net, LinkManager)
        
        #all links in MyRoadNetwork are 100m long, thus, supporting 20 vehicles each
        #also, price will be 100 (equally high)
        for mgr in self._net_mgr.list_of_managers:
            self.assertEqual(20, mgr.link_capacity())
            self.assertEqual(100, mgr.price)
            
        #price shall not change during the timesteps
        for timestep in range(1, 1001):
            for mgr in self._net_mgr.list_of_managers:
                mgr.timestep_action()
                self.assertEqual(100, mgr.price)
                
        #price shall not change during commutes
        for commute in range(1, 31):
            for mgr in self._net_mgr.list_of_managers:
                mgr.commute_finished_action()
                self.assertEqual(100, mgr.price)  
    
    def test_prc_within_limits(self):
        road_net = MyRoadNetwork()
        self._net_mgr = NetworkManager(road_net, LinkManager)
        
        link_mgr = LinkManager(MyEdge('test'), self._net_mgr)
        
        link_mgr._price = -1
        self.assertEquals(0, link_mgr.price)
        
        link_mgr._price = 101
        self.assertEquals(100, link_mgr.price)
        
        link_mgr._next_commute_price = -1 
        self.assertEquals(0, link_mgr.next_commute_price)
        
        link_mgr._next_commute_price = 101
        self.assertEquals(100, link_mgr.next_commute_price)
                        
    def test_greedy_prc_update(self):
        #Monkey-patches traci to use the custom mock
        traci.edge.getLastStepOccupancy = my_traci_edge_getLastStepOccupancy
        
        road_net = MyRoadNetwork()
        self._net_mgr = NetworkManager(road_net, GreedyLinkManager)
        
        e2 = self._net_mgr.manager_of_link(road_net.getEdge('e2'))
        e3 = self._net_mgr.manager_of_link(road_net.getEdge('e3'))
        
        e2._price = 50
        e3._price = 70
        
        e2._average_occupancy = 0.5
        e3._average_occupancy = 0.3
        
        #print e2, e2._average_occupancy
        #as e2 is more occupied, it should raise its price to 80
        e2.commute_finished_action()
        self.assertEquals(80, e2.next_commute_price)
        
        #as e3 is less occupied, it should decrease its price to 40
        e3.commute_finished_action()
        self.assertEqual(40, e3.next_commute_price)
        
        #starts a new commute
        e2.before_commute_action()
        e3.before_commute_action()
        
        #tests if price received the next_commute_price
        self.assertEquals(80, e2.price)
        self.assertEquals(40, e3.price)
        
        #as e2 is more occupied AGAIN, and its price is already the highest
        #it should keep the price of 80
        e2.commute_finished_action()
        self.assertEquals(80, e2.next_commute_price)
        
        #as e3 is less occupied AGAIN and its price is already the lowest
        #it should keep its price of 40
        e2.commute_finished_action()
        self.assertEquals(40, e3.next_commute_price)
        
    def test_incremental_prc_update(self):
        #Monkey-patches traci to use the custom mock
        traci.edge.getLastStepOccupancy = my_traci_edge_getLastStepOccupancy
        
        road_net = MyRoadNetwork()
        self._net_mgr = NetworkManager(road_net, IncrementalLinkManager)
        
        e2 = self._net_mgr.manager_of_link('e2') #tests manager_of_link with str parameter
        e3 = self._net_mgr.manager_of_link(road_net.getEdge('e3'))
        
        e2._price = 50
        e3._price = 70
        
        e2._average_occupancy = 0.5
        e3._average_occupancy = 0.3
        
        #as e2 is more occupied, it should raise its price to 60
        e2.commute_finished_action()
        self.assertEquals(60, e2.next_commute_price)
        
        #as e3 is less occupied, it should decrease its price to 60
        e3.commute_finished_action()
        self.assertEqual(60, e3.next_commute_price)
        
        
        
            
def my_traci_edge_getLastStepOccupancy(edgeID):
    '''
    Mock for traci.edge.getLastStepOccupancy
    
    returns 80 for e2, 50 for e3 and 40 for the other edges of
    test_driver.MyRoadNetwork()
    '''
    if edgeID == 'e2':
        return 80
    
    if edgeID == 'e3':
        return 50
    
    return 40
    
            
            

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()