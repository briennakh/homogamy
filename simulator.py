#!/usr/local/bin/python -u
# -*- coding: utf-8 -*-
# We generally follow PEP 8: http://legacy.python.org/dev/peps/pep-0008/

'''
    Samir Jain, Eric Epstein, Trevor Klemp, Maggie Gray, Selman Jawed, Derek
    Braun* (*derek.braun@gallaudet.edu)

    Simulation module which uses simuPOP. Simulation parameters are set via
    setting global variables, and, for changing assortative mating, sometimes
    by changing the code.

    Last updated: 2-Apr-2019 by Derek Braun
'''


# Simulation Parameters
# At least some of these variables MUST be globals b/c this is the only way to
# get them into the customChooser generator function
aa_HOMOGAMY = 0.9
aa_FITNESS = 1.0
a_FREQ = 0.01304
#DEAFNESS_FREQ = 0.01
POP_SIZE = 10000
GEN = 100
SIMULATIONS = 10000

import fileio
experiment = fileio.Experiment( constant_pop_size   = POP_SIZE,
                                aa_fitness          = aa_FITNESS,
                                aa_homogamy         = aa_HOMOGAMY,
                                a                   = a_FREQ,
                                gen                 = GEN)

import os
import time
import random
import argparse
import subprocess
import multiprocessing
import simuOpt
simuOpt.setOptions(optimized=True, numThreads=0, quiet=True)
import simuPOP as sim

def customChooser(pop, subPop):
    '''
        Generator function which chooses parents.

        Upon initialization, this chooser mates couples in a monogamous
        mating scheme.

        The algorithm goes through each eligible person
        listwise. If that person is deaf, that person either marries deaf
        or hearing based on the probability in aa_HOMOGAMY. If either
        parent is dead, they have a number of children based on the
        fitness in aa_FITNESS (non-integers are handled with a randomizer).
    '''

    def mate_with_fitness(parent1, parent2):
        '''
            Mates a couple. Creates a number of entries in the
            final list (representing the parents for each child born, based on
            reproductive fitness. Non-integer number of children are handled by
            using a randomizer for the fractional amount.

            Accepts:
            parent1, parent2             sim.individual objects

            Returns a list of (parent1, parent2) parental pairs
            reflecting fitness.
        '''

        if parent1.genotype() == [1,1] or parent2.genotype() == [1,1]:
            r = float(aa_FITNESS)
            l = []
            while r >= 1:
                l += [(parent1, parent2)]
                r -= 1
            if random.random() < r:
                l += [(parent1, parent2)]
            return l
        else:
            return [(parent1, parent2)]


    def output_diagnostics(couples):
        '''
            Outputs some summary statistics about the final mating pool.
            Helps with troubleshooting.

            Accepts:
            couples             a list of (female, male) sim.individual objects
        '''
        ddm = 0     # deaf-deaf marriages
        dp = 0      # deaf parents

        for parent1, parent2 in couples:
            if parent1.genotype() == [1,1] and parent2.genotype() == [1,1]:
                ddm += 1
            if parent1.genotype() == [1,1]:
                dp += 1
            if parent2.genotype() == [1,1]:
                dp += 1
        print 'couples = {:,d}  homogamy = {:.1%}  deaf-deaf marriages = {:,d} ({:.1%})' \
              ''.format(len(couples), 2.*ddm/dp, ddm, ddm/float(len(couples)))

    deaf_parents = []
    hearing_parents = []
    couples = []

    # bin individuals
    for person in pop.individuals():
        if person.genotype() == [1,1]:
            deaf_parents.append(person)
        else:
            hearing_parents.append(person)

    # calculate how many deaf-deaf marriages we need, then marry them off
    homogamy_target = round(aa_HOMOGAMY * len(deaf_parents)/2)
    while len(deaf_parents) >= 2 and homogamy_target > 0:
        couples += mate_with_fitness(deaf_parents.pop(), deaf_parents.pop())
        homogamy_target -= 1

    # Move remaining deaf parents into the hearing bin, so that their alleles
    # are not lost. Then, mate off the rest
    hearing_parents += deaf_parents
    #hearing_parents.shuffle()
    while len(hearing_parents) >= 2:
        couples += mate_with_fitness(hearing_parents.pop(), hearing_parents.pop())

    output_diagnostics(couples)

    # This is what's called whenever the generator function is called.
    while True:
        yield random.choice(couples)


def simuAssortativeMatingWithFitness(constant_pop_size, gen, a,
                                    aa_fitness, aa_homogamy):
    '''
        Accepts:
        constant_pop_size   population size, which remains constant throughout
        gen                 number of generations
        a                   starting frequency of the a allele
        aa_fitness          _relative_ fitness of deaf (aa) individuals
        aa_homogamy         the percent of assortative mating between
                            deaf individuals
        Returns a dict containing the results from the simulation:
        gen                 generation number
        AA/Aa_size          size of the AA/aa population
        aa_size             size of the aa population
        A                   frequency of the A allele
        a                   frequency of the a allele

        Adopted from: http://simupop.sourceforge.net/Cookbook/AssortativeMating
    '''
    sim.setRNG(random.seed(sim.getRNG().seed()))
    pop = sim.Population(constant_pop_size, loci=[1])
    pop.dvars().headers = []
    pop.dvars().row = []
    pop.evolve(
        initOps= [sim.InitSex(),
                  # Assigns individuals randomly to be male or female.
                  # This can result in slightly more males or females,
                  # which can cause errors if the wrong mating scheme is
                  # selected.
                  sim.InitGenotype(freq=[1-a, a])
                  ],
        matingScheme = sim.HomoMating(
                        chooser = sim.PyParentsChooser(customChooser),
                        generator = sim.OffspringGenerator(sim.MendelianGenoTransmitter())),
        postOps = [sim.Stat(alleleFreq=[0], genoFreq=[0]),
                   sim.PyExec(r"headers += ['gen','A', 'a',"\
                               "'AA', 'Aa', 'aa',"\
                               "'AA_size', 'Aa_size', 'aa_size',"\
                               "'F']"),
                   sim.PyExec(r"row += [gen, "\
                               "alleleFreq[0][0],"                             # A          \
                               "alleleFreq[0][1],"                             # a          \
                               "genoFreq[0][(0,0)],"                           # AA         \
                               "genoFreq[0][(0,1)]+genoFreq[0][(1,0)],"        # Aa         \
                               "genoFreq[0][(1,1)],"                           # aa         \
                               "genoNum[0][(0,0)],"                            # AA_size    \
                               "genoNum[0][(0,1)]+genoNum[0][(1,0)],"          # Aa_size    \
                               "genoNum[0][(1,1)],"                            # aa_size    \
                               "1.0-((genoFreq[0][(0,1)]+genoFreq[0][(1,0)])/" # F          \
                               "(2.0*alleleFreq[0][0]*alleleFreq[0][1]))"\
                               "if alleleFreq[0][0] != 0.0 and alleleFreq[0][1]"\
                               "!= 0.0 else 0.0]")
                   ],
        gen = gen
    )
    return {'headers':pop.dvars().headers, 'row':pop.dvars().row}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__,
                    formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('path',
                        help = 'results folder path. If the folder does not exist, '\
                               'it will be created',
                        nargs = '?',  # makes this argument optional
                        default = os.getcwd())
    parser.add_argument('-o','--overwrite',action='store_true',
                        help = 'overwrite tsv file')
    parser.add_argument('-s','--sample_run',action='store_true',
                        help = 'sample run only; display results')
    args=parser.parse_args()

    # This quick sample run obtains the headers for the data file.
    sample_run = simuAssortativeMatingWithFitness(experiment.constant_pop_size,
                                                  experiment.gen,
                                                  experiment.a,
                                                  experiment.aa_fitness,
                                                  experiment.aa_homogamy)
    if args.sample_run:
        print experiment.metadata()
        for h in sample_run['headers'][0:10]:
            print "{h:>8}".format(h=h),
        print
        for h in sample_run['headers'][0:10]:
            print " -------",
        print
        for gen in range(0,len(sample_run['row'])/10):
            for datum in sample_run['row'][10*gen:10*(1+gen)]:
                if type(datum) is int or datum == int(datum):
                    print " {datum:>7,}".format(datum=int(datum)),
                else:
                    print " {datum:>7.5f}".format(datum=datum),
            print
    else:
        if fileio.create_folder(args.path):
            print "Created folder '{}'".format(args.path)
        else:
            print "Using folder '{}'".format(args.path)
        experiment.headers = sample_run['headers']
        experiment.source_code = os.path.split(__file__)[-1].replace('.pyc','.py')
        experiment.filename = os.path.join(args.path,
                                           'pop{experiment.constant_pop_size}'\
                                           '_fitness{experiment.aa_fitness}'\
                                           '_homogamy{experiment.aa_homogamy:.2}.tsv'\
                                           ''.format(**locals()))
        if experiment.write_metadata():
            print "Created '{}'".format(experiment.filename)
        elif args.overwrite:
            experiment.write_metadata(overwrite=True)
            print "Overwrote '{}'".format(experiment.filename)
        else:
            print "'{}' exists.".format(experiment.filename)
            print "  Use --overwrite to overwrite this file."
            exit()


        experiment.cpu = subprocess.check_output(['/usr/sbin/sysctl', "-n", \
                                         "machdep.cpu.brand_string"]).strip() + \
                                         " ({} threads)".format(multiprocessing.cpu_count())
        print experiment.metadata()
        print "Running {:,} simulations...".format(SIMULATIONS)

        def _worker():
                '''
                    The worker function exists as a convenient way of passing
                    simuAssortativeMatingWithFitness with its parameters to the
                    multiprocessing pool.
                '''
                return simuAssortativeMatingWithFitness(experiment.constant_pop_size,
                                                        experiment.gen,
                                                        experiment.a,
                                                        experiment.aa_fitness,
                                                        experiment.aa_homogamy)['row']

        def _format_time (time):
            h = time//3600
            m = (time - 3600*(time//3600))//60
            s = time%60
            if h:
                return '{:.0f}h {:.0f}m'.format(h, m)
            elif m:
                return '{:.0f}m {:.0f}s'.format(m, s)
            else:
                return '{:.1f}s'.format(s)


        mp_chunk_size = cpu_count = multiprocessing.cpu_count()
        pool = multiprocessing.Pool()
        simulations = 0
        while simulations < SIMULATIONS:
            start_time = time.time()
            p = [pool.apply_async(_worker) for i in range(mp_chunk_size)]
            table = [item.get() for item in p]
            experiment.write(table)
            simulations += mp_chunk_size
            rate = mp_chunk_size/(time.time()-start_time)
            time_remaining = (SIMULATIONS-simulations)/rate if rate > 0 else 0
            print '{:,} completed ' \
                  '({:,.1f} simulations/min) '\
                  '{} remaining.'\
                  ''.format(simulations, 60*rate, _format_time(time_remaining))
            # mp_chunk_size is dynamically adjusted based on actual
            # execution speed such that file writes occur once per minute.
            mp_chunk_size = int(60*rate - 60*rate%cpu_count)
            if simulations + mp_chunk_size > SIMULATIONS:
                mp_chunk_size = SIMULATIONS-simulations
    print 'Done.'
