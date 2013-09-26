'''
This script has several functions to plot metrics related to global performance.

A good way to use it is by running: python -i plotglobals.py

This way, the functions can be called by the user in the interactive console.

Created on 14/06/2013

@author: artavares
'''

import numpy as np
import matplotlib.pyplot as plt
from plotparams import *
from matplotlib.ticker import FuncFormatter

def get_data(fname, delim=','):
    keys = ['a05','gsn','uni','tm']
    
    fxdata = dict(
        (key,np.genfromtxt('fxprc-norm/%s/%s' % (key,fname),skip_header=1,delimiter=delim)) for key in keys
    )
    
    qdata = dict(
        (key,np.genfromtxt('ql03-norm/%s/%s' % (key,fname),skip_header=1,delimiter=delim)) for key in keys
    )
    
    return (fxdata,qdata)

def plotgawron(figsz=(8,4),output=None,axis=[0,400,16000,22500]):
    '''
    Plots the absolute flow found in garwon's method
    
    '''
    g = np.genfromtxt('dua/global.csv', skip_header=1, delimiter='\t')
    plt.figure(figsize=(8,4))
    plt.title('Desempenho do metodo de Gawron', size=TITLE_SIZE)
    plt.xlabel('episodio', size=AXIS_FONTSIZE)
    plt.ylabel('# viagens concluidas', size=AXIS_FONTSIZE)
    plt.plot(g[:,0], g[:,4], label='gawron', ms=MARKER_SIZE + 1, markevery=MARKER_INTERVAL)
    plt.axis(axis)
    plt.legend()
    if output is not None:
        plt.savefig(output, bbox_inches='tight')
    
    plt.show()

def plotvsgwr(lcols=3,axis=[0,400,.6,1.08],oprefix=None, figsz = LONG_FIG_SIZE, mksz=MARKER_SIZE):
    '''
    Plots both fixed pricing and ql pricing compared to the gawron's method
    
    '''
    fdata,qdata = get_data('global.csv',delim='\t')
    gwrdata = np.genfromtxt('dua/global.csv', skip_header=1, delimiter='\t')
    
    axes = { 
        'a05': [0,400,.6,1.05],
        'tm': [0,400,.6,1.05],
        'uni': [0,400,.7,1.05],
        'gsn': [0,400,.7,1.05]
    }
    
    for key,data in qdata.iteritems():
        fig = plt.figure(figsize=figsz)
        ax = fig.add_subplot(111)
        plt.title('Distribuicao %s' % DIST_NAMES[key], size=TITLE_SIZE)
        plt.xlabel('episodio', size=AXIS_FONTSIZE)
        plt.ylabel('fluxo comparado', size=AXIS_FONTSIZE)
        dshape = data.shape
        gd = gwrdata[:dshape[0]]
        qvs = data / gd
        fvs = fdata[key] / gwrdata
        plt.plot(data[:,0], qvs[:,4], 'cd-', label='AR', ms=mksz, markevery=MARKER_INTERVAL-5,mec='c',mfc='None',mew=2,lw=2)
        plt.plot(fdata[key][:,0], fvs[:,4], 'go-', label='fixa', ms=mksz, markevery=MARKER_INTERVAL-5,mec='g',mfc='None',mew=2,lw=2)
        plt.plot(range(400),[1]*400,'--', color='orange', label='base (gawron)',lw=3)
        plt.axis(axes[key])
        plt.legend(ncol=lcols,numpoints=1,loc=4)
        for label in ax.get_yticklabels() + ax.get_xticklabels():
            label.set_size(TICK_FONTSIZE)
        
        plt.subplots_adjust(bottom=BOTTOM_MARGIN)
        if oprefix is not None:
            plt.savefig('/home/anderson/Diss/texto/img/%s_%s.eps' % (oprefix,key), bbox_inches='tight')
#    if len(outputs) > 2:
#        plt.savefig(outputs[2])    
    
    plt.show()
    
    
def revenue(lcols=3,axis=[0,400,.6,1.08],oprefix=None, figsz = REDUCED_FIG_SIZE, mksz=MARKER_SIZE):
    '''
    Plots revenue in 4 charts
    
    '''
    fdata,qdata = get_data('totalrevenue.csv')
    
    axes = { 
        'a05': [0,400,.6,1.05],
        'tm': [0,400,.6,1.05],
        'uni': [0,400,.7,1.05],
        'gsn': [0,400,.7,1.05]
    }
    
    for key,data in qdata.iteritems():
        fig = plt.figure(figsize=figsz)
        ax = fig.add_subplot(111)
        plt.title('Distribuicao %s' % DIST_NAMES[key], size=TITLE_SIZE)
        plt.xlabel('episodio', size=AXIS_FONTSIZE)
        plt.ylabel('arrecadacao (milhoes)', size=AXIS_FONTSIZE)
        plt.plot(
            qdata[key][:,0], qdata[key][:,1], 
            'cd-', label='AR', ms=mksz, 
            markevery=MARKER_INTERVAL+10,
            mec='c',mfc='None',mew=2,lw=2
        )
        
        plt.plot(
            fdata[key][:,0], fdata[key][:,1], 
            'go-', label='fixa', ms=mksz, 
            markevery=MARKER_INTERVAL+10,
            mec='g',mfc='None',mew=2,lw=2
        )
        plt.axis([0,400,2000000,9000000])
        plt.gca().yaxis.set_major_formatter(FuncFormatter(millions))
        plt.legend(ncol=lcols,numpoints=1,loc=4)
        for label in ax.get_yticklabels() + ax.get_xticklabels():
            label.set_size(TICK_FONTSIZE)
        
        plt.subplots_adjust(bottom=BOTTOM_MARGIN)
        if oprefix is not None:
            plt.savefig('/home/anderson/Diss/texto/img/%s_%s.eps' % (oprefix,key), bbox_inches='tight')
#    if len(outputs) > 2:
#        plt.savefig(outputs[2])    
    
    plt.show()    
    



def plotflow(outputs=[],lcols=3,axis=[0,400,10000,24000]):
    '''
    Deprecated -- use plotvsgwr instead
    
    '''
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
    
    
    
def plot2(fname, outputs=[], ylabel='', axis = [0,400,500,1100],lcols=2, figsz=REDUCED_FIG_SIZE):
    '''
    Plots a result for fixed and RL approaches (useful for reward)
    
    '''
    fxdata,qdata = get_data(fname)
    
    fig = plt.figure(figsize=figsz)
    ax = fig.add_subplot(111)
    
    mk_evry = { #for reward--reinf. learning data
        'a05': (0,MARKER_INTERVAL),
        'uni': (0,MARKER_INTERVAL),
        'gsn': (10,MARKER_INTERVAL),
        'tm': (10,MARKER_INTERVAL),
    }
    
    plt.title('Tarifacao fixa', size=TITLE_SIZE)
    plt.xlabel('episodio', size=AXIS_FONTSIZE)
    plt.ylabel(ylabel, size=AXIS_FONTSIZE)
    for key,data in fxdata.iteritems():
        plt.plot(
            data[:,0], data[:,1], 
            DIST_MARKERS[key], label=DIST_NAMES[key],
            color=DIST_COLORS[key], 
            ms=MARKER_SIZE-3, markevery=mk_evry[key],
            mec=DIST_COLORS[key],
            mfc='None', mew=2, lw=2
        )
    
    plt.axis(axis)
    plt.legend(ncol=lcols,numpoints=1,loc=4)#lower right
    for label in ax.get_yticklabels() + ax.get_xticklabels():
            label.set_size(TICK_FONTSIZE)
            
    plt.subplots_adjust(bottom=0.14)
    if len(outputs) > 0:
        plt.savefig(outputs[0],bbox_inches='tight')
        
    fig = plt.figure(figsize=figsz)
    ax = fig.add_subplot(111)
    plt.title('Tarifacao via AR', size=TITLE_SIZE)
    plt.xlabel('episodio', size=AXIS_FONTSIZE)
    plt.ylabel(ylabel, size=AXIS_FONTSIZE)
    for key,data in qdata.iteritems():
        plt.plot(
            data[:,0], data[:,1], 
            DIST_MARKERS[key], label=DIST_NAMES[key],
            color=DIST_COLORS[key], 
            ms=MARKER_SIZE-3, markevery=mk_evry[key],
            mec=DIST_COLORS[key], mfc='None',
            mew=2, lw=2
        )
        
    plt.axis(axis)
    plt.legend(ncol=lcols,numpoints=1,loc=4)#lower right
    for label in ax.get_yticklabels() + ax.get_xticklabels():
            label.set_size(TICK_FONTSIZE)
            
    plt.subplots_adjust(bottom=0.14)
    if len(outputs) > 0:
        plt.savefig(outputs[1],bbox_inches='tight')
        
    plt.show()
    
def plotrevenue(fname='totalrevenue.csv', outputs=[], ylabel='arrecadacao (milhoes)', axis = [0,400,2000000,11000000],lcols=2, figsz=REDUCED_FIG_SIZE):
    '''
    Plots a result for fixed and RL approaches
    
    '''
    fxdata,qdata = get_data(fname)
    
    fig = plt.figure(figsize=figsz)
    ax = fig.add_subplot(111)
    
    #millions = lambda str: '%2.0f' % float(str) * 10
    mkst = {
       'a05': 0,
       'tm':0,
       'gsn':0,
       'uni':15
    }
    
    plt.title('Tarifacao fixa', size=TITLE_SIZE)
    plt.xlabel('episodio', size=AXIS_FONTSIZE)
    plt.ylabel(ylabel, size=AXIS_FONTSIZE)
    for key,data in fxdata.iteritems():
        plt.plot(data[:,0], data[:,1], DIST_MARKERS[key], label=DIST_NAMES[key], ms=MARKER_SIZE, markevery=(mkst[key],MARKER_INTERVAL+10,),mfc='None',color=DIST_COLORS[key],mec=DIST_COLORS[key],mew=3,lw=2)
    #ax.set_yscale('log',basey=2,subsy=[1,3,5,6,7])
    plt.axis([0,400,2300000,4800000])
    plt.gca().yaxis.set_major_formatter(FuncFormatter(millions))
    plt.legend(ncol=lcols,numpoints=1,loc=4)
    for label in ax.get_yticklabels() + ax.get_xticklabels():
            label.set_size(TICK_FONTSIZE)
    
            
    #plt.subplots_adjust(bottom=0.14)
    if len(outputs) > 0:
        print 'saving to %s' % outputs[0]
        plt.savefig('/home/gauss/artavares/dissertacao/texto/img/' + outputs[0],bbox_inches='tight')
        
    fig = plt.figure(figsize=figsz)
    ax = fig.add_subplot(111)
    plt.title('Tarifacao via AR', size=TITLE_SIZE)
    plt.xlabel('episodio', size=AXIS_FONTSIZE)
    plt.ylabel(ylabel, size=AXIS_FONTSIZE)
    for key,data in qdata.iteritems():
        plt.plot(data[:,0], data[:,1], DIST_MARKERS[key], label=DIST_NAMES[key], ms=MARKER_SIZE, markevery=MARKER_INTERVAL+10,mfc='None',color=DIST_COLORS[key],mec=DIST_COLORS[key],mew=3,lw=2)
    #ax.set_yscale('log',basey=2,subsy=[1,3,5,6,7])
    #plt.axis([0,400,2000000,9000000])
    plt.gca().yaxis.set_major_formatter(FuncFormatter(millions))
    plt.legend(ncol=lcols,numpoints=1,loc=4)
    for label in ax.get_yticklabels() + ax.get_xticklabels():
            label.set_size(TICK_FONTSIZE)
            
    #plt.subplots_adjust(bottom=0.14)
    if len(outputs) > 1:
        print 'saving to %s' % outputs[1]
        plt.savefig('/home/gauss/artavares/dissertacao/texto/img/' + outputs[1],bbox_inches='tight')
        
    plt.show()
    
def millions(x, pos):
    """Formatter for Y axis, values are in millions"""
    return '%.1f' % (x * 1e-6)    
        
if __name__ == '__main__':
    pass