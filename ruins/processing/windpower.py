from typing import Union, Tuple, List
import warnings
from itertools import product
from collections import defaultdict

import numpy as np
import pandas as pd
from scipy.stats import gaussian_kde

from ruins.core import DataManager


TURBINES = dict(
    e53=(0.8, 53),
    e115=(3, 115),
    e126=(7.5, 126)
)


def turbine_footprint(turbine: Union[str, Tuple[float, int]], unit: str = 'ha'):
    """
    Calculate the footprint for the given turbine dimension. The turbine can
    be either specified by rated power and rotor diameter, or by one the the type
    names: E53, E115, E126.

    Parameters
    ----------
    turbine : str or tuple
        Either the turbine name or a tuple of (rated power, rotor diameter)
    unit : str, optional
        The unit of the returned footprint. Either 'ha' or 'km2'.
        Defaults to 'ha'.
    
    Returns
    -------
    area : float
        The area of the turbine in the given unit.
    mw : float
        The rated power of the turbine in MW.

    """
    if isinstance(turbine, str):
        turbine = TURBINES[turbine.lower()]
    mw, r = turbine
    
    # get the area - 5*x * 3*y 
    area = ((5 * r) * (3 * r))   # m2

    if unit == 'ha':
        area /= 10000
    elif unit == 'km2':
        area / 1000000

    # return area, mw
    return area, mw


def upscale_windenergy(turbines: List[Union[str, Tuple[float, int]]], specs: List[Tuple[float]], site: float = 396.0) -> np.ndarray:
    """
    Upscale the given turbines to the site.
    Pass a list of turbine definitions (either names or MW, rotor_diameter tuples.).
    The function will apply the specs to the site. The specs can either be absolute number of
    turbines per turbine or relative shares per turbine type.
    Returns a tuple for each turbine type.

    Parameters
    ----------
    turbines : list
        List of turbine definitions. Either names or MW, rotor_diameter tuples.
    specs : list
        List of the upscaling specifications. For this, the share of each turbine
        in the turbines list, a area share has to be specified. Ideally, these
        should at most sum up to 1. 
    site : float, optional
        Site area in ha. The upscaling will apply the specified area share
        to each turbine type and return the maximum number of possible turbines.

    Returns
    -------
    results : List[Tuple[float, int, float]]
        A list of tuples per turbine type. (n_turbines, total_area, total_mw)
    """
    # check input data
    #if not all([len(spec)==len(turbines) for spec in specs]):
    #    raise ValueError('The number of turbines and the number of specs must be equal.')
    
    # result container
    results = np.ones((len(specs) * len(turbines), len(turbines))) * np.NaN

    # get the area and MW for each used turbine type
    turbine_dims = [turbine_footprint(turbine) for turbine in turbines]

    for i in range(len(specs)):
        for j in range(len(turbine_dims)):
            # get the footprint
            #area, mw = turbine_footprint(turbine, unit='ha')
            area, mw = turbine_dims[j]

            # get the available space and place as many turbines as possible
            n_turbines = int((site * specs[i][j]) / area)
            
            # get the used space and total MW
            used_area = n_turbines * area
            used_mw = n_turbines * mw

            results[i * len(turbines) + j,:] = [n_turbines, used_area, used_mw]

    return results


def load_windpower_data(dataManager: DataManager, joint_only: bool = False) -> pd.DataFrame:
    """
    Load the raw windpower simulations and apply a MultiIndex. The rows are indexed
    by all years contained in the climate simulations. The coluns group the single
    simulations by Turbine type, global circulation model (GCM), regional climate 
    model (RCM), and the CO2 scenario (RCP).
    
    Parameters
    ----------
    joint_only : bool
        If True, only data for 16 joint simulations are returned (combinations of global circulation 
        model (GCM), regional climate model (RCM) and ensemble available for all three RCPs).
    
    Returns
    df : pd.DataFrame
        Result dataframe with all contained years as row index and a simulation type
        as column index.
    """
    
    # read windpower timeseries data
    raw = dataManager.read('wind_timeseries').copy()

    # build the MultiIndex
    multi_index = pd.MultiIndex.from_tuples(
        list(zip(raw['LMO'], raw['RCP'], raw['GCM'], raw['RCM'], raw['Ensemble'], raw['joint'])), 
        names=['LMO', 'RCP', 'GCM', 'RCM', 'Ensemble', 'joint']
    )

    # tstamp index from year columns
    tstamp = pd.date_range(start='2006-12-31', periods=94, freq='Y')
    
    # transpose data
    df = raw.transpose()

    # apply multiindex
    df.columns = multi_index

    # drop multiindex rows
    df.drop(df.index[0:6], axis=0, inplace=True)

    # replace index
    df.index = tstamp
    df.index.name = 'time'

    # drop na values
    df.dropna(axis=1, how='all', inplace=True)

    if joint_only:
        # only return columns where joint==True
        return df.drop(False, level=5, axis=1)
    else:
        return df


def windpower_actions_projection(dataManager: DataManager, scenarios, site: float = 396.0, filter_={}) -> Tuple[List[pd.DataFrame], List[Tuple[int, float]]]:
    """
    Windpower management options (actions) upscaling.
    This function can be used to specifiy several scenarios, how the three windturbines
    E53, E115, E126 are balanced out. For each of these scenarios, the function will return
    a pandas dataframe with the provisioned windpower for each of the three turbines and 
    each year.
    The used climate scenarios can be filtered by GCM, RCM, RCP or to only use combinations
    of GCM RCM and ensemble, that are available for all RCPS (N=16).
    The windpower data for each model combination that fits the filter will be concatenated,
    thus there can be duplicate rows.

    Parameters
    ----------
    dataManager : DataManager
        DataManager instance to obtain the model data.
    scenarios : list
        List of scenario specifications.
    site : float, optional
        Site area in ha.
    filter_ : dict, optional
        Filter to apply to the scenarios. The filter can contain the keys:
        'gcm', 'rcm', 'rcp', 'joint'.
    
    Returns
    -------
    actions : List[pd.DataFrame]
        List of dataframes for each scenario.
    dim : List[tuple]
        The applied dimenisoning (number of turbines) for each scenario

    """
    # ignore MultiIndex sorting warnings as the df is small anyway
    warnings.simplefilter('ignore', category=pd.errors.PerformanceWarning) 
    
    # I guess we have to stick to those here
    turbines=['e53', 'e115', 'e126']

    # handle the specs
    if len(scenarios) == 1 and any([isinstance(s, range) for s in scenarios]):
        # there is a range definition
        scenarios = []
        for e1 in scenarios[0]:
            for e2 in scenarios[1]:
                for e3 in scenarios[2]:
                    scenarios.append((e1 / 100, e2 / 100, e3 / 100))
    else:
        scenarios = scenarios

    # upscale the turbines to the site
    power_share = upscale_windenergy(turbines, scenarios)

    # get the data
    df = load_windpower_data(dataManager, joint_only=filter_.get('joint', False))

    # set the filter keys
    gcm_level = 2
    rcm_level = 3
    # apply filters
    for key, val in filter_.items():
        if key == 'year':
            df = df[val]
        elif key == 'rcp':
            df = df.xs(val, level=1, axis=1)

            # Multiindex has one level less
            gcm_level -= 1
            rcm_level -= 1

        elif key == 'gcm':
            df = df.xs(val, level=gcm_level, axis=1)

            # Multiindex has one level less
            rcm_level -= 1
        
        elif key == 'rcm':
            df = df.xs(val, level=rcm_level, axis=1)

    # aggregate everything
    actions = []
    dims = []
    for i in range(0, len(power_share), len(turbines)):
        data = None
        dim = []
        for j, turbine in enumerate(turbines):
            # get the chunk for this turbine (can have more than one col)
            c = df[turbine.upper(), ]

            # check the type
            if isinstance(c, pd.Series):
                chunk = c
            else:
                # c is a Dataframe -> there was more than one GCM RCM RCP combination
                chunk = c.melt().value

            # multiply with the number of turbines
            chunk *= power_share[i + j][0]

            # append the number of turbines
            dim.append(power_share[i + j][0])
            
            # merge
            if data is None:
                data = {turbine: chunk.values}
            elif turbine in data:
                data[turbine] = np.concatenate([data[turbine], chunk.values])    
            else:
                data[turbine] = chunk.values
        
        # append the data
        actions.append(pd.DataFrame(data))
        dims.append(dim)

    return actions, dims


def crra(payoff: np.array, gamma: float = 1.0, p: List[float] = None) -> Tuple[float]:
    """
    Von Neumann-Morgenstern constant relative risk aversion (CRRA).
    Returns the expected utility, certainty equivalent, expected value and the 
    risk premium assocaiated to a management decision, based on an array of 
    payoffs.
    
    Parameters
    ----------
    payoff : numpy.array
        The payoff array includes all possible outcomes of the decision.
    gamma : float
        Risk aversion factor. If higher, the decision maker is willing to take more risk.
    p : List[float]
        List if probabilities associated to the payoffs. If None (default), all
        payoffs are euqally probable.
    
    Returns
    -------
    eu : float
        Expected utility (E[U(x)]) is the probability weighted sum of utilities associated with each possible payoff.
    ce : float
        certainty equivalent (CER) is the sure amount of payoff that is as desirable to the 
        decision-maker (same utility) as the risky outcome.
    ev : float
        Expected value (EV)
    rp : float
        Risk premium (RP) sure amount of payoff that one is willing to forego at
        maximum to reach a situation of certainty

    Notes
    -----
    Translation of the R function `CRRA.leila` from taken from R-code Laila (Appendix 8, Master Thesis, 2020)
    """
    idx = payoff != 0.0
    payoff = payoff[idx]
    if p is not None:
        p = p[idx]
    
    if abs(gamma - 1.0) < 1e-15:
        # expected utility (E[U(x)]) is the probability weighted sum of utilities associated with each possible payoff
        eu = np.average(np.log(payoff), weights=p)

        # = input for uncertainty valuation
        ce = np.exp(eu)
        
    else:
        # expected utility, see eq. 3.2/3.3 (p. 44)
        eu = np.average((np.power(payoff, 1 - gamma) - 1) / (1 - gamma), weights=p)  

        # certainty equivalent, see eq. 3.4 (p. 44)
        ce = np.power(eu * (1 - gamma) + 1, 1 / (1 - gamma))
    
    # expected value
    ev = np.average(payoff, weights=p)
    
    # risk premium
    rp = ev - ce

    return (eu, ce, ev, rp)


def atk(ce: Union[np.array, float], alpha: float = 0.75) -> Tuple[float]:
    """
    Atkinson's inequality aversion (ATK).

    Parameters
    ----------
    ce : numpy.array
        possible payoff vector, usually the certainty equivalent (CER) of the payoff vector
    alpha : float
        Uncertainty aversion coefficient. If higher, the decision maker is more risk averse.

    Returns
    -------
    u : float
        Utility (U(x)) is the utility associated with the payoff vector.
    up : float
        Uncertainty premium (UP) is the average payoff that the decision-maker would demand
        in order to willingly take on uncertainty

    Notes
    -----
    Translation of the R function `Atk` from taken from R-code Laila (Appendix 8, Master Thesis, 2020)
    """
    # get the number of scenarios
    if isinstance(ce, float):
        n = 1
    else:
        n = len(ce)

    # get utility
    if abs(alpha - 1.0) < 1e-15:
        u = np.power(np.prod(ce), 1 / n)
    else:
        u = np.power((1 / n) * np.sum(np.power(ce, 1 - alpha)), 1 / (1 - alpha))

    # uncertainty premium
    up = ((1 / n) * np.sum(ce)) - u

    return (u, up)


def create_action_grid(dataManager: DataManager, resolution: float = 0.1, filter_: dict = {}) -> Tuple[list, list]:
    """
    Create a grid of management actions by balacing all three turbine types.
    The function balances the area occupied by each turbine type in steps of
    resolution. The grid is created for all possible combinations, wich sum
    up to 100% of the area.

    Parameters
    ----------
    dataManager : DataManager
        RUINS data manager instance to load the wind provisioning dataset.
    resolution : float, optional
        Resolution of the grid. The default is 0.1. Has to be bewteen 0 and 1.
    filter_ : dict, optional
        Filter to apply to the wind provisioning dataset. The default is no
        filter. Possible to load only joint datasets, fitler by GCM, RCM, RCP
        or slice to years
    
    Returns
    -------
    actions : List[pandas.DataFrame]
        Returns a dataframe for each management action. 
        Each dataframe represents the provisioned windpower for each turbine type
        and year.
    scenarios : List[Tuples[float, float, float]]
        Returns tuple for each management option. The tuple contains the
        area shares for each of the turbines associated with the action.

    """
    # hardode the turbines
    turbines = ['e53', 'e115', 'e126']
    n_turbines = len(turbines)
    
    # get all combinations
    gen = [np.arange(0.0, 1.0, resolution) for _ in range(n_turbines)]
    scenarios = [t for t in product(*gen) if abs(sum(t) - 1.0) < 1e-5][1:]

    # get the actions
    actions, _ = windpower_actions_projection(dataManager, scenarios, filter_=filter_)

    return actions, scenarios


def uncertainty_analysis(actions: List[pd.DataFrame], gamma: float = 1.2, alpha: float = 0.75) -> pd.DataFrame:
    """
    Run the uncertainty analysis for a list of provisioned windpower scenarios. Each 
    scenario represent the outcome of a management option.

    Parameters
    ----------
    actions : List[pandas.DataFrame]
        List of provisioned windpower scenarios. Each scenario represents the outcome
        of a management option.
    gamma : float, optional
        Risk aversion factor. If higher, the decision maker is willing to take more risk.
        The default is 1.2.
    alpha : float, optional
        Uncertainty aversion coefficient. If higher, the decision maker is more risk averse.
        The default is 0.75.
    
    Returns
    -------
    df : pandas.DataFrame
        Returns a dataframe with the uncertainty analysis results for each scenario.
    
    See Also
    --------
    ruins.processing.windpower.crra
    ruins.processing.windpower.atk

    """
    result = defaultdict(lambda: [])

    for action in actions:
        # apply the KDE to obtain probability estimates
        y = action.sum(axis=1).values

        # resolve the annual windpower production to 100 steps
        x = np.linspace(y.min(), y.max(), 100)

        # get the KDE
        kde = gaussian_kde(y)(x)

        # apply constant relative risk aversion
        eu, ce, ev, rp = crra(x, gamma=gamma, p=kde)
    
        # atkinson risk premium
        au, up = atk(ce, alpha=alpha)

        # append the results
        result['eu'].append(eu)
        result['ce'].append(ce)
        result['ev'].append(ev)
        result['rp'].append(rp)
        result['au'].append(au)
        result['up'].append(up)
    
    # return
    return pd.DataFrame(result)
