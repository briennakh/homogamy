#!/usr/local/bin/python -u
# -*- coding: utf-8 -*-
# We generally follow PEP 8: http://legacy.python.org/dev/peps/pep-0008/

'''
    Samir Jain, Eric Epstein, Trevor Klemp, Maggie Gray, Selman Jawed, Derek 
    Braun* (*derek.braun@gallaudet.edu)
    
    Produces graphs for the data files created by Simulator.py.
    Last updated: 23-Jun-2017 by Derek Braun
'''

import argparse
import matplotlib
import numpy
matplotlib.use('pdf')
from matplotlib import pyplot as plt, lines
import fileio
import os

#see: http://matplotlib.sourceforge.net/users/customizing.html
ASPECT_RATIO = (16,9)
BLUE = '#00457c'
BUFF = '#e8d4a2'
PLOT_PARAMS = { 'print':
                { 'aspect'      : 1.0,
                  'colors'      : ['black', 'white', BLUE,
                                    BUFF, 'LightSteelBlue',
                               'LightGoldenRodYellow','LightSkyBlue',
                               'LightPink','LightGreen','LightSalmon'],
                  'font'        : 12,
                  'title'       : 14,
                  'axes'        : 12,
                  'ticklabel'   : 10,
                  'minsize'     : 6,
                  'linewidth'   : 1,
                  'minwidth'    : 0.5},
                'slides_light_bg':
                { 'aspect'      : 1.6,
                  'colors'      : ['black', 'white', BLUE,
                                   BUFF, 'LightSteelBlue',
                                   'LightGoldenRodYellow','LightSkyBlue',
                                   'LightPink','LightGreen','LightSalmon'],
                  'font'        : 20,
                  'title'       : 14,
                  'axes'        : 20,
                  'ticklabel'   : 20,
                  'minsize'     : 8,
                  'linewidth'   : 1,
                  'minwidth'    : 0.5},
                'slides_dark_bg':
                {   'aspect'    : 1.6,
                    'colors'    : ['white', 'black', BUFF,
                                   BLUE, 'LightSteelBlue',
                                   'LightGoldenRodYellow','LightSkyBlue',
                                   'LightPink','LightGreen','LightSalmon'],
                    'font'      : 20,
                    'title'     : 14,
                    'axes'      : 20,
                    'ticklabel' : 20,
                    'minsize'   : 8,
                    'linewidth' : 1,
                    'minwidth'  : 0.5}}


def _set_plot_params(use='print', scaling=1.0):
    '''
        This routine sets all the plot parameters globally, which takes effect
        with the next plot. Setting these parameters globally using 
        matplotlib's rcParams simplifies the downstream charting code because
        it is no longer necessary specify the size and color parameters
        in every charting command.
        
        In the future, consider: 
            (a) using matplotlib.rc_params_from_file, and setting up a 
                different file for each use.
            (b) using the same rcParams name for each dict field, then
                the rcparams can just be loaded iteratively, although
                this would complicate scaling. Scaling would need to be done
                by reading the appropriately scalable rcParams, scaling,
                then rewriting (which could also be done iteratively).
    '''
    d = PLOT_PARAMS[use]
    matplotlib.rc('font',  size=max(d['font']*scaling, d['minsize']))
    #matplotlib.rc('figure',titlesize=d['title']*scaling)
    matplotlib.rc('font',  size=max(d['font']*scaling, d['minsize']))
    matplotlib.rc('text',  color=d['colors'][0],
                           usetex=False)
    matplotlib.rc('axes',  titlesize=max(d['title']*scaling, d['minsize']),
                           labelsize=max(d['axes']*scaling, d['minsize']),
                           labelcolor=d['colors'][0],
                           linewidth=max(d['linewidth']*scaling, d['minwidth']),
                           edgecolor='#cccccc')
    matplotlib.rc('xtick', labelsize=max(d['ticklabel']*scaling, d['minsize']),
                           color=d['colors'][0])
    matplotlib.rc('ytick', labelsize=max(d['ticklabel']*scaling, d['minsize']),
                           color=d['colors'][0])
    matplotlib.rc('lines', linewidth = max(d['linewidth']*scaling, d['minwidth']),
                           color=d['colors'][0])
    matplotlib.rc('figure.subplot', wspace=0.3,
                                       hspace=0.3)
    return d['colors']


def density_plot(ax, X, Ya, title=None, xlabel=None, ylabel=None, 
                            use='print', gradients=32, scaling=1.0):
    # The algorithm is horribly inefficient and confusing to read, but it works 
    # very well. I have found that a smaller number of gradient steps seems to 
    # give better results, and this also makes the algorithm run faster; 
    # therefore it may not be worth the effort to re-write the algorithm.
    # Currently it takes about 5 seconds to make a plot.
    '''
        Produces a density plot.
        The median values and 95% credible intervals are also represented 
        with lines.
        
        Accepts:
            ax              a matplotlib.pyplot axis instance
            X               an array of x values
            Ya              an array of an array of y values
            xlabel          x axis label string
            ylabel          y axis label string
            use             determines the font size and line width according
                            to the global PLOT_PARAMS dict.
            gradients       the number of gradients. More gradients means
                            a smoother looking density plot at the cost of
                            many more polygons and therefore a larger vector
                            file which may not, for example, print.
            scaling         scaling factor needed for creating subplots,
                            where the text and lines need to be scaled down.
    '''
    _set_plot_params(use, scaling)
    # calculate gradient
    Y_upper_cis = []
    Y_medians = []
    Y_lower_cis = []
    Ygrads = []
    for Y in Ya:
        Y = list(Y)
        Y = map(float, Y)
        Y.sort()
        Y_upper_cis.append(Y[int(0.975*len(Y))])
        Y_medians.append(numpy.median(Y))
        Y_lower_cis.append(Y[int(0.025*len(Y))])
    Ygrads = []
    for i in range(gradients):
        Yugs=[]
        Ylgs=[]
        for Y in Ya:
            # horribly inefficient
            Y = list(Y)
            Y = map(float, Y)
            Y.sort()
            step = len(Y)/(2*gradients)
            uidx = len(Y) - i*step - 1
            lidx = i*step
            Yugs.append(Y[uidx])
            Ylgs.append(Y[lidx])
        Ygrads.append((Yugs,Ylgs))
        
    
    ax.set_xlim(min(X),max(X))
    if title is not None:
        ax.set_title(title)
    if xlabel is not None:
        ax.set_xlabel(xlabel)
    if ylabel is not None:
        ax.set_ylabel(ylabel)
    for i, Yg in enumerate(Ygrads):
        ax.fill_between(X, Yg[0], Yg[1], color=BUFF, alpha=1./(gradients/4.))
    ax.plot(X, Y_upper_cis, color=BLUE)
    ax.text(max(X)*1.02, Y_upper_cis[-1], '{:.2f}'.format(Y_upper_cis[-1]), 
            va='bottom', ha='left')
    ax.plot(X, Y_medians, color=BLUE)
    ax.text(max(X)*1.02, max(Y_medians), '{:.2f}'.format(Y_medians[-1]), 
            va='bottom', ha='left')
    ax.plot(X, Y_lower_cis, color=BLUE)
    ax.text(max(X)*1.02, Y_lower_cis[-1], '{:.2f}'.format(Y_lower_cis[-1]), 
            va='top', ha='left')
    ax.grid(False)  
    return ax
    
def adjustFigAspect(fig, aspect=1.5):
        '''
            Adjusts the whitespace around a figure so that each subplot 
            achieves the desired aspect ratio (square by default).
            Accepts a matplotlib figure object.
            Doesn't need to return anything because it directly modifies the 
            figure object.
        '''
        xsize, ysize = fig.get_size_inches()
        minsize = min(xsize, ysize)
        xlim = .4*minsize/xsize
        ylim = .4*minsize/ysize
        if aspect < 1:
            xlim *= aspect
        else:
            ylim /= aspect
        fig.subplots_adjust(left=.375-xlim,
                            right=.625+xlim,
                            bottom=.375-ylim,
                            top=.625+ylim)
    
def write_summary_density_plot(filename, Xarr, Yarr, nrows, ncols, multiplot_titles=[], 
                               title=None, xlabel=None, ylabel=None,
                               use='print'):
    '''
        Produces a type of line chart, where for each x, the median value is 
        shown as a line, and the area between the 5% and 95% CI are shaded.
        
        Accepts:
            filename    the filename (including path and extension) for the
                        new plot to be created
            Xarr        an array of arrays of x values
            Yarr        an array of arrays consisting of a tuple of three 
                        Y values:
                            (5%, median, 95%)
            multiplot_titles      an array of plot multiplot_titles
            title       main plot title
            xlabel      x axis label string
            ylabel      y axis label string
            
        Doesn't return anything
        Writes a PDF file to filename.
        
        Examples for setting up multiple charts on shared axes are at:
        http://matplotlib.org/examples/pylab_examples/subplots_demo.html
    '''

    _set_plot_params(use, scaling=1./nrows)
    plt.clf()
    fig, axarr = plt.subplots(nrows, ncols, sharex=True, sharey=False)
    fig.suptitle(title)
    
    if multiplot_titles[0] == 'Change of Allele "a" over Time':
        fig, axarr = plt.subplots(nrows, ncols, sharex=True, sharey=False)
        for ax, X, Ya, title in zip(axarr.flat, Xarr, Yarr, multiplot_titles[0:5]):
            ax = density_plot(ax, X, Ya,
                              xlabel=xlabel,
                              ylabel=ylabel,
                              title=title,
                              use=use,
                                scaling=1./nrows)
        axarr[0,0].set_ylabel('a',fontsize=8,labelpad=10,rotation=0)
        axarr[0,1].set_ylabel('AA',fontsize=8,labelpad=10,rotation=0)
        axarr[1,0].set_ylabel('Aa',fontsize=8,labelpad=10,rotation=0)
        axarr[1,1].set_ylabel('aa',fontsize=8,labelpad=10,rotation=0)
        axarr[2,0].set_ylabel('F',fontsize=8,labelpad=10,rotation=0)
        fig.suptitle(multiplot_titles[-1], fontsize=10, fontweight='bold')
    
    else:
        for ax, X, Ya, title in zip(axarr.flat, Xarr, Yarr, multiplot_titles):
            ax = density_plot(ax, X, Ya,
                              xlabel=xlabel,
                              ylabel=ylabel,
                              title=title,
                              use=use,
                              scaling=1./nrows)
    adjustFigAspect(fig)
    plt.savefig(filename, transparent=True)
    plt.close()

def write_density_plot(filename, X, Y, title=None, xlabel=None, ylabel=None, use='print'):
    _set_plot_params(use)
    plt.clf()
    fig = plt.figure()
    if title is not None:
        plt.title(title)
    ax = fig.add_subplot(111)
    ax = density_plot(ax, X, Y, xlabel=xlabel, ylabel=ylabel, use=use)
    plt.savefig(filename, transparent=True)
    plt.close()
    
    
#
#   MAIN ROUTINE
#
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__,
                    formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('filename',
                        help = 'filename for data file')
    parser.add_argument('-s','--sample arg',action='store_true',
                        help = 'sample argument')
    args=parser.parse_args()
    
    if os.path.isfile(args.filename):
        e = fileio.Experiment(args.filename)
        print '  Reading {}'.format(args.filename)
    else:
        print '  File not found.'
   
    X = e.select('gen', 0)    
    title='N={:,}   '\
          'fitness={:.1f}    '\
          'homogamy={:.1f}'\
          ''.format(int(e.constant_pop_size),
                    float(e.aa_fitness),
                    float(e.aa_homogamy))
     
    # Create summary (TEST) contour charts
    for use in ['print']:
        bn1 = 'summaryFrequency_Comparison.{}.pdf'.format(use)
        filename = os.path.join(args.path, bn1)
        print "Saving summary chart to '{}'.".format(filename)
        Ya = [multiplot_a_freqs[0]]+[multiplot_AA_Freqs[0]]+[multiplot_Aa_Freqs[0]]+\
        [multiplot_aa_Freqs[0]]+[multiplot_FAa[0]]
        multiplot_titles = 'Change of Allele "a" over Time',\
        'Change of Genotype "AA" over Time', 'Change of Genotype "Aa" over Time',\
        'Change of Genotype "aa" over Time', 'Change of "F" over Time',\
        'Fitness 1.0, Homogamy '+aa_HOMOGAMY,' N = 10,000'
        gm.write_summary_density_plot(filename, 
                                   Xarr=[X for i in range(len(Ya))],
                                   Yarr=Ya,
                                   nrows=3,
                                   ncols=2,
                                   title=title,
                                   multiplot_titles=multiplot_titles,
                                   xlabel='Generations',
                                   ylabel='Allele Frequency',
                                   use = use)