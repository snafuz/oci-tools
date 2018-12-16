import logging

class OCI_Resource(dict):
    """
    archetype for OCI resources
    it contains the current resources and all the nested ones
    """
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
        if issubclass(type(value),OCI_Resource):
            self._nested_resources.append(value.resource)

    @property
    def resource_type(self):
        """
        return resource type
        """
        return self._res_type

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
class OCI_Instance(OCI_Resource):

    def __init__(self,res, api_client=None):
        super().__init__(res,
                         api_client=api_client,
                         name=res.display_name,
                         id=res.id,
                         res_type='instance')

    def _terminate(self, force=False):
        pass


class OCI_Vnic(OCI_Resource):

    def __init__(self,res, api_client=None):
        super().__init__(res,
                         api_client=api_client,
                         name=res.display_name,
                         id=res.id,
                         res_type='vnic')

    def _terminate(self, force=False):
        pass



class OCI_VCN(OCI_Resource):

    def __init__(self,res, api_client=None):
        super().__init__(res,
                         api_client=api_client,
                         name=res.display_name,
                         id=res.id,
                         res_type='vcn')

    def _terminate(self, force=False):
        pass


class OCI_Subnet(OCI_Resource):

    def __init__(self, res, api_client=None):
        super().__init__(res,
                         api_client=api_client,
                         name=res.display_name,
                         id=res.id,
                         res_type='subnet')

    def _terminate(self, force=False):
        pass




class OCI_IG(OCI_Resource):
    def __init__(self, res, api_client=None):
        super().__init__(res,
                         api_client=api_client,
                         name=res.display_name,
                         id=res.id,
                         res_type='igw')


class OCI_NatGateway(OCI_Resource):
    def __init__(self, res, api_client=None):
        super().__init__(res,
                         api_client=api_client,
                         name=res.display_name,
                         id=res.id,
                         res_type='natgw')


class OCI_DRG(OCI_Resource):
    def __init__(self, res, api_client=None):
        super().__init__(res,
                         api_client=api_client,
                         name=res.display_name,
                         id=res.id,
                         res_type='drg')

    def _terminate(self, force=False):
        pass


class OCI_ServiceGateway(OCI_Resource):
    def __init__(self, res, api_client=None):
        super().__init__(res,
                         api_client=api_client,
                         name=res.display_name,
                         id=res.id,
                         res_type='servicegw')

    def _terminate(self, force=False):
        pass


class OCI_LocalPeeringGw(OCI_Resource):
    def __init__(self, res, api_client=None):
        super().__init__(res,
                         api_client=api_client,
                         name=res.display_name,
                         id=res.id,
                         res_type='lpg')

    def _terminate(self, force=False):
        pass


class OCI_SecurityList(OCI_Resource):
    def __init__(self, res, api_client=None):
        super().__init__(res,
                         api_client=api_client,
                         name=res.display_name,
                         id=res.id,
                         res_type='securitylist')

    def _terminate(self, force=False):
        pass


class OCI_RouteTable(OCI_Resource):
    def __init__(self, res, api_client=None):
        super().__init__(res,
                         api_client=api_client,
                         name=res.display_name,
                         id=res.id,
                         res_type='routetable')

    def _terminate(self, force=False):
        pass


    

