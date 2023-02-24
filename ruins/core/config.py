from typing import Callable, Dict, Union
import os
from os.path import join as pjoin
import json
from collections.abc import Mapping

from ruins.core.i18n import get_translator

from streamlit import session_state
import streamlit as st

# check if streamlit is running
#if not st._is_running_with_streamlit:
#    session_state = dict()

class Config(Mapping):
    """
    Streamlit app Config object.

    This class holds all configs needed to run the apps. 
    It can be instantiated just like this to load default
    values. 
    If a path is provided, it will load the configs from
    the referenced json file. Any config can be updated
    by passed kwargs.

    This design makes the config updateable and easy to
    to manage. At the same time it can be persisted to
    the disk and even mirrored to a database if needed in
    the future.

    """
    def __init__(self, path: str = None, **kwargs) -> None:
        # set the default values

        # debug mode
        self._debug = False
        self.lang = 'en'

        # path 
        self.basepath = os.path.abspath(pjoin(os.path.dirname(__file__), '..', '..'))
        self.datapath = pjoin(self.basepath, 'data')
        self.hot_load = kwargs.get('hot_load', False)

        # datafile names, without file extension
        self.datafile_names = {
            'stations': 'stats',
            'cordex_grid': 'CORDEXgrid',
            'cimp_grid': 'CIMP5grid',
            'weather': 'weather',
            'climate': 'cordex_krummh',
            'pdsi': 'scPDSI',
            'wind_timeseries': 'windenergy_timeseries',
            'CE': 'CEs_PCSE'
            #'climate_coast': 'cordex_coast',
            #'hydro': 'hydro_krummh'
        }

        # mime readers
        self.default_sources = {
            'nc': 'HDF5Source',
            'csv': 'CSVSource',
            'dat': 'DATSource'
        }
        self.default_sources.update(kwargs.get('include_mimes', {}))

        # reader args
        self.sources_args = {
            'stats.csv': dict(index_col=0),
            'hsim_collect.csv': dict(index_col=0),
            'windpowerx.csv': dict(index_col=0),
            'estQ.csv': dict(index_col=[0], parse_dates=[0]),
            'levelknock.csv': dict(index_col=[0], parse_dates=[0]),
            'levelW.csv': dict(index_col=[0], parse_dates=[0]),
            'prec.csv': dict(index_col=[0], parse_dates=[0]),
            'Qknock.csv': dict(index_col=[0], parse_dates=[0]),
            'scPDSI.csv': dict(index_col=[0]),
            'CEs_PCSE.csv': dict(sep=';', index_col=[0], decimal=',')
        }
        self.sources_args.update(kwargs.get('include_args', {}))

        # app management
        self.layout = 'centered'

        # store the keys
        self._keys = ['debug', 'lang', 'basepath', 'datapath', 'hot_load', 'datafile_names', 'default_sources', 'sources_args', 'layout']

        # check if a path was provided
        conf_args = self.from_json(path) if path else {}

        # update with kwargs
        conf_args.update(kwargs)
        self._update(conf_args)

    @property
    def debug(self):
        return self._debug

    @property
    def story_mode(self):
        return self._story_mode
    
    @debug.setter
    def debug(self, value: Union[str, bool]):
        if isinstance(value, str):
            self._debug = value.lower() != 'false'
        else:
            self._debug = bool(value)

    @story_mode.setter
    def story_mode(self, value: Union[str, bool]):
        if isinstance(value, str):
            self._story_mode = value.lower() != 'false'
        else:
            self._story_mode = bool(value)

    def from_json(self, path: str) -> dict:
        """loads the content of the JSON config file"""
        if os.path.exists(path):
            with open(path, 'r') as f:
                return json.load(f)
        else:
            raise AttributeError(f"Config file {path} does not exist")
    
    def _update(self, new_settings: dict) -> None:
        """Update this instance with new settings"""
        for k, v in new_settings.items():
            setattr(self, k, v)
            if k not in self._keys:
                self._keys.append(k)
    
    def get_control_policy(self, control_name: str) -> str:
        """
        Get the control policy for the given control name.

        allowed policies are:
            - show: always show the control on the main container
            - hide: hide the control on the main container, but move to the expander
            - ignore: don't show anything

        """
        if self.has_key(f'{control_name}_policy'):
            return self.get(f'{control_name}_policy')
        elif self.has_key('controls_policy'):
            return self.get('controls_policy')
        else:
            # TODO: discuss with conrad to change this
            return 'show'

    def translator(self, **translations: Dict[str, str]) -> Callable[[str], str]:
        """Return a translator function"""
        return get_translator(self.lang, **translations)
    
    def get(self, key: str, default = None):
        if hasattr(self, key):
            return getattr(self, key)
        elif hasattr(session_state, key):
            return getattr(session_state, key)
        elif key in session_state:
            return session_state[key]
        else:
            return default
    
    def has_key(self, key) -> bool:
        if hasattr(self, key) and not key in session_state:
            session_state[key] = getattr(self, key)
        return hasattr(self, key) or hasattr(session_state, key) or key in session_state
    
    def __len__(self) -> int:
        return len(self._keys)

    def __iter__(self):
        for k in self._keys:
            yield k
    
    def __getitem__(self, key: str):
        if hasattr(self, key):
            return getattr(self, key)
        elif key in session_state:
            return session_state[key]
        else:
            raise KeyError(f"Key {key} not found")
    
    def __setitem__(self, key: str, value):
        setattr(self, key, value)
        if key not in self._keys:
            self._keys.append(key)
