'''
Created on Jan 2, 2013

@author: anderson
'''

import util

class TAZ(object):
    '''
    Encapsulates a Traffic Assignment Zone (TAZ)
    
    '''
    def __init__(self, taz_id, sources, sinks, destinations = {}):
        '''
        Initializes the TAZ
        :param taz_id: the ID of this TAZ
        :type taz_id: str
        :param sources: contains the source edges and their weights: [{'id':x, 'weight':y},...] 
        :type sources: list(dict)
        :param sinks: contains the sink edges and their weights [{'id':x, 'weight':y},...]
        :type sinks: list(dict)
        :param destinations: contains the destination TAZ's and the number of trips {'taz_id':#trips,...} 
        :type destinations: dict
        
        '''
        
        self.taz_id = taz_id
        self.sources = sources
        self.sinks = sinks
        self.destinations = destinations
        
    def set_destinations(self, destinations):
        '''
        Stores the given destination dict in this TAZ
        :param destinations: dict in the form {'taz_id1': #trips, 'taz_id2': #trips, ...}
        :type destinations: dict 
        
        '''
        self.destinations = destinations
        
    def outgoing_trips(self):
        '''
        return: the number of trips originated in this TAZ
        :rtype: int 
        '''
        return sum(self.destinations.values())
    
    def select_source(self):
        '''
        Returns the ID of a source edge within this TAZ. The chance
        for each source to be selected is proportional
        to its weight
        return: the ID of an edge among the sources of this TAZ
        :rtype: str
        
        '''
        return self._select_edge(self.sources)
    
    def select_sink(self):
        '''
        Returns the ID of a sink edge within this TAZ. The chance
        for each sink to be selected is proportional
        to its weight
        return: the ID of an edge among the sinks of this TAZ
        :rtype: str
        
        '''
        return self._select_edge(self.sinks)
        
        
    def _select_edge(self, the_list):
        '''
        Selects an edge in the the_list according to its weight
        :param the_list: a list of sources or destinations of this TAZ 
        :type the_list: list(dict)
        
        '''
        return util.weighted_selection(
           sum([s['weight'] for s in the_list]),
           the_list, 
           lambda s: s['weight']
        )
    
        
class ODMatrix(object):
    '''
    Encapsulates an OD Matrix. Stores the Traffic Assignment Zones (TAZ) and 
    the proportion of trips among them
    
    '''


    def __init__(self):
        '''
        Initializes the OD Matrix 
        
        '''
        
        self.taz_list = []
        
    def add_taz(self, taz):
        '''
        Adds a traffic assignment zone to the matrix
        :param taz: the traffic assignment zone to be added 
        :type taz: odmatrix.TAZ
        
        '''
        self.taz_list.append(taz)
        
    def all_taz(self):
        '''
        return: a list with all traffic assignment zones
        :rtype: list(odmatrix.TAZ)
        
        '''
        return self.taz_list
    
    def select_od_taz(self):
        '''
        Performs the weighted selection of origin and destination TAZs
        The origin is selected according in proportion to the number of outgoing 
        its trips compared to the total of all TAZs. 
        The destination is weighted-selected according to the 
        number of trips that the origin TAZ generates to each destination.
        
        return: the origin and destination TAZ's in a list: [odmatrix.TAZ, odmatrix.TAZ]
        :rtype: list(odmatrix.TAZ) 
        
        '''
        total_out_trips = sum([taz.outgoing_trips() for taz in self.taz_list])
        origin_taz = util.weighted_selection(
            total_out_trips, self.taz_list, lambda taz: taz.outgoing_trips()
        )
        
        destinations_list = [{'name': x, 'numtrips': y} for x,y in origin_taz.destinations.items()]
        
        dest_taz_dict = util.weighted_selection(
            origin_taz.outgoing_trips(), 
            destinations_list, 
            lambda dest: dest['numtrips']
        )
        return [origin_taz, self.find(dest_taz_dict['name'])]
        
    
    def find(self, taz_id):
        '''
        Search TAZ by its id and returns it if found. 
        Returns None if no TAZ is found.
        :param taz_id: the ID of the TAZ to be found
        :type taz_id: str 
        return: the TAZ identified by its ID or None 
        :rtype: odmatrix.TAZ
         
        '''
        for taz in self.taz_list:
            if taz.taz_id == taz_id:
                return taz
        
        return None