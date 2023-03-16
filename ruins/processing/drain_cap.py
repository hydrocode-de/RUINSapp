from typing import Tuple
import numpy as np
import pandas as pd

### Define parameters of the default pumping function / pump chart
x = np.array([7.,6.,5.,4.,3.5,3.,2,1,0,5.,4.,3.5,3.,2]) * 1000 # water gradient [mm] (by factor 1000 from m)
y = np.array([0,4.2,8.4,12.6,14.5,15.8,17.5,19,20.5,8.4,12.6,14.5,15.8,17.5]) * 3600 / (35000 * 100 * 100) * 1000 * 4  # "*3600 / (35000 * 100 * 100) * 1000 * 4)" converts m^3/s in mm/h
pumpcap_fit = np.polynomial.polynomial.Polynomial.fit(x = x, y = y, deg = 2)

 
def drain_cap(h_tide: np.ndarray, h_store: np.ndarray, h_min: int = -2000, pump_par = pumpcap_fit, canal_par: Tuple[float, float] = [1.016 , 2572.], h_increment: int = 50, h_wind_safe: int = 0, h_grad_pump_max: int = 4000):
    """
    Find the maximal flow rate in a system with a pump and a canal.
    The flow through the pump is determined by the gradient from inner to outer water level and a pump function.
    The flow through the canal is determined by the gradient from the canal water level to the pump inner water level and a canal flow function.
    The inner water level is unknown and estimated within this function, but a lower limit can be set.
    
    Parameters
    ----------
    h_tide : np.ndarray
        the outer water level at the pump
    h_store : np.ndarray
         the canal water level
    h_min : int
        the lower boundary of the inner water level
    pump_par : np.ndarray
        parameters of the pump function
    canal_par : Tuple[float, float]
        parameters of the canal flow function
    h_increment : int
        increment of inner water level estimation
    h_wind_safe : int
        gradient from canal to inner water level, which is induced by wind and therefore not contributing to flow
    h_grad_pump_max :int
        maximum gradient from inner to outer water level, at which pumps shall run 

    Returns
    -------
    q_channel : np.ndarray
        the actual maximum flow through canal and pump
    h_min : float
        the estimated inner water level
    q_pump : float
         the maximum flow, which could be pumped if not limited by canals

    """
    # set h_min to either absolute technical lower limit or maximal pump gradient 
    h_min = np.maximum(h_min, h_tide - h_grad_pump_max)
    
    pumplim = True
    
    # in case drainage ist limited by pumps, the minimum water level at knock increases until the flow is limited by channel_
    while pumplim:
        if(h_tide <= h_min): # if outer water level is lower then inner water level we can sluice
            q_pump = pump_par(1) # assume 1 mm gradient to pump to get some estimate - eventually sluicing is more effective
        else:
            q_pump = pump_par(h_tide - h_min)

        if(((h_store - h_min) - h_wind_safe) <= 0):
            q_channel = 0.
        else:
            q_channel = ((((h_store - h_min) - h_wind_safe)**canal_par[0])/canal_par[1])
            
        # end the loop, if h_min is set to value that q_channel is smaller than q_pump, otherwise increase h_min
        if(q_pump >= q_channel or q_channel <= 0) :
            pumplim = False
        else:
            h_min += h_increment

    # set output h_min to either technical lower limit or water level in canals
    h_min = np.minimum(h_min, h_store)

    return (q_channel, h_min, q_pump)

def storage_model (forcing_data, canal_par, v_store = 0, h_store_target = -1400, canal_area = 4, h_forecast_pump = 0, h_grad_pump_max = 6000, h_canal_max = -900, pump_par = pumpcap_fit, h_min = -2000):
    """
    Storage model used for the Krummhoern region

    Parameters
    ----------
    forcing_data : pd.DataFrame
        time series forcing data of the storage model with the columns:
         - 'recharge' the water volume [waterbalace mm] which flows into the storage
         - 'h_tide' the outer (tidal) water level at the pumps [mm NHN]
         - 'wig' a wind induced gradient [mm height] in the canals, which alters the flow capacity of the canals
    canal_par : np.ndarray
         parameters of the canal flow capacity
    v_store : numeric
        initial water volume [waterbalace mm] in the canals above target water level
    h_store_target : numeric
        target water level [mm NHN] in the canals
    canal_area : numeric
        share of water area on total landscape area [%]
    h_forecast_pump : numeric
        water level [mm height] which is substracted from target water level to allow lower canal water level before forecasted event
    h_grad_pump_max : numeric
        allowed maximal gradient [h_tide - h_min] for pumps, at which pumps will be turned off for their technical protection
    pump_par : np.ndarray
        parameters of the pump function
    h_min : numeric
        minimum water level height [mm NHN] at inner side of pumps

    Returns
    -------
    h_store_rec : np.ndarray
        water height in canals [mm NHN]
    q_pump_rec : np.ndarray
        possible drainage capacity by pumps [waterbalace mm]
    h_min_rec : np.ndarray
        evaluated lowest inner water level [mm NHN]
    q_rec : np.ndarray
        "real" flow [waterbalace mm], either limited by drainage capacity or pump capacity
    usage_pump_rec : np.ndarray
        Actually used percentage of possible pumping capacity
    v_store_rec : np:ndarray
        time series of water volume in storage [waterbalace mm]
    """
    v_store_rec = []
    h_min_rec = []
    q_pump_rec = []
    usage_pump_rec = []
    q_rec = []
    
    for step_id, step in forcing_data.iterrows():

        # recharge storage
        v_store += step['recharge']
        v_store_max_step = v_store

        cap = drain_cap(h_tide = step['h_tide'],                                      # parse tidal water level
                        h_store = np.min(((h_store_target + v_store*100/canal_area), h_canal_max)),   # limit maximal water flow at upper canal crest
                        h_min = h_min,                                     # parse lowest inner water level
                        pump_par = pump_par,                                     # parse pump parameters
                        canal_par = canal_par,                                     # parse canal parameters
                        h_increment = 1,                                              # increment inner water level by 1 mm steps
                        h_wind_safe = step['wig'],                             # parse wind induced gradient
                        h_grad_pump_max = h_grad_pump_max)                                     # parse maximum pump gradient
        # drain storage
        v_store -= cap[0]
        # compare new storage value to lower limit of storage
        v_store = np.maximum(v_store, -h_forecast_pump/100*canal_area)
        # save time step
        v_store_rec = np.append(v_store_rec, v_store)
        h_min_rec = np.append(h_min_rec, cap[1])
        q_pump_rec = np.append(q_pump_rec, cap[2])

        v_flow = v_store_max_step - v_store
        q_rec = np.append(q_rec, v_flow)
        # save "power consumption" of pumps
        usage_pump_rec = np.append(usage_pump_rec, v_flow/cap[2])

    h_store_rec = h_store_target + v_store_rec*100/canal_area
    
    return (h_store_rec, q_pump_rec, h_min_rec, q_rec, usage_pump_rec, v_store_rec)
