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
    def vcn_tree(self):
        return self._vcn_tree

    def vcn_tree_append(self, vcn_id, res: OciResource=None):
        """
        VCN dependency tree used for clean-up operation

        :param vcn_id: vcn id to identify the vcn tree
        :param res: resource the vcn depend on
        """

        self._vcn_tree.setdefault(vcn_id, {}).setdefault(res.resource_type, []).append(res)

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
        return self._config_region_filter if hasattr(self, '_config_region_filter') and self._config_region_filter else None

    @property
    def compartment_filter(self):
        return self._config_compartment_filter if hasattr(self,'_config_compartment_filter') and self._config_compartment_filter else None

    @property
    def vcn_filter(self):
        return self._config_vcn_filter if hasattr(self, '_config_vcn_filter') and self._config_vcn_filter else None
