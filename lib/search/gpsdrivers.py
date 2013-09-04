#!/usr/bin/env python
"""Simulates drivers on SUMO with and without GPS and extra information.

Handles SUMO vehicles with drivers that calculate the route upon
insertion, and may also reinsert the vehicle when the destination
is reached.

Drivers may calculate the cost of each edge in several ways, defined
by the driver type:

 - glength: global knowledge of the topology, the cost of each edge
  is length / number of lanes.

 - plength: partial knowledge of the topology, non-arterial edges
  outside the origin and destination districts have a very high,
  fixed cost; otherwise behaves as glength.

 - glength-gstate: global knowledge of topology and current state,
  favoring edges with high mean speed; the cost of glength is
  multiplied by MAX_SPEED / current mean speed.

 - glength-pstate: global knowledge of topology, partial of state;
  behaves as glength-gstate except that the mean speed is observed
  by the driver along the way, and such value is used instead of the
  real, current one.

 - plength-pstate: partial knowledge of topology and state; calculates
  the basic cost as glength-pstate, but bumps up the cost of unknown
  edges like plength.

"""

import logging as log
import sys

from collections import deque
from optparse import OptionParser
from xml import sax


from averagingwindow import AveragingWindow
from decoratorclass import DecoratorClass
from search import dijkstra

#
#
# This file is organized as follows:
#  1. main loop, using higher-level constructs;
#  2. driver classes, dealing with routing (parameterized
#     on edge evaluation) and reinsertion;
#  3. edge evaluation classes, with composable behaviour;
#  4. command line option parsing;
#  5. loading of information from files.
#
#


#
#
# SUMO packages import
IMPORT_ERR_MSG = """Error: Cannot import the {package} package.

This package is distributed with SUMO, on the tools/{package}
directory. Such directory should have a copy or link somewhere
on the python search path. The recommended location on
linux is ~/.local/lib/pythonX.Y/site-packages/, where X.Y
indicates the installed version of python.
"""
try:
    import traci
except ImportError:
    print IMPORT_ERR_MSG.format(package='traci')
    sys.exit(1)
try:
    import sumolib
except ImportError:
    print IMPORT_ERR_MSG.format(package='sumolib')
    sys.exit(1)


#
#
# Main body of code
def main():
    """Main body of code, defined as a function to ease interactive debugging.
    """
    log.basicConfig(stream=sys.stdout, level=log.INFO)
    (options, args) = parse_options()

    # Read information from configuration files
    net = load_network(options.network_file, options.district_files, options.window_size)
    drivers = load_vehicles(options.route_files, net, options.reinsert)

    # Connect to SUMO
    log.info("Pre-connection to TraCI")
    traci.init(options.port)
    log.info("Connected to TraCI server")

    # Obtain necessary values
    end_time, step_length = options.end, options.step_length
    curr_time = 0
    no_vehicles = False

    # Simulates until end time, if defined, otherwise until there are no vehicles
    while (curr_time < end_time if end_time else no_vehicles):
        # Update drivers of departed vehicles
        departed_ids = traci.simulation.getDepartedIDList()
        departed = [drivers[veh] for veh in departed_ids if veh in drivers]
        log.info('Updating %d departed vehicles.', len(departed))

        for driver in departed:
            driver.on_depart()

        # Update drivers of arrived vehicles
        arrived_ids = traci.simulation.getArrivedIDList()
        arrived = [drivers[veh] for veh in arrived_ids if veh in drivers]
        log.info('Updating %d arrived vehicles.', len(arrived))

        for driver in arrived:
            driver.on_arrive()

        # Update information about edges on ALL drivers
        for edge in net.getEdges():
            edge_id = edge.getID().encode('utf-8')

            # Update the average speed
            curr_speed = traci.edge.getLastStepMeanSpeed(edge_id)
            edge.speed_window.add_point(curr_speed)

            # Update the drivers on this edge
            edge_vehs = traci.edge.getLastStepVehicleIDs(edge_id)
            edge_drivers = [drivers[veh] for veh in edge_vehs if veh in drivers]

            for driver in edge_drivers:
                driver.update_edge(edge)

        # Advance the simulation
        traci.simulationStep(0)
        curr_time += step_length
        log.info('Advanced a timestep to %d.', curr_time/step_length)
        no_vehicles = len(traci.vehicle.getIDList()) < 1

    # Disconnect after simulation
    traci.close()


#
#
# Drivers
class RoutedDriver(object):
    """A driver that calculates its route upon departure.

    Parameterized on edge evaulation, which may also
    accumulate information about the edges.
    """

    def __init__(self, veh_id, origin, dest, net, edge_evaluator):
        self.veh_id = veh_id
        self.origin = origin
        self.dest = dest
        self.net = net
        self._edge_evaluator = edge_evaluator

    def on_depart(self):
        """Calculates the route upon departure."""
        curr_edge = self.net.getEdge(
            traci.vehicle.getRoadID(self.veh_id.encode('utf-8')))

        route = dijkstra(self.net, curr_edge, self.dest,
                         self.evaluate_edge)
        if route is None:
            raise Exception('Cannot find a route for %s, from %s to %s.'
                            % (self.veh_id, curr_edge.getID(), self.dest.getID()))
        edges = [edge.getID().encode('utf-8') for edge in route]

        traci.vehicle.setRoute(self.veh_id.encode('utf-8'), edges)
        log.debug('Calculated route for vehicle %s.', self.veh_id)

    def evaluate_edge(self, edge):
        return self._edge_evaluator.evaluate_edge(edge, self)

    def on_arrive(self):
        """React to arrival on the destination."""
        pass

    def update_edge(self, edge):
        """Update information about given edge."""
        self._edge_evaluator.update_edge(edge)

class ReinsertionDriver(DecoratorClass):
    """Decorator class that should be used with drivers."""

    def __init__(self, driver):
        super(ReinsertionDriver, self).__init__(driver)
        self.__first_trip = True        

    def on_depart(self):
        """Record the route ID and delegate to the decorated instance."""
        self.decoratedObject.on_depart()

        if self.__first_trip:
            # Creates a duplicate route that SUMO won't delete
            # when the vehicle exits the network
            orig_route_id = traci.vehicle.getRouteID(self.veh_id.encode('utf-8'))
            route = traci.route.getEdges(orig_route_id)
            self.__route_id = '__veh__' + self.veh_id.encode('utf-8')

            traci.route.add(self.__route_id, route)
            self.__first_trip = False

    def on_arrive(self):
        """Reinsert on arrival."""
        # Insert with the prerecorded route with same ID as the vehicle
        traci.vehicle.add(self.veh_id.encode('utf-8'), self.__route_id)
        log.debug('Reinserted vehicle %s.', self.veh_id)


#
#
# Edge evaluation
class Evaluator(object):
    """Shows the common interface for evaluators."""

    def evaluate_edge(self, edge, driver):
        """Returns the cost of the edge for the given driver."""
        raise NotImplementedError()

    def update_edge(self, edge):
        """Updates information about the given edge."""
        # By default, do nothing
        pass

class CompositeEvaluator(DecoratorClass):
    """Base for evaluators which build upon simpler evaluators."""

    def evaluate_edge(self, edge, driver):
        subcost = self.subevaluator.evaluate_edge(edge, driver)
        return self._reevaluate(edge, driver, subcost)

    def _reevaluate(self, edge, driver, subcost):
        """Modify and return the value of a subevaluation."""
        raise NotImplementedError()

    @property
    def subevaluator(self):
        return self.decoratedObject

class LengthBreadthEvaluator(Evaluator):
    """The cost is simply length / number of lanes."""

    def evaluate_edge(self, edge, driver):
        return edge.getLength() / edge.getLaneNumber()

class EdgeSpeedEvaluator(CompositeEvaluator):
    """Use the edge mean speed to weight the subevaluator."""

    def _reevaluate(self, edge, driver, subcost):
        speed = edge.speed_window.average
        max_speed = edge.getSpeed()
        return subcost * max_speed / speed

class ObservedSpeedEvaluator(CompositeEvaluator):
    """Use the observed speed to weight the subevaluator."""

    def __init__(self, subevaluator):
        super(ObservedSpeedEvaluator, self).__init__(subevaluator)
        self.__edge_speeds = {}

    def update_edge(self, edge):
        self.subevaluator.update_edge(edge)
        self.__edge_speeds[edge.getID()] = edge.speed_window.average

    def _reevaluate(self, edge, driver, subcost):
        max_speed = edge.getSpeed()
        speed = self.__edge_speeds.get(edge.getID(), max_speed)
        return subcost * max_speed / speed

class DistrictRestrictedEvaluator(CompositeEvaluator):
    """Restrict the set of known edges and bump their costs up."""

    COST_OF_UNKNOWN = 1.0e+10

    def _reevaluate(self, edge, driver, subcost):
        driver_districts = driver.origin.districts.union(driver.dest.districts)
        if any(d in driver_districts for d in edge.districts):
            return subcost
        else:
            return self.COST_OF_UNKNOWN


#
#
# Command line option parsing

USAGE = "  %prog [options] --net-file FILE --district-files FILES --route-files FILES"
DESCRIPTION = '\n'.join(__doc__.split('\n\n')[:2]) # First two paragraphs of docstring
EPILOG = '\n' + '\n\n'.join(__doc__.split('\n\n')[2:]) # Rest of the docstring

def parse_options(argv=None):
    """Parses command line options from the given argv.

    By default parses options from sys.argv[1:].
    """
    # Hack to properly print the epilog
    OptionParser.format_epilog = lambda self, formatter: self.epilog

    # Define the options
    parser = OptionParser(usage=USAGE,
                          description=DESCRIPTION,
                          epilog=EPILOG)

    parser.add_option('-p', '--port', dest='port', type='int',
                      metavar='PORT', default=4444,
                      help='Port used to connect to SUMO '
                      '[default: %default]')

    parser.add_option('-n', '--net-file', dest='network_file',
                      help='Load network from given file.',
                      type='string', metavar='FILE', default=None)

    parser.add_option('-r', '--route-files', dest='route_files',
                      help='Load vehicles from given files.',
                      type='string', default=[], action='callback',
                      callback=parse_list_to('route_files'),
                      metavar='FILES')

    parser.add_option('-d', '--district-files', dest='district_files',
                     help='Load districts from given files.',
                     type='string', default=[], action='callback',
                     callback=parse_list_to('district_files'),
                     metavar='FILES')

    parser.add_option('--no-reinsertion', dest='reinsert',
                      action='store_false', default=True,
                      help="Don't reinsert drivers when they"
                      " reach destinations.")

    parser.add_option('-e', '--end', dest='end', type='int',
                      default=None, metavar='TIME',
                      help='End time of simulation in milliseconds. '
                      'By default, end when no vehicles are left. '
                      'Must be defined when reinsertion is active.')

    parser.add_option('--step-length', dest='step_length', type='int',
                      default=1000, metavar='TIME',
                      help='Length of a timestep in milliseconds. '
                      '[default: %default]')

    parser.add_option('--window-size', dest='window_size', type='int',
                      default=500000, metavar='MILLISECONDS',
                      help='Size of the moving window used for obtaining '
                      'the mean speed, in milliseconds. [default: %default]')

    parser.add_option('--cost-of-unknown', dest='cost_of_unknown',
                      type='float', metavar='COST',
                      default=DistrictRestrictedEvaluator.COST_OF_UNKNOWN,
                      help='Fixed cost given to unknown edges. '
                      '[default: %default]')

    # Parse the arguments
    (options, args) = parser.parse_args(argv)

    # Verify the options
    if options.network_file is None:
        parser.error('A network file is required, and none was given.')
    if len(options.route_files) < 1:
        parser.error('At least one route file is required, none was given.')
    #if len(options.district_files) < 1:
    #    parser.error('At least one districts file is required, none was given.')
    if options.reinsert and options.end is None:
        parser.error('When reinserting vehicles an end time is mandatory, '
                     'none was given.')

    return (options, args)


def parse_list_to(dest):
    """Creates a callback to parse a comma-separated list into dest.

    The returned function can be used as a callback for an
    OptionParser, and it takes the string value and splits
    it on commas.

    The resulting list is assigned to the attribute of the
    options object, identified by dest.
    """
    def callback(options, opt_str, value, parser):
        setattr(parser.values, dest, value.split(','))

    return callback


#
#
# File loading

# Edge evaluators, by vehicle type
EVALUATOR_FACTORIES = {
    'glength': LengthBreadthEvaluator,
    'plength': lambda: DistrictRestrictedEvaluator(LengthBreadthEvaluator()),
    'glength-gstate': lambda: EdgeSpeedEvaluator(LengthBreadthEvaluator()),
    'glength-pstate': lambda: ObservedSpeedEvaluator(LengthBreadthEvaluator()),
    'plength-pstate': lambda: DistrictRestrictedEvaluator(
        ObservedSpeedEvaluator(LengthBreadthEvaluator()))
}

def load_network(net_file, district_files, window_size):
    """Reads and initializes all edges from the network.

    Besides the default properties of edges in sumolib,
    adds a set of 'districts' and a 'speed_window', to observe
    mean speed in a moving window of time.
    """
    # Load the edges of the network
    try:
        net = sumolib.net.readNet(net_file)
    except IOError as err:
        print 'Error reading net file:', err
        sys.exit(1)

    # Initialize extra attributes of such edges
    for edge in net.getEdges():
        edge.districts = set()
        edge.speed_window = AveragingWindow(window_size)

    # Add the district to each edge
    district_handler = DistrictReader(net)
    parser = sax.make_parser()
    parser.setContentHandler(district_handler)
    for filename in district_files:
        try:
            parser.parse(filename)
        except IOError as err:
            print 'Error reading district file:', err
            sys.exit(1)

    return net

def load_vehicles(route_files, net, reinsert):
    """Reads vehicles and initializes their drivers.
    """
    # Read vehicles from route files
    route_handler = RoutesReader(net)
    parser = sax.make_parser()
    parser.setContentHandler(route_handler)
    for filename in route_files:
        try:
            parser.parse(filename)
        except IOError as err:
            print 'Error reading routes file:', err 
            sys.exit(1)

    # Create drivers for each vehicle
    drivers = dict()
    for veh in route_handler.vehicles:
        # Obtain the edge evaluation according to vehicle type
        evaluator_factory = EVALUATOR_FACTORIES.get(veh.type)
        evaluator_factory = lambda: EdgeSpeedEvaluator(LengthBreadthEvaluator())
        if evaluator_factory:
            # Build a basic driver
            driver = RoutedDriver(veh.id, veh.origin, veh.dest,
                                  net, evaluator_factory())
            # Add reinsertion when required
            if reinsert:
                driver = ReinsertionDriver(driver)

            drivers[veh.id] = driver

    return drivers

class DistrictReader(sax.handler.ContentHandler):
    """Adds districts to the edges of a network.
    """

    def __init__(self, net):
        self.__net = net
        self.__current_district = None

    def startElement(self, name, attrs):
        # Register current district
        if name == 'taz' or name == 'district':
            self.__current_district = attrs['id']
            self.__current_sources = deque()
            self.__current_sinks = deque()

        # Register sources and sinks for current district
        elif self.__current_district is not None:
            if name == 'tazSource' or name == 'dsource':
                self.__current_sources.append(attrs['id'])
            elif name == 'tazSink' or name == 'dsink':
                self.__current_sinks.append(attrs['id'])

    def endElement(self, name):
        # Add district to its edges
        if name == 'taz' or name == 'district':
            # Reset the current district
            district = self.__current_district
            self.__current_district = None

            # Obtain the district's edges
            edge_ids = set(self.__current_sources).union(set(self.__current_sinks))
            edges = [self.__net.getEdge(id) for id in edge_ids]

            # Add to each edge
            for edge in edges:
                edge.districts.add(district)

class Vehicle(object):
    """Conatainer for necessary vehicle data."""
    def __init__(self, id, type, origin, dest):
        self.id = id
        self.type = type
        self.origin = origin
        self.dest = dest

class RoutesReader(sax.handler.ContentHandler):
    """Accumulates vehicle data."""

    def __init__(self, net):
        self.vehicles = deque()
        self.__net = net
        self.__current_vehicle = None
        self.__current_route = None
        self.__routes = {}

    def startElement(self, name, attrs):
        # Register current vehicle and attributes
        if name == 'vehicle':
            self.__current_vehicle = attrs['id']
            self.__current_vehtype = attrs.get('type')

            route_id = attrs.get('route')
            if route_id and route_id in self.__routes:
                route = self.__routes[route_id]
                self.__current_origin = route[0]
                self.__current_dest = route[-1]
            else:
                self.__current_origin = None
                self.__current_dest = None

        # Register routes
        if name == 'route':
            route = attrs['edges'].split()

            # Inside a vehicle, just register the origin and dest
            if self.__current_vehicle:
                self.__current_origin = route[0]
                self.__current_dest = route[-1]

            # Outside a vehicle, register the full route
            else:
                self.__routes[attrs['id']] = route

    def endElement(self, name):
        # Save the vehicle data
        if name == 'vehicle':
            origin = self.__net.getEdge(self.__current_origin)
            dest = self.__net.getEdge(self.__current_dest)
            veh = Vehicle(self.__current_vehicle,
                          self.__current_vehtype,
                          origin, dest)

            self.vehicles.append(veh)


#
#
# Execution when called as a script
if __name__ == '__main__':
    main()
