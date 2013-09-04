'''
OD populator package main file

Contains functions to generate the od_matrix and parse .taz.xml and .odm files

'''

import xml.etree.ElementTree as ET
import odmatrix
import odparser
import odloader

def generate_odmatrix(taz_file, odm_file):
    '''
    Generates an ODMatrix from the .taz.xml and .odm files
    :param taz_file: the path to the .taz.xml file
    :type taz_file: str
    :param odm_file: the path to the .odm file
    :type odm_file: str
    return: the OD matrix loaded with the districts and trips from the files
    :rtype: odmatrix.ODMatrix
    '''
    od_matrix = odmatrix.ODMatrix()
    
    parse_taz_file(od_matrix, taz_file)
    parse_odm_file(od_matrix, odm_file)
        
    return od_matrix

def parse_taz_file(od_matrix, taz_file):
    '''
    Fills the od_matrix with the districts found in the taz_file
    :param od_matrix: the OD matrix to be filled
    :type od_matrix: odmatrix.ODMatrix
    :param taz_file: the path to the .taz.xml file
    :type taz_file: str
    return: the OD matrix loaded with the districts information
    :rtype: odmatrix.ODMatrix
    
    '''
    taz_tree = ET.parse(taz_file)
    
    
    for element in taz_tree.getroot():
        sources = []
        sinks = []
        for src_snk in element:
            
            if src_snk.tag == 'tazSource':
            
                sources.append({
                    'id': src_snk.get('id'), 
                    'weight': float(src_snk.get('weight'))
                })
                
            else:
                sinks.append({
                    'id': src_snk.get('id'), 
                    'weight': float(src_snk.get('weight'))
                })
            
        
        
        taz = odmatrix.TAZ(element.get('id'), sources, sinks)
        od_matrix.add_taz(taz)
        
    return odmatrix
        
def parse_odm_file(od_matrix, odm_file):
    '''
    Fills the od_matrix with trip information of the odm_file.
    The matrix must be already filled with the districts information
    :param od_matrix: the OD matrix to be filled
    :type od_matrix: odmatrix.ODMatrix
    :param odm_file: the path to the .odm file
    :type odm_file: str
    return: the OD matrix loaded with the trip information
    :rtype: odmatrix.ODMatrix
    
    '''
    odm_parser = odparser.create_parser(odm_file, od_matrix)
    odm_parser.parse()
    return od_matrix