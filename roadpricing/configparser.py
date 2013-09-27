'''
Provides a parser to the xml file with experiment configurations

Created on Feb 1, 2013

@author: anderson

'''
import os
import xml.etree.ElementTree as ET

def str_to_bool(value):
    if value in ['True', 'true']:
        return True
    return False
    
class ConfigParser(object):
    '''
    Parses the .xml file with the configs
    
    '''

    def __init__(self, cfgpath):
        '''
        Constructor
        
        '''
        self.cfgdir = os.path.dirname(os.path.realpath(cfgpath))
        self._set_defaults()
        cfgtree = ET.parse(cfgpath)
        
        
        print 'Parsing config file...'
        
        for io_element in cfgtree.find('input-output'):
            #TODO: check if io_element refers to absolute path
            if io_element.tag == 'net-file':
                self.netfile = self._parse_path(io_element.get('value'))
            
            if io_element.tag == 'drivers-file':
                self.drivers_file = self._parse_path(io_element.get('value'))
            
            if io_element.tag == 'result-prefix':
                self.resultprefix = io_element.get('value')
            
            if io_element.tag == 'output-path':
                self.output_path = self._parse_path(io_element.get('value'))
            
            if io_element.tag == 'initial-prices-file':
                self.initial_prices_file = self._parse_path(io_element.get('value'))
                
            if io_element.tag == 'initial-traveltime-file':
                self.initial_traveltime_file = self._parse_path(io_element.get('value'))
                
        for param_element in cfgtree.find('parameters'):
            
            if param_element.tag == 'iterations': 
                self.iterations = int(param_element.get('value'))
                
            if param_element.tag == 'link-manager-class':
                self.link_manager_class = param_element.get('value')
           
            if param_element.tag == 'ql-alpha':
                self.ql_alpha = float(param_element.get('value'))    
            
            if param_element.tag == 'time-limit':
                self.time_limit = int(param_element.get('value'))
            
            if param_element.tag == 'aux-demand':
                self.aux_demand = int(param_element.get('value'))
            
            if param_element.tag == 'broadcast-prices':
                self.broadcast_prices = str_to_bool(param_element.get('value'))
                
        if cfgtree.find('qlparams'): #qlparams are optional         
            for param_element in cfgtree.find('qlparams'):
                
                if param_element.tag == 'alpha':
                    self.qlparams.alpha = float(param_element.get('value')) 
                    
                if param_element.tag == 'epsilon_begin':
                    self.qlparams.epsilon_begin = float(param_element.get('value'))
                     
                if param_element.tag == 'epsilon_end':
                    self.qlparams.epsilon_end = float(param_element.get('value'))
                    
                if param_element.tag == 'exploration':
                    self.qlparams.exploration = int(param_element.get('value'))     
                
        for sumo_element in cfgtree.find('sumo'):
            if sumo_element.tag == 'port':
                self.port = int(sumo_element.get('value'))
            
            if sumo_element.tag == 'use-gui':
                self.usegui = str_to_bool(sumo_element.get('value'))
                
            if sumo_element.tag == 'sumo-path':
                self.sumopath = self._parse_path(sumo_element.get('value'))
            
            if sumo_element.tag == 'warm-up-time':
                self.warmuptime = int(sumo_element.get('value'))
                
            if sumo_element.tag == 'summary-output-prefix':
                self.summary_prefix = self._parse_path(sumo_element.get('value'))

    def _parse_path(self, value):
        return os.path.join(
            self.cfgdir, os.path.expanduser(value)
        )
        
    def _set_defaults(self):
        
        #input-output group
        self.netfile = None
        self.drivers_file = None
        self.resultprefix = 'exp'
        self.output_path = self.cfgdir
        self.initial_prices_file = None
        self.initial_traveltime_file = None
        
        #parameters group
        self.link_manager_class = None
        self.iterations = 5
        self.aux_demand = 0
        self.use_lk = False
        self.time_limit = -1
        self.broadcast_prices = False
        
        #qlparams group (empty coz params need to be explicit)
        self.qlparams = type('qlparams', (object,), {})()
        
        
        #sumo group
        self.port = 8813
        self.usegui = False
        self.sumopath = None
        self.summary_prefix = None
        self.warmuptime = 0
