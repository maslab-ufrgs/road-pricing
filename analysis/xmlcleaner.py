'''
Cleans everything outside the <maintag>..</maintag> 
of a xml document

Created on 22/02/2013

@author: artavares
'''
    
def clean_xml(filename, rootname):
    f = open(filename)
    lines = f.readlines()
    f.close
    
    while not lines[0].startswith(rootname):
        del(lines[0])
        
    f = open(filename, 'w')
    f.writelines(lines)
    f.close
    
if __name__ == '__main__':
    import sys
    
    clean_xml(sys.argv[1], sys.argv[2])
    
    print "File '%s' cleaned" % sys.argv[1]
    