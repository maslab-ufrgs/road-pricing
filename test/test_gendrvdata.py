'''
Created on 22/02/2013

@author: artavares
'''
import unittest
import os, sys

sys.path.append(os.path.join('..', 'analysis'))

from gendrvdata import new_average

class Test(unittest.TestCase):


    def test_new_average(self):
        values = [10, 400, 9010, 36369, -1, 15, -4, 59, 1065464, -20]
        
        avg = 0
        for i in range(len(values)):
            avg = new_average(avg, values[i], i)
        
        self.assertAlmostEqual(float(sum(values)) / len(values), avg, None, None, 0.00001) 

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()