r"""Pywaterbal module.

Soil water model.

How to use:

    python pywaterbal.py <flags>

where <flags> are the following:
    -i <model input text file>
    -o <model output/results text file>
    -n <number of daily time steps to run the model, in days>
    -p <plot charts to show the model results, optional>

The -p flag is optional and must either be 'b' for basic chart plotting.
For detailed chart plotting, use any single letter other than'b'.

Example:
    python pywaterbal -i 'c:\pywaterbal\ini.txt'
                      -o 'c:\pywaterbal\out.txt'
                      -n 90
                      -pb or -pd

means the model input is 'ini.txt' and output file is 'out.txt',
and both these files are stored in 'c:\pywaterbal\' folder. The model is
to be run for 90 simulation days, and after the model run, the simulation
results will be plotted. The 'basic' chart plots will be produced if 
'-pb' is specified, else '-pd' for more detailed charts.

@author Christopher Teh Boon Sung

"""


import getopt
import sys
import traceback

from plot import Plot


def main(argv):
    """Main entry point for the program.

    Run the daily model simulation

    Args:
        argv: the commandline options and arguments
    """
    if len(argv) == 0:      # no arguments given, so print help and exit
        print(__doc__)
        sys.exit(2)

    try:
        # set the accepted flags, and parse the options and arguments:
        inifile = outfile = duration = plottype = None
        opts, a = getopt.getopt(argv, "hi:o:n:p:")
        for opt, arg in opts:
            if opt == '-h':             # help flag
                print(__doc__)
                sys.exit()
            elif opt == '-i':           # initialization file flag
                inifile = arg
            elif opt == '-o':           # output file flag
                outfile = arg
            elif opt == '-n':           # duration of model run flag
                duration = int(arg)
            elif opt == '-p':           # chart plotting flag
                plottype = arg

        if None in [inifile, outfile, duration]:
            print('One or more flags are missing. Flag -p is optional.')
            print(__doc__)
            sys.exit(2)

        ui = Plot(inifile, outfile)
        ui.run(duration)
        if plottype:
            ui.plot(True if plottype.lower() == 'b' else False)

    except getopt.GetoptError:
        traceback.print_exc(file=sys.stdout)
        sys.exit(2)
    except Exception:
        print('Error encountered. Aborting.')
        traceback.print_exc(file=sys.stdout)
        sys.exit(1)

    return 0    # error code 0 means no error


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

# from dailydata import DailyData
# from soilwater import SoilWater
#
# dt = DailyData('data.txt')
# sw = SoilWater('ini.txt')
# for day in range(1, 91):
#     sw.daily_water_balance(*dt[day])
#     print('Water content for day', day)
#     for i, layer in enumerate(sw.layers):
#         print('\tlayer no. {}: {:.2f}'.format(i+1, layer.wc))

# from facade import Facade
#
# fac = Facade('ini.txt', 'out.txt')
# fac.run(90)
#
# day = 3             # day 3
# idx = day - 1       # indexing starts at 0
# res = fac.results   # shorthand
#
# print(res['rain'][idx])         # rain (mm)
# print(res['rootdepth'][idx])    # rooting depth (m)
# print(res['rootvwc'][idx])      # water content in root zone (m3/m3)
# print(res['rootwc'][idx])       # water content in root zone (mm)
#
# # print the water content and water fluxes for every soil layer
# for layer in res['layers']:
#     print(layer['vwc'][idx])        # water content (m3/m3)
#     print(layer['wc'][idx])         # water content (mm)
#     print(layer['t'][idx])          # water uptake by roots (mm)
#     print(layer['e'][idx])          # soil evaporation (mm)
#     print(layer['influx'][idx])     # water entry into layer (mm)
#     print(layer['outflux'][idx])    # water exiting layer (mm)
#     print(layer['netflux'][idx])    # net change (mm)
