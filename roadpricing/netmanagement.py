'''
This module contains classes and functions related to the Link Managers

Created on Nov 17, 2012

@author: anderson
'''

import math
import random
import traci
import xml.etree.ElementTree as ET

def is_internal_edge(edge_id):
    return edge_id.find(':') == 0

class NetworkManager(object):
    def __init__(self, road_network, link_mgr_class, parameters = None):
        '''
        Initializes the network manager that creates the link managers
        
        :param road_network: The road network object 
        :type road_network: sumolib.net.Net
        :param link_mgr_class: Class of the link managers that will be created 
        :type link_mgr_class: class
        
        '''
        
        self._road_network = road_network
        self._managers = {}
        self._list_of_managers = []
        
        if type(link_mgr_class) == str:
            link_mgr_class = manager_classes[link_mgr_class]
            
        
        #creates a link manager for each edge
        for edg in self._road_network.getEdges():
            manager = link_mgr_class(edg, self)
                
            if parameters:
                manager.set_params(parameters)

            self._managers[edg] = manager
            self._list_of_managers.append(manager)
            
        #after creating all managers, initializes their prices
        for mgr in self.list_of_managers:
            mgr.initialize_price()
            
    def manager_of_link(self, edge):
        '''
        Returns the link manager of the given edge
        :param edge: the given edge
        :type edge: str|sumolib.net.Edge
        :return: the link manager object
        :rtype: LinkManager
        
        '''
        if isinstance(edge,str):
            return self._managers[self._road_network.getEdge(edge)]
        
        return self._managers[edge]
    
    @property
    def list_of_managers(self):
        return self._list_of_managers
    
    def timestep_action(self):
        '''
        Updates links status
        '''
        for lm in self._list_of_managers:
            lm.timestep_action()
        
        
    def calculate_link_users(self, route_info_file):
        '''
        Assumes that route_info_file is a clean .xml file
        (without the <!-- --> stuff that SUMO generates)
        
        '''
        rtree = ET.parse(route_info_file)
        
        for vehicle in rtree.getroot():
            edges = vehicle[0].get('edges').split(' ')
            
            for e in edges:
                self.manager_of_link(e).increment_users() 
        
    

class LinkManager(object):
    '''
    Represents a standard link manager
    
    '''
    DEFAULT_CAR_SIZE = 5 #(meters) used to calculate the capacity of the link
    
    MAX_PRICE = 100
    MIN_PRICE = 0

    def __init__(self, link, net_manager):
        '''
        Initializes link manager properties
        
        :param link: The link to be managed 
        :type link: sumolib.net.Edge
        :param net_manager: The network manager 
        :type net_manager: NetworkManager
        '''
        self._price = 0
        self._next_commute_price = 0
        self._link = link
        self._net_mgr = net_manager
        self._average_occupancy = 0
        self._timestep = 0
        self._total_users = 0
        
    def set_params(self, params):
        '''
        Does nothing, subclasses can override this method
        
        '''
        pass
        
    def initialize_price(self):
        '''The standard link manager inits its price in proportion to the
        capacity of its link, compared to the maximum capacity of other 
        links
        
        '''
        #finds the highest capacity manager
        max_cap_mgr = max(
                          self._net_mgr.list_of_managers, 
                          key=lambda m: m.link_capacity()
                          )
        
        self._price = int(self.link_capacity() * 
                          self.MAX_PRICE / max_cap_mgr.link_capacity())
        
        self._next_commute_price = self._price #does not bug when 'before_commute' is called for 1st time
    
    def find_alternative_managers(self):
        '''
        Builds a list with the managers responsible for the alternatives of the
        link managed by this manager. The alternatives are the outgoing links 
        of the incoming links of this link
        
        :return: list with the managers of the alternatives of this LM's link
        :rtype: list
        '''
        incoming = [e for e in self._link.getIncoming()] #turns dict to list =/
        
        alternative_managers = [self._net_mgr.manager_of_link(l) for l in incoming[0].getOutgoing()]
        alternative_managers.remove(self)
        
        return alternative_managers
    
    def average_occ_of_alternatives(self):
        '''
        Returns the average occupancy of the alternative links to the one 
        managed by this manager. The alternatives are the outgoing links 
        of the incoming links of this link
        
        '''
        
        alternatives = self.find_alternative_managers()
        #prevents division by zero
        if len(alternatives) == 0:
            return 0.5
        return sum([m.occupancy for m in alternatives]) / float(len(alternatives))
    
    @property             
    def occupancy(self):
        '''
        Returns the occupancy (%) of the link managed by this link manager
        
        '''
        return self._average_occupancy 
        #return traci.edge.getLastStepOccupancy(self._link.getID().encode("utf-8"))
        
    @property
    def price(self):
        '''
        Returns the current price imposed by this link manager. Price is
        checked and corrected to be within the max and min prices
        
        '''
        if self._price > self.MAX_PRICE:
            self._price = self.MAX_PRICE
        
        if self._price < self.MIN_PRICE:
            self._price = self.MIN_PRICE
             
        return self._price
    
    @property
    def next_commute_price(self):
        '''
        Returns the price to be imposed by this link manager in the next 
        commute. Price is checked and corrected to be within the max and min 
        prices
        
        '''
        
        if self._next_commute_price > self.MAX_PRICE:
            self._next_commute_price = self.MAX_PRICE
            
        if self._next_commute_price < self.MIN_PRICE:
            self._next_commute_price = self.MIN_PRICE
            
        return self._next_commute_price
    
    @property
    def total_users(self):
        '''
        Returns the total number of vehicles that used
        the link controlled by this manager in the current
        iteration
        
        '''
        return self._total_users
    
    def increment_users(self):
        '''
        Increments the total number of users of this link
        
        '''
        self._total_users += 1
    
    def managed_link(self):
        return self._link
    
    def link_capacity(self):
        return int(self._link.getLength() * self._link.getLaneNumber() / self.DEFAULT_CAR_SIZE)
    
    def timestep_action(self):
        '''
        Performs an action at every timestep (must be called in this interval)
        The standard link manager performs no action.
        
        '''
        value = traci.edge.getLastStepOccupancy(self._link.getID().encode('utf-8'))
        self._average_occupancy = ((value - self._average_occupancy) / (self._timestep + 1)) + self._average_occupancy
        
        self._timestep += 1
    
    def commute_finished_action(self):
        '''
        Performs an action at the end of a commuting period. Must be called 
        after all drivers finish their trips.
        The standard link manager performs no action.
        
        '''
        pass
    
    
    def before_commute_action(self):
        '''
        Performs an action before a commuting period. Must be called 
        before all drivers begin their trips.
        
        '''
        self._price = self._next_commute_price
        self._average_occupancy = 0
        self._timestep = 0
        self._total_users = 0
    
class GreedyLinkManager(LinkManager):
    '''
    Implements the greedy link manager whose update policy is as follows:
    If the link's occupancy is higher than the average of its 
    alternatives, the link's price receives the highest value of its 
    alternatives, plus 10 units. The inverse occurs if the occupancy is lower.
    Differently from the NetLogo implementation, price is NOT adjusted when 
    it is already the highest (and link is less occupied) NOR when it is 
    already the lowest (and link is more occupied)
     
    '''
    def commute_finished_action(self):
        alternative_managers = self.find_alternative_managers()
        alt_avg_occ = self.average_occ_of_alternatives()
        
        #tests if price has to be incremented or decremented
        increment = 0 
        cmp_func = lambda x,y: []
        if self.occupancy > alt_avg_occ:
            cmp_func = max
            increment = 10
            
        elif self.occupancy < alt_avg_occ:
            cmp_func = min
            increment = - 10
        
        #adjusts price if needed     
        if increment != 0:
            if alternative_managers != []:
                reference_mgr = cmp_func(alternative_managers, key=lambda m: m.price)
            else:
                reference_mgr = self
            #price is NOT increased when it is already the highest
            #NOR is decreased when it is already the lowest
            #this is a difference from the netlogo implementation!
            if self._price != cmp_func(reference_mgr.price, self._price):
                self._next_commute_price = reference_mgr.price + increment
    
    
    
class IncrementalLinkManager(LinkManager):
    '''
    Implements the greedy link manager whose update policy is as follows:
    If the link's occupancy is higher than the average of its 
    alternatives, price raises by 10 units. The inverse occurs if the 
    occupancy is lower.
    
    '''
    def commute_finished_action(self):
        #alternatives = self.find_alternative_managers()
        alt_avg_occ = self.average_occ_of_alternatives()
        
        if self.occupancy > alt_avg_occ:
            self._next_commute_price = self._price + 10
            
        elif self.occupancy < alt_avg_occ:
            self._next_commute_price = self._price - 10
            
class QLearningLinkManager(LinkManager):
    '''
    Implements the Q-learning link manager.
    It calculates the reward as the number of drivers that 
    used the managed link
    
    '''
    
    MAX_COST = 30 #constant cost of operating this road
    
    def __init__(self, link, net_manager, alpha = 0.5, epsilon_begin = 1.0, exploration = 200):
        '''
        Initializes the q-table
        
        '''
        super(QLearningLinkManager, self).__init__(link, net_manager)


        self.alpha = alpha
        self.epsilon = epsilon_begin
        self.epsilon_end = 0.01
        self.exploration = exploration
        self.decay = (self.epsilon_end / self.epsilon) ** (1.0 / self.exploration)
        self.curr_iter = 1
        
        #print 'QLearningLingManager created with alpha =', alpha
        #initializes q-table (1 entry per discretized price)        
        prices = [i*10 for i in range(11)] #0,10,...,100
        self._qtable = dict((prc, 0) for prc in prices)
        
    def set_params(self, params):
        '''
        Configures q-learning parameters
        
        '''
        if params.alpha: self.alpha = params.alpha
        if params.epsilon_begin: self.epsilon = params.epsilon_begin
        if params.epsilon_end: self.epsilon_end = params.epsilon_end
        if params.exploration: self.exploration = params.exploration
        
        self.decay = (self.epsilon_end / self.epsilon) ** (1.0 / self.exploration)
        
        
    def initialize_price(self):
        '''
        Initializes the price

        '''

        #self._price = random.choice(self._qtable.keys())
        #self._next_commute_price = self._price
        #finds the highest capacity manager
#        max_cap_mgr = max(
#              self._net_mgr.list_of_managers, 
#              key=lambda m: m.link_capacity()
#        )
#        
#        self._price = (self.link_capacity() * 
#                          self.MAX_PRICE / max_cap_mgr.link_capacity())
#        
#        self._price = round(self._price / 10) * 10 #makes it a multiple of 10
        
        self._price = random.choice(self._qtable.keys())
        self._next_commute_price = self._price
        

    def commute_finished_action(self):
        '''
        Updates Q-table and chooses a new price.
        
        '''            
        
        #calculates the profit earned by this link manager
        profit = (self.total_users * self.price) - \
        self._timestep * (self.MAX_COST * pow(math.e, -self.total_users))
        
        #reward = profit
        reward = self.total_users
        
        #updates q-table using q-learning update rule, reward is the profit
        self._qtable[self.price] = self.alpha * reward + (1 - self.alpha) * self._qtable[self.price]
        
        #decreases epsilon

        #sets new price (epsilon-greedily)
        if random.random() < self.epsilon: #tries random action
            self._next_commute_price = random.choice(self._qtable.keys())
        
        else: #executes action of max q
            max_q = max(self._qtable.values())
            for k,v in self._qtable.iteritems():
                if v == max_q:
                    self._next_commute_price = k      
                    
        #decays epsilon
        if self.curr_iter <= self.exploration:
            self.epsilon *= self.decay
            
        self.curr_iter += 1
        #print self.epsilon
        
class OldQLinkManager(QLearningLinkManager):
    '''
    Implements the old Q-learning link manager. It calculates the
    reward as the profit (revenue - cost)
    of operating the link with the given price.
    
    '''
    def commute_finished_action(self):
        '''
        Updates Q-table and chooses a new price.
        
        '''            
        
        #calculates the profit earned by this link manager
        profit = (self.total_users * self.price) - \
        self._timestep * (self.MAX_COST * pow(math.e, -self.total_users))
        
        reward = profit
        
        #updates q-table using q-learning update rule, reward is the profit
        self._qtable[self.price] = self.alpha * reward + (1 - self.alpha) * self._qtable[self.price]

        #sets new price (epsilon-greedily)
        if random.random() < self.epsilon: #tries random action
            self._next_commute_price = random.choice(self._qtable.keys())
        
        else: #executes action of max q
            max_q = max(self._qtable.values())
            for k,v in self._qtable.iteritems():
                if v == max_q:
                    self._next_commute_price = k                
            
#little hack to create the manager classes from strings        
manager_classes = {
   'LinkManager' : LinkManager,
   'IncrementalLinkManager': IncrementalLinkManager,
   'GreedyLinkManager': GreedyLinkManager, 
   'QLearningLinkManager': QLearningLinkManager,
   'OldQLinkManager': OldQLinkManager,
}       

        
