'''
This auxiliary script prepares a series of config files
to test different values of the learning rate for the QLearningLinkManagers 

Created on Jul 11, 2013

@author: anderson
'''

files = [open('%s/config.xml' % i).read() for i in [str(j).zfill(2) for j in range(1,11)]]

for i in range(len(files)):
    files[i] = files[i].replace('<ql-alpha value="0.1"','<ql-alpha value="%.1f"' % ((i+1)/10.0))
    files[i] = files[i].replace('<alpha value="0.1"','<alpha value="%.1f"' % ((i+1)/10.0))
    files[i] = files[i].replace('<port value="8001"','<port value="80%s"' % str(i+1).zfill(2))
    
outfiles = [open('%s/config.xml' % i,'w') for i in [str(j).zfill(2) for j in range(1,11)]]

for i in range(len(outfiles)):
    outfiles[i].write(files[i])
    outfiles[i].write('\n')
    #print files[i]
    outfiles[i].close()
    
    
    
    