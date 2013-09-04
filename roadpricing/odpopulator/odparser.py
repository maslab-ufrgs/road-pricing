'''
Created on Jan 2, 2013

@author: anderson
'''
from tokenize import generate_tokens
from odpopulator import odmatrix
import token
import StringIO

def create_parser(od_file_name, od_matrix):
    '''
    Creates a OD trip definition parser depending on the type of the input file
    :param od_file_name: the path to the od trips definition file  
    :type od_file_name: str
    :param od_matrix: the OD matrix to be filled with the trip information 
    :type od_matrix: odmatrix.ODMatrix
    
    '''
    
    od_file = open(od_file_name, 'r')
    firstline = od_file.readline() 
    od_file.close()
    
    if '$V' in firstline:
        return VFormatODParser(od_file_name, od_matrix)
    
    else:
        raise NotImplementedError('Parser for other OD file format is not available')
    

class ODParser(object):
    '''
    Abstract class for a Parser of OD trip information files
    
    '''

    def __init__(self, od_file, od_matrix):
        '''
        Initializes the parser
        :param od_file: path to the od trip definition file 
        :type od_file: str
        :param od_matrix: the OD matrix to be filled with the trip information
        :type od_matrix: odmatrix.ODMatrix
        
        '''
        
        self.od_file = od_file
        self.taz_list = od_matrix
      
    def parse(self):
        '''
        Parses the od trip information file and fills the OD matrix 
        with the trip information
        
        '''
        raise NotImplementedError('parse should be called by subclasses of ODParser only')  

class VFormatODParser(ODParser):
    '''
    Parser for V-Format OD matrix files. Follow this link to check the
    description of a V-Format file: http://sourceforge.net/apps/mediawiki/sumo/index.php?title=Demand/Importing_O/D_Matrices#Describing_the_Matrix_Cells
             
    '''
    
    def parse(self):
        
        odfile = open(self.od_file,'r')
        
        district_names = []
        
        line_number = 0
        
        for line in odfile.readlines():
            #discounts lines starting with *
            if '*' == line[0]:
                continue
            
            line_number += 1
            
            #district names are in line 6    
            if line_number == 6:
                tokens = generate_tokens(StringIO.StringIO(line).readline)   # tokenize the string
                for toktyp, tokval, _, _, _  in tokens:
                    if toktyp == token.NUMBER or toktyp == token.STRING:
                        district_names.append(tokval)
            
            #trip assignment start at line 7        
            if line_number > 6:
                #finds the origin TAZ in the array of names
                index = line_number - 7
                origin_taz = self.taz_list.find(district_names[index])
                destinations = {}
                
                #tokenize the current line to get the number of trips for each destiny
                tokens = generate_tokens(StringIO.StringIO(line).readline)
                
                #traverses the tokens and fill the number of trips for each destination
                dest_index = 0
                for toktyp, tokval, _, _, _  in tokens:
                    if toktyp == token.NUMBER:
                        destinations[district_names[dest_index]] = int(tokval)
                        dest_index += 1
                origin_taz.set_destinations(destinations)
                
                
            
        
    