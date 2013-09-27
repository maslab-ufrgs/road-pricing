'''
Unused module

Created on Feb 16, 2013

@author: anderson

'''
import traci

class EdgeData(object):
    '''
    Class responsible for measuring edge data from the simulation
    '''
    
    

    def __init__(self, road_net):
        '''
        Constructor
        '''
        
        self.edge_data = []
        self._road_net = road_net
        
        #header
        self.edge_data.append(' '.join([e.getID() for e in road_net.getEdges()]))
        
    
    def timestep_action(self):
        '''
        Stores a line of the output file, which corresponds to the edges occupation
        
        '''
        eids = [e.getID().encode('utf-8') for e in self._road_net.getEdges()]
        occs = [traci.edge.getLastStepOccupancy(e) for e in eids]
        self.edge_data.append(
            ' '.join([str(oc) for oc in occs])
        )
        
    def write_output(self, outfile):
        out = open(outfile, 'w')
        for line in self.edge_data:
            out.write(line + '\n')
            
        out.close()
        