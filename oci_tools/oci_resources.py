import logging
import oci


class OciResource(dict):
    """
    archetype for OCI resources
    it contains the current resources and all the nested ones
    """
    resource_type = 'oci-resource'

    def __init__(self, res, api_client=None, name='resource', id=None, res_type='resource'):
        """
        Init OCI Resource
        :param res: OCI API resource
        :param api_client:  OCI API Client object
        :param name: resource name/display_name
        :param id: resource OCID
        :param res_type: resource type
        """
        super().__init__({'name':name, 'id':id, 'nested':[]})
        self._name = name
        self._id=id
        self._resource=res
        self._nested_resources=[]
        self.resource_type = res_type
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

    resource_type = 'instance'

    def __init__(self,res, api_client=None):
        super().__init__(res,
                         api_client=api_client,
                         name=res.display_name,
                         id=res.id)

    def _terminate(self, force=False):

        # attached vnics are automatically detached and terminated
        try:
            self._api_client.terminate_instance(self.id, preserve_boot_volume = not force)
            oci.wait_until(self._api_client,
                           self._api_client.get_instance(self.id),
                           'lifecycle_state',
                           'TERMINATED')
        except:
            logging.error('unable to terminate the instance {}'.format(self.id))


class OciVnic(OciResource):

    resource_type = 'vnic'

    def __init__(self,res, api_client=None):
        super().__init__(res,
                         api_client=api_client,
                         name=res.display_name,
                         id=res.id)

    def _terminate(self, force=False):
        pass


class OciVcn(OciResource):

    resource_type = 'vcn'

    def __init__(self,res, api_client=None):
        super().__init__(res,
                         api_client=api_client,
                         name=res.display_name,
                         id=res.id)

    def _terminate(self, force=False):
        if force:
            self._nested_resources[OciSecurityList.resource_type]
        pass


class OciSubnet(OciResource):

    resource_type = 'subnet'

    def __init__(self, res, api_client=None):
        super().__init__(res,
                         api_client=api_client,
                         name=res.display_name,
                         id=res.id)

    def _terminate(self, force=False):
        pass


class OciInternetGw(OciResource):

    resource_type = 'igw'

    def __init__(self, res, api_client=None):
        super().__init__(res,
                         api_client=api_client,
                         name=res.display_name,
                         id=res.id)

    def _terminate(self, force=False):
        try:
            self._api_client.delete_internet_gateway(self.id)
        except:
            logging.error('unable to delete ig {}'.format(self.id))


class OciNatGw(OciResource):

    resource_type = 'natgw'

    def __init__(self, res, api_client=None):
        super().__init__(res,
                         api_client=api_client,
                         name=res.display_name,
                         id=res.id)


class OciDRG(OciResource):

    resource_type = 'drg'

    def __init__(self, res, api_client=None):
        super().__init__(res,
                         api_client=api_client,
                         name=res.display_name,
                         id=res.id)

    def _terminate(self, force=False):
        pass


class OciServiceGw(OciResource):

    resource_type = 'servicegw'

    def __init__(self, res, api_client=None):
        super().__init__(res,
                         api_client=api_client,
                         name=res.display_name,
                         id=res.id)

    def _terminate(self, force=False):
        pass


class OciLocalPeeringGw(OciResource):

    resource_type = 'lpg'

    def __init__(self, res, api_client=None):
        super().__init__(res,
                         api_client=api_client,
                         name=res.display_name,
                         id=res.id)

    def _terminate(self, force=False):
        pass


class OciSecurityList(OciResource):

    resource_type = 'securitylist'

    def __init__(self, res, api_client=None):
        super().__init__(res,
                         api_client=api_client,
                         name=res.display_name,
                         id=res.id)

    def _terminate(self, force=False):
        try:
            self._api_client.delete_security_list(self.id)
            oci.wait_until(self._api_client,
                           self._api_client.get_security_list(self.id),
                           'lifecycle_state',
                           'TERMINATED')
        except:
            logging.error('unable to terminate {} {}'.format(self.resource_type, self.id))


class OciRouteTable(OciResource):

    resource_type = 'routetable'

    def __init__(self, res, api_client=None):
        super().__init__(res,
                         api_client=api_client,
                         name=res.display_name,
                         id=res.id)

    def _terminate(self, force=False):
        try:
            self._api_client.delete_route_table(self.id)
            oci.wait_until(self._api_client,
                           self._api_client.get_route_table(self.id),
                           'lifecycle_state',
                           'TERMINATED')
        except:
            logging.error('unable to terminate {} {}'.format(self.resource_type, self.id))


class OciBlockVolume(OciResource):

    resource_type = 'bv'

    def __init__(self, res, api_client=None):
        super().__init__(res,
                         api_client=api_client,
                         name=res.display_name,
                         id=res.id)

    def _terminate(self, force=False):
        pass

    

