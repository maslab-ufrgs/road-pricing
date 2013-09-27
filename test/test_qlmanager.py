'''
This modules performs basic testing of QLearningLinkManager
regarding the configuration of parameters and the decrease
of epsilon along the episodes

Created on Mar 21, 2013

@author: anderson

'''
import unittest
import sys
import os

sys.path.append(os.path.join('..','roadpricing'))
from netmanagement import QLearningLinkManager

class Test(unittest.TestCase):


    def test_init(self):
        qlmgr = QLearningLinkManager(None, None, 0.3, 0.2, 300)
        
        self.assertEqual(qlmgr.alpha, 0.3)
        self.assertEqual(qlmgr.epsilon, 0.2)
        self.assertEqual(qlmgr.exploration, 300)
        
    def test_set_params(self):
        params = type('qlparams', (object,), {})()
        params.alpha = 0.5
        params.epsilon_begin = 0.9
        params.epsilon_end = 0.001
        params.exploration = 250
        
        qlmgr = QLearningLinkManager(None, None, 0.3, 0.2, 300)
        qlmgr.set_params(params)
        
        self.assertEqual(0.5, qlmgr.alpha)
        self.assertEqual(0.9, qlmgr.epsilon)
        self.assertEqual(0.001, qlmgr.epsilon_end)
        self.assertEqual(250, qlmgr.exploration)
        self.assertAlmostEqual(0.973157267, qlmgr.decay, None, None, 0.000000001)
        
    def test_epsilon_decrease(self):
        params = type('qlparams', (object,), {})()
        params.alpha = 0.5
        params.epsilon_begin = 0.9
        params.epsilon_end = 0.001
        params.exploration = 250
        
        qlmgr = QLearningLinkManager(None, None, 0.3, 0.2, 300)
        qlmgr.set_params(params)
        
        for i in range(300):
            qlmgr.commute_finished_action()
        
        #epsilon should reach the final value
        self.assertAlmostEqual(0.001, qlmgr.epsilon, None, None, 0.000000001)
        
        for i in range(1000):
            qlmgr.commute_finished_action()
        #epsilon should not change now
        self.assertAlmostEqual(0.001, qlmgr.epsilon, None, None, 0.000000001)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testEpsilonDecrease']
    unittest.main()