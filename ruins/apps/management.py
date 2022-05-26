import streamlit as st
import numpy as np

import pandas as pd # TODO  this should be covered by the DataManager
import xarray as xr # TODO  this should be covered by the DataManager
import matplotlib.pyplot as plt # TODO this should be moved into plotting submodule


from ruins import components


def load_alldata():
    weather = xr.load_dataset('data/weather.nc')
    climate = xr.load_dataset('data/cordex_coast.nc')

    # WARNING - bug fix for now:
    # 'HadGEM2-ES' model runs are problematic and will be removed for now
    # The issue is with the timestamp and requires revision of the ESGF reading routines
    kys = [s for s in list(climate.keys()) if 'HadGEM2-ES' not in s] #remove all entries of HadGEM2-ES (6 entries)
    climate = climate[kys]

    return weather, climate


def applySDM(wdata, data, meth='rel', cdf_threshold=0.9999999, lower_limit=0.1):
    '''apply structured distribution mapping to climate data and return unbiased version of dataset'''
    from sdm import SDM
    data_ub = data.copy()

    for k in data_ub.columns:
        data_col = data_ub[k].dropna()
        overlapx = pd.concat(
            [wdata.loc[data_col.index[0]:wdata.index[-1]], data_col.loc[data_col.index[0]:wdata.index[-1]]], axis=1)
        overlapx.columns = ['obs', 'cm']
        overlapx = overlapx.dropna()
        try:
            data_ub[k] = SDM(overlapx.obs, overlapx.cm, data_col, meth, cdf_threshold, lower_limit)
        except:
            data_ub[k] = data_ub[k] * np.nan

    data_ub[data_ub == 0.0000000] = np.nan
    data_ub = data_ub.loc[data_ub.index[0]:pd.to_datetime('2099-12-31 23:59:59')]

    return data_ub



def ub_climate(cdata, wdata, ub=True):
    varis = ['T', 'Tmax', 'Tmin', 'aP', 'Prec', 'RH', 'Rs', 'u2', 'EToHG']
    firstitem = True
    for vari in varis:
        data = cdata.sel(vars=vari).to_dataframe()
        data = data[data.columns[data.columns != 'vars']]

        if (vari == 'T') | (vari == 'Tmax') | (vari == 'Tmin'):
            meth = 'abs'
        else:
            meth = 'rel'

        if ub:
            wdatax = wdata.sel(vars=vari).to_dataframe().iloc[:, -1].dropna()
            data_ub = applySDM(wdatax, data, meth=meth)

        else:
            data_ub = data

        data_ubx = data_ub.mean(axis=1)
        data_ubx.columns = [vari]

        if firstitem:
            data_ubc = data_ubx
            firstitem = False
        else:
            data_ubc = pd.concat([data_ubc, data_ubx], axis=1)

    data_ubc.columns = varis
    return data_ubc


def get_turbine(pfi, plotit=False):
    dummy = pd.read_csv(pfi)
    v_start = dummy.loc[3].astype(np.float).values[0]
    v_max = dummy.loc[2].astype(np.float).values[0]
    P_v = dummy.loc[4:28].astype(np.float)
    P_v.index = np.arange(int(np.ceil(v_max)) + 1)[1:]
    if plotit:
        P_v.plot()
    return [P_v, v_start, v_max]


def P_wind(wind, pfi):
    [P_v, v_start, v_max] = get_turbine(pfi, False)

    # stephours = (wind.index[2] - wind.index[1]).days * 24
    # stephours = 1.

    def interp(val):
        if (val >= v_max) | (val < v_start):
            return 0.
        elif ~np.isnan(val):
            if np.ceil(val) == np.floor(val):
                return P_v.loc[int(np.floor(val))].values[0]
            else:
                x1 = P_v.loc[int(np.floor(val))].values[0]
                x2 = P_v.loc[int(np.ceil(val))].values[0]
                return ((val - np.floor(val)) * x2 + (1. - (val - np.floor(val))) * x1)
        else:
            return np.nan

    ip_vec = np.vectorize(interp)

    def get_windpower(u2):
        val = np.fmax(-1. * np.cos(np.arange(0., 2 * np.pi, 0.27)) + u2, 0.)
        return np.sum(ip_vec(val))

    return wind.apply(get_windpower)


def cropmodel(data,crop='wheat',rcp='rcp85',name='croprunname'):
    import get_climate_data.cli_crop as clc
    #read co2 concentrations
    if rcp == 'rcp85':
        CO2 = pd.read_csv('data/RCP85_MIDYEAR_CONCENTRATIONS.DAT', skiprows=38, delim_whitespace=True, index_col=0).CO2EQ
    elif rcp == 'rcp45':
        CO2 = pd.read_csv('data/RCP45_MIDYEAR_CONCENTRATIONS.DAT', skiprows=38, delim_whitespace=True, index_col=0).CO2EQ
    else:
        CO2 = pd.read_csv('data/RCP45_MIDYEAR_CONCENTRATIONS.DAT', skiprows=38, delim_whitespace=True, index_col=0).CO2EQ * 0. + 400.

    if crop == 'maize':
        x = np.array([9.375e+00, 3.198e+01, 1.973e+00, 8.700e+01, 1.144e+01, 3.630e+01, 7.260e-02, 1.237e+00, 2.180e+03, 1.501e-01, 5.230e-01, 5.678e+01, 6.970e+02])
    elif crop == 'meadow':
        x = np.array([6.543e+00, 1.238e+01, 1.029e+00, 8.706e+01, 1.510e+01, 3.253e+01, 1.199e+00, 1.535e+03, 7.784e+03, 6.530e+03, 8.030e+03, 8.092e+03, 5.884e+03])
    elif crop == 'wheat':
        x = np.array([1.257e+00, 1.276e+01, 1.101e+00, 1.010e+02, 2.578e+01, 2.769e+01, 3.416e-01, 4.940e-01, 1.906e+03, 1.921e-01, 4.595e-01, 6.066e+01, 5.360e+02])
    else:
        print('ERROR: Crop not specified with parameters.')

    yields = clc.cli_SC(data, x, CO2, nme=name)

    return yields


def water_proj():
    #hsim = pd.read_csv('data/hsim.csv',index_col=0)
    #hsim.index = pd.to_datetime(hsim.index)
    hsim_collect = pd.read_csv('data/hsim_collect.csv', index_col=0)
    hsim_collect.index = pd.to_datetime(hsim_collect.index)
    all_vals = np.ravel(hsim_collect.values)[~np.isnan(np.ravel(hsim_collect.values))]

    perci = st.slider('Adjust percentile of extreme events:', min_value=90., max_value=99.9999, value=99., key='perci')

    firstitem = True
    for i in hsim_collect.columns:
        hc = hsim_collect.loc[hsim_collect[i] > np.percentile(all_vals, perci), i].resample('1Y').count()
        hc.name = i
        if firstitem:
            h_count = hc
            firstitem = False
        else:
            h_count = pd.concat([h_count, hc], axis=1)

    fig = plt.figure(constrained_layout=True,figsize=(10,2.5))
    gs = fig.add_gridspec(1, 5)
    ax = fig.add_subplot(gs[0, :-1])
    ax1 = ax.twinx()
    ax2 = fig.add_subplot(gs[0, -1])

    all_vals = np.ravel(hsim_collect.values)[~np.isnan(np.ravel(hsim_collect.values))]
    sns.distplot(all_vals, ax=ax2)
    ax2.vlines(np.percentile(all_vals, perci), 0., 0.06, colors='red')
    ax2.text(np.percentile(all_vals, perci), 0.065, str(perci) + '%', c='red', ha='center')
    ax2.set_xlim(-3, np.percentile(all_vals, 99.98))

    for i in hsim_collect.columns:
        hsim_collect[i].plot(style='.', label='_nolegend_', c='gray', alpha=0.2, ax=ax)
        try:
            hsim_collect.loc[hsim_collect[i] > np.percentile(all_vals, perci), i].plot(style='.', label='_nolegend_',
                                                                                   c='red', alpha=0.2, ax=ax)
        except:
            pass

    (h_count.sum(axis=1) / len(h_count.columns)).rolling(7).mean().plot(ax=ax1, grid=False, ls='--', label='all')
    cc = [x for x in h_count.columns if x.split('.')[-1] == 'rcp45']
    (h_count[cc].sum(axis=1) / len(cc)).rolling(7).mean().plot(ax=ax1, grid=False, label='rcp45')

    cc = [x for x in h_count.columns if x.split('.')[-1] == 'rcp85']
    (h_count[cc].sum(axis=1) / len(cc)).rolling(7).mean().plot(ax=ax1, grid=False, label='rcp85')
    ax1.legend()
    ax.set_ylabel('Q (mm/day)')
    ax1.set_ylabel('days w/ Q>' + str(np.round(perci / 100., 3)) + ' percentile\n7 year rolling mean')
    st.pyplot()



def management_explorer(w_topic: str):
    rcps = ['rcp45', 'rcp85']  # 'rcp26',
    rcp = st.sidebar.selectbox('RCP:', rcps)

    weather, climate = load_alldata()
    data = climate.filter_by_attrs(RCP=rcp)

    ub = st.sidebar.checkbox('Apply SDM bias correction', True)

    cdata = ub_climate(data, weather['krummhoern'], ub)

    if w_topic == 'Agriculture':
        crops = ['wheat', 'maize', 'meadow']
        crop = st.sidebar.selectbox('Crop:', crops)

        yieldx = cropmodel(cdata,crop,rcp,name=crop+' @ '+rcp)

        yieldx.rolling(7).mean().plot()
        st.pyplot()

    elif w_topic == 'Wind Energy':
        storeddata = st.checkbox('Use pre-calculated data (calculation not yet optimized - very slow)', True)
        if storeddata:
            cwind_p = pd.read_csv('data/windpowerx.csv', index_col=0)
            cwind_p.index = pd.to_datetime(cwind_p.index)
            plt.figure(figsize=(10, 2.5))
            cwind_p[[x for x in cwind_p.columns if rcp in x][::3]].mean(axis=1).plot(label='Enercon 3MW')
            cwind_p[[x for x in cwind_p.columns if rcp in x][1::3]].mean(axis=1).plot(label='9x Enercon 0.33MW')
            cwind_p[[x for x in cwind_p.columns if rcp in x][2::3]].mean(axis=1).plot(label='0.4x Enercon 7.5MW')
        else:
            wpengine = ['Enercon 3MW', 'Vestas 3MW', '9x Enercon 0.33MW', '13x Vestas 0.23MW', '0.4x Enercon 7.5MW']
            #wpengine = ['Enercon 3MW', '9x Enercon 0.33MW', '0.4x Enercon 7.5MW']
            turbine = st.sidebar.selectbox('Select turbine:', wpengine)

            plt.figure(figsize=(10,2.5))
            if turbine == 'Enercon 3MW':
                pfi = 'data/pow/Enercon E-115 3000kW (MG).pow'
                P_wind(cdata.u2, pfi).resample('1Y').sum().rolling(7).mean().plot(label=turbine)
            elif turbine == 'Vestas 3MW':
                pfi = 'data/pow/Vestas 112m 3MW (MT).pow'
                P_wind(cdata.u2, pfi).resample('1Y').sum().rolling(7).mean().plot(label=turbine)
            elif turbine == '9x Enercon 0.33MW':
                pfi = 'data/pow/Enercon E33_33.4m _330kw(MT).pow'
                (P_wind(cdata.u2, pfi).resample('1Y').sum()*9.).rolling(7).mean().plot(label=turbine)
            elif turbine == '13x Vestas 0.23MW':
                pfi = 'data/pow/Vestas V29-225kw(MT).pow'
                (P_wind(cdata.u2, pfi).resample('1Y').sum() * 13.).rolling(7).mean().plot(label=turbine)
            elif turbine == '0.4x Vestas 7.5MW':
                pfi = 'data/pow/Enercon E-126_127m_7500kW (MT).pow'
                (P_wind(cdata.u2, pfi).resample('1Y').sum() * 0.4).rolling(7).mean().plot(label=turbine)

        plt.legend()
        plt.ylabel('Wh/yr')
        st.pyplot()

    elif w_topic == 'Extreme Events':
        water_proj()


def main_app():
    st.header('Management Explorer')
    st.markdown('''In this section we project the climate model outputs to ecosystem services through diffferent model approaches. The impact of potential management is tackeled at a rather broad level in terms of exemplary options.''', unsafe_allow_html=True)
    
    # TODO: refactor this
    topics = ['Warming', 'Weather Indices', 'Drought/Flood', 'Agriculture', 'Extreme Events', 'Wind Energy']
    
    # topic selector
    topic = components.legacy.topic_selector(topic_list=topics, container=st.sidebar)
    
    # TODO refactor this    
    management_explorer(topic)


if __name__ == '__main__':
    main_app()
