"""Facade module.

Run the soil water model, store the model results in a dictionary,
and print the results to an output file.

@author Christopher Teh Boon Sung

"""


import json

from dailydata import DailyData
from soilwater import SoilWater


class Facade(object):
    """Facade class.

    Run the soil water model,
    store the model results in a dictionary, and
    print the results to an output file.

    ATTRIBUTES:
        dailydata - data read from the model input file
        model - the soil water model
        fname_out - fullpath and name of output text file
        results - model results kept here

    METHODS:
        Statics:
            show_progress - keep track of model simulation
                            and show a progress bar

        run - start the daily simulation of soil water
    """

    def __init__(self, fname_in, fname_out):
        """Create the Facade object.

        Args:
            fname_in: model input text file
            fname_out: model output (results) text file
        """
        with open(fname_in, 'rt') as fin:
            ini = json.loads(fin.read())    # read everything in the file
        # initialize attributes:
        self.dailydata = DailyData(ini['dailydatafile'])
        self.model = SoilWater(fname_in)
        self.fname_out = fname_out
        self.results = None

    @staticmethod
    def show_progress(totalruns):
        """Print a progress bar, e.g., [#####     ] 50%."""
        barlength = 20
        fmt = '\rCompleted: [{0}] {1}%'
        for i in range(totalruns):
            f = i / totalruns
            hashes = '#' * int(round(f * barlength))
            spaces = ' ' * (barlength - len(hashes))
            print(fmt.format(hashes + spaces,
                             int(round(f * 100))), end='')
            yield i

    def run(self, duration):
        """Run the soil water model in daily time steps.

        Write the model output to the file and return the model results
        as a dictornary.

        Args:
            duration: no. of daily simulation days (days)

        Returns:
            Dictionary containing the model results
        """
        with open(self.fname_out, 'wt') as fout:
            nlayers = self.model.numlayers
            # selected model parameters to be stored and written to file
            outlayers = ['vwc', 'wc', 't', 'e', 'influx', 'outflux',
                         'netflux']
            res = {'rain': [], 'rootdepth': [], 'rootvwc': [],
                   'rootwc': [],
                   'layers': [{key: [] for key in outlayers}
                              for _ in range(nlayers)]}

            # the column headers in the output  file
            headers = ['day', 'rain', 'rootdepth', 'rootvwc', 'rootwc']
            fmt1 = '{:>15d}' + ',{:>15.3f}' * (len(headers) - 1)
            fmt2 = ',{:>15.3f}' * len(outlayers)

            # print the headers to the output file
            for i in range(nlayers):
                prefix = 'layer' + str(i + 1) + '_'
                headers.extend([prefix + field for field in outlayers])
            fmt = ('{:>15s},' * len(headers)).rstrip(',')
            fout.write(fmt.format(*headers))
            fout.write('\n')

            # run the model and after every run,
            #    print the model results to the file
            print('Running ...')
            for i in Facade.show_progress(duration):
                day = i + 1     # day number starts at 1, not 0
                # run the model
                self.model.daily_water_balance(*self.dailydata[day])

                # retrieve the model results
                rain = self.dailydata[day][0]
                rootdepth = self.model.rootdepth
                rootvwc = self.model.rootwater.vwc
                rootwc = self.model.rootwater.wc
                res['rain'].append(rain)
                res['rootdepth'].append(rootdepth)
                res['rootvwc'].append(rootvwc)
                res['rootwc'].append(rootwc)
                fout.write(fmt1.format(day, rain, rootdepth, rootvwc,
                                       rootwc))
                for j, layer in enumerate(self.model.layers):
                    vwc = layer.vwc
                    wc = layer.wc
                    # all water fluxes to be in mm/day
                    t = layer.fluxes.t * 1000
                    e = layer.fluxes.e * 1000
                    influx = layer.fluxes.influx * 1000
                    outflux = layer.fluxes.outflux * 1000
                    netflux = layer.fluxes.netflux * 1000
                    d = res['layers'][j]
                    d['vwc'].append(vwc)
                    d['wc'].append(wc)
                    d['t'].append(t)
                    d['e'].append(e)
                    d['influx'].append(influx)
                    d['outflux'].append(outflux)
                    d['netflux'].append(netflux)
                    fout.write(fmt2.format(vwc, wc, t, e,
                                           influx, outflux, netflux))
                fout.write('\n')

            self.results = res      # store the model results
            print('\ndone.')
