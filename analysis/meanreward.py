'''
This script outputs the mean reward of the link managers 
along the iterations.

Created on Jun 13, 2013

@author: anderson
'''
import numpy as np
from optparse import OptionParser

def calc(lfile, ofile):
    ldata = np.genfromtxt(lfile,skip_header=1,delimiter=',')[:,1:]
    meanrw_per_it = np.mean(ldata,axis=1)
    
    ncols = len(meanrw_per_it)
    
    result = np.append(
        np.array(range(1,ncols+1)).reshape(ncols,1),
        meanrw_per_it.reshape(ncols,1),
        axis=1
    )
    
    out = open(ofile,'w')
    
    out.write('#it,meanrw\n')
    np.savetxt(out, result, fmt='%.2f', delimiter=',')
    out.close()
    

if __name__ == '__main__':
    
    desc='''Calculates the mean reward of the link managers along the iterations'''
    
    parser = OptionParser(description=desc)

    parser.add_option("-r", "--reward-file", type="string", default='lnkusage.csv',
        help="path to the input file with individual rewards")    
    
    parser.add_option("-o", "--output", type="string", 
        help="The path to the output file")
                         
    
    (options, args) = parser.parse_args()
    
    calc(options.reward_file, options.output)
    
    print 'Output file %s written.' % options.output
    