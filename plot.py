"""Plot module.

Plot charts to depict model results. The soil water model
must be run first before any charts can be plotted.

Requires matplotlib version of at least 2.0.

@author Christopher Teh Boon Sung

"""


import webbrowser

import matplotlib.pyplot as plt
from matplotlib.widgets import Button

from facade import Facade


class Plot(Facade):
    """Plot class.

    Plot charts to visually depict the model results.
    Uses matplotlib for plotting.

    Note:
        Run soil water model first before any charts can be plotted.

    ATTRIBUTES:

    METHODS:
        Statics:
            generate_xvalues - generate a series of equally spaced values
                               (only integers)
            color - the color scheme for chart lines
            turnon_grid - show major gridlines on all charts
                          (for both x- and y-axis)
            set_ylmt - Adjust the y-axis to cover the full y data range
            set_common_ylimits - set same scale for the y-axis for
                                 selected charts

        plot_soil_layers - plot charts to show a given layer property
        get_layers_legend_text - create a legend for each soil layer's
                                 physical properties
        set_layers_legend - display the soil layer properties legend
        set_charts_legend - display the chart legend
        remove_ticks - remove x-axis labels for selected axis objects
        open_outputfile - open the output text file
        set_button_dataview - show a button to open the model
                              output/results text file
        plot_detailed - plot charts on soil water content and fluxes
        plot_basic - plot charts focussing more on the soil water content
        plot - set True to call plot_basic function,
               or False for plot_detailed function
    """

    def __init__(self, fname_in, fname_out):
        """Create the Plot object.

        Args:
            fname_in: model input text file
            fname_out: model output (results) text file
        """
        # parent handles the initialization
        Facade.__init__(self, fname_in, fname_out)
        self.__button = None    # matplotlib Button to open output file

    @staticmethod
    def generate_xvalues(start, end, max_intervals=25):
        """Generate a series of equally spaced values.

        Given a range (such as from 1 to 365), this functon attempts to
        find an appopriate interval size so that a series of equally
        spaced values can be generated and returned. The generated values
        will include the start and end values. This function is used for
        finding the right scale for chart axis.

        Note:
            This function is only for integer values (not floats).

        Args:
            start: start generating from this value
            end: values generated until and including this value
            max_intervals: the maximum number of intervals to have
                           between the given range (start, end). Default
                           is a max. of 25 intervals.
        """
        rg = end - start
        num = max_intervals
        while num > 1 and rg % num != 0:
            num -= 1
        vals = None
        if num > 1:
            # found the interval size that can divide the range
            #    without any remainders
            sz = rg // num
            vals = [val for val in range(start, end + 1, sz)]
        if vals is None:
            # failed to find a suitable interval size, so try again
            #    but with an adjusted end point. Such failure can happen
            #    if the range between start and end is a prime number.
            vals = Plot.generate_xvalues(start, end + 1, max_intervals)
        return vals

    @staticmethod
    def color(idx):
        """The color scheme for chart lines.

        Args:
            idx: color index (starting from 0)

        Note:
            Colors are reused if argument idx exceeds the number
            of available colors.
        """
        colors = ['#000000', '#e41a1c', '#377eb8', '#4daf4a', '#984ea3',
                  '#ff7f00', '#a65628', '#f781bf', '#ffff33']
        return colors[idx % len(colors)]

    @staticmethod
    def turnon_grid(axs):
        """Turn on major gridlines for all charts (both x- & y-axis)."""
        for ax in axs:
            ax.grid(True)

    @staticmethod
    def set_ylmt(ax, yvals=None, miny=None):
        """Adjust the y-axis limits to cover the full range of data.

        Will add some padding if needed, so that the min. and max. y
        values are not so close to the y-axis limits.

        Args:
            ax: y-axis
            yvals: a list of y data
            miny: the minimum value of y-axis.
                  Minimum y-axis cannot be below this level.

        Returns:
            None.
        """
        if yvals is None:
            lines = ax.get_lines()
            yvals = []
            for line in lines:
                ydata = line.get_ydata()
                yvals.extend(ydata)

        min_yval = min(yvals)
        max_yval = max(yvals)
        min_yaxis, max_yaxis = ax.get_ylim()
        locs = plt.yticks()[0]
        scale = abs(abs(locs[1]) - abs(locs[0]))
        if abs(abs(max_yaxis) - abs(max_yval)) < 0.5 * scale:
            max_yaxis += scale
            ax.set_ylim(top=max_yaxis)
        if abs(abs(min_yval) - abs(locs[0])) < 0.5 * scale:
            min_yaxis = locs[0] - scale
            if miny is None or (miny is not None and miny <= min_yaxis):
                ax.set_ylim(bottom=min_yaxis)
        if miny is not None and min_yaxis < miny:
            ax.set_ylim(bottom=miny)

    @staticmethod
    def set_common_ylimits(axs):
        """Set given charts to have the same scale for their y-axis.

        Args:
            axs: a list of axis objects to have the same y-axis scale
        """
        mn = []     # minimum y limits
        mx = []     # maximum y limits
        for ax in axs:
            miny, maxy = ax.get_ylim()
            mn.append(miny)
            mx.append(maxy)
        miny = min(mn)
        maxy = max(mx)
        for ax in axs:
            ax.set_ylim(miny, maxy)

    def plot_soil_layers(self, ax, x, field, include_layers=None):
        """Plot a given soil layer property.

        Args:
            ax: axes object
            x: series of x values (x-axis values)
            field: name of soil layer property (string)
            include_layers: a list of soil layers to include in display.
                            Default: all layers will be displayed.
        """
        for i, layer in enumerate(self.results['layers']):
            if not include_layers or i in include_layers:
                y = layer[field]
                txt = 'layer' + str(i + 1)
                ax.plot(x, y, lw=2, label=txt, color=Plot.color(i))

    # noinspection PyProtectedMember
    def get_layers_legend_text(self):
        """Create a legend for each soil layer's physical properties.

        Returns the text information for the legend as a plain string.
        """
        nlayers = self.model.numlayers
        if nlayers < 1:
            return None   # need at least one layer to display info.

        # prepare the text formatting
        #    (need a monospace font to align the text columns correctly):
        fmt = '{: <14s}' + '{:>9s}' * nlayers
        headers = ['property']
        headers.extend(['layer' + str(i + 1) for i in range(nlayers)])
        yestable = '(with watertable)'
        nonetable = '(no watertable)'
        wt = yestable if self.model.has_watertable else nonetable
        totallen = 14 + 9 * nlayers
        titlelen = len(wt)
        ndashes = (totallen - titlelen) // 2
        wt = '\n' + '-' * ndashes + wt + '-' * ndashes + '\n'
        legendtxt = fmt.format(*headers) + wt
        fmt = '{: <14s}' + '{:>9.3f}' * nlayers

        # saturated hydraulic conductivity:
        vals = []
        for layer in self.model.layers:
            vals.append(layer.ksat * 1000)
        legendtxt += fmt.format('ksat (mm/day)', *vals) + '\n'

        # soil water characteristics:
        units = [' (m3/m3)', ' (m3/m3)', ' (m3/m3)', ' (-)', ' (%)',
                 ' (kPa)']
        for i, field in enumerate(self.model.layers[0].swc._fields):
            txt = field + units[i]
            vals = []
            for layer in self.model.layers:
                val = getattr(layer.swc, field) * (1.0 if i != 4
                                                   else 100.0)
                vals.append(val)
            legendtxt += fmt.format(txt, *vals) + '\n'

        # soil thickness:
        vals = []
        for layer in self.model.layers:
            vals.append(layer.thick)
        legendtxt += fmt.format('thick (m)', *vals) + '\n'

        # depth from soil surface:
        vals = []
        for layer in self.model.layers:
            vals.append(layer.depth)
        legendtxt += fmt.format('depth (m)', *vals) + '\n'

        # soil texture:
        for field in self.model.layers[0].texture._fields:
            txt = field + '(%)'
            vals = []
            for layer in self.model.layers:
                vals.append(getattr(layer.texture, field))
            legendtxt += fmt.format(txt, *vals) + '\n'

        # done, so return the whole text information
        return legendtxt

    def set_layers_legend(self):
        """Format and diplay the legend for soil layer properties."""
        ax = plt.axes([0.52, 0.0, 0.4, 0.2])     # lower right corner
        ax.spines['left'].set_visible(False)     # turn off tick marks
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.set_facecolor(plt.rcParams['figure.facecolor'])  # seamless
        ax.tick_params(axis='both', which='both', bottom='off',
                       top='off', labelbottom='off', right='off',
                       left='off', labelleft='off')
        data = self.get_layers_legend_text()  # get the layer properties
        # display legend (monospace font to properly align column texts)
        ax.text(0, 0, data, fontname='Courier New', fontsize=9,
                weight='bold',
                horizontalalignment='left', verticalalignment='bottom')

    def set_charts_legend(self):
        """Format and display the chart lines legend."""
        ax = plt.axes([0, 0.96, 0.5, 0.04])   # upper right corner
        ax.spines['left'].set_visible(False)  # no ticks
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        # create fake charts, so we can get the legend text and lines:
        nlayers = self.model.numlayers
        for i in range(nlayers):
            txt = 'layer' + str(i + 1)
            ax.plot([0], [0], label=txt, lw=3, color=Plot.color(i))

        ax.plot([0], [0], label='root zone', lw=4, ls='dashed',
                color=Plot.color(nlayers))
        ax.set_facecolor(plt.rcParams['figure.facecolor'])   # seamless
        ax.legend(loc='upper left', ncol=nlayers + 1)
        ax.tick_params(axis='both', which='both', bottom='off',
                       top='off', labelbottom='off', right='off',
                       left='off', labelleft='off')

    def remove_ticks(self, axs):
        """Remove x-axis labels for selected axis objects.

        Some charts share the same x-axis, so declutter the charts by
        removing shared tick labels on the x-axis.

        Args:
            axs: a list of axis objects. Only the last axis object will
                 have its x tick labels displayed.
        """
        naxs = len(axs)
        for i, ax in enumerate(axs):
            if i < naxs - 1:
                # all charts: turn off their tick labels on the x-axis
                plt.setp(ax.get_xticklabels(), visible=False)
            else:
                # exception is the last (most bottom) chart
                ax.set_xlabel('days')
                nlen = len(self.results['rain'])
                xvals = Plot.generate_xvalues(1, nlen)
                if xvals:
                    ax.autoscale_view(tight=True)
                    ax.set_xticks(xvals)    # tick intervals for x-axis

    # noinspection PyUnusedLocal
    def open_outputfile(self, event):
        """Open the weather stats file using the OS's default program."""
        webbrowser.open(self.fname_out)  # NB: may not always work

    def set_button_dataview(self):
        """Show a button to open the model output/results text file."""
        ax = plt.axes([0, 0, 0.1, 0.05])    # lower left corner
        ax.spines['left'].set_visible(False)      # borderless button
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        self.__button = Button(ax, 'View Data',
                               color=plt.rcParams['figure.facecolor'])
        # set up the button event mouse click
        self.__button.on_clicked(self.open_outputfile)

    def plot_detailed(self):
        """Plot charts on soil water content but emphasize water fluxes.

        Unlike the plot_basic function, this function will plot the data
        from all soil layers, not just the first six layers.

        Note:
            This function must be used only after a model run
            to set the results attribute.
        """
        nlayers = self.model.numlayers
        out = self.results
        if nlayers < 1 or not out:
            return None   # if there are no layers or no model results

        ncol = 2
        nrow = 5
        nlen = len(out['rain'])
        x = [i + 1 for i in range(nlen)]

        # 1st column: plot the rainfall:
        y = out['rain']
        ax1 = plt.subplot(nrow, ncol, 1)
        ax1.bar(x, y, label='rain', color=Plot.color(0))
        Plot.set_ylmt(ax1, y, 0.0)
        ax1.set_ylabel('rain\n(mm)')
        totrain = 'total rain = {:.1f} mm\n'.format(sum(y))
        ax1.text(x[0], ax1.get_ylim()[1], totrain)

        # 1st column: plot the volumetric water content (vwc):
        ax2 = plt.subplot(nrow, ncol, 3, sharex=ax1)
        ax2.set_ylabel('VWC\n' + r'(m$^{3}$ m$^{-3}$)')
        self.plot_soil_layers(ax2, x, 'vwc')
        y = out['rootvwc']
        ax2.plot(x, y, lw=3, label='root zone', ls='dashed',
                 color=Plot.color(nlayers))
        Plot.set_ylmt(ax2, miny=0.0)

        # 1st column: plot net fluxes:
        ax3 = plt.subplot(nrow, ncol, 5, sharex=ax1)
        ax3.set_ylabel('net flux\n' + r'(mm day$^{-1}$)')
        self.plot_soil_layers(ax3, x, 'netflux')
        Plot.set_ylmt(ax3)

        # 1st column: plot influxes:
        ax4 = plt.subplot(nrow, ncol, 7, sharex=ax1)
        ax4.set_ylabel('influx\n' + r'(mm day$^{-1}$)')
        self.plot_soil_layers(ax4, x, 'influx')
        Plot.set_ylmt(ax4)

        # 1st column: plot outfluxes:
        ax5 = plt.subplot(nrow, ncol, 9, sharex=ax1)
        ax5.set_xlim([1, nlen])
        ax5.set_ylabel('outflux\n' + r'(mm day$^{-1}$)')
        self.plot_soil_layers(ax5, x, 'outflux')
        Plot.set_ylmt(ax5)

        # 2nd column: plot rainfall again (as reference)
        y = out['rain']
        ax6 = plt.subplot(nrow, ncol, 2)
        ax6.bar(x, y, label='rain', color=Plot.color(0))
        Plot.set_ylmt(ax6, y, 0.0)
        ax6.set_ylabel('rain\n(mm)')
        ax6.text(x[0], ax6.get_ylim()[1], totrain)

        # 2nd. column: plot the water content (wc):
        ax7 = plt.subplot(nrow, ncol, 4, sharex=ax6)
        ax7.set_xlim([1, nlen])
        ax7.set_ylabel('water\n(mm)')
        self.plot_soil_layers(ax7, x, 'wc')
        nlayers = self.model.numlayers
        y = out['rootwc']
        ax7.plot(x, y, lw=3, label='root zone', ls='dashed',
                 color=Plot.color(nlayers))
        Plot.set_ylmt(ax7, miny=0.0)

        # 2nd. column: plot the transpiration (t):
        ax8 = plt.subplot(nrow, ncol, 6, sharex=ax6)
        ax8.set_xlim([1, nlen])
        ax8.set_ylabel('T\n' + r'(mm day$^{-1}$)')
        self.plot_soil_layers(ax8, x, 't')
        Plot.set_ylmt(ax8, miny=0.0)

        # 2nd. column: plot the evaporation (e):
        ax9 = plt.subplot(nrow, ncol, 8, sharex=ax6)
        ax9.set_xlim([1, nlen])
        ax9.set_ylabel('E\n' + r'(mm day$^{-1}$)')
        # evaporation only from layer 1, so exclude others
        self.plot_soil_layers(ax9, x, 'e', [0])
        Plot.set_ylmt(ax9, miny=0.0)

        # display the legends:
        self.set_layers_legend()    # soil properties legend
        self.set_charts_legend()    # soil chart lines legend
        self.set_button_dataview()  # button to view results text file

        # format the subplots:
        self.set_common_ylimits([ax8, ax9])
        self.set_common_ylimits([ax3, ax4, ax5])
        axsleft = [ax1, ax2, ax3, ax4, ax5]
        axsright = [ax6, ax7, ax8, ax9]
        self.remove_ticks(axsleft)      # first column charts
        self.remove_ticks(axsright)     # second column charts
        Plot.turnon_grid(axsleft + axsright)  # on grid for all charts
        plt.gcf().canvas.set_window_title('Pywaterbal')

        # now show all the subplots:
        mng = plt.get_current_fig_manager()
        mng.window.showMaximized()
        plt.show()
        self.__button = None

    def plot_basic(self):
        """Plot charts focusing more on the soil water content.

        Only data from the first six (6) soil layers will be plotted;
        use plot_detailed function to plot all soil layers.

        Note:
           This function must be used only after a model run to
           set the results attribute.
        """
        nlayers = self.model.numlayers
        out = self.results
        if nlayers < 1 or not out:
            return None   # if there are no layers or no model results

        ncol = 2
        nrow = 5
        nlen = len(out['rain'])
        x = [i + 1 for i in range(nlen)]

        axsleft = []
        axsright = []
        # 1st column: plot the rainfall:
        y = out['rain']
        ax1 = plt.subplot(nrow, ncol, 1)
        ax1.bar(x, y, label='rain', color=Plot.color(0))
        Plot.set_ylmt(ax1, y, 0.0)
        totrain = 'total rain = {:.1f} mm\n'.format(sum(y))
        ax1.text(x[0], ax1.get_ylim()[1], totrain)
        ax1.set_ylabel('rain\n(mm)')
        axsleft.append(ax1)

        # 1st column: plot the volumetric water content for all layers:
        ax2 = plt.subplot(nrow, ncol, 3, sharex=ax1)
        ax2.set_ylabel('VWC\n' + r'(m$^{3}$ m$^{-3}$)')
        self.plot_soil_layers(ax2, x, 'vwc')
        y = out['rootvwc']
        ax2.plot(x, y, lw=3, label='root zone', ls='dashed',
                 color=Plot.color(nlayers))
        Plot.set_ylmt(ax2, miny=0.0)
        axsleft.append(ax2)

        # 2nd column: plot rainfall again (as reference)
        y = out['rain']
        ax6 = plt.subplot(nrow, ncol, 2)
        ax6.bar(x, y, label='rain', color=Plot.color(0))
        Plot.set_ylmt(ax6, y, 0.0)
        ax6.set_ylabel('rain\n(mm)')
        ax6.text(x[0], ax6.get_ylim()[1], totrain)
        axsright.append(ax6)

        for i, layer in enumerate(self.results['layers']):
            y = layer['vwc']
            txt = 'layer' + str(i + 1)
            if i < 3:
                ax = plt.subplot(nrow, ncol, 2 * i + 5, sharex=ax1)
                axsleft.append(ax)
            else:
                ax = plt.subplot(nrow, ncol, 2 * i - 2, sharex=ax6)
                axsright.append(ax)

            ax.set_ylabel(txt + ' VWC\n' + r'(m$^{3}$ m$^{-3}$)')
            ax.plot(x, y, lw=2, label=txt, color=Plot.color(i))
            Plot.set_ylmt(ax, miny=0.0)

        ax8 = ax9 = None
        if nlayers < 6:
            loc = 4
            if nlayers == 4:
                loc = 6
            elif nlayers == 5:
                loc = 8
            ax7 = plt.subplot(nrow, ncol, loc, sharex=ax6)
            ax7.set_ylabel('VWC\n' + r'(m$^{3}$ m$^{-3}$)')
            y = out['rootvwc']
            ax7.plot(x, y, lw=3, label='root zone',
                     ls='dashed', color=Plot.color(nlayers))
            Plot.set_ylmt(ax7, miny=0.0)
            axsright.append(ax7)

            if nlayers < 5:
                loc = 6
                if nlayers == 4:
                    loc = 8
                ax8 = plt.subplot(nrow, ncol, loc, sharex=ax6)
                ax8.set_xlim([1, nlen])
                ax8.set_ylabel('water\n(mm)')
                self.plot_soil_layers(ax8, x, 'wc')
                y = out['rootwc']
                ax8.plot(x, y, lw=3, label='root zone',
                         ls='dashed', color=Plot.color(nlayers))
                Plot.set_ylmt(ax8, miny=0.0)

                if nlayers < 4:
                    loc = 8
                    ax9 = plt.subplot(nrow, ncol, loc, sharex=ax6)
                    ax9.set_ylabel('net flux\n' + r'(mm day$^{-1}$)')
                    self.plot_soil_layers(ax9, x, 'netflux')
                    Plot.set_ylmt(ax9)

        # display the legends:
        self.set_layers_legend()    # soil properties legend
        self.set_charts_legend()    # soil chart lines legend
        self.set_button_dataview()  # button to view results text file

        # format the subplots:
        self.set_common_ylimits([ax2] + axsleft[1:] + axsright[1:])
        if ax8:
            axsright.append(ax8)
        if ax9:
            axsright.append(ax9)

        self.remove_ticks(axsleft)    # first column charts
        self.remove_ticks(axsright)   # second column charts
        Plot.turnon_grid(axsleft + axsright)    # on grid for all charts
        plt.gcf().canvas.set_window_title('Pywaterbal')

        # now show all the subplots:
        mng = plt.get_current_fig_manager()
        mng.window.showMaximized()
        plt.show()
        self.__button = None

    def plot(self, basic=True):
        """Call either plot_basic or plot_detailed function for plotting.

        Plots charts to visually show the results from the model
        simulation. Ensure the model has been run first before calling
        this function; otherwise, no charts will be plotted.

        Note:
            Read docstring of the plot_basic and plot_detailed functions
            on what both these functions do.

        Args:
            basic - True to call plot_basic, or False for plot_detailed

        Returns:
            None
        """
        if basic:
            self.plot_basic()
        else:
            self.plot_detailed()
