"""Soil water movement and content module.

Model one-dimensional soil water movement (fluxes).
Includes groundwater (assumes constant water table depth).

@author Christopher Teh Boon Sung

"""

from collections import namedtuple
import json
import math


# Soil water characteristics.
#    sat: saturation point
#    fc: field capacity
#    pwp: permanent wilting point
#    psd: pore-size distribution
#    porosity: soil porosity
#    airentry: air-entry value
SWC = namedtuple('SWC', 'sat fc pwp psd porosity airentry')

# Soil texture.
#    clay: percentage of clay
#    sand: percentage of sand
#    om: percentage of organic matter
Texture = namedtuple('Texture', ['clay', 'sand', 'om'])

# Soil water characteristics in the rooting zone.
#    wc: soil water content (in mm)
#    vwc: soil water content (volumetric)
#    critical: soil water content threshold, below which
#              plant water stress occurs
#    sat: saturation point
#    fc: field capacity
#    pwp: permanent wilting point
RootZone = namedtuple('RootZone', 'wc vwc critical sat fc pwp')

# Actual evapotranspiration (ET).
#    crop - actual transpiration (from crop)
#    soil - actual evaporation (from soil)
ActualET = namedtuple('ActualET', 'crop soil')

# Water fluxes into a given soil layer.
#    t: water uptake via plant transpiration
#    e: water loss via soil evaporation
#    influx: water entry (input) into the soil layer
#    outflux: water exit (output) out of the soil layer
#    netflux: difference between water entry and water exit
Fluxes = namedtuple('Fluxes', 't e influx outflux netflux')


class SoilLayer(object):
    """Soil layer properties class.

    The physical properties of a soil layer, dealing with
    soil water content and fluxes.

    ATTRIBUTES:
        thick - thickness of the soil layer (m)
        texture - sand, clay, and organic matter (%)
        vwc - vol. water content (m3/m3)
        wc - water content (mm)
        accthick - cumulative thickness (m)
        depth - depth of layer from soil surface (m)
        swc - soil water characteristics (varying units)
        ksat - saturated hydraulic conductivity (m/day)
        k - hydraulic conductivity (m/day)
        matric - matric head (m)
        gravity - gravity head (m)
        fluxes = Fluxes namedtuple for the various water flux components:
                 t - plant water uptake via transpiration (m/day)
                 e - loss of water via evaporation (m/day)
                 influx - influx: water entry into layer (m/day)
                 outflux - outflux: water exit out of layer (m/day)
                 netflux - net flux: difference between influx & outflux
                           (m/day)

    METHODS:
        initialize_layer - initialize all attributes
        update_heads_k - update the matric head, gravity head, and
                         the unsaturated hydraulic conductivity

        Getters:
            tothead - total/sum of matric and gravity head (m)

    Note:
        Volumetric water content (vwc) can be given as a negative value.
        Negative values are a special code to mean that the water content
        is a fraction between SAT and FC or between FC and PWP. The codes
        are along a scale from -3 to -1:

        Scale:
                  -2.75      -2.25              -1.5
            [-3 ....|..........|....-2 ...........|..........-1]
             PWP                    FC                      SAT

        so that if the given water content is -1, -2, or -3, it means the
        water content should be set to saturation, field capacity, or
        permanent wilting point, respectively. A value of -1.5 means the
        water content will be set at halfway between SAT and FC.
        Likewise, -2.25 and -2.75 mean the water content will be lower
        than FC, where the former (-2.25) means the water content will be
        set nearer to FC, but the latter (-2.75) closer to PWP.

        Any negative values outside the range of -3 to -1 means the water
        content wil be set at FC.
    """

    __accdepth = 0.0    # internal use: used to determine a layer's depth

    def __init__(self):
        """Initialize the SoilLayer object."""
        self.thick = 0.0
        self.texture = Texture(0.0, 0.0, 0.0)
        self.vwc = 0.0
        self.wc = 0.0
        self.accthick = 0.0
        self.depth = 0.0
        self.swc = SWC(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        self.ksat = 0.0
        self.k = 0.0
        self.matric = 0.0
        self.gravity = 0.0
        self.fluxes = Fluxes(0.0, 0.0, 0.0, 0.0, 0.0)
        self.prev = None
        self.next = None

    def initialize_layer(self, prevlayer, nextlayer):
        """Initialize all attributes.

        Note:
            This function sets the water content to within the range of
            SAT and FC or between FC and PWP, if the vol. water content
            is given as negative value. See this class's docstring above.

        Args:
            prevlayer - the previous soil layer (above layer)
            nextlayer - the next soil layer (below layer)

        Returns:
            None
        """
        self.prev = prevlayer
        self.next = nextlayer

        # 1. set layer depth and cumulative thickness:
        prevaccthick = self.prev.accthick if self.prev else 0.0
        self.accthick = self.thick + prevaccthick
        prevthick = self.prev.thick if self.prev else 0.0
        d = 0.5 * (prevthick + self.thick)
        self.depth = SoilLayer.__accdepth + d
        SoilLayer.__accdepth += d

        # 2. set soil water characteristics (Saxton & Rawls, 2008):
        c, s, om = self.texture
        s /= 100  # convert sand and clay from % to fraction, but om is %
        c /= 100
        # 2a. permanent wilting, field capacity, then saturation points:
        n1 = -0.024 * s + 0.487 * c + 0.006 * om
        n2 = 0.005 * (s*om) - 0.013 * (c * om) + 0.068 * (s * c) + 0.031
        theta1500t = n1 + n2
        theta1500 = theta1500t + (0.14 * theta1500t - 0.02)
        n1 = -0.251 * s + 0.195 * c + 0.011 * om
        n2 = 0.006 * (s*om) - 0.027 * (c * om) + 0.452 * (s * c) + 0.299
        theta33t = n1 + n2
        theta33 = theta33t + (1.283*theta33t**2 - 0.374*theta33t - 0.015)
        n1 = 0.278 * s + 0.034 * c + 0.022 * om
        n2 = - 0.018 * (s*om) - 0.027 * (c*om) - 0.584 * (s * c) + 0.078
        theta_s33t = n1 + n2
        theta_s33 = theta_s33t + 0.636 * theta_s33t - 0.107
        theta0 = theta33 + theta_s33 - 0.097 * s + 0.043
        # 2b. pore size distribution index (no unit):
        b = math.log(1500) - math.log(33)
        b /= math.log(theta33) - math.log(theta1500)
        psd = 1 / b
        # 2c. air-entry suction (kPa):
        awc = theta0 - theta33
        n1 = -21.674 * s - 27.932 * c - 81.975 * awc + 71.121 * (s * awc)
        n2 = 8.294 * (c * awc) + 14.05 * (s * c) + 27.161
        aet = n1 + n2
        ae = max(0.0, aet + (0.02 * aet ** 2 - 0.113 * aet - 0.7))
        # 2d. store calculated soil water characteristics (all in m3/m3)
        # calibrations/adjust for Malaysian soils:
        theta1500 = 1.528 * theta1500 * (1 - theta1500)  # PWP
        theta33 = 1.605 * theta33 * (1 - theta33)  # FC
        theta0 = 2.225 * theta0 * (1 - theta0)  # SAT (= porosity)
        self.swc = SWC(theta0, theta33, theta1500, psd, theta0, ae)
        # 3. saturated hydraulic conductivity (convert mm/hour to m/day):
        self.ksat = 1930 * awc ** (3 - psd) * 24 / 1000

        # 4. check for special code:
        if self.vwc < 0:
            # vol. water content is a fraction between SAT, FC, and PWP:
            vwc = -self.vwc     # make a +ve
            fc = self.swc.fc
            if 1 <= vwc <= 2:
                # water content is between SAT and FC
                sat = self.swc.sat
                vwc = sat - (vwc - 1) * (sat - fc)  # interpolation
            elif 2 < vwc <= 3:
                # water content is between FC and PWP
                pwp = self.swc.pwp
                vwc = fc - (vwc - 2) * (fc - pwp)   # interpolation
            else:
                # out of range, so just set to FC
                vwc = fc
            self.vwc = vwc  # m3/m3
            self.wc = self.vwc * self.thick * 1000  # mm/day

        # 5. update the matric and gravity heads,
        #    then the hydraulic conductivity:
        self.update_heads_k()

    def update_heads_k(self):
        """Update the matric and gravity heads (m), then
           the unsaturated hydraulic conductivity (m/day).

        Update is based on current soil water content.
        """
        fc = self.swc.fc
        vwc = self.vwc      # current soil water content
        # matric suction, convert from kPa to m by dividing by 10
        if vwc >= fc:
            df = vwc - fc
            hm = 33 - (33 - self.swc.airentry) * df / (self.swc.sat - fc)
            hm /= 10
        else:
            b = 1 / self.swc.psd
            a = math.exp(3.496508 + b * math.log(fc))
            hm = (a * max(0.05, vwc) ** (-b)) / 10
        # matric head (m)
        self.matric = max(0.0, hm)
        # gravity head (m) is always constant and equal to layer's depth
        #    from surface
        self.gravity = self.depth
        # unsaturated hydraulic conductivity (m/day)
        ae = self.swc.airentry / 10  # air entry (convert to m)
        hm = self.matric  # matric head (m)
        ratio = self.vwc / self.swc.sat
        if hm > ae:
            self.k = self.ksat * ratio ** (3 + 2 / self.swc.psd)
        else:
            self.k = self.ksat

    @property
    def tothead(self):
        """Total head (m)."""
        return self.matric + self.gravity


class SoilWater(object):
    """Soil water balance class.

    Model the soil water flow in one dimension and water balance.
    Include the effect of groundwater, if any, but assume constant
    water table depth.

    EXTERNAL INFORMATION REQUIRED:
        rain - total amount of rain (mm/day)
        lai - leaf area index (m2 leaf/m2 ground)
        petcrop - potential transpiration (from crop) (mm/day)
        petsoil - potential evaporation (from soil) (mm/day)

    METHODS:
        Statics:
            net_rainfall - net rainfall amount (mm/day)
            hydraulic_conductivity - hydraulic conductivity (m/day)
            hydraulic_gradient - hydraulic gradient (m)

        daily_water_balance - solve for the water content in each layer
    """

    def __init__(self, fname_in):
        """Initialize the SoilWater object."""
        with open(fname_in, 'rt') as fin:
            ini = json.loads(fin.read())    # read everything in the file

        self.numintervals = ini['numintervals']  # integration intervals
        self.rootdepth = ini['rootdepth']  # rooting depth (m)
        self.has_watertable = ini['has_watertable']  # has a water table?
        self.numlayers = ini['numlayers']  # the number of soil layers
        # create the soil layers
        self.layers = list(SoilLayer() for _ in range(self.numlayers))

        # read in the properties for each layer. If there is a water
        #    table, the last layer is assumed to border the water table
        layers = ini['layers']
        for i, layer in enumerate(self.layers):
            layer.thick = layers[i]['thick']  # thickness of layer (m)
            layer.vwc = layers[i]['vwc']  # vol. water content in m3/m3
            # convert from m3/m3 to mm water
            layer.wc = layer.vwc * layer.thick * 1000
            tex = layers[i]['texture']  # clay, sand, and OM (%)
            layer.texture = Texture(tex['clay'], tex['sand'], tex['om'])

        # initialize the soil layers
        #    (those that do not change with water content):
        for i in range(self.numlayers):
            prevlayer = self.layers[i - 1] if i > 0 else None
            nextlayer = self.layers[i+1] if i<self.numlayers-1 else None
            self.layers[i].initialize_layer(prevlayer, nextlayer)

        # speedier calculations: proxy to store intermediate water fluxes
        self.__pf = [{field: 0.0 for field in Fluxes._fields}
                     for _ in range(self.numlayers)]
        self.__prz = {field: 0.0 for field in RootZone._fields}
        self._rootzone_water()    # water in the root zone (mm and m3/m3)
        self.rootwater = RootZone(*[0.0] * len(RootZone._fields))

        # reduction to evaporation and transpiration due to water stress
        self.waterstresses = self._reduce_et()
        self.netrain = 0.0  # net rainfall (mm/day)
        self.aet = ActualET(0.0, 0.0)  # actual water loss by ET (mm/day)

    @staticmethod
    def net_rainfall(rain, lai):
        """Net rainfall (mm/day).

        Args:
            rain: total amount of rain (mm/day)
            lai: leaf area index (m2 leaf/m2 ground)

        Returns:
            Net rainfall (mm/day) as a float
        """
        fraction = max(0.8, 0.267 * lai)  # net rain depends on lai
        return fraction * rain

    def _rooting_depth(self):
        """Increase in rooting depth (m)."""
        # root growth rate = 8 mm/day but limited by total soil depth
        newdepth = self.rootdepth + 0.008
        depthlimit = self.layers[-1].accthick
        return min(newdepth, depthlimit)

    def _rootzone_water(self):
        """Water content in the rooting zone (m3/m3)."""
        wc = wcsat = wcfc = wcpwp = 0.0
        # only consider those soil layers in where the roots reside:
        for layer in self.layers:
            diff = layer.thick - max(0.0, layer.accthick-self.rootdepth)
            if diff <= 0:
                break  # found all the layers holding the roots, so exit
            wc += layer.vwc * diff
            wcsat += layer.swc.sat * diff
            wcfc += layer.swc.fc * diff
            wcpwp += layer.swc.pwp * diff
        vwc = wc / self.rootdepth  # convert from m water to m3/m3
        vwcsat = wcsat / self.rootdepth
        vwcfc = wcfc / self.rootdepth
        vwcpwp = wcpwp / self.rootdepth
        vwccr = vwcpwp + 0.5 * (vwcsat - vwcpwp)   # critical point 50%
        # store in a proxy dictionary to speed up calculations:
        self.__prz['wc'] = wc * 1000
        self.__prz['vwc'] = vwc
        self.__prz['critical'] = vwccr
        self.__prz['sat'] = vwcsat
        self.__prz['fc'] = vwcfc
        self.__prz['pwp'] = vwcpwp

    def _reduce_et(self):
        """Reduction in ET (0-1, 1=no stress, 0=max. stress)."""
        rde = 1 / (1 + (3.6073 * (self.layers[0].vwc /
                                  self.layers[0].swc.sat)) ** (-9.3172))
        vwc = self.__prz['vwc']
        vwcpwp = self.__prz['pwp']
        vwccr = self.__prz['critical']
        if vwc >= vwccr:
            rdt = 1.0
        elif vwcpwp < vwc < vwccr:
            rdt = (vwc - vwcpwp) / (vwccr - vwcpwp)
        else:
            rdt = 0.01
        return ActualET(rdt, rde)

    def _actual_et(self, petcrop, petsoil):
        """Actual evaporation and transpiration (mm/day).

        Args:
            petcrop: potential water loss from the crop (mm/day)
            petsoil: potential water loss from the soil (mm/day)

        Returns:
            ActualET object
        """
        return ActualET(self.waterstresses.crop * petcrop,
                        self.waterstresses.soil * petsoil)

    def _influx_from_watertable(self):
        """Influx of water from the water table (m/day)."""
        # water table assumed just beneath the last soil layer:
        last = self.layers[-1]
        k = (last.ksat - last.k) / (math.log(last.ksat)-math.log(last.k))
        hm = (33 - (33 - last.swc.airentry)) / 10   # saturated table
        hg = last.accthick
        tothead = hm + hg
        return k * (tothead - last.tothead) / (last.thick * 0.5)

    def _calc_water_fluxes(self, cummfluxes, petcrop, petsoil):
        """Calculate the various water fluxes (m/day) for all layers.

        Flux can either have a positive or negative sign:
            +ve flux - means downward flow
            -ve flux - means upward flow (against gravity)

        Args:
            cummfluxes: storing various water fluxes for each soil layer
            petcrop: potential water loss from the crop (mm/day)
            petsoil: potential water loss from the soil (mm/day)

        Returns:
            None
        """
        self._rootzone_water()
        self.waterstresses = self._reduce_et()
        self.aet = self._actual_et(petcrop, petsoil)

        # 1. calculates the influx
        prvpsi = 0.0
        for idx in range(self.numlayers):
            cur = self.layers[idx]  # current soil layer
            prv = cur.prev  # previous soil layer (None for first layer)

            # set the total head (m) and unsaturated k (m/day)
            cur.update_heads_k()  # total (gravity and matric) head (m)

            # actual evaporation E (only from first layer) and
            #    transpiration T loss (all in m/day):
            ei = 0.0 if prv is not None else self.aet.soil / 1000  # E
            cj = min(1.0, cur.accthick / self.rootdepth)
            curpsi = 1.8 * cj - 0.8 * cj ** 2
            ti = self.aet.crop * (curpsi - prvpsi) / 1000     # T
            prvpsi = curpsi

            # influx into current layer:
            if prv is not None:
                # use Darcy's law for second soil layer onwards
                n = math.log(cur.k) - math.log(prv.k)
                # logarithmic mean of k:
                k = (cur.k - prv.k) / n if n != 0.0 else cur.k
                grad = (cur.tothead-prv.tothead) / (cur.depth-prv.depth)
                curinflux = k * grad - ti
            else:
                # first layer influx is simply the net rainfall
                #    after losses from E and T
                netrain = self.netrain / 1000     # net rainfall (m)
                curinflux = min(netrain, cur.ksat) - ei - ti

            # store the intermediary fluxes:
            self.__pf[idx]['t'] = ti
            self.__pf[idx]['e'] = ei
            self.__pf[idx]['influx'] = curinflux

        # 2. calculates the net flux then the soil water content
        for idx in range(self.numlayers):
            cur = self.layers[idx]  # current soil layer
            nxt = cur.next  # next soil layer (None for last soil layer)

            wc = cur.vwc * cur.thick  # current water content (m)
            influx = self.__pf[idx]['influx']  # water into current layer
            if nxt is not None:
                # outflux is the next soil layer's influx
                outflux = self.__pf[idx + 1]['influx']
            elif not self.has_watertable:
                # water flow driven only by gravity for last layer
                outflux = cur.k
            else:
                # influx due to water table
                outflux = self._influx_from_watertable()

            # ensure a soil layer cannot be too dry (<0.005 m3/m3)
            #    or exceed soil saturation
            nextwc = influx + wc - outflux
            drylmt = cur.thick * 0.005
            satlmt = cur.thick * cur.swc.sat
            if nextwc < drylmt:
                outflux = influx + wc - drylmt
            elif nextwc > satlmt:
                outflux = influx + wc - satlmt

            if nxt is not None:
                self.__pf[idx + 1]['influx'] = outflux

            # net fluxes and water content for current layer:
            self.__pf[idx]['outflux'] = outflux
            self.__pf[idx]['netflux'] = \
                self.__pf[idx]['influx'] - self.__pf[idx]['outflux']

            # update at every sub-interval step:
            wc += self.__pf[idx]['netflux'] / self.numintervals
            # cap water content to prevent extreme, out-of-range
            #    values in later calculations
            cur.vwc = max(0.005, min(cur.swc.sat, wc/cur.thick))  # m3/m3
            cur.wc = cur.vwc * cur.thick * 1000  # water content (mm)

            # sum the water fluxes in every sub-interval step
            for field in Fluxes._fields:
                n1 = self.__pf[idx][field] / self.numintervals
                cummfluxes[idx][field] += n1

    def daily_water_balance(self, rain, lai, petcrop, petsoil):
        """Solve for the water content in each soil layer.

        Args:
            rain: total amount of rain (mm/day)
            lai: leaf area index (m2 leaf/m2 ground)
            petcrop: potential water loss from the crop (mm/day)
            petsoil: potential water loss from the soil (mm/day)

        Returns:
            None
        """
        # update the values that will not change within a day
        self.netrain = SoilWater.net_rainfall(rain, lai)
        self.rootdepth = self._rooting_depth()

        # to store the intermediary water fluxes during calculations
        cummfluxes = [{field: 0.0 for field in Fluxes._fields}
                      for _ in range(self.numlayers)]

        # solve the water balance:
        for i in range(self.numintervals):
            self._calc_water_fluxes(cummfluxes, petcrop, petsoil)

        # update the various water fluxes and
        #    the water content in the root zone:
        self.rootwater = RootZone(*[self.__prz[field]
                                    for field in RootZone._fields])
        for i, layer in enumerate(self.layers):
            layer.fluxes = Fluxes(*[cummfluxes[i][field]
                                    for field in Fluxes._fields])
