import logging, time
import oci
from oci.core import *
from oci.load_balancer import *

from oci_tools import LIFECYCLE_KO_STATUS, LIFECYCLE_INACTIVE_STATUS, RESOURCE as R


class _Registry:
    """
    helper class to keep track of the inner dependencies not inferable via compartment scanning
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
        return self.lifecycle_state not in LIFECYCLE_INACTIVE_STATUS

    def terminate(self, force=False, simulate=False):
        """
        delete the resources and all the nested resources
        """
        logging.info(':: Terminating {} {} [{}]'.format(self.resource_type, self.name, self.id))
        #logging.info('Terminating resource {}'.format(self))
        if self._terminate(force, simulate):
            logging.info(':: {} {} terminated [{}]'.format(self.resource_type,self.name, self.id))
        else:
            logging.error(':: unable to terminate {} {} {}'.format(self.resource_type, self.name, self.id))

    def _terminate(self, force=False, simulate=False, **kwargs):
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

    def cleanup(self, force=True,
                preserve_compartments=False,
                preserve_top_level_compartment=False,
                simulate=False,
                compartment_filter=None):
        """
        Clean up resource in a compartment.

        ****IMPORTANT*****
        compartments can be delete only if:
            1 - empty in every regions
            2 - the script is running against home region API

        :param force: force termination of all the nested resources
        :param preserve_compartments: if true doesn't terminate the sub-compartment
        :param simulate: simulate termination/cleanup process without affect any resource
        :param compartment_filter: list of compartment to be terminated
        :param preserve_top_level_compartment: if true don't delete the top level compartments
        in case compartment_filter is used then the compartments specified will be the top level compartments
        :return:
        """

        if not self.is_active():
            logging.info('{} resource {} is not active'.format(self.resource_type, self.id))
            return False

        # preserve the compartment if the filter is not empty and the compartment is not listed
        preserve = bool(compartment_filter) and self.name not in compartment_filter

        items = self.get(R.COMPARTMENT)
        for nested in [] if not items else items:

            nested.cleanup(simulate=simulate,
                           preserve_compartments=preserve_compartments,
                           preserve_top_level_compartment=preserve and preserve_top_level_compartment,
                           #if the current compartment is going to be delete, don't pass the filter to subcompartment
                           compartment_filter=compartment_filter if preserve or preserve_compartments else None)

        # if preserve don't cleanup the resources
        if preserve:
            logging.info('::: skip compartment {}'.format(self.name))
            return

        logging.info(':: cleaning up compartment {} [{}]'.format(self.name, self.id))

        items = self.get(R.INSTANCE)
        for nested in [] if not items else items:
            nested.terminate(force, simulate)

        items = self.get(R.LB)
        for nested in [] if not items else items:
            nested.terminate(force, simulate)

        items = self.get(R.VCN)
        for nested in [] if not items else items:
            nested.terminate(force, simulate)

        if not preserve_compartments and not preserve_top_level_compartment:
            self.terminate(simulate=simulate)
            logging.info('::: terminate {}'.format(self.name))

        return True

    def _terminate(self, force=False, simulate=False):

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
            # if force the boot volume is deleted
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
            # *** the below order is critical to avoid dependency issues ***
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
            # the default SL can't be deleted
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
            # the default RT can't be deleted --> cleanup all the route rules
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


class OciLoadBalancer(OciResource):

    def __init__(self, res, api_client:LoadBalancerClient=None):
        super().__init__(res,
                         api_client=api_client,
                         name=res.display_name,
                         id=res.id,
                         res_type=R.LB)

    def _terminate(self, force=False, simulate=False):
        if not self.is_active():
            logging.info('{} resource {} is not active'.format(self.resource_type, self.id))
            return False

        if simulate:
            return True

        try:
            # waiter function doesn't work, so I'm checking manually the lifecycle of the resource
            # if ServiceError.404 is returned then the resource has been deleted
            self._api_client.delete_load_balancer(self.id)
            while True:
                time.sleep(3)
                logging.info('checking lb status')
                try:
                    tmp = self._api_client.get_load_balancer(self.id)
                    if tmp and tmp.data.lifecycle_state in LIFECYCLE_KO_STATUS:
                        break
                except oci.exceptions.ServiceError as se:
                    if se.status == 404:
                        break
                    raise se
            self._status = 'DELETED'
            return True
        except oci.exceptions.ServiceError as se:
            logging.error(se.message)
            return False
        except Exception as e:
            logging.error(str(e))
            return False