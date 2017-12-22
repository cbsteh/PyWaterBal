# PyWaterBal v. 0.0.1 (README)

Unsaturated Soil Water Flow Model

by [Christopher Teh Boon Sung](http://www.christopherteh.com)

## Overview

PyWaterBal is a unsaturated soil water flow model. It models the vertical flow (one-dimensional) of water in the soil, following a "tipping bucket" system. This model was published as a [`book by Uni. Putra Malaysia Press`](http://www.christopherteh.com/soilwaterbook/) (also see references below).



## Installation

1. To simplify the installation process, download the [`Anaconda`](https://www.anaconda.com/download/) suite. **Make sure you only choose the Python version 3.5 or higher (NOT ver 2.7).** Downloading the [`Anaconda`](https://www.anaconda.com/download/) suite will include not only the Python interpreter but also the `matplotlib` module which is required by PyWaterBal.

1. Download the entire [`PyWaterBal`](https://github.com/cbsteh/PyWaterBal/archive/master.zip) repository.

## How to use

At the command prompt:

```text
    python pywaterbal.py <flags>
```

where `<flags>` are the following:

```text
    -i <model input text file>
    -o <model output/results text file>
    -n <number of daily time steps to run the model, in days>
    -p <plot charts to show the model results, optional>
```

The `-p` flag is optional and must either be `b` for basic chart plotting. For detailed chart plotting, use any single letter other than `b`.

Example:

```text
    python pywaterbal -i 'c:\pywaterbal\ini.txt'
                      -o 'c:\pywaterbal\out.txt'
                      -n 90
                      -pb or -pd
```

means the model input is `ini.txt` and output file is `out.txt`, and both these files are stored in `c:\pywaterbal\` folder. The model is to be run for 90 simulation days, and after the model run, the simulation results will be plotted. The 'basic' chart plots will be produced if `-pb` is specified, else `-pd` for more detailed charts.

## Citation

1. TEH, C.B.S. 2018. Development and validation of an unsaturated soil water flow model for oil palm. Pertanika Journal of Tropical Agriculture. (In Press).
1. TEH, C.B.S. 2017. Modeling soil water flow in Python and Excel. Universiti Putra Malaysia, Serdang. [see book](http://www.christopherteh.com/soilwaterbook/)
