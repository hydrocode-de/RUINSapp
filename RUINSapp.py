# -*- coding: utf-8 -*-

import streamlit as st
import pandas as pd
import numpy as np
import xarray as xr

import seaborn as sns
sns.set_style('whitegrid', {'grid.linestyle': u'--'})

from sdm import SDM

#import statsmodels.api as sm
#import altair as alt
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
from PIL import Image
from pathlib import Path

st.title('RUINS climate data app')

# helper functions
#@st.cache(persist=True)
def load_alldata():
    weather = xr.load_dataset('data/weather.nc')
    climate = xr.load_dataset('data/cordex_coast.nc')

    # WARNING - bug fix for now:
    # 'HadGEM2-ES' model runs are problematic and will be removed for now
    # The issue is with the timestamp and requires revision of the ESGF reading routines
    kys = [s for s in list(climate.keys()) if 'HadGEM2-ES' not in s] #remove all entries of HadGEM2-ES (6 entries)
    climate = climate[kys]

    return weather, climate

weather, climate = load_alldata()


def load_data(sel='Weather',regagg=None):
    #Read data from netcdf files and return xarray
    if sel == 'Weather':
        data = xr.load_dataset('data/weather.nc')
    elif sel == 'CORDEX':
        data = xr.load_dataset('data/cordex_coast.nc')
    else:
        if regagg == 'North Sea Coast':
            data = xr.load_dataset('data/cordex_coast.nc')
            data.filter_by_attrs(RCP=sel)

    return data


def read_markdown_file(markdown_file):
    return Path(markdown_file).read_text()


def kde(data, cmdata='none', split_ts=1, cplot=True, eq_period=True):
    # plot of kde with stripes
    from sklearn.neighbors import KernelDensity
    cxx = ['#E69F00', '#009E73', '#0072B2', '#D55E00', '#CC79A7']
    cxx2 = ['#8c6bb1', '#810f7c']

    data = data[~np.isnan(data)]
    x_d = np.linspace(np.min(data) * 0.9, np.max(data) * 1.1, len(data))

    # instantiate and fit the KDE model
    kde = KernelDensity(bandwidth=1.0, kernel='gaussian')
    kde.fit(data[:, None])

    # score_samples returns the log of the probability density
    logprob = kde.score_samples(x_d[:, None])

    if cplot & (split_ts == 1):
        plt.fill_between(x_d, np.exp(logprob), alpha=0.4, facecolor='grey')

    lp = np.exp(logprob)
    xd = x_d

    if type(cmdata) != str:
        fig, (ax, cax, cax2) = plt.subplots(ncols=3, figsize=(10.5, 2.3), gridspec_kw={"width_ratios": [1, 0.02, 0.02]})

        x_d2 = np.linspace(np.min(cmdata) * 0.9, np.max(cmdata) * 1.1, len(cmdata))
        # instantiate and fit second KDE model
        kde2 = KernelDensity(bandwidth=1.0, kernel='gaussian')
        kde2.fit(cmdata[:, None])

        # score_samples returns the log of the probability density
        logprob2 = kde2.score_samples(x_d2[:, None])

        if cplot & (split_ts == 1):
            ax.fill_between(x_d2, np.exp(logprob2), alpha=0.4, facecolor='grey')

        lp2 = np.exp(logprob2)
        xd2 = x_d2
    else:
        fig, (ax, cax) = plt.subplots(ncols=2, figsize=(10.5, 2.3), gridspec_kw={"width_ratios": [1, 0.06]})

    if split_ts > 1:
        if eq_period:
            spliti = [0, len(data) - 40, len(data) - 20, len(data)]
        else:
            spliti = np.linspace(0, len(data), split_ts + 1).astype(int)

        for i in np.arange(split_ts):
            datax = data.iloc[spliti[i]:spliti[i + 1]]
            x_d = np.linspace(np.min(datax) * 0.9, np.max(datax) * 1.1, len(datax))

            try:
                # instantiate and fit the KDE model
                kde = KernelDensity(bandwidth=1.0, kernel='gaussian')
                kde.fit(datax[:, None])

                # score_samples returns the log of the probability density
                logprob = kde.score_samples(x_d[:, None])

                if cplot:
                    ax.fill_between(x_d, np.exp(logprob), alpha=0.4, facecolor=cxx[i],
                                    label='-'.join([str(datax.index.year.min()), str(datax.index.year.max())]))
            except:
                pass

    if type(cmdata) != str:
        # add climate model data
        csplit_ts = [2040, 2080]
        for i in np.arange(2):
            datax = cmdata.loc[(cmdata.index.year >= csplit_ts[i]) & (cmdata.index.year < csplit_ts[i] + 20)]
            x_d = np.linspace(np.min(datax) * 0.9, np.max(datax) * 1.1, len(datax))

            try:
                # instantiate and fit the KDE model
                kde = KernelDensity(bandwidth=1.0, kernel='gaussian')
                kde.fit(datax[:, None])

                # score_samples returns the log of the probability density
                logprob = kde.score_samples(x_d[:, None])

                if cplot:
                    ax.fill_between(x_d, np.exp(logprob), alpha=0.4, facecolor=cxx2[i],
                                    label='-'.join([str(datax.index.year.min()), str(datax.index.year.max())]))

            except:
                pass

    ax.legend(loc=1, ncol=5)

    if cplot:
        # cmap = plt.cm.get_cmap('cividis_r')
        cmap = plt.cm.get_cmap('viridis_r')
        colors = plt.cm.cividis_r(np.linspace(0, 1, len(data)))
        colorsx = cmap(np.arange(cmap.N))

        for i in np.arange(len(data)):
            ax.plot([data.iloc[i], data.iloc[i]], [0, np.max(lp) * 0.9], c=colors[i])

        labcb = 'Year'
        if type(cmdata) != str:
            cmap2 = plt.cm.get_cmap('plasma')
            colors2 = plt.cm.plasma(np.linspace(0, 1, len(cmdata)))
            colorsx2 = cmap2(np.arange(cmap2.N))

            for i in np.arange(len(cmdata)):
                ax.plot([cmdata.iloc[i], cmdata.iloc[i]], [0, np.max(lp) * 0.9], c=colors2[i])

            cbar2 = plt.colorbar(plt.cm.ScalarMappable(cmap=cmap2), cax=cax2, label=labcb,
                                 ticks=[0, 0.2, 0.4, 0.6, 0.8, 1], fraction=0.0027, anchor=(1.0, 0.1))
            cbar2.ax.set_yticklabels(
                np.round(np.linspace(cmdata.index.year.min(), cmdata.index.year.max(), 6)).astype(int).astype(str))
            labcb = ''

        cbar = plt.colorbar(plt.cm.ScalarMappable(cmap=cmap), cax=cax, label=labcb, ticks=[0, 0.2, 0.4, 0.6, 0.8, 1])
        cbar.ax.set_yticklabels(
            np.round(np.linspace(data.index.year.min(), data.index.year.max(), 6)).astype(int).astype(
                str))  # vertically oriented colorbar

    ax.set_ylabel('Occurrence (KDE)')

    return ax


def yrplot_hm(sr, ref=[1980, 2000], ag='sum', qa=0.95, cbar_title='Temperature anomaly (K)', cmx='coolwarm', cmxeq=True, li=False):
    # plot of heatmap with monthyl and annual stripes
    yrs = sr.index.year.unique()
    dummy = np.zeros((len(yrs), 14)) * np.nan
    dummy = pd.DataFrame(dummy)
    dummy.index = yrs
    dummy.columns = ['J', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D', '', 'Year']

    for i in sr.index:
        dummy.iloc[i.year - yrs[0], i.month - 1] = sr.loc[i]
    for i in yrs:
        if ag == 'sum':
            dummy.iloc[i - yrs[0], 13] = sr.loc[sr.index.year == i].sum()
            cmx = 'coolwarm_r'
        elif ag == 'min':
            dummy.iloc[i - yrs[0], 13] = sr.loc[sr.index.year == i].min()
        elif ag == 'max':
            dummy.iloc[i - yrs[0], 13] = sr.loc[sr.index.year == i].max()
        else:  # ag == 'mean'
            dummy.iloc[i - yrs[0], 13] = sr.loc[sr.index.year == i].mean()

    if ref == None:
        pass
    else:
        refx = dummy.loc[ref[0]:ref[1]].mean(axis=0)
        dummy = dummy - refx

    if cmxeq:
        vxU = dummy.abs().quantile(qa).quantile(qa)
        vxL = -1. * vxU
    else:
        vxU = dummy.quantile(qa).quantile(qa)
        vxL = dummy.quantile(1. - qa).quantile(1. - qa)

    if ag == 'sum':
        dummy.iloc[:, 13] = dummy.iloc[:, 13] / 12

    plt.figure(figsize=(8,len(dummy)/15.))
    ax = sns.heatmap(dummy, cmap=cmx, vmin=vxL, vmax=vxU, cbar_kws={'label': cbar_title})

    if ref == None:
        pass
    else:
        ax.add_patch(
            plt.Rectangle((0, ref[0] - yrs[0]), 12, ref[1] - ref[0], fill=True, edgecolor='red', facecolor='gray', lw=2,
                          alpha=0.3, clip_on=False))
        ax.add_patch(
            plt.Rectangle((13, ref[0] - yrs[0]), 1, ref[1] - ref[0], fill=True, edgecolor='red', facecolor='gray', lw=2,
                          alpha=0.3, clip_on=False))
        ax.annotate('Reference period', (0.5, ref[1] - yrs[0] - 2), color='white', weight='bold', ha='left',
                    va='bottom', alpha=0.6)

    if type(li) == int:
        ax.axhline(li - yrs[0], color='k', ls='--', lw=1, alpha=0.5)
        ax.annotate(' >> observed', (12.5, li - yrs[0] - 0.5), color='k', ha='center', va='bottom', alpha=0.6,
                    rotation=90.)
        ax.annotate('modelled << ', (12.5, li - yrs[0] + 0.5), color='k', ha='center', va='top', alpha=0.6,
                    rotation=90.)
        # ax.add_patch(plt.Rectangle((0, li-yrs[0]), 12, 0, fill=False, edgecolor='k', ls='--', lw=1, alpha=0.5, clip_on=False))

    ax.set_ylabel('Year')
    ax.set_xlabel('Month          ')
    return


def monthlyx(dy, dyx=1, ylab='T (°C)', clab1='Monthly Mean in Year', clab2='Monthly Max in Year', pls='cividis_r'):
    cmap = plt.cm.get_cmap(pls)
    colors = cmap(np.linspace(0, 1, len(dy.index.year.unique())+1))
    colorsx = cmap(np.arange(cmap.N))

    idx1 = dy.index.year - dy.index.year.min()
    idx1m = dy.index.month

    if type(dyx) == int:
        pass
    else:
        idx2 = (dyx.index.year - dyx.index.year.min()).astype(int)
        idx2m = dyx.index.month

        cmap1 = plt.cm.get_cmap('gist_heat_r')
        colors1 = plt.cm.gist_heat_r(np.linspace(0, 1, len(dyx.index.year.unique()) + 1))
        colorsx1 = cmap1(np.arange(cmap1.N))

    for i in dy.columns:
        plt.scatter(idx1m + (np.random.rand(len(dy)) - 1.5), dy[i].values.astype(np.float), c=colors[idx1], alpha=0.6, s=2)

    if type(dyx) == int:
        pass
    else:
        for i in dyx.columns:
            plt.scatter(idx2m + (np.random.rand(len(dyx)) - 1.5), dyx[i].values.astype(np.float), c=colors1[idx2], alpha=0.6, s=2)

    cbar = plt.colorbar(plt.cm.ScalarMappable(cmap=cmap), label=clab1, ticks=[0, 0.2, 0.4, 0.6, 0.8, 1])
    cbar.ax.set_yticklabels(np.round(np.linspace(dy.index.year.min(), dy.index.year.max(), 6)).astype(int).astype(str))

    if type(dyx) == int:
        pass
    else:
        cbar1 = plt.colorbar(plt.cm.ScalarMappable(cmap=cmap1), label=clab2, ticks=[0, 0.2, 0.4, 0.6, 0.8, 1])
        cbar1.ax.set_yticklabels(
            np.round(np.linspace(dyx.index.year.min(), dyx.index.year.max(), 6)).astype(int).astype(str))

    plt.xticks([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
           ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])
    plt.ylabel(ylab)
    return


def plt_map(sel='all',cm='none'):
    import plotly.graph_objs as go
    import plotly.express as px

    dummy = xr.open_dataset('data/CORDEXgrid.nc')
    dummy5 = xr.open_dataset('data/CMIP5grid.nc')
    stats = pd.read_csv('data/stats.csv', index_col=0)
    stats['ms'] = 15.
    stats['color'] = 'gray'

    mapbox_access_token = 'pk.eyJ1IjoiY29qYWNrIiwiYSI6IkRTNjV1T2MifQ.EWzL4Qk-VvQoaeJBfE6VSA'
    px.set_mapbox_access_token(mapbox_access_token)

    nodexy = pd.DataFrame([dummy.lon.values.ravel(), dummy.lat.values.ravel()]).T
    nodexy.columns = ['lon', 'lat']
    nodexy['hov'] = 'CORDEX grid'

    def lin_grid(fig, dummy, chex='#d95f0e', opc=0.7):
        x1, x2 = np.shape(dummy.lon)
        lond = np.diff(dummy.lon.values)
        latd = np.diff(dummy.lat.values)
        lond1 = np.diff(dummy.lon.values, axis=0)
        latd1 = np.diff(dummy.lat.values, axis=0)

        for i in np.arange(x2)[1:-1]:
            fig.add_trace(go.Scattermapbox(
                mode='lines',
                lon=dummy.lon.values[:, i] - 0.5 * lond[:, i - 1],
                lat=dummy.lat.values[:, i] - 0.5 * latd[:, i - 1],
                line={'color': chex, 'width': 1},
                hoverinfo='skip',
                opacity=opc))

        fig.add_trace(go.Scattermapbox(
            mode='lines',
            lon=dummy.lon.values[:, i] + 0.5 * lond[:, i - 1],
            lat=dummy.lat.values[:, i] + 0.5 * latd[:, i - 1],
            line={'color': chex, 'width': 1},
            hoverinfo='skip',
            opacity=opc))

        for i in np.arange(x1)[1:-1]:
            fig.add_trace(go.Scattermapbox(
                mode='lines',
                lon=dummy.lon.values[i, :] - 0.5 * lond1[i - 1, :],
                lat=dummy.lat.values[i, :] - 0.5 * latd1[i - 1, :],
                line={'color': chex, 'width': 1},
                hoverinfo='skip',
                opacity=opc))

        fig.add_trace(go.Scattermapbox(
            mode='lines',
            lon=dummy.lon.values[i, :] + 0.5 * lond1[i - 1, :],
            lat=dummy.lat.values[i, :] + 0.5 * latd1[i - 1, :],
            line={'color': chex, 'width': 1},
            hoverinfo='skip',
            opacity=opc))

        return fig

    def add_stats(sel='all'):


        if sel == 'all':
            ac = '#2c7fb8'
            stats1 = stats
        else:
            ac = 'gray'

            fig.add_trace(go.Scattermapbox(
                lat=stats.lat,
                lon=stats.lon,
                mode='markers',
                marker=go.scattermapbox.Marker(
                    size=10,
                    color=ac,
                    opacity=0.8
                ),
                text=stats['Station name']
            ))

            ac = '#df65b0'
            if sel == 'krummhoern':
                stats1 = stats.loc[stats.krummhoern == True]
            elif sel == 'coast':
                stats1 = stats.loc[stats.coast == True]
            elif sel == 'niedersachsen':
                stats1 = stats.loc[stats.niedersachsen == True]
            elif sel == 'inland':
                stats1 = stats.loc[stats.inland == True]
            else:
                try:
                    stats1 = pd.DataFrame(stats.loc[sel]).T
                except:
                    ac = 'gray'
                    stats1 = pd.DataFrame(stats.loc['Norderney']).T

        fig.add_trace(go.Scattermapbox(
            lat=stats1.lat,
            lon=stats1.lon,
            mode='markers',
            marker=go.scattermapbox.Marker(
                size=10,
                color=ac,
                opacity=0.8
            ),
            text=stats1['Station name']
        ))

        return fig

    def add_cmpx(cm):
        maskcordex_coast = [[10, 4], [11, 4], [11, 5], [11, 6], [11, 7], [11, 8], [10, 8], [9, 8], [8, 8], [8, 9],
                            [8, 10], [9, 10], [10, 10], [10, 11], [11, 12], [12, 12], [12, 13], [12, 14], [13, 14],
                            [14, 14], [15, 14], [16, 14], [17, 14], [18, 14], [19, 15], [20, 15], [21, 14], [22, 14],
                            [22, 13],
                            [9, 4], [10, 5], [10, 6], [10, 7], [10, 8], [9, 7], [8, 7], [7, 7], [7, 8], [7, 9], [9, 9],
                            [10, 12], [11, 13], [11, 14], [14, 15], [15, 15], [16, 15], [17, 15], [18, 15], [19, 16],
                            [20, 16], [21, 15], [22, 15],
                            [11, 4], [12, 4], [12, 5], [12, 6], [12, 7], [12, 8], [11, 10], [11, 11], [13, 12],
                            [13, 13], [14, 13], [15, 13], [16, 13], [17, 13], [18, 13], [19, 14], [20, 14], [21, 13]]
        for cc in maskcordex_coast:
            fig.add_trace(go.Scattermapbox(
                lat=[dummy.lat.values[tuple(cc)]],
                lon=[dummy.lon.values[tuple(cc)]],
                mode='markers',
                marker=go.scattermapbox.Marker(
                    size=8,
                    color='#fec44f',
                    opacity=0.8
                ),
                hoverinfo='skip'
            ))
        return fig

    # fig = go.Scattermapbox(lon = nodexy.lon, lat= nodexy.lat, mode='markers', marker_symbol='square', marker_size=15)
    #fig = px.scatter_mapbox(nodexy, lat='lat', lon='lon', center={'lat': 53.0, 'lon': 8.3}, zoom=5, opacity=0.1, hover_data=['hov'])
    fig = px.scatter_mapbox(stats, lat='lat', lon='lon', center={'lat': 53.0, 'lon': 8.6}, zoom=5, size='ms', opacity=0.8, color='color', hover_data=['Station name', 'lat', 'lon'], size_max=10)
    if cm != 'none':
        fig = lin_grid(fig, dummy)
        fig = lin_grid(fig, dummy5, '#2c7fb8')
        fig = add_cmpx(cm)
    fig = add_stats(sel)
    fig.update_layout(showlegend=False,width=300, height=350,margin=dict(l=10, r=10, b=10, t=10))  # ,center={'lat':54.0,'lon':8.3}, zoom=7)
    st.sidebar.plotly_chart(fig)
    return


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


def climate_indi(ts, indi='Summer days (Tmax ≥ 25°C)'):
    '''
    Calculate climate indicator days.
    Input time series of meteorological data
    '''
    if pd.infer_freq(ts.index) != 'D':
        print('Please provide daily data.')
        return

    if indi == 'Summer days (Tmax ≥ 25°C)':  # summer days
        return (ts.Tmax >= 25.).groupby(ts.index.year).sum()
    elif indi == 'Ice days (Tmax < 0°C)':  # ice days
        return (ts.Tmax < 0.).groupby(ts.index.year).sum()
    elif indi == 'Frost days (Tmin < 0°C)':  # frost days
        return (ts.Tmin < 0.).groupby(ts.index.year).sum()
    elif indi == 'Hot days (Tmax ≥ 30°C)':  # hot days
        return (ts.Tmax >= 30.).groupby(ts.index.year).sum()
    elif indi == 'Tropic nights (Tmin ≥ 20°C)':  # tropic night
        return (ts.Tmin >= 20.).groupby(ts.index.year).sum()
    elif indi == 'Rainy days (Precip ≥ 1mm)':  # rainy days
        return (ts.Prec >= 1.).groupby(ts.index.year).sum()
    else:
        print('Nothing calculated.')
        return


def climate_indices(stati='coast',cliproj=True):
    cindi = ['Ice days (Tmax < 0°C)', 'Frost days (Tmin < 0°C)', 'Summer days (Tmax ≥ 25°C)', 'Hot days (Tmax ≥ 30°C)','Tropic nights (Tmin ≥ 20°C)', 'Rainy days (Precip ≥ 1mm)']
    ci_topic = st.selectbox('Select Index:', cindi)

    if ci_topic == 'Rainy days (Precip ≥ 1mm)':
        vari = 'Prec'
        meth = 'rel'
    elif (ci_topic == 'Frost days (Tmin < 0°C)') | (ci_topic == 'Tropic nights (Tmin ≥ 20°C)'):
        vari = 'Tmin'
        meth = 'abs'
    else:
        vari = 'Tmax'
        meth = 'abs'

    w1 = weather[stati].sel(vars=vari).to_dataframe().dropna()
    w1.columns = ['bla', vari]

    plt.figure(figsize=(10,2.5))
    wi = climate_indi(w1, ci_topic).astype(int)
    wi.plot(style='.', color='steelblue', label='Coast weather')
    wi.rolling(10, center=True).mean().plot(color='steelblue', label='Rolling mean\n(10 years)')

    if cliproj:
        c1 = climate.sel(vars=vari).to_dataframe()
        c1 = c1[c1.columns[c1.columns != 'vars']]
        c2 = applySDM(w1[vari], c1, meth=meth)

        firstitem = True
        for j in c2.columns:
            dummyt = pd.DataFrame(c2[j])
            dummyt.columns = [vari]
            ci = pd.DataFrame(climate_indi(dummyt, ci_topic).astype(int))
            ci.columns = [j]

            if firstitem:
                ci[j].plot(style='.', color='gray', alpha=0.1, label='all climate projections')
                cid = ci
                firstitem = False
            else:
                ci[j].plot(style='.', color='gray', alpha=0.1, label='_')
                cid = pd.concat([cid, ci], axis=1)

        rcpx = np.array([x[-5:] for x in cid.columns.values])
        for n in np.unique(rcpx):
            nx = n
            if n == np.unique(rcpx)[-1]:
                nx = n + '\n(Rolling of 5 years)'
            cid[cid.columns[rcpx == n]].mean(axis=1).rolling(5, center=True).mean().plot(label='Mean of ' + nx)

    plt.legend(ncol=2)
    plt.ylabel('Number of days')
    plt.title(ci_topic)
    st.pyplot()

    if ci_topic == 'Ice days (Tmax < 0°C)':
        st.markdown('''Number of days in one year which persistently remain below 0°C air temperature.''')
    elif ci_topic == 'Frost days (Tmin < 0°C)':
        st.markdown('''Number of days in one year which reached below 0°C air temperature.''')
    elif ci_topic == 'Summer days (Tmax ≥ 25°C)':
        st.markdown('''Number of days in one year which reached or exceeded 25°C air temperature.''')
    elif ci_topic == 'Hot days (Tmax ≥ 30°C)':
        st.markdown('''Number of days in one year which reached or exceeded 30°C air temperature.''')
    elif ci_topic == 'Tropic nights (Tmin ≥ 20°C)':
        st.markdown('''Number of days in one year which persistently remained above 20°C air temperature.''')
    elif ci_topic == 'Rainy days (Precip ≥ 1mm)':
        st.markdown('''Number of days in one year which received at least 1 mm precipitation.''')
    return



def weather_explorer():
    #weather = load_data('Weather')

    #aspects = ['Annual', 'Monthly', 'Season']
    #w_aspect = st.sidebar.selectbox('Temporal aggregate:', aspects)

    #cliproj = st.sidebar.checkbox('add climate projections',False)

    statios = list(weather.keys())
    stat1 = st.selectbox('Select station/group (see map in sidebar for location):', statios)

    aspects = ['Annual', 'Monthly']  # , 'Season']
    w_aspect = st.selectbox('Select temporal aggregate:', aspects)

    cliproj = st.checkbox('add climate projections (for coastal region)',False)
    if cliproj:
        plt_map(stat1, 'CORDEX')
        st.sidebar.markdown(
            '''Map with available stations (<span style="color:blue">blue dots</span>) and selected reference station (<span style="color:magenta">magenta highlight</span>). The climate model grid is given in <span style="color:orange">orange</span> with the selected references as filled dots.''',
            unsafe_allow_html=True)
    else:
        plt_map(stat1)
        st.sidebar.markdown(
            '''Map with available stations (<span style="color:blue">blue dots</span>) and selected reference station (<span style="color:magenta">magenta highlight</span>).''',
            unsafe_allow_html=True)

    if w_topic == 'Warming':

        navi_vars = ['Maximum Air Temperature', 'Mean Air Temperature', 'Minimum Air Temperature']
        navi_var = st.sidebar.radio("Select variable:", options=navi_vars)
        if navi_var[:4] == 'Mini':
            vari = 'Tmin'
            afu = np.min
            ag = 'min'
        elif navi_var[:4] == 'Maxi':
            vari = 'Tmax'
            afu = np.max
            ag = 'max'
        else:
            vari = 'T'
            afu = np.mean
            ag = 'mean'

        if w_aspect == 'Annual':
            wdata = weather[stat1].sel(vars=vari).resample(time='1Y').apply(afu).to_dataframe()[stat1]
            wdata = wdata[~np.isnan(wdata)]
            allw = weather.sel(vars=vari).resample(time='1Y').apply(afu).to_dataframe().iloc[:, 1:]

            dataLq = float(np.floor(allw.min().quantile(0.22)))
            datamin = float(np.min([dataLq, np.round(allw.min().min(), 1)]))
            if cliproj:
                rcps = ['rcp26', 'rcp45', 'rcp85']
                rcp = st.selectbox(
                    'RCP (Mean over all projections will be shown. For more details go to section "Climate Projections"):',
                    rcps)

                data = climate.filter_by_attrs(RCP=rcp).sel(vars=vari).resample(time='1Y').apply(afu).to_dataframe()
                data = data[data.columns[data.columns != 'vars']]
                data_ub = applySDM(wdata, data, meth='abs')

                dataUq = float(np.ceil(data_ub.max().quantile(0.76)))
                datamax = float(np.max([dataUq, np.round(data_ub.max().max(), 1)]))
            else:
                dataUq = float(np.ceil(allw.max().quantile(0.76)))
                datamax = float(np.max([dataUq,np.round(allw.max().max(), 1)]))

            datarng = st.slider('Adjust data range on x-axis of plot:', min_value=datamin, max_value=datamax, value=(dataLq, dataUq), step=0.1, key='drangew')

            if cliproj:
                ax = kde(wdata, data_ub.mean(axis=1), split_ts=3)
            else:
                ax = kde(wdata, split_ts=3)

            ax.set_title(stat1 + ' Annual ' + navi_var)
            ax.set_xlabel('T (°C)')
            ax.set_xlim(datarng[0],datarng[1])
            st.pyplot()

            sndstat = st.checkbox('Show second station for comparison')

            if sndstat:
                stat2 = st.selectbox('Select second station:', [x for x in statios if x != stat1])
                wdata2 = weather[stat2].sel(vars=vari).resample(time='1Y').apply(afu).to_dataframe()[stat2]

                ax2 = kde(wdata2, split_ts=3)
                ax2.set_title(stat2 + ' Annual ' + navi_var)
                ax2.set_xlabel('T (°C)')
                ax2.set_xlim(datarng[0],datarng[1])
                st.pyplot()

            expl_md = read_markdown_file('explainer/stripes.md')
            st.markdown(expl_md, unsafe_allow_html=True)

        elif w_aspect == 'Monthly':
            wdata = weather[stat1].sel(vars=vari).resample(time='1M').apply(afu).to_dataframe()[stat1]
            wdata = wdata[~np.isnan(wdata)]
            ref_yr = st.slider('Reference period for anomaly calculation:', min_value=int(wdata.index.year.min()), max_value=2020,value=(max(1980, int(wdata.index.year.min())), 2000))

            if cliproj:
                rcps = ['rcp26', 'rcp45', 'rcp85']
                rcp = st.selectbox('RCP (Mean over all projections will be shown. For more details go to section "Climate Projections"):', rcps)

                data = climate.filter_by_attrs(RCP=rcp).sel(vars=vari).resample(time='1M').apply(afu).to_dataframe()
                data = data[data.columns[data.columns != 'vars']]

                #ub = st.sidebar.checkbox('Apply SDM bias correction',True)
                ub = True # simplify here and automatically apply bias correction

                if ub:
                    data_ub = applySDM(wdata, data, meth='abs')
                    yrplot_hm(pd.concat([wdata.loc[wdata.index[0]:data.index[0] - pd.Timedelta('1M')], data_ub.mean(axis=1)]),ref_yr, ag, li=2006)
                else:
                    yrplot_hm(pd.concat([wdata.loc[wdata.index[0]:data.index[0] - pd.Timedelta('1M')], data.mean(axis=1)]), ref_yr, ag, li=2006)

                plt.title(stat1 + ' ' + navi_var + ' anomaly to ' + str(ref_yr[0]) + '-' + str(ref_yr[1]))
                st.pyplot()



            else:
                yrplot_hm(wdata,ref_yr,ag)
                plt.title(stat1 + ' ' + navi_var + ' anomaly to ' + str(ref_yr[0]) + '-' + str(ref_yr[1]))
                st.pyplot()

                sndstat = st.checkbox('Compare to a second station?')

                if sndstat:
                    stat2 = st.selectbox('Select second station:', [x for x in statios if x != stat1])
                    data2 = weather[stat2].sel(vars=vari).resample(time='1M').apply(afu).to_dataframe()[stat2]
                    data2 = data2[~np.isnan(data2)]

                    ref_yr2 = list(ref_yr)
                    if ref_yr2[1]<data2.index.year.min():
                        ref_yr2[0] = data2.index.year.min()
                        ref_yr2[1] = ref_yr2[0]+10
                    if ref_yr2[0]<data2.index.year.min():
                        ref_yr2[0] = data2.index.year.min()
                        if ref_yr2[1] - ref_yr2[0] < 10:
                            ref_yr2[1] = ref_yr2[0] + 10

                    yrplot_hm(data2, ref_yr2, ag)
                    plt.title(stat2 + ' ' + navi_var + ' anomaly to ' + str(ref_yr2[0]) + '-' + str(ref_yr2[1]))
                    st.pyplot()

            expl_md = read_markdown_file('explainer/stripes_m.md')
            st.markdown(expl_md, unsafe_allow_html=True)

    elif w_topic == 'Weather Indices':
        climate_indices(stat1,cliproj)

    if cliproj:
        st.markdown(
            '''RCPs are scenarios about possible greenhouse gas concentrations by the year 2100. RCP2.6 is a world in which little further greenhouse gasses are emitted -- similar to the Paris climate agreement from 2015. RCP8.5 was intendent to explore a rather risky, more worst-case future with further increased emissions. RCP4.5 is one candidate of a more moderate greenhouse gas projection, which might be more likely to resemble a realistic situation. It is important to note that the very limited differentiation between RCP scenarios have been under debate for several years. One outcome is the definition of Shared Socioeconomic Pathways (SSPs) for which today, however, there are not very many model runs awailable. For more information, please check with the [Climatescenario Primer](https://climatescenarios.org/primer/), [CarbonBrief](https://www.carbonbrief.org/explainer-how-shared-socioeconomic-pathways-explore-future-climate-change) and this [NatureComment](https://www.nature.com/articles/d41586-020-00177-3)''',
            unsafe_allow_html=True)


def climate_explorer():
    cliprojs = ["Global", "Regional"]
    cliproj = st.sidebar.radio("Climate Model Scaling:", options=cliprojs)

    expl_md = read_markdown_file('explainer/climatescale.md')
    st.sidebar.markdown(expl_md, unsafe_allow_html=True)

    if cliproj=='Regional':
        regaggs = ['North Sea Coast', 'Krummhörn',  'Niedersachsen', 'Inland']
        regagg = st.sidebar.selectbox('Spatial aggregation:', regaggs)

        if regagg=='North Sea Coast':
            climate = xr.load_dataset('data/cordex_coast.nc')
            climate.filter_by_attrs(RCP='rcp45')
        elif regagg=='Krummhörn':
            climate = xr.load_dataset('data/cordex_krummh.nc')

    st.subheader('Climate Model Comparison')
    crefs = ['Weather Data', 'all RCPs', 'RCP2.6', 'RCP4.5','RCP8.5']
    cref1 = st.sidebar.selectbox('Select first reference:', options=crefs)

    if cref1=='Weather Data':
        data1 = load_data('Weather')
        data1 = data1.coast
        drngx1 = (1980,2000)
    elif cref1 == 'all RCPs':
        data1 = load_data('CORDEX')
        drngx1 = (2050, 2070)
    elif cref1 == 'RCP2.6':
        data1 = load_data('rcp26','North Sea Coast')
        drngx1 = (2050, 2070)
    elif cref1 == 'RCP4.5':
        data1 = load_data('rcp45', 'North Sea Coast')
        drngx1 = (2050, 2070)
    elif cref1 == 'RCP8.5':
        data1 = load_data('rcp85','North Sea Coast')
        drngx1 = (2050, 2070)

    drng1 = [pd.to_datetime(data1.isel(time=0, vars=1).time.values).year, pd.to_datetime(data1.isel(time=-1, vars=1).time.values).year]
    datarng1 = st.sidebar.slider('Data range', drng1[0], drng1[1], drngx1, key='dr1')

    cref2 = st.sidebar.selectbox('Select second reference:', options=crefs)
    if cref2 == 'Weather Data':
        data2 = load_data('Weather')
        drngx2 = (1980, 2000)
    elif cref2 == 'all RCPs':
        data2 = load_data('CORDEX')
        drngx2 = (2050, 2070)
    elif cref2 == 'RCP2.6':
        data2 = load_data('rcp26','North Sea Coast')
        drngx2 = (2050, 2070)
    elif cref2 == 'RCP4.5':
        data2 = load_data('rcp45', 'North Sea Coast')
        drngx2 = (2050, 2070)
    elif cref2 == 'RCP8.5':
        data2 = load_data('rcp85','North Sea Coast')
        drngx2 = (2050, 2070)

    drng2 = [pd.to_datetime(data2.isel(time=0, vars=1).time.values).year, pd.to_datetime(data2.isel(time=-1, vars=1).time.values).year]
    datarng2 = st.sidebar.slider('Data range', drng2[0], drng2[1], drngx2, key='dr2')

    if w_topic == 'Warming':
        navi_vars = ['Maximum Air Temperature', 'Mean Air Temperature', 'Minimum Air Temperature']
        navi_var = st.sidebar.radio("Select variable:", options=navi_vars)
        if navi_var[:4] == 'Mini':
            vari = 'Tmin'
            afu = np.min
            ag = 'min'
        elif navi_var[:4] == 'Maxi':
            vari = 'Tmax'
            afu = np.max
            ag = 'max'
        else:
            vari = 'T'
            afu = np.mean
            ag = 'mean'

        dyp = data1.sel(vars=vari).to_dataframe().resample('1M').apply(afu)
        dyp = dyp.loc[(dyp.index.year>=datarng1[0]) & (dyp.index.year<datarng1[1]),dyp.columns[dyp.columns!='vars']]
        dyp2 = data2.sel(vars=vari).to_dataframe().resample('1M').apply(afu)
        dyp2 = dyp2.loc[(dyp2.index.year >= datarng2[0]) & (dyp2.index.year < datarng2[1]),dyp2.columns[dyp2.columns!='vars']]

        monthlyx(dyp, dyp2, 'Temperature (°C)', 'Monthly '+ag+' in Year ('+cref1+')', 'Monthly '+ag+' in Year ('+cref2+')')
        st.pyplot()


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


def management_explorer():
    rcps = ['rcp45', 'rcp85']  # 'rcp26',
    rcp = st.sidebar.selectbox('RCP:', rcps)

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

# main app
## get sub-files
ruinslogo = Image.open('RUINS_logo_small.png')
intro_md = read_markdown_file('explainer/Intro.md')

## sidebar header
st.sidebar.image(ruinslogo, caption='', use_column_width=True)
st.sidebar.header('Control Panel')

## sidebar section navigation
navi_secs = ["Introduction","Weather Data", "Climate Projections", "Uncertainty", "Management"]
navi_sec = st.sidebar.radio("Select Chapter:", options=navi_secs)

topics = ['Warming', 'Weather Indices', 'Drought/Flood', 'Agriculture', 'Extreme Events', 'Wind Energy']
w_topic = st.sidebar.selectbox('Select Topic:', topics)

if navi_sec=="Introduction":
    st.markdown(intro_md, unsafe_allow_html=True)
elif navi_sec=="Weather Data":
    st.header('Weather Data Explorer')
    st.markdown('''In this section we provide visualisations to explore changes in observed weather data. Based on different variables and climate indices it is possible to investigate how climate change manifests itself in different variables, at different stations and with different temporal aggregation.''',unsafe_allow_html=True)
    weather_explorer()
elif navi_sec=="Climate Projections":
    st.header('Climate Projections Explorer')
    st.markdown('''In this section we add climate model projections to the table. The same variables and climate indices are used to explore the projections of different climate models and downscaling models. It is also possible to compare projections under different scenarios about the CO<sub>2</sub>-concentration pathways to observed weather and between different model projections.''',unsafe_allow_html=True)
    climate_explorer()
elif navi_sec=="Uncertainty":
    st.header('Uncertainty Explorer')
elif navi_sec=="Management":
    st.header('Management Explorer')
    st.markdown('''In this section we project the climate model outputs to ecosystem services through diffferent model approaches. The impact of potential management is tackeled at a rather broad level in terms of exemplary options.''', unsafe_allow_html=True)
    management_explorer()
