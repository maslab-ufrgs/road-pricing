'''
This module contains the Experiment class which actually executes a
road pricing experiment

'''

import drivers
from auxiliaryload import DynamicLoadController
import sumolib
import netmanagement
import traci
#from roadpricing.drivers import KBLoader, KBSaver
from statistics.statswriter import StatsWriter

from time import time
import sys
import os
import subprocess
import odpopulator
import edgedata

class Experiment(object):
    '''
    Executes a road pricing experiment. 
    
    Receives several experiment parameters and executes all iterations,
    writing all statistics.
    
    '''
    
    _drivers = []
    _road_network = None
    _network_manager = None
    
    def __init__(self, drv_file, road_net_file, link_mgr_class, 
                 aux_drv_num, warm_up_time, result_prefix, output_path, 
                 initial_prc_file, initial_tt_file, ql_params,
                 num_iterations, start_iteration, broadcast_prices, time_limit, 
                 sumo_port, client_port, 
                 stats_port, gui, summary_prefix = None, sumopath = None):
        '''
        Initializes the experiment class, parsing the input files.
        If initial prices or travel times are to be loaded into drivers, BOTH 
        initial_prc_file and initial_tt_file must be provided
                 
        :param drv_file: path to the file containing the drivers to be loaded
        :type drv_file: string
        :param road_net_file: path to the road network .net.xml file
        :type road_net_file: string
        :param link_mgr_class: name of the link manager to be used (Greedy or Incremental)
        :type link_mgr_class: string 
        :param aux_drv_num: number of auxiliary vehicles that populate the road network
        :type aux_drv_num: int
        :param warm_up_time: time to wait for the road network to get populated
        :type warm_up_time: int
        :param result_prefix: the prefix for the statistics output files
        :type result_prefix: string
        :param output_path: the path for the outputs
        :type output_path: string
        :param initial_prc_file: path or stream to load the initial known prices into drivers
        :type initial_prc_file: str|file
        :param initial_tt_file: path or stream to load the initial travel times into drivers
        :type initial_tt_file: str|file
        :param num_iterations: the number of iterations for the experiment
        :type num_iterations: int
        :param sumo_port: the port that SUMO will be listening to
        :type sumo_port: int
        :param client_port: the port this client will use to connect to tracihub
        :type client_port: int
        :param stats_port: the port the statistics client will use to connect to tracihub
        :type stats_port: int
        :param gui: call SUMO with the graphical user interface?
        :type gui: bool
        
        '''
        self._network_file = road_net_file
        self._road_network = sumolib.net.readNet(road_net_file)
        
        self._warm_up_time = warm_up_time
        
        self._num_iterations = num_iterations
        self._start_iteration = start_iteration
        self._time_limit = time_limit
        self._aux_drv_num = aux_drv_num
        self._broadcast_prices = broadcast_prices
        
        self._result_prefix = result_prefix
        self._output_path = output_path
        
        self._network_manager = netmanagement.NetworkManager(
            self._road_network, link_mgr_class, ql_params
        )
        
        self._sumo_port = sumo_port
        self._client_port = client_port
        self._stats_port = stats_port
        
        self._gui = gui
        
        self._sumopath = sumopath
        self._summary_prefix = summary_prefix
        
        #self._edge_data = edgedata.EdgeData(self._road_network)
        
        #parses the drivers file and stores drivers on the list
        print 'Parsing drivers file...'
        self._drivers = drivers.parse_drivers(drv_file, self._road_network)
        
        
        if self._result_prefix is not None:
            o = os.path.join(self._output_path, self._result_prefix)
            #link manager drv_stats writer is 'special', it is about the edges and
            #writes before iterations too, so it is created separately
            self._lm_stats = StatsWriter(o + '_edg_prc.csv')
            
            self.drv_stats = [
                {'attr': 'norm_travel_time', 'writer': StatsWriter(o + '_drv_tt.csv'), 'items': self._drivers},
                {'attr': 'trip_expenses', 'writer': StatsWriter(o + '_drv_xps.csv'), 'items': self._drivers},
                {'attr': 'perceived_trip_cost', 'writer': StatsWriter(o + '_drv_z.csv'), 'items': self._drivers},
                #{'attr': 'revenue', 'writer': StatsWriter(o + '_hops.csv'), 'items': self._network_manager.list_of_managers()},
            ]
            
            self.edg_stats = [
                {'attr': 'occupancy', 'writer': StatsWriter(o + '_edg_occ.csv'), 'items': self._network_manager.list_of_managers},
                {'attr': 'price', 'writer': self._lm_stats, 'items': self._network_manager.list_of_managers},
                {'attr': 'total_users', 'writer': StatsWriter(o + '_edg_lus.csv'), 'items': self._network_manager.list_of_managers}
            ]
        else:
            self.drv_stats = []
            self.edg_stats = []
        
    def open_connections(self, iter_number):
        '''
        Opens SUMO and tracihub, then connects tracihub to SUMO, 
        starts the drv_stats utilitary, connecting it to tracihub and
        the connects this road pricing client to tracihub as well
        
        The connection diagram is like this:
        
                             ---- road_pricing_experiment
        sumo --- tracihub ---|
                             ---- statistics utilitary 
        
        '''
        #builds the string to be used to call SUMO    
        sumoExec = 'sumo-gui' if self._gui else 'sumo'
            
        if self._sumopath is not None:
            sumoExec = self._sumopath + sumoExec
        
        sumoCmd = '%s -n %s --remote-port %d' % \
            (sumoExec, self._network_file, self._sumo_port)
        
        sumoCmd += ' --vehroute-output %s --vehroute-output.exit-times' %\
        (os.path.join(self._output_path, 'routeinfo_%d.xml' % (iter_number) ))
        
        if self._summary_prefix is not None:
            sumoCmd += ' --summary-output %s%d.xml' % (self._summary_prefix, iter_number)
        
#        self._tracihub_cmd = 'tracihub %d %d %d' % (sumo_port, client_port, stats_port)
        
        print 'Calling SUMO with:', sumoCmd
        
        #starts SUMO 
        self._sumo_instance = subprocess.Popen(['nohup'] + sumoCmd.split(' '))
        
        #connects road pricing client
        traci.init(self._sumo_port)
        
    def iterations(self):
        '''
        Runs the iterations. Before each iteration, SUMO, tracihub and
        the drv_stats utilitary are opened and the road network is warmed-up. 
        After each iteration, the statistics are written.
        
        '''
        
        #writes the headers into the output files
        if self._result_prefix is not None and self._start_iteration == 1:
            print 'Writing statistics headers...'
            for stats in self.drv_stats:
                stats['writer'].writeLine('x', self._drivers, 'driver_id')
                stats['writer'].writeLine('pref', self._drivers, 'preference')
                
            for stats in self.edg_stats:
                stats['writer'].writeLine('x', [e.managed_link() for e in self._network_manager.list_of_managers], 'getID')
            #writes the ID of edges and their initial price     
            self._lm_stats.writeLine('0', self._network_manager.list_of_managers, 'price')
        
        if self._start_iteration > 1:
            print 'Loading data %d previous iteration(s) to resume experiment.' % self._start_iteration -1
            for it in range(1, self._start_iteration):
                print 'Calculating road users...'
                self._network_manager.calculate_link_users(
                    os.path.join(self._output_path, 'routeinfo_%d.xml' % it)
                )
                #for d in self._drivers:
                #    print '%s: %s %s' % (d.driver_id, d.route, [self._network_manager.manager_of_link(e).price for e in d.route] )
                
                print 'Saving statistics...'
                for s in self.drv_stats + self.edg_stats:
                    s['writer'].writeLine(it+1, s['items'], s['attr'])
                    
    #            print 'Outputting edge data...'
    #            self._edge_data.write_output(os.path.join(self._output_path, 'edges_%d.xml' % (it+1)))
                
                print 'Performing price adjustment...'
                #performs price adjustment
                for mgr in self._network_manager.list_of_managers:
                    mgr.commute_finished_action()
            
        print 'Starting iterations...'
        
        for it in range(self._start_iteration -1, self._num_iterations):
            print 'Preparing iteration', (it+1)
            self.open_connections(it + 1)
            
            iteration = Iteration(self._drivers, self._network_manager)
            aux_demand_ctrl = odpopulator.odloader.UniformLoader(
                 self._road_network, None, self._aux_drv_num, 5, 'aux'
            )
            
            if self._warm_up_time > 0: 
                print 'Warming-up the network for %d timesteps...' % self._warm_up_time
            #warms up the network        
            for i in range(self._warm_up_time):
                traci.simulationStep()
                aux_demand_ctrl.act()
            
            
            print 'Preparing for trips...'
            iteration.prepare_for_trip()
            
            garage = self._drivers[:] #copies the list of drivers
            
            if self._broadcast_prices:
                print 'Broadcasting prices...'
                for d in self._drivers:
                    for lm in self._network_manager.list_of_managers:
                        d.set_known_price(lm.managed_link(), lm.price)
                    
            
            print 'Simulating...'
            arrived = 0
            timestep = 0
            #executes each timestep of the iteration
            while arrived < len(self._drivers):
                start = time()
                
                if self._time_limit > 0 and timestep >= self._time_limit:
                    print 'Time limit reached.'
                    break
                
                #loads cars that are scheduled to depart in up to 100 timesteps
                while len(garage) > 0:
                    if garage[0].depart_time < timestep + 100:
                        garage[0].prepare_next_trip() #calc. route and loads car
                        del garage[0] #removes from garage
                    else:
                        break #breaks when 1st car in list is not scheduled for launch in 100 ts.
                    
                traci.simulationStep()
                #self._edge_data.timestep_action()
                self._network_manager.timestep_action()
                arrived += traci.simulation.getArrivedNumber()
                
                timestep += 1
                sys.stdout.write("\rIteration %d's timestep #%d took %5.3f ms" % (it+1, timestep, time() - start))
                sys.stdout.flush()
                
                #iteration.timestep_action()
                #aux_demand_ctrl.act()
            print 'Simulation finished. Closing connection and waiting for SUMO to terminate...'
            traci.close()
            self._sumo_instance.wait()
            
#            for d in self._drivers:
#                prices = [self._network_manager.manager_of_link(e).price for e in d.route]
#                print '%s: %s Tot: %s' % (d.driver_id, d.route, sum(prices))
            
            print 'Updating drivers knowledge base...'
            drivers.update_kb(
                self._drivers, 
                self._network_manager, 
                os.path.join(self._output_path, 'routeinfo_%d.xml' % (it+1))
            )
            
            print 'Calculating road users...'
            self._network_manager.calculate_link_users(
                os.path.join(self._output_path, 'routeinfo_%d.xml' % (it+1))
            )
            #for d in self._drivers:
            #    print '%s: %s %s' % (d.driver_id, d.route, [self._network_manager.manager_of_link(e).price for e in d.route] )
            
            print 'Saving statistics...'
            for s in self.drv_stats + self.edg_stats:
                s['writer'].writeLine(it+1, s['items'], s['attr'])
                
#            print 'Outputting edge data...'
#            self._edge_data.write_output(os.path.join(self._output_path, 'edges_%d.xml' % (it+1)))
            
            print 'Performing price adjustment...'
            #performs price adjustment
            for mgr in self._network_manager.list_of_managers:
                mgr.commute_finished_action()
                
            print 'Iteration %d finished.' % (it + 1)
        
        for stats in self.drv_stats + self.edg_stats:
            del(stats['writer'])
        
        print 'Experiment finished.'
            
            
class Iteration(object):
    '''
    Manages one iteration, performing drivers initialization, 
    route calculation and the action performed in each timestep
    
    '''
    
    def __init__(self, drivers, net_manager):
        '''
        Initializes Iteration object  
        
        '''
        self._drivers = drivers
        self._net_mgr = net_manager
    
    def prepare_for_trip(self, prc_file = None, tt_file = None):
        '''
        Loads knowledge base into drivers (if provided), 
        performs route calculation and prepares drivers for the trip.
        BOTH prc_file and tt_file must be provided in order to the
        knowledge base to be loaded 
        
        '''    

        for d in self._drivers:
            d.reset()
        
        for lm in self._net_mgr.list_of_managers:
            lm.before_commute_action()
    
    def timestep_action(self):
        arrived_list = traci.simulation.getArrivedIDList()
        departed_list = traci.simulation.getDepartedIDList()
        
        for d in self._drivers:
                
            #checks if driver has departed
            if not d.departed and d.driver_id in departed_list:
                d.on_depart()
                
            if not d.arrived:
                #checks if driver has arrived
                if d.driver_id in arrived_list:
                    d.on_arrive()
                    
                d.on_timestep()
            
            '''
            If entered a new link, pay the credits and save the price of this link
            in knowledge base
            '''    
            if d.has_changed_link() and not netmanagement.is_internal_edge(d.current_edge_id):
                edge_price = self._net_mgr.manager_of_link(d.current_edge_id).price
                d.pay_credits(edge_price)
                d.set_known_price(d.current_edge_id, edge_price) 
    
    def has_finished(self):
        '''
        Returns whether the iteration has finished
        (i.e. all drivers have arrived)
        '''
        
        for d in self._drivers:
            if not d.arrived:
                return False
            
        return True    
    