import oci


class OCIConfig:

    def __init__(self, config_path=None, **kwargs):
        self._compartments_tree = None
        self._workon_region = None

        self._config = oci.config.from_file(config_path)
                
        if self._config['regions']: 
            self.regions=self._config['regions']
        
        for key,value in self._config.items():
            if value:
                setattr(self, key, value.split(',') if isinstance(value, str) and ',' in value else value)

        # set the value from command line
        # note that it overwrite config file value
        for key,value in kwargs.items():
            if value :
                setattr(self, key, value.split(',') if isinstance(value, str) and ',' in value else value)

    @property
    def tenancy(self):
        return self.tenancy

    @property    
    def compartments_scope(self):
        """
        compartment list to work with
        """
        return self.compartment if hasattr(self, 'compartment') and self.compartment else self.tenancy
    
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
            self._config['region']=None
        return self._config['region']

    @workon_region.setter
    def workon_region(self,region):
        """
        region currently in use
        """
        self._config['region']=region
