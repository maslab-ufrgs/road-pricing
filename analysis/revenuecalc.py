'''
Created on Jun 14, 2013

@author: anderson

'''
import numpy as np
from optparse import OptionParser

def _getdata(lfile,pfile):
    
    #checks if headers are equal
    if open(lfile).readline() != open(pfile).readline():
        print 'ERROR: header of files (%s and %s) are different!' % (lfile,pfile)
        exit(1)
    
    
    ldata = np.genfromtxt(lfile,skip_header=1,delimiter=',')[:,1:]
    pdata = np.genfromtxt(pfile,skip_header=2,delimiter=',')[:,1:]
    
    return (ldata, pdata)

def _writeoutput(ofile, data, dataname):
    ncols = len(data)
    
    result = np.append(
        np.array(range(1,ncols+1)).reshape(ncols,1),
        data.reshape(ncols,1),
        axis=1
    )
    out = open(ofile,'w')
    
    out.write('#it,%s\n' % dataname)
    np.savetxt(out, result, fmt='%.2f', delimiter=',')
    out.close()
    
def totalrevenue(lfile, pfile, ofile):
    ldata,pdata = _getdata(lfile,pfile)
    
    revenue = ldata * pdata
    
    maxrev_per_it = np.sum(revenue,axis=1)
    
    _writeoutput(ofile, maxrev_per_it, 'maxrev')

def meanrevenue(lfile, pfile, ofile):
    ldata,prcdata = _getdata(lfile,pfile)
    
    
    #print ldata.shape, prcdata.shape
    revenue = ldata * prcdata
    
    meanrev_per_it = np.mean(revenue,axis=1)
    
    _writeoutput(ofile, meanrev_per_it,'meanrev')
    
    

if __name__ == '__main__':
    
    desc='''Do calculations (mean/sum) on the revenue of the link managers along the iterations'''
    
    parser = OptionParser(description=desc)

    parser.add_option("-u", "--usage-file", type=str, default='lnkusage.csv',
        help="path to the input file with number of link users")    
    
    parser.add_option("-p", "--prices-file", type=str,
        help="path to the input file with prices of links")  
    
    parser.add_option("-o", "--output", type=str, 
        help="The path to the output file")
    
    parser.add_option('--operation', type=str,
        help="Which operation to perform: 'total' or 'mean' revenue")
    
    (options, args) = parser.parse_args()
    
    if options.operation == 'mean':
        meanrevenue(options.usage_file, options.prices_file, options.output)
        
    elif options.operation == 'total':
        totalrevenue(options.usage_file, options.prices_file, options.output)
    else:
        print 'Please specify the --operation.'
        exit()
    
    print 'Output file %s written.' % options.output
    