'''
Created on 14/06/2013

@author: artavares
'''

import numpy as np
import matplotlib.pyplot as plt
from plotparams import *

def get_data(fname, delim=','):
    keys = ['a05','gsn','uni','tm']
    
    fxdata = dict(
        (key,np.genfromtxt('fxprc-norm/%s/%s' % (key,fname),skip_header=1,delimiter=delim)) for key in keys
    )
    
    qdata = dict(
        (key,np.genfromtxt('ql03-norm/%s/%s' % (key,fname),skip_header=1,delimiter=delim)) for key in keys
    )
    
    return (fxdata,qdata)

def plotabs(fname=None, lcols=3,axis=[0,400,.7,1.15],oprefix=None,ylabel='desempenho comparado'):
    if fname is None:
        print 'Please inform the fname parameter. Exiting...'
        exit()
        
    fdata,qdata = get_data(fname,delim='\t')
    
    categs = {
        'tm': [0.0, 1.0],
        'a05': [1.0],
        'gsn': [.35, .5, .65, 1],
        'uni': [.25, .50, .75, 1]
    }
    
    for key,qd in qdata.iteritems():
        plt.figure(figsize=REDUCED_FIG_SIZE)
        plt.title('$\Pi=$%s' % key, size=TITLE_SIZE )
        plt.xlabel('episodio', size=AXIS_FONTSIZE)
        plt.ylabel(ylabel, size=AXIS_FONTSIZE)
        dshape = qd.shape
        #fd = ftdata[key][:dshape[0]]
        #vs = qtdata[key] / fd
        
        #plt.plot(qdata[:,0], vs[:,(1)], label='a05')
                 
        plt.plot(qdata[:,0], qd[:,1], label='tarif. via AR', ms=MARKER_SIZE, markevery=MARKER_INTERVAL)
        plt.plot(fdata[:,0], fdata[:,1], label='tarif fixa', ms=MARKER_SIZE, markevery=MARKER_INTERVAL)
        
        #plt.axis(axis)
        plt.legend(ncol=lcols)
        if oprefix is not None:
            plt.savefig('%s_%s.eps' % (oprefix,key))
#    if len(outputs) > 2:
#        plt.savefig(outputs[2])    
    
    plt.show()
    
def tabulate(fname=None, lcols=2,axis=[0,400,.7,1.31],oprefix=None,ylabel='desempenho comparado',figsz=TALL_FIG_SIZE):
    '''
    OK
    
    '''
    if fname is None:
        print 'Please inform the fname parameter. Exiting...'
        return
        
    ftdata,qtdata = get_data(fname,delim='\t')
    
    print 'means:'
    for key,qdata in qtdata.iteritems():
        dshape = qdata.shape
        fd = ftdata[key][:dshape[0]]
        vs = qtdata[key] / fd
        print key, ['%.2f' % np.mean(vs[-100:,(1+i)]) for i in range(len(DRV_GRP[key]))]
        
    print '\nstddevs:'
    for key,qdata in qtdata.iteritems():
        dshape = qdata.shape
        fd = ftdata[key][:dshape[0]]
        vs = qtdata[key] / fd
        print key, ['%.2f' % np.std(vs[-100:,(1+i)]) for i in range(len(DRV_GRP[key]))]

def plot(fname=None, lcols=2,axis=[0,400,.7,1.31],oprefix=None,ylabel='desempenho comparado',figsz=TALL_FIG_SIZE):
    '''
    OK
    
    '''
    if fname is None:
        print 'Please inform the fname parameter. Exiting...'
        return
        
    ftdata,qtdata = get_data(fname,delim='\t')
    
    colors = {
        'tm': ['b','g'],
        'a05': ['b'],
        'gsn': ['c', 'g', 'r', 'b'],
        'uni': ['c', 'g', 'r', 'b']
    }
    
    axestt = { #drvtt
        'a05': [0,400,.7,1.21],
        'tm': [0,400,.7,1.21],
        'uni': [0,400,.88,1.15],
        'gsn': [0,400,.88,1.15]
    }
    
    axesxps = { #drvxps
        'a05': [0,400,.9,2.8],
        'tm': [0,400,.9,2.8],
        'uni': [0,400,1.6,2.8],
        'gsn': [0,400,1.6,2.8]
    }
    
    axesz = { #drvz
        'a05': [0,400,.9,2.2],
        'tm': [0,400,.9,2.2],
        'uni': [0,400,.9,2.2],
        'gsn': [0,400,.9,2.2]
    }
    
    axes = axestt
    
    mkst = { #drvtt
        'a05': [0],
        'tm': [0,0],
        #'uni': [10,20,0,0], #drvtt
        #'gsn': [10,20,0,0],
        'uni': [0,20,0,10], #drvz
        'gsn': [0,20,0,10],
    }
    
    z = { #drvtt
        'a05': [0],
        'tm': [0,0],
        'uni': [1,0,0,0],
        'gsn': [1,0,0,0],
    }
    
    st = { #drvtt
        'a05': ['-'],
        'tm': ['-','-'],
        'uni': ['-','-','-','-'],
        'gsn': ['-','-','-','-'],
    }
    
    for key,qdata in qtdata.iteritems():
        fig = plt.figure(figsize=figsz)
        ax = fig.add_subplot(111)
        
        plt.title('%s' % DIST_NAMES[key], size=TITLE_SIZE)
        plt.xlabel('episodio', size=AXIS_FONTSIZE)
        plt.ylabel(ylabel, size=AXIS_FONTSIZE-4)
        dshape = qdata.shape
        fd = ftdata[key][:dshape[0]]
        vs = qtdata[key] / fd
        
        #plt.plot(qdata[:,0], vs[:,(1)], label='a05')
        #print [DRV_GRP[key][i] for i in range(len(DRV_GRP[key]))]
        #print [RHO_MARKERS[key][i]  for i in range(len(RHO_MARKERS[key]))]
        [plt.plot(qdata[:,0], vs[:,(1+i)], RHO_MARKERS[key][i], label=DRV_GRP[key][i], color=colors[key][i],  ms=MARKER_SIZE, markevery=(mkst[key][i],MARKER_INTERVAL+10),zorder=z[key][i],mec=colors[key][i],mfc='None',mew=3,lw=3,ls=st[key][i]) for i in range(len(DRV_GRP[key]))]
        plt.plot(range(400),[1]*400,'--', color='orange', label='base (tarif. fixa)',lw=3)
        
        plt.axis(axes[key])
        plt.legend(
            ncol=lcols,numpoints=1, 
            prop={'size':LGND_FONTSIZE},
            bbox_to_anchor=(1, 1.035)
        )
        for label in ax.get_yticklabels() + ax.get_xticklabels():
            label.set_size(TICK_FONTSIZE)
        
        #plt.subplots_adjust(bottom=BOTTOM_MARGIN)
        if oprefix is not None:
            #plt.savefig('/home/anderson/Diss/texto/img/%s_%s.eps' % (oprefix,key),bbox_inches='tight')
            plt.savefig('%s_%s.eps' % (oprefix,key),bbox_inches='tight')
#    if len(outputs) > 2:
#        plt.savefig(outputs[2])    
    
    plt.show()

def plotflow(outputs=[],lcols=3,axis=[0,400,10000,24000]):
    fdata,qdata = get_data('global.csv',delim='\t')
    gwrdata = np.genfromtxt('dua/global.csv', skip_header=1, delimiter='\t')
    
    
    #fx vs gwr
    plt.figure()
    plt.title('Tarifacao fixa vs. Gawron')
    plt.xlabel('episodio')
    plt.ylabel('# viagens concluidas')
    plt.plot(gwrdata[:,0], gwrdata[:,4], label='gawron')
    for key,data in fdata.iteritems():
        plt.plot(data[:,0], data[:,4], label=key)
    
    plt.axis(axis)
    plt.legend(ncol=lcols)
    if len(outputs) > 0:
        plt.savefig(outputs[0])
        
    
        
    #ql vs gwr
    plt.figure()
    plt.title('Tarifacao via AR vs. Gawron')
    plt.xlabel('episodio')
    plt.ylabel('# viagens concluidas')
    plt.plot(gwrdata[:,0], gwrdata[:,4], label='gawron')
    for key,data in qdata.iteritems():
        plt.plot(data[:,0], data[:,4], label=key)
    
    plt.axis(axis)
    plt.legend(ncol=lcols)
    if len(outputs) > 1:
        plt.savefig(outputs[1])
        
    
    #ql vs fx
    plt.figure(figsize=(8,4))
    plt.title('Tarifacao via AR vs. Tarifacao fixa')
    plt.xlabel('episodio')
    plt.ylabel('# viagens concluidas')
    for key,data in qdata.iteritems():
        dshape = data.shape
        fd = fdata[key][:dshape[0]]
        vs = data / fd
        plt.plot(data[:,0], vs[:,4], label=key)
        
    plt.plot(range(400),[1]*400,'y--', label='base')
    
    plt.axis([0,400,.75,1.10])
    plt.legend(ncol=lcols)
    if len(outputs) > 2:
        plt.savefig(outputs[2])    
    
    plt.show()
    
    
    
def plot2(fname, outputs=[], ylabel='', axis = [0,400,500,1300],lcols=4):
    '''
    DEPRECATED?
    
    '''
    fxdata,qdata = get_data(fname)
    
    plt.figure()
    plt.title('Tarifacao fixa')
    plt.xlabel('episodio')
    plt.ylabel(ylabel)
    for key,data in fxdata.iteritems():
        plt.plot(data[:,0], data[:,1], label=key)
    plt.axis(axis)
    plt.legend(ncol=lcols)
    if len(outputs) > 0:
        plt.savefig(outputs[0])
        
    plt.figure()
    plt.title('Tarifacao via AR')
    plt.xlabel('episodio')
    plt.ylabel(ylabel)
    for key,data in qdata.iteritems():
        plt.plot(data[:,0], data[:,1], label=key)
    plt.axis(axis)
    plt.legend(ncol=lcols)
    if len(outputs) > 0:
        plt.savefig(outputs[1])
        
    plt.show()
    
    

if __name__ == '__main__':
    pass