from ruins.apps import weather
from ruins.tests.util import get_test_config

from ruins.core import DataManager, Config

# create the test config
config = get_test_config()


def test_climate_indices():
    """Test only climate indices """
    # add the include_climate config
    config['include_climate'] = True
    dm = DataManager(**config)

    # run
    weather.climate_indices(dataManager=dm, config=config)
