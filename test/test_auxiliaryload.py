'''
Created on Nov 25, 2012

@author: anderson
'''
import unittest
import traci
from sumomockup.tracipatch import TraCIReplacement
from roadnetpatch import MyRoadNetwork

import sys,os
sys.path.append(os.path.join('..','roadpricing'))
from auxiliaryload import DynamicLoadController

class Test(unittest.TestCase):


    def setUp(self):
        self._road_net = MyRoadNetwork()
        
        self._traci = TraCIReplacement(self._road_net)
        self._traci.perform_patch()
        
    def test_dynamic_load_ctrl(self):
        load_ctrl = DynamicLoadController(self._road_net, 300)
        
        load_ctrl.act()
        self.assertEquals(300, self._traci.num_vehicles)
        
        #simulates vehicles leaving the network
        self._traci.remove_vehicles(7)
        self.assertEquals(293, self._traci.num_vehicles)
        
        #calls the load controller to raise #veh to 300:
        load_ctrl.act()
        self.assertEquals(300, self._traci.num_vehicles)



if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()