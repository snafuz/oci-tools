import logging
import oci
from oci.core import *

from oci_tools import LIFECYCLE_KO_STATUS, RESOURCE as R



class _Registry:
    """
    helper class to keep track of the inner dependency not inferable via compartment scanning
    It contains a flat dict with all the resources.
    """

    def __init__(self):
        self._registry = {}

    def append(self, id, obj):
        self._registry[id] = obj

    def get(self, id):
        return self._registry[id]


_registry = _Registry()




class OciResource(dict):
    """
    archetype for OCI resources
    it contains the current resources and all the nested ones
    """
    @staticmethod
    def set_dependency(parent_id, nested):
        """
        use the registry to inject nested dependency not inferable via compartment scan

        :param parent_id: OCID id of the parent resource you want to append the neted to
        :param nested:  nested OCI resource
        """
        res = _registry.get(parent_id)
        if res:
            res[parent_id] = nested

    def __init__(self, res, api_client=None, name='resource', id=None, res_type='resource'):
        """
        Init OCI Resource
        :param res: OCI API resource
        :param api_client:  OCI API Client object
        :param name: resource name/display_name
        :param id: resource OCID
        :param res_type: resource type
        """
        super().__init__({'name': name, 'id': id})
        self._name = name
        self._id = id
        self._resource=res
        self._resource_type = res_type
        self._api_client = api_client
        self._lifecycle_state = res.lifecycle_state
        self._compartment = res.compartment_id
        _registry.append(self._id, self)


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
        return self.items()

    def append(self, res_obj):
        """

        :param res:
        :return:
        """
        self.setdefault(res_obj.resource_type, []).append(res_obj)


    @property
    def id(self):
        return self._id

    @property
    def name(self):
        return self._name

    @property
    def lifecycle_state(self):
        return self._status()

    @property
    def compartment(self):
        return self.compartment

    @property
    def resource_type(self):
        return self._resource_type

    def is_active(self):
        return self.lifecycle_state not in LIFECYCLE_KO_STATUS

    def terminate(self, force=False, simulate=False):
        """
        delete the resources and all the nested resources
        """
        #logging.info('Terminating resource {}'.format(self))
        if self._terminate(force, simulate):
            logging.info(':: {} terminated [{}]'.format(self.resource_type, self.id))
        else:
            logging.error(':: unable to terminate {} {} {}'.format(self.resource_type, self.name, self.id))

    def _terminate(self, force=False, simulate=False):
        """
        internal Terminate implementation
        Child classes should override this method
        """
        pass
    
    def _status(self):
        return self._lifecycle_state

####################################
# Resource definitions
####################################
class OciCompartment(OciResource):

    def __init__(self, res, api_client=None):
        super().__init__(res,
                         api_client=api_client,
                         name=res.name,
                         id=res.id,
                         res_type=R.COMPARTMENT)

    def cleanup(self, force=True, preserve_sub_compartment=False, simulate=False, compartment_filter=None):
        """
        Clean up resource in a compartment

        :param force: force termination of all the nested resources
        :param preserve_sub_compartment: if true doesn't terminate the sub-compartment
        :param simulate: simulate termination/cleanup process without affect any resource
        :param compartment_filter: list of compartment to be terminated
        :return:
        """

        if not self.is_active():
            logging.info('{} resource {} is not active'.format(self.resource_type, self.id))
            return False



        preserve = bool(compartment_filter) and self.name not in compartment_filter

        items = self.get(R.COMPARTMENT)
        for nested in [] if not items else items:
            if preserve or preserve_sub_compartment:
                nested.cleanup(simulate=simulate, compartment_filter=compartment_filter)
            else:
                nested.terminate(force, simulate)

        if preserve:
            logging.info('::: skip compartment {}'.format(self.name))
            return

        logging.info(':: cleaning up compartment {} [{}]'.format(self.name, self.id))

        items = self.get(R.INSTANCE)
        for nested in [] if not items else items:
            nested.terminate(force, simulate)

        items = self.get(R.VCN)
        for nested in [] if not items else items:
            nested.terminate(force, simulate)

        return True

    def _terminate(self, force=False, simulate=False, filter=None):

        if not self.is_active():
            logging.info('{} resource {} is not active'.format(self.resource_type, self.id))
            return

        self.cleanup(simulate=simulate)

        if not self.is_active():
            logging.info('{} resource {} is not active'.format(self.resource_type, self.id))
            return False

        if simulate:
            return True

        try:

            oci.identity.IdentityClientCompositeOperations(self._api_client)\
                .delete_compartment_and_wait_for_state(self.id, LIFECYCLE_KO_STATUS)
            self._status = 'DELETED'
            return True
        except oci.exceptions.ServiceError as se:
            logging.error(se.message)
            return False
        except Exception as e:
            logging.error(str(e))
            return False


class OciInstance(OciResource):

    def __init__(self, res, api_client:ComputeClient=None):
        super().__init__(res,
                         api_client=api_client,
                         name=res.display_name,
                         id=res.id,
                         res_type=R.INSTANCE)

    def _terminate(self, force=False, simulate=False):

        if not self.is_active():
            logging.info('{} resource {} is not active'.format(self.resource_type, self.id))
            return False

        if simulate:
            return True

        # attached vnics are automatically detached and terminated
        try:
            oci.core.ComputeClientCompositeOperations(
                self._api_client
            ).terminate_instance_and_wait_for_state(self.id,
                                                    LIFECYCLE_KO_STATUS,
                                                    {'preserve_boot_volume': (not force)})

            self._status = 'TERMINATED'
            return True
        except oci.exceptions.ServiceError as se:
            logging.error(se.message)
            return False
        except Exception as e:
            logging.error(str(e))
            return False


class OciVnicAttachment(OciResource):

    def __init__(self,res, api_client=None):
        super().__init__(res,
                         api_client=api_client,
                         name=res.display_name,
                         id=res.id,
                         res_type=R.VNIC_ATTACHMENT)

    def _terminate(self, force=False, simulate=False):
        if not self.is_active():
            logging.info('{} resource {} is not active'.format(self.resource_type, self.id))
            return False

        if simulate:
            return True


class OciVcn(OciResource):

    def __init__(self, res, api_client:VirtualNetworkClient=None):
        super().__init__(res,
                         api_client=api_client,
                         name=res.display_name,
                         id=res.id,
                         res_type=R.VCN)

    def _terminate(self, force=False, simulate=False):

        if force:
            # !! the below order is critical to be able to terminate all the resources
            items = self.get(R.SUBNET)
            for nested in [] if not items else items:
                nested.terminate(force, simulate)

            items = self.get(R.SEC_LIST)
            for nested in [] if not items else items:
                nested.terminate(force, simulate)

            items = self.get(R.ROUTE_TABLE)
            for nested in [] if not items else items:
                nested.terminate(force, simulate)

            items = self.get(R.IGW)
            for nested in [] if not items else items:
                nested.terminate(force, simulate)

            items = self.get(R.LPEERINGGW)
            for nested in [] if not items else items:
                nested.terminate(force, simulate)

            items = self.get(R.NATGW)
            for nested in [] if not items else items:
                nested.terminate(force, simulate)

        if not self.is_active():
            logging.info('{} resource {} is not active'.format(self.resource_type, self.id))
            return False

        if simulate:
            return True

        try:

            oci.core.VirtualNetworkClientCompositeOperations(self._api_client)\
                .delete_vcn_and_wait_for_state(self.id, LIFECYCLE_KO_STATUS)
            self._status = 'TERMINATED'
            return True
        except oci.exceptions.ServiceError as se:
            logging.error(se.message)
            return False
        except Exception as e:
            logging.error(str(e))
            return  False


class OciSubnet(OciResource):

    def __init__(self, res, api_client:VirtualNetworkClient=None):
        super().__init__(res,
                         api_client=api_client,
                         name=res.display_name,
                         id=res.id,
                         res_type=R.SUBNET)

    def _terminate(self, force=False, simulate=False):

        if not self.is_active():
            logging.info('{} resource {} is not active'.format(self.resource_type, self.id))
            return False

        if simulate:
            return True

        try:
            oci.core.VirtualNetworkClientCompositeOperations(self._api_client)\
                .delete_subnet_and_wait_for_state(self.id, LIFECYCLE_KO_STATUS)
            self._status = 'TERMINATED'
            return True
        except oci.exceptions.ServiceError as se:
            logging.error(se.message)
            return False
        except Exception as e:
            logging.error(str(e))
            return False


class _SubnetRegistry:
    """
    Registry to keep track of inter-compartment dependencies
    """

    def __init__(self):
        self._registry = {}

    def append(self, subnet: OciSubnet):
        self._registry.setdefault(subnet.id, subnet)

    def get(self, subnet_id):
        return self._registry[subnet_id]


_subnet_registry = _SubnetRegistry()


class OciInternetGw(OciResource):

    def __init__(self, res, api_client:VirtualNetworkClient=None):
        super().__init__(res,
                         api_client=api_client,
                         name=res.display_name,
                         id=res.id,
                         res_type=R.IGW)

    def _terminate(self, force=False, simulate=False):
        if not self.is_active():
            logging.info('{} resource {} is not active'.format(self.resource_type, self.id))
            return False

        if simulate:
            return True

        try:
            oci.core.VirtualNetworkClientCompositeOperations(self._api_client)\
                .delete_internet_gateway_and_wait_for_state(self.id, LIFECYCLE_KO_STATUS)
            self._status = 'TERMINATED'
            return True
        except oci.exceptions.ServiceError as se:
            logging.error(se.message)
            return False
        except Exception as e:
            logging.error(str(e))
            return  False


class OciNatGw(OciResource):

    def __init__(self, res, api_client:VirtualNetworkClient=None):
        super().__init__(res,
                         api_client=api_client,
                         name=res.display_name,
                         id=res.id,
                         res_type=R.NATGW)

    def _terminate(self, force=False, simulate=False):
        if not self.is_active():
            logging.info('{} resource {} is not active'.format(self.resource_type, self.id))
            return False

        if simulate:
            return True

        try:
            oci.core.VirtualNetworkClientCompositeOperations(self._api_client)\
                .delete_nat_gateway_and_wait_for_state(self.id, LIFECYCLE_KO_STATUS)
            self._status = 'TERMINATED'
            return True
        except oci.exceptions.ServiceError as se:
            logging.error(se.message)
            return False
        except Exception as e:
            logging.error(str(e))
            return False


class OciDRG(OciResource):

    def __init__(self, res, api_client:VirtualNetworkClient=None):
        super().__init__(res,
                         api_client=api_client,
                         name=res.display_name,
                         id=res.id,
                         res_type=R.DRG)

    def _terminate(self, force=False, simulate=False):
        if not self.is_active():
            logging.info('{} resource {} is not active'.format(self.resource_type, self.id))
            return False

        if simulate:
            return True

        try:
            oci.core.VirtualNetworkClientCompositeOperations(self._api_client)\
                .delete_drg_and_wait_for_state(self.id, LIFECYCLE_KO_STATUS)
            self._status = 'TERMINATED'
            return True
        except oci.exceptions.ServiceError as se:
            logging.error(se.message)
            return False
        except Exception as e:
            logging.error(str(e))
            return False


class OciServiceGw(OciResource):

    def __init__(self, res, api_client:VirtualNetworkClient=None):
        super().__init__(res,
                         api_client=api_client,
                         name=res.display_name,
                         id=res.id,
                         res_type=R.SERVICEGW)

    def _terminate(self, force=False, simulate=False):
        if not self.is_active():
            logging.info('{} resource {} is not active'.format(self.resource_type, self.id))
            return False

        if simulate:
            return True

        try:
            oci.core.VirtualNetworkClientCompositeOperations(self._api_client)\
                .delete_service_gateway_and_wait_for_state(self.id, LIFECYCLE_KO_STATUS)
            self._status = 'TERMINATED'
            return True
        except oci.exceptions.ServiceError as se:
            logging.error(se.message)
            return False
        except Exception as e:
            logging.error(str(e))
            return False


class OciLocalPeeringGw(OciResource):

    def __init__(self, res, api_client:VirtualNetworkClient=None):
        super().__init__(res,
                         api_client=api_client,
                         name=res.display_name,
                         id=res.id,
                         res_type=R.LPEERINGGW)

    def _terminate(self, force=False, simulate=False):
        if not self.is_active():
            logging.info('{} resource {} is not active'.format(self.resource_type, self.id))
            return False

        if simulate:
            return True

        try:
            oci.core.VirtualNetworkClientCompositeOperations(self._api_client)\
                .delete_local_peering_gateway_and_wait_for_state(self.id, LIFECYCLE_KO_STATUS)
            self._status = 'TERMINATED'
            return True
        except oci.exceptions.ServiceError as se:
            logging.error(se.message)
            return False
        except Exception as e:
            logging.error(str(e))
            return False


class OciSecurityList(OciResource):


    def __init__(self, res, api_client:VirtualNetworkClient=None):
        super().__init__(res,
                         api_client=api_client,
                         name=res.display_name,
                         id=res.id,
                         res_type=R.SEC_LIST)

    def _terminate(self, force=False, simulate=False):
        """
            The default security list for a given VCN can't be deleted
        """

        if not self.is_active():
            logging.info('{} resource {} is not active'.format(self.resource_type, self.id))
            return False

        if simulate:
            return True

        try:
            oci.core.VirtualNetworkClientCompositeOperations(self._api_client)\
                .delete_security_list_and_wait_for_state(self.id, LIFECYCLE_KO_STATUS)

            self._status = 'TERMINATED'
            return  True
        except oci.exceptions.ServiceError as se:
            #If it is the default SL can't be deleted
            if se.code == 'IncorrectState' and se.status==409:
                return True
            logging.error(se.message)
            return False
        except Exception as e:
            logging.error(str(e))
            return False


class OciRouteTable(OciResource):

    def __init__(self, res, api_client:VirtualNetworkClient=None):
        super().__init__(res,
                         api_client=api_client,
                         name=res.display_name,
                         id=res.id,
                         res_type=R.ROUTE_TABLE)

    def _terminate(self, force=False, simulate=False):
        """
        The default route table for a given VCN can't be deleted but need to be emptied.
        """

        if not self.is_active():
            logging.info('{} resource {} is not active'.format(self.resource_type, self.id))
            return False

        if simulate:
            return True

        try:
            oci.core.VirtualNetworkClientCompositeOperations(self._api_client)\
                .delete_route_table_and_wait_for_state(self.id, LIFECYCLE_KO_STATUS)

            self._status = 'TERMINATED'
            return True
        except oci.exceptions.ServiceError as se:
            # If it is the default RT can't be deleted and need to cleanup all the route rules
            if se.code == 'IncorrectState' and se.status == 409:
                return self.cleanup()
            logging.error(se.message)
            return False
        except Exception as e:
            logging.error(str(e))
            return False

    def cleanup(self):
        try:
            self._api_client.update_route_table(self.id, oci.core.models.UpdateRouteTableDetails(route_rules=[]))
            return True
        except oci.exceptions.ServiceError as se:
            logging.error(se.message)
            return False

class OciBlockVolume(OciResource):

    def __init__(self, res, api_client:BlockstorageClient=None):
        super().__init__(res,
                         api_client=api_client,
                         name=res.display_name,
                         id=res.id,
                         res_type=R.BLOCKVOLUME)

    def _terminate(self, force=False, simulate=False):

        if not self.is_active():
            logging.info('{} resource {} is not active'.format(self.resource_type, self.id))
            return False

        if simulate:
            return True

        try:
            oci.core.VirtualNetworkClientCompositeOperations(self._api_client)\
                .delete_volume_and_wait_for_state(self.id, LIFECYCLE_KO_STATUS)
            self._status = 'TERMINATED'
            return True
        except oci.exceptions.ServiceError as se:
            logging.error(se.message)
            return False
        except Exception as e:
            logging.error(str(e))
            return False


class OciVnic(OciResource):

    def __init__(self, res, api_client:VirtualNetworkClient=None):
        super().__init__(res,
                         api_client=api_client,
                         name=res.display_name,
                         id=res.id,
                         res_type=R.VNIC)

    def _terminate(self, force=False, simulate=False):
        if not self.is_active():
            logging.info('{} resource {} is not active'.format(self.resource_type, self.id))
            return False

        if simulate:
            return True

        try:
            oci.core.VirtualNetworkClientCompositeOperations(self._api_client)\
                .detach_vnic_and_wait_for_state(self.id, LIFECYCLE_KO_STATUS)
            self._status = 'TERMINATED'
            return True
        except oci.exceptions.ServiceError as se:
            logging.error(se.message)
            return False
        except Exception as e:
            logging.error(str(e))
            return False
