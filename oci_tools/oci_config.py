import oci
from .oci_resources import OciResource


class OCIConfig:

    def __init__(self, config_path=None, **kwargs):
        """
        Init OCIConfig dynamically creating attributes based on the configuration file or command line parameters
        :param config_path: configuration file path
        :param kwargs: command line parameters
        """

        self._compartments_tree = None
        self._workon_region = None
        self._vcn_tree = {}

        self._config = oci.config.from_file(config_path)

        for key, value in self._config.items():
            key = '_config_{}'.format(key)
            if value:
                setattr(self, key, value.split(',') if isinstance(value, str) and ',' in value else value)

        # set the value from command line
        # note that it overwrites config file value
        for key, value in kwargs.items():
            key = '_config_{}'.format(key)
            if value:
                setattr(self, key, value.split(',') if isinstance(value, str) and ',' in value else value)

    @property
    def tenancy(self):
        return self._config_tenancy

    @property    
    def compartments_scope(self):
        """
        compartment list to work with
        """
        return self._config_compartment if hasattr(self, '_config_compartment') and self._config_compartment else self._config_tenancy
    
    @property
    def compartments_tree(self):
        return self._compartments_tree
    
    @compartments_tree.setter
    def compartments_tree(self,c_tree):
        self._compartments_tree = c_tree

    @property
    def config(self):
        return self._config

    @property
    def workon_region(self):
        if 'region' not in self._config:
            self._config['region'] = None
        return self._config['region']

    @workon_region.setter
    def workon_region(self, region):
        """
        region currently in use
        """
        self._config['region'] = region

    @property
    def region_filter(self):
        if hasattr(self, '_config_region_filter'):
            return self._config_region_filter if isinstance(self._config_region_filter,list) else [self._config_region_filter]
        return None

    @property
    def compartment_filter(self):
        if hasattr(self, '_config_compartment_filter'):
            return self._config_compartment_filter if isinstance(self._config_compartment_filter,list) else [self._config_compartment_filter]
        return None

    @property
    def vcn_filter(self):
        if hasattr(self, '_config_vcn_filter'):
            return self._config_vcn_filter if isinstance(self._config_vcn_filter,list) else [self._config_vcn_filter]
        return None

    @property
    def simulate_deletion(self):
        try:
            if hasattr(self, '_config_simulate_deletion'):
                if self._config_simulate_deletion and self._config_simulate_deletion.lower() == 'true':
                    return True
        except:
            pass
        return False

    @property
    def operation(self):
        """
        set list as default operation

        :return: operation
        """
        return self._config_operation if hasattr(self, '_config_operation') and self._config_operation else 'list'
