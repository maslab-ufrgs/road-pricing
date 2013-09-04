'''
Created on Jan 3, 2013

@author: anderson

'''
import random

def weighted_selection(total_ammount, items_list, weight_selector):
    '''
    Selects an item with chance proportional to its weight among the total
    
    Algorithm source: 
    http://stackoverflow.com/questions/3655430/selection-based-on-percentage-weighting/3655453#3655453
    
    :param total_ammount: the sum of weights contained in the items_list 
    :type total_ammount: int|double
    :param items_list: the list with the items to be weight-selected
    :type items_list: list
    :param weight_selector: a function that receives an item and returns its weight
    :type weight_selector: function
    
    '''
        
    variate = random.random() * total_ammount
    cumulative = 0.0
    for item in items_list:
        weight = weight_selector(item)
        cumulative += weight
        if variate < cumulative:
            return item
    return item # Shouldn't get here, but just in case of rounding...   