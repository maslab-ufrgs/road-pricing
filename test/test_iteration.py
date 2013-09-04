'''
Created on Dec 26, 2012

@author: anderson
'''
import unittest
import os, sys
from roadnetpatch import MyRoadNetwork, MyEdge

#TODO remove this by installing the module in PYTHONPATH
sys.path.append(os.path.join('..','roadpricing'))

from netmanagement import NetworkManager, IncrementalLinkManager
from drivers import Driver
from experiment import Iteration


class Test(unittest.TestCase):


    def test_iteration_has_finished(self):
        
        road_net = MyRoadNetwork()
        edges = road_net.getEdges()
        
        drivers = [
            Driver('d1', road_net, edges[0], edges[-1]), 
            Driver('d2', road_net, edges[0], edges[-1])
        ]
        
        net_mgr = NetworkManager(road_net, IncrementalLinkManager)
        sample = Iteration(drivers, net_mgr)
        
        for i in range(0, 10):
            sample.timestep_action()
            self.assertEqual(False, sample.has_finished())
         
         #make 1 driver arrive
         
         #make second driver arrive   

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.test_iteration_has_finished']
    unittest.main()