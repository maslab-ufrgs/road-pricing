'''
Created on Feb 12, 2013

@author: anderson
'''

import sys
from optparse import OptionParser
import configparser
import experiment

def register_options(parser):
    parser.add_option(
      '-p', '--port', dest='port', type='int',
      default = 8813,
      help = 'the port used to communicate with the TraCI server'
    )
    
    parser.add_option(
        '-r', '--route-files', dest='maindemand',
        help='files defining the main drivers, the ones participating in the experiment',
        type='string', default=None, metavar='FILES'
    )
    
    parser.add_option(
      '-n','--net-file', dest='netfile', type='string',
      default=None, help = 'the .net.xml file with the network definition'
    )
    
    parser.add_option(
      '-i','--iterations', dest='iterations', type='int',
      default=50, help = 'the number of iterations in the experiment'
    )
    
    parser.add_option(
      '-s','--sumo-path', dest='sumopath', type='string',
      default=None, help = 'path to call the sumo executable'
    )
    
    parser.add_option(
      '-w','--warm-up-time', dest='warmuptime', type='int',
      default=0, help = 'the number of timesteps needed to the road network achieve a steady state'
    )
    
    parser.add_option(
      '-a','--aux-demand', dest='auxdemand', type='int',
      default=0, help = 'The number of auxiliary drivers that populate the road network'
    )
    
    parser.add_option(
      '-o','--resultprefix', dest='resultprefix', type='string',
      default=None, help = 'prefix of output files to be written with the statistics'
    )
    
    parser.add_option(
        "-g", "--usegui", action="store_true",
        default=False, help="activate graphical user interface"
    )
    
    parser.add_option('-c','--config-file',
        default=None, help="loads experiment configuration from a file"
    )


if __name__ == '__main__':
    
    parser = OptionParser()
    
    register_options(parser)
    
    (options, args) = parser.parse_args(sys.argv)
    
    if options.config_file:
        cfg = configparser.ConfigParser(options.config_file)
    else:
        cfg = options
    
    experiment = experiment.Experiment(
        cfg.drivers_file, 
        cfg.netfile, 
        cfg.link_manager_class, 
        cfg.aux_demand,
        cfg.warmuptime, 
        cfg.resultprefix,
        cfg.output_path, 
        cfg.initial_prices_file, 
        cfg.initial_traveltime_file,
        cfg.qlparams,
        cfg.iterations,
        1, #start_iteration (complicated to use 'resume' now...)
        cfg.broadcast_prices,
        cfg.time_limit,
        cfg.port,
        8814,
        8815,
        cfg.usegui,
        cfg.summary_prefix,
        cfg.sumopath
    )
    #self.coordinated = True
    #self.sumopath = None
    
    experiment.iterations()
    
