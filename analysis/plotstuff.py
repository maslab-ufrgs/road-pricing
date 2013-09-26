'''
This script generates plots for specific experiments.

It was once used to visualize data in order to discuss some results.

Created on May 31, 2013

@author: anderson

'''
import numpy as np
import matplotlib.pyplot as plt

def plotstuff():#datafname, xdatacol=0, ydatacol=1, headersz=1, delim=',', subplot=111 ):
    #data = np.genfromtxt(datafname, skip_header=headersz, delimiter=delim)
    #plt.plot(data[:,xdatacol], data[:,ydatacol])
    pass

def plotglobal():
    qdata = np.genfromtxt('2013-04-18_qlparams/22h53/a85-ql03-gsn-summary.csv',skip_header=1,delimiter='\t')[:,:-1]
    fxdata = np.genfromtxt('2013-05-05_fxprc/13h11/a85-fx-summary.csv',skip_header=1,delimiter='\t')[:,:-1]
    duadata = np.genfromtxt('2013-04-18_19h41_dua/a85-dua-summary.csv',skip_header=1,delimiter='\t')[:,:-1]
    
    #ratio
    #plt.plot(qdata[:,4]/fxdata[:,4])plt.subplot(412)
    plt.subplot(411)
    plt.plot(qdata[:,4],'g:')
    plt.plot(fxdata[:,4],'r--')
    plt.plot(duadata[:,4],'b')
    
    
    qdata = np.genfromtxt('2013-05-06_ql03/14h42/a85-ql03-all05-summary.csv',skip_header=1,delimiter='\t')[:,:-1]
    fxdata = np.genfromtxt('2013-05-05_fxprc/13h12/a85-fx-summary.csv',skip_header=1,delimiter='\t')[:,:-1]
    plt.subplot(412)
    plt.plot(qdata[:,4],'g:')
    plt.plot(fxdata[:,4],'r--')
    plt.plot(duadata[:,4],'b')
    
    qdata = np.genfromtxt('2013-05-06_ql03/14h43/a85-ql03-uni-summary.csv',skip_header=1,delimiter='\t')[:,:-1]
    fxdata = np.genfromtxt('2013-05-05_fxprc/13h13/a85-fx-summary.csv',skip_header=1,delimiter='\t')[:,:-1]
    plt.subplot(413)
    plt.plot(qdata[:,4],'g:')
    plt.plot(fxdata[:,4],'r--')
    plt.plot(duadata[:,4],'b')
    
    qdata = np.genfromtxt('2013-05-06_ql03/14h44/a85-ql03-tm-summary.csv',skip_header=1,delimiter='\t')[:,:-1]
    fxdata = np.genfromtxt('2013-05-05_fxprc/13h14/a85-fx-summary.csv',skip_header=1,delimiter='\t')[:,:-1]
    plt.subplot(414)
    plt.plot(qdata[:,4],'g:')
    plt.plot(fxdata[:,4],'r--')
    plt.plot(duadata[:,4],'b')
    
def _plotindiv_alldrv(w = 'z'):
    qdata = np.genfromtxt('2013-04-18_qlparams/22h53/ar85-ql03_%s.dvs' % w,skip_header=1, delimiter='\t')
    fxdata = np.genfromtxt('2013-05-05_fxprc/13h11/a85-fx_%s.dvs' % w,skip_header=1,delimiter='\t')
    
    plt.subplot(421)
    plotabsolute(fxdata, qdata)
    
    plt.subplot(422)
    plotrelative(fxdata, qdata)
    
    qdata = np.genfromtxt('2013-05-06_ql03/14h42/ar85-ql03-all05_%s.dvs' % w,skip_header=1, delimiter='\t')
    fxdata = np.genfromtxt('2013-05-05_fxprc/13h12/a85-fx_%s.dvs' % w,skip_header=1,delimiter='\t')
    
    plt.subplot(4,2,3)
    plt.plot(range(0,400), fxdata[:,1],'r--')
    plt.plot(range(0,392), qdata[:,1],'g:')
    
    plt.subplot(4,2,4)
    plt.plot(range(0,400), fxdata[:,1] / np.array([fxdata[0,1]]*400),'r--')
    plt.plot(range(0,392), qdata[:,1] / np.array([qdata[0,1]]*392),'g:')
    
    
    qdata = np.genfromtxt('2013-05-06_ql03/14h43/ar85-ql03-uni_%s.dvs' % w,skip_header=1, delimiter='\t')
    fxdata = np.genfromtxt('2013-05-05_fxprc/13h13/a85-fx_%s.dvs' % w,skip_header=1,delimiter='\t')
    
    plt.subplot(4,2,5)
    plotabsolute(fxdata, qdata)
    
    plt.subplot(4,2,6)
    plotrelative(fxdata, qdata)
    
    qdata = np.genfromtxt('2013-05-06_ql03/14h44/a85-ql_%s.dvs' % w,skip_header=1, delimiter='\t')
    fxdata = np.genfromtxt('2013-05-05_fxprc/13h14/a85-fx_%s.dvs' % w,skip_header=1,delimiter='\t')
    
    plt.subplot(4,2,7)
    plotabsolute(fxdata, qdata)
    
    plt.subplot(4,2,8)
    plotrelative(fxdata, qdata)
    
def plotindiv_alldrv():
    _plotindiv_alldrv('z')

def plotindiv_alldrv_tt():
    _plotindiv_alldrv('tt')
    
    
def plot_all():
    #global
    qdata = np.genfromtxt('2013-04-18_qlparams/22h53/a85-ql03-gsn-summary.csv',skip_header=1,delimiter='\t')[:,:-1]
    fxdata = np.genfromtxt('2013-05-05_fxprc/13h11/a85-fx-summary.csv',skip_header=1,delimiter='\t')[:,:-1]
    duadata = np.genfromtxt('2013-04-18_19h41_dua/a85-dua-summary.csv',skip_header=1,delimiter='\t')[:,:-1]
    
    #ratio
    #plt.plot(qdata[:,4]/fxdata[:,4])plt.subplot(412)
    plt.subplot(421)
    plt.plot(qdata[:,4],'g:')
    plt.plot(fxdata[:,4],'r--')
    plt.plot(duadata[:,4],'b')
    
    
    qdata = np.genfromtxt('2013-05-06_ql03/14h42/a85-ql03-all05-summary.csv',skip_header=1,delimiter='\t')[:,:-1]
    fxdata = np.genfromtxt('2013-05-05_fxprc/13h12/a85-fx-summary.csv',skip_header=1,delimiter='\t')[:,:-1]
    plt.subplot(423)
    plt.plot(qdata[:,4],'g:')
    plt.plot(fxdata[:,4],'r--')
    plt.plot(duadata[:,4],'b')
    
    qdata = np.genfromtxt('2013-05-06_ql03/14h43/a85-ql03-uni-summary.csv',skip_header=1,delimiter='\t')[:,:-1]
    fxdata = np.genfromtxt('2013-05-05_fxprc/13h13/a85-fx-summary.csv',skip_header=1,delimiter='\t')[:,:-1]
    plt.subplot(425)
    plt.plot(qdata[:,4],'g:')
    plt.plot(fxdata[:,4],'r--')
    plt.plot(duadata[:,4],'b')
    
    qdata = np.genfromtxt('2013-05-06_ql03/14h44/a85-ql03-tm-summary.csv',skip_header=1,delimiter='\t')[:,:-1]
    fxdata = np.genfromtxt('2013-05-05_fxprc/13h14/a85-fx-summary.csv',skip_header=1,delimiter='\t')[:,:-1]
    plt.subplot(427)
    plt.plot(qdata[:,4],'g:')
    plt.plot(fxdata[:,4],'r--')
    plt.plot(duadata[:,4],'b')
    
    
    #individual
    qdata = np.genfromtxt('2013-04-18_qlparams/22h53/drvdata_z.fdvs',skip_header=1, delimiter=',')
    fxdata = np.genfromtxt('2013-05-05_fxprc/13h11/drvdata_z.fdvs',skip_header=1,delimiter=',')
    
    plt.subplot(422)
    plotabsolute(fxdata, qdata)
    
    qdata = np.genfromtxt('2013-05-06_ql03/14h42/drvdata_z.fdvs',skip_header=1, delimiter=',')
    fxdata = np.genfromtxt('2013-05-05_fxprc/13h12/drvdata_z.fdvs',skip_header=1,delimiter=',')
    
    plt.subplot(4,2,4)
    plt.plot(range(0,400), fxdata[:,1],'r--')
    plt.plot(range(0,392), qdata[:,1],'g:')
    
    qdata = np.genfromtxt('2013-05-06_ql03/14h43/drvdata_z.fdvs',skip_header=1, delimiter=',')
    fxdata = np.genfromtxt('2013-05-05_fxprc/13h13/drvdata_z.fdvs',skip_header=1,delimiter=',')
    
    plt.subplot(4,2,6)
    plotabsolute(fxdata, qdata)
    
    qdata = np.genfromtxt('2013-05-06_ql03/14h44/drvdata_z.fdvs',skip_header=1, delimiter=',')
    fxdata = np.genfromtxt('2013-05-05_fxprc/13h14/drvdata_z.fdvs',skip_header=1,delimiter=',')
    
    plt.subplot(4,2,8)
    plotabsolute(fxdata, qdata)
    
def plotindiv_first():
    
    qdata = np.genfromtxt('2013-04-18_qlparams/22h53/drvdata_z.fdvs',skip_header=1, delimiter=',')
    fxdata = np.genfromtxt('2013-05-05_fxprc/13h11/drvdata_z.fdvs',skip_header=1,delimiter=',')
    
    plt.subplot(421)
    plotabsolute(fxdata, qdata)
    
    plt.subplot(422)
    plotrelative(fxdata, qdata)
    
    qdata = np.genfromtxt('2013-05-06_ql03/14h42/drvdata_z.fdvs',skip_header=1, delimiter=',')
    fxdata = np.genfromtxt('2013-05-05_fxprc/13h12/drvdata_z.fdvs',skip_header=1,delimiter=',')
    
    plt.subplot(4,2,3)
    plt.plot(range(0,400), fxdata[:,1],'r--')
    plt.plot(range(0,392), qdata[:,1],'g:')
    
    plt.subplot(4,2,4)
    plt.plot(range(0,400), fxdata[:,1] / np.array([fxdata[0,1]]*400),'r--')
    plt.plot(range(0,392), qdata[:,1] / np.array([qdata[0,1]]*392),'g:')
    
    
    qdata = np.genfromtxt('2013-05-06_ql03/14h43/drvdata_z.fdvs',skip_header=1, delimiter=',')
    fxdata = np.genfromtxt('2013-05-05_fxprc/13h13/drvdata_z.fdvs',skip_header=1,delimiter=',')
    
    plt.subplot(4,2,5)
    plotabsolute(fxdata, qdata)
    
    plt.subplot(4,2,6)
    plotrelative(fxdata, qdata)
    
    qdata = np.genfromtxt('2013-05-06_ql03/14h44/drvdata_z.fdvs',skip_header=1, delimiter=',')
    fxdata = np.genfromtxt('2013-05-05_fxprc/13h14/drvdata_z.fdvs',skip_header=1,delimiter=',')
    
    plt.subplot(4,2,7)
    plotabsolute(fxdata, qdata)
    
    plt.subplot(4,2,8)
    plotrelative(fxdata, qdata)
    
    
    
def plotabsolute(fxdata, qdata, xticks=400):
    plt.plot(range(0,xticks), fxdata[:,1],'r--')
    plt.plot(range(0,xticks), qdata[:,1],'g:')
    
def plotrelative(fxdata, qdata, xticks=400):
    plt.plot(range(0,xticks), fxdata[:,1] / np.array([fxdata[0,1]]*xticks),'r--')
    plt.plot(range(0,xticks), qdata[:,1] / np.array([qdata[0,1]]*xticks),'g:')
    
if __name__ == 'main':
    pass
    
    