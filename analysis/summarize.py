'''
Created on 04/03/2013

@author: artavares
'''

import xml.etree.ElementTree as ET
import xmlcleaner
from optparse import OptionParser

def summarize(iteration_number, output, fields, prefix = 'summary', timestep = -1, separator=','):
    
    out = open(output, 'w')
    sep = separator
    
    #prints the header line in the output file
    header = list(fields)
    header.insert(0, '#it')
    out.write( sep.join(header).decode('string-escape') + '\n')
    
    for it in range(1, iteration_number+1):
        filename = '%s%d.xml' % (prefix, it)
        
        if options.zero_fill:
            filename = '%s%s.xml' % (prefix, str(it-1).zfill(3))
        
        if not options.keep_comments:
            xmlcleaner.clean_xml(filename, '<summary>')
        
        print filename
        step_node = ET.parse(filename).getroot()[timestep]
            
        places = ['%d'] + ['%s' for f in fields]
        variables = [it] + [step_node.get(f) for f in fields]
        
        out.write( (sep.join(places + ['\n']) % tuple(variables)).decode('string-escape') )
        
        
if __name__ == '__main__':
    optParser = OptionParser()
    
    optParser.add_option("-p", "--prefix", default='summary',
                            help="the prefix of the summary files to be summarized")
    optParser.add_option("-o", "--output-file",
                            help="the output file (mandatory)")
    optParser.add_option("-s", "--separator", default=" ", type=str,
                            help="the separator for the output file (default=whitespace)")
    optParser.add_option("-i", "--iteration-number", type=int,
                            help="the number of iterations to be summarized")
    optParser.add_option("-f", "--fields", default=None, type=str,
                            help="the fields you want to output in the .csv file (field1,field2,field3,...).")
    
    optParser.add_option("-t", "--timestep", default=None, type=int,
                            help="the number of the timestep to get the data from. defaults to the last timestep")
    
    optParser.add_option("-z", "--zero-fill", action='store_true', default=False,
                            help="use this flag if file numbering needs to have leading zeroes (e.g.: prefix_001 instead of prefix_1)")
    
    optParser.add_option("-k", "--keep-comments", action='store_true', default=False,
                            help="use this flag if there is no need to comment SUMO's leading comments in the .xml file")
    
    
    (options, args) = optParser.parse_args()
    
    print 'Summarizing data from %s1.xml to %s%d.xml' % (options.prefix, options.prefix, options.iteration_number)
    
    fields = options.fields.split(',') if options.fields else []   
    
    summarize(
        options.iteration_number, 
        options.output_file, 
        fields, 
        options.prefix, 
        options.timestep,
        options.separator
    )
    
    print 'Done.'
