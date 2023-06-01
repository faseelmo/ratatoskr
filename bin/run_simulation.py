""" Fast and convienent script for urand traffic benchmarks """
import os
import shutil
import subprocess
import xml.etree.ElementTree as ET
import csv
import numpy as np
from joblib import Parallel, delayed
import multiprocessing
import pickle
import configparser
import pandas as pd
from combine_hists import combine_VC_hists, combine_Buff_hists,\
init_data_structure
###############################################################################


class Configuration:
    """
    The main configuration for all of the individual simulations.
    """
    def __init__(self, path):
        self.path = path
        self.config = configparser.ConfigParser()

        try:
            self.config.read(self.path)
        except Exception:
            raise

        self.topologyFile = self.config['DEFAULT']['topologyFile']

        self.libdir = self.config['DEFAULT']['libdir']
        self.simdir = self.config['DEFAULT']['simdir']
        self.basedir = os.getcwd()

        self.simulation_time = int(self.config['DEFAULT']['simulation_time'])
        self.restarts = int(self.config['DEFAULT']['restarts'])

        self.warmup_start = int(self.config['DEFAULT']['warmup_start'])
        self.warmup_duration = int(self.config['DEFAULT']['warmup_duration'])
        self.warmup_rate = float(self.config['DEFAULT']['warmup_rate'])

        self.run_rate_min = float(self.config['DEFAULT']['run_rate_min'])
        self.run_rate_max = float(self.config['DEFAULT']['run_rate_max'])
        self.run_rate_step = float(self.config['DEFAULT']['run_rate_step'])

        self.run_start_after_warmup = int(self.config['DEFAULT']['run_start_after_warmup'])
        self.run_start = self.warmup_start + self.warmup_duration + self.run_start_after_warmup
        self.run_duration = int(self.config['DEFAULT']['run_duration'])
        self.num_cores = int(self.config['DEFAULT']['num_cores'])
        if (self.num_cores == -1):
            self.num_cores = multiprocessing.cpu_count()
###############################################################################


def write_config_file(config, configFileSrc, configFileDst, injectionRate):
    """
    Write the configuration file for the urand simulation.

    Parameters:
        - config: configuration object.
        - configFileSrc: the source of the configuration file.
        - configFileDst: the destination of the config file.
        - injectionRate: the injection rate.

    Return:
        - None.
    """
    try:
        configTree = ET.parse(configFileSrc)
    except Exception:
        raise

    configTree.find('noc/nocFile').text = 'config/' + config.topologyFile + '.xml'
    configTree.find('general/simulationTime').set('value', str(config.simulation_time))
    configTree.find('general/outputToFile').set('value', 'true')
    configTree.find('general/outputToFile').text = 'report'

    for elem in list(configTree.find('application/synthetic').iter()):
        if elem.get('name') == 'warmup':
            elem.find('start').set('min', str(config.warmup_start))
            elem.find('start').set('max', str(config.warmup_start))
            elem.find('duration').set('min',
                     str(config.warmup_start + config.warmup_duration))
            elem.find('duration').set('max',
                     str(config.warmup_start + config.warmup_duration))
            elem.find('injectionRate').set('value', str(injectionRate))
        if elem.get('name') == 'run':
            elem.find('start').set('min', str(config.run_start))
            elem.find('start').set('max', str(config.run_start))
            elem.find('duration').set('min', str(config.run_start + config.run_duration))
            elem.find('duration').set('max', str(config.run_start + config.run_duration))
            elem.find('injectionRate').set('value', str(injectionRate))
    configTree.write(configFileDst)
###############################################################################


def write_sim_files(config, simdir):
    """
    Write the files that are associated with each run of the simulation
    (the executable sim + the configuration file).

    Parameters:
        - config: configuration object.
        - simdir: the path of the simulation directory.

    Return:
        - None.
    """
    confdir = simdir + '/config'
    shutil.rmtree(simdir, ignore_errors=True)

    try:
        os.makedirs(simdir)
        os.makedirs(confdir)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

    shutil.copy('sim', simdir)
    shutil.copy(config.libdir + '/' + config.topologyFile + '.xml', confdir)
###############################################################################


def run_indivisual_sim(simdir, basedir):
    """
    Run an individual simulation.

    Parameters:
        - simdir: the path to the simulatin directory.
        - basedir: the path to root of all simulations.

    Return:
        - None.
    """
    os.chdir(simdir)
    args = ('./sim')
    outfile = open('log', 'w')

    try:
        subprocess.run(args, stdout=outfile, check=True)
    except subprocess.CalledProcessError:
        raise

    outfile.flush()
    outfile.close()
    os.chdir(basedir)
###############################################################################


def get_latencies(latencies_results_file):
    """
    Read the resulting latencies from the csv file.

    Parameters:
        - results_file: the path to the result file.

    Return:
        - A list of the filt, packet and network latencies.
    """
    latencies = []
    try:
        with open(latencies_results_file, newline='') as f:
            spamreader = csv.reader(f, delimiter=' ', quotechar='|')
            for row in spamreader:
                latencies.append(row[1])
    except Exception:
        # Add dummy values to latencies, -1.
        latencies.append(-1)
        latencies.append(-1)
        latencies.append(-1)

    return(latencies)
###############################################################################


def begin_individual_sim(config, restart, injectionRates, injIter):
    """
    Begin a simulation with a specif injection rate.

    Parameters:
        - config: configuration object.
        - restart: the index of restarts.
        - injectioRates: the list of injection rates.
        - injIter: the index of the injection rate to be run.

    Return:
        - None.
    """
    print('Simulation with injection rate: ' + str(injectionRates[injIter])
            + ' restart ' + str(restart))
    currentSimDir = config.simdir + str(restart)
    currentConfDir = currentSimDir + '/config'
    write_sim_files(config, currentSimDir)
    write_config_file(config, 'config/config.xml', currentConfDir + '/config.xml',
                      injectionRates[injIter])
    run_indivisual_sim(currentSimDir, config.basedir)
###############################################################################


def begin_all_sims(config):
    """
    Begin all simulations.

    Parameters:
        - config: configuration object.

    Retrun:
        - results: a dictionary of the results.
    """
    print('Generating urand simulation with injection rate from ' +
    str(config.run_rate_min) + ' to ' + str(config.run_rate_max) + ' steps ' +
    str(config.run_rate_step))

    # Initialze the latencies.
    injectionRates = np.arange(config.run_rate_min, config.run_rate_max, config.run_rate_step)
    injectionRates = [round(elem, 4) for elem in injectionRates]
    latenciesFlit = -np.ones((len(injectionRates), config.restarts))
    latenciesPacket = -np.ones((len(injectionRates), config.restarts))
    latenciesNetwork = -np.ones((len(injectionRates), config.restarts))

    # Run the full simulation (for all injection rates).
    injIter = 0
    VCUsage = []
    BuffUsage = init_data_structure()  # a dict of dicts
    for inj in injectionRates:
        print('Starting Sims with ' + str(config.num_cores) + ' processes')
        Parallel(n_jobs=config.num_cores)(delayed(begin_individual_sim)
        (config, restart, injectionRates, injIter) for restart in range(config.restarts))

        VCUsage_inj = [pd.DataFrame() for i in range(3)]
        BuffUsage_inj = init_data_structure()  # a dict of dicts
        # Run the simulation several times for each injection rate.
        for restart in range(config.restarts):
            currentSimdir = 'sim' + str(restart)
            lat = get_latencies(currentSimdir + '/report_Performance.csv')
            latenciesFlit[injIter, restart] = lat[0]
            latenciesPacket[injIter, restart] = lat[1]
            latenciesNetwork[injIter, restart] = lat[2]
            VCUsage_run = combine_VC_hists(currentSimdir + '/VCUsage')
            if VCUsage_run is not None:
                for ix, layer_df in enumerate(VCUsage_run):
                    VCUsage_inj[ix] = pd.concat([VCUsage_inj[ix], layer_df])
            BuffUsage_run = combine_Buff_hists(currentSimdir + '/BuffUsage')
            if BuffUsage_run is not None:
                for l in BuffUsage_inj:
                    for d in BuffUsage_inj[l]:
                        BuffUsage_inj[l][d] = BuffUsage_inj[l][d].add(
                                BuffUsage_run[l][d], fill_value=0)
            # input('press any key')
            shutil.rmtree(currentSimdir)

        # Calculate the average and std for VC usage.
        VCUsage_temp = []
        for df in VCUsage_inj:
            if not df.empty:
                VCUsage_temp.append(df.groupby(df.index).agg(['mean', 'std']))
        VCUsage.append(VCUsage_temp)

        # Average the buffer usage over restarts.
        for l in BuffUsage_inj:
            for d in BuffUsage_inj[l]:
                BuffUsage_inj[l][d] = np.ceil(BuffUsage_inj[l][d] / config.restarts)
                BuffUsage[l][d] = BuffUsage[l][d].add(BuffUsage_inj[l][d], fill_value=0)

        injIter += 1

    # Average the buffer usage over injectionRates.
    for l in BuffUsage:
        for d in BuffUsage[l]:
            BuffUsage[l][d] = np.ceil(BuffUsage[l][d] / len(injectionRates))

    print('Executed all sims of all injection rates.')

    results = {'latenciesFlit': latenciesFlit,
               'latenciesNetwork': latenciesNetwork,
               'latenciesPacket': latenciesPacket,
               'injectionRates': injectionRates,
               'VCUsage': VCUsage,
               'BuffUsage': BuffUsage}
    return results
###############################################################################


def save_results(results, results_file):
    """
    Save the results to a pickle file.

    Parameters:
        - results: a dictionary of the results.
        - result_file: the path to the pickle file.

    Return:
        - None.
    """
    with open(results_file, 'wb') as f:
        pickle.dump(results, f)
###############################################################################


""" Main point of execution """

config = Configuration('config.ini')

results = begin_all_sims(config)

save_results(results, 'rawResults.pkl')
