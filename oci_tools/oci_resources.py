import logging

class OciResource(dict):
    """
    archetype for OCI resources
    it contains the current resources and all the nested ones
    """
    resource_type = 'oci-resource'

    def __init__(self,res,api_client=None,name='resource',id=None,res_type='resource'):
        super().__init__({'name':name, 'id':id, 'nested':[]})
        self._name = name
        self._id=id
        self._resource=res
        self._nested_resources=[]
        self._res_type = res_type
        self._api_client = api_client

    def __setitem__(self, key, value):
        self.setdefault('nested', []).append({key:value})
        if issubclass(type(value), OciResource):
            self._nested_resources.append(value.resource)

    @property
    def resource(self):
        """
        return current resource in json format
        """
        return self._resource

    @property
    def nested_resources(self):
        """
        return nested resources in json format
        """
        return  self._nested_resources

    @property
    def id(self):
        return self._id

    def terminate(self, force=False):
        """
        delete the resources and all the nested resources
        """
        logging.info('Terminating resource {}'.format(self))
        self._terminate(force)


    def _terminate(self, force=False):
        """
        internal Terminate implementation
        Child classes should override this method
        """
        pass

####################################
# Resource definitions
####################################
class OciInstance(OciResource):

    _res_type = 'instance'

    def __init__(self,res, api_client=None):
        super().__init__(res,
                         api_client=api_client,
                         name=res.display_name,
                         id=res.id)

    def _terminate(self, force=False):

        #attached vnics are automatically detached and terminated
        self._api_client.terminate_instance(self.id, preserve_boot_volume = not force)


class OciVnic(OciResource):

    _res_type = 'vnic'

    def __init__(self,res, api_client=None):
        super().__init__(res,
                         api_client=api_client,
                         name=res.display_name,
                         id=res.id)

    def _terminate(self, force=False):
        pass



class OciVcn(OciResource):

    _res_type = 'vcn'

    def __init__(self,res, api_client=None):
        super().__init__(res,
                         api_client=api_client,
                         name=res.display_name,
                         id=res.id)

    def _terminate(self, force=False):
        if force:
            self._nested_resources[OciSecurityList._res_type]
        pass


class OciSubnet(OciResource):

    _res_type = 'subnet'

    def __init__(self, res, api_client=None):
        super().__init__(res,
                         api_client=api_client,
                         name=res.display_name,
                         id=res.id)

    def _terminate(self, force=False):
        pass




class OciInternetGw(OciResource):

    _res_type = 'igw'

    def __init__(self, res, api_client=None):
        super().__init__(res,
                         api_client=api_client,
                         name=res.display_name,
                         id=res.id)


class OciNatGw(OciResource):

    _res_type = 'natgw'

    def __init__(self, res, api_client=None):
        super().__init__(res,
                         api_client=api_client,
                         name=res.display_name,
                         id=res.id)


class OciDRG(OciResource):

    _res_type = 'drg'

    def __init__(self, res, api_client=None):
        super().__init__(res,
                         api_client=api_client,
                         name=res.display_name,
                         id=res.id)

    def _terminate(self, force=False):
        pass


class OciServiceGw(OciResource):

    _res_type = 'servicegw'

    def __init__(self, res, api_client=None):
        super().__init__(res,
                         api_client=api_client,
                         name=res.display_name,
                         id=res.id)

    def _terminate(self, force=False):
        pass


class OciLocalPeeringGw(OciResource):

    _res_type = 'lpg'

    def __init__(self, res, api_client=None):
        super().__init__(res,
                         api_client=api_client,
                         name=res.display_name,
                         id=res.id)

    def _terminate(self, force=False):
        pass


class OciSecurityList(OciResource):

    _res_type = 'securitylist'

    def __init__(self, res, api_client=None):
        super().__init__(res,
                         api_client=api_client,
                         name=res.display_name,
                         id=res.id)

    def _terminate(self, force=False):
        self._api_client.delete_security_list(self.id)


class OciRouteTable(OciResource):

    _res_type = 'routetable'

    def __init__(self, res, api_client=None):
        super().__init__(res,
                         api_client=api_client,
                         name=res.display_name,
                         id=res.id)

    def _terminate(self, force=False):
        pass


class OciBlockVolume(OciResource):

    _res_type = 'bv'

    def __init__(self, res, api_client=None):
        super().__init__(res,
                         api_client=api_client,
                         name=res.display_name,
                         id=res.id)

    def _terminate(self, force=False):
        pass

    

