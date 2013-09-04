'''
Created on May 4, 2013

@author: anderson

This script removes previously stored results from a file. These are in the form:

x,drv1,drv2
pref,0.5,0.5
1,200,200
2,199,199
x,drv1,drv2        <<<should discard previous results and keep only from here onwards
pref,0.5,0.5
1,100,100
2,199,199

'''
import sys

f = open(sys.argv[1])

flines = f.readlines()

for i in range(len(flines)):
    if flines[i][0] == 'x':
        filtlines = flines[i:]

o = open(sys.argv[1],'w')
o.writelines(filtlines)

print 'DONE.'