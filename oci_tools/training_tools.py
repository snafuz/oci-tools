import copy
from pprint import pformat

from .oci_config import OCIConfig
from .oci_resources import *

from oci_tools import RESOURCE as R


compute_client: oci.core.ComputeClient = None
network_client: oci.core.VirtualNetworkClient = None
bv_client: oci.core.BlockstorageClient = None
identity_client: oci.identity.IdentityClient = None
lb_client: oci.load_balancer.LoadBalancerClient = None



def run(config: OCIConfig):

    scan_tenancy(config)
    if config.operation == 'delete':
        cleanup(config)
    elif config.operation =='cleanup':
        cleanup(config)


def scan_tenancy(config: OCIConfig):
    """
    Scan the tenancy by compartments

    :param config: OCIConfig object
    """
    compartment_list(config)
    resource_list(config)
    logging.info('{}'.format(pformat(config.compartments_tree)))


def cleanup(config: OCIConfig, force=False):
    """
    Clean up operations
    TODO: currently the cleanup operation follow the compartment tree. It should take in consideration the dependency tree

    :param config: OCIConfig object
    :param force: terminate also the top level compartment
    """

    for r in config.compartments_tree.keys():
        # logging.info(r)
        config.workon_region = r
        logging.info("Clean-up resources in {} region".format(r))

        for tree in config.compartments_tree[r]:
            if force:
                pass
            else:
                tree.cleanup(simulate=config.simulate_deletion,
                             compartment_filter=config.compartment_filter,
                             preserve_top_level_compartment=config.preserve_top_level_compartment,
                             preserve_compartments=config.preserve_compartments)


def compartment_list(conf: OCIConfig):
    """
    list all compartments

    :param conf: OCIConfig object
    """
    region_tree = {}
    for r in conf.region_filter:
        conf.workon_region=r
        # TODO: implement copy function to avoid scanning compartment for each region
        region_tree[r] = compartment_tree_build(conf)
        '''
        logging.info('_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-')
        logging.info('Compartment tree')
        logging.info('Region: {}\n{}'.format(r, pformat(region_tree[r])))
        logging.info('_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-')
        '''
    conf.compartments_tree = region_tree


def compartment_tree_build(conf: OCIConfig):
    """
    build a full compartment tree
    """
    global identity_client
    identity_client = oci.identity.IdentityClient(conf.config)
    tree = []

    def _get_nested_resources(api_list_call: identity_client.list_compartments, id: str, tree: []) :

        elems = oci.pagination.list_call_get_all_results(api_list_call, id,compartment_id_in_subtree=False)
        for item in elems.data:
            compartment = OciCompartment(item, identity_client)
            if not compartment.is_active():
                continue
            _get_nested_resources(api_list_call, compartment.id, compartment)
            tree.append(compartment)

    _get_nested_resources(identity_client.list_compartments, conf.tenancy, tree)

    return tree


def resource_list(conf: OCIConfig):
    """
    recursively visit all  compartments in all regions and retrieve resources

    :param conf: OCIConfig object
    """
    def _retrieve_resources_in_compartment(tree, region, traverse_level=1):
        
        logging.info('{} {}'.format('__'*traverse_level, tree['name']))
        items = tree.get(R.COMPARTMENT)
        for nested_item in [] if not items else items:
            traverse_level += 1
            _retrieve_resources_in_compartment(nested_item, region, traverse_level)
            traverse_level -= 1
        _get_network_resources(tree, region)
        _get_bv_resources(tree, region)
        _get_instance_resources(tree, region)
        _get_lb_resources(tree, region)

    global compute_client
    global network_client
    global bv_client
    global lb_client

    for r in conf.compartments_tree.keys():
        # logging.info(r)
        conf.workon_region = r
        logging.info("Resource discovery - visit compartments in {} region".format(r))
        lb_client = oci.load_balancer.LoadBalancerClient(conf.config)
        network_client = oci.core.VirtualNetworkClient(conf.config)
        compute_client = oci.core.ComputeClient(conf.config)
        bv_client = oci.core.BlockstorageClient(conf.config)

        # bv_client.list_volumes('').data
        for tree in conf.compartments_tree[r]:
            _retrieve_resources_in_compartment(tree, r)


def _get_instance_resources(tree: OciResource, region):
    """
    retrieve instances and vnics

    :param tree: compartment subtree
    :param region: current region
    """
    ilist = oci.pagination.list_call_get_all_results(compute_client.list_instances, compartment_id=tree['id'])

    def _get_nested_resources(api_list_call, res: OciResource):
        try:
            rlist = oci.pagination.list_call_get_all_results(api_list_call,
                                                             compartment_id=tree['id'],
                                                             instance_id=i.id)
            for r in rlist.data:
                res_obj = res(r, compute_client)
                if not res_obj or not res_obj.is_active():
                    continue
                instance.append(res_obj)
                # vcn dependency tree for clean-up operation
                if isinstance(res_obj, OciVnicAttachment):
                    # if primary vnic the dependency is on the instance as I can't detach the primary vnic
                    # else is just the vnic-attachment
                    vnic_id= res_obj.resource.vnic_id
                    vnic = network_client.get_vnic(vnic_id)
                    if vnic.data.is_primary:
                        OciResource.set_dependency(r.subnet_id, instance)
                    else:
                        OciResource.set_dependency(r.subnet_id, res_obj)

        except Exception as e:
            logging.error('unable to retrieve {} in [{}] Instance {}'.format(res.resource_type, region, i.id))

    for i in ilist.data:
        instance = OciInstance(i, compute_client)
        if not instance.is_active():
            continue
        _get_nested_resources(compute_client.list_vnic_attachments, OciVnicAttachment)

        tree.append(instance)


def _get_network_resources(tree, region):
    """
    retrieve: vcn, subnet, gateways, secury list, route tables

    :param tree: compartment subtree
    :param region: current region
    """

    ilist = oci.pagination.list_call_get_all_results(network_client.list_vcns, compartment_id=tree['id'])

    def _get_nested_resources(api_list_call, res: OciResource):
        try:
            rlist = oci.pagination.list_call_get_all_results(api_list_call,
                                                             compartment_id=tree['id'],
                                                             vcn_id=vcn.id)
            for r in rlist.data:
                res_obj = res(r, network_client)
                if not res_obj or not res_obj.is_active():
                    continue
                vcn.append(res_obj)
        except:
            logging.error('unable to retrieve {} in [{}] VCN {}'.format(res.resource_type, region, vcn.id))

    for i in ilist.data:
        vcn = OciVcn(i, network_client)
        _get_nested_resources(network_client.list_subnets, OciSubnet)
        _get_nested_resources(network_client.list_internet_gateways, OciInternetGw)
        _get_nested_resources(network_client.list_nat_gateways, OciNatGw)
        _get_nested_resources(network_client.list_security_lists, OciSecurityList)
        _get_nested_resources(network_client.list_route_tables, OciRouteTable)
        _get_nested_resources(network_client.list_local_peering_gateways, OciLocalPeeringGw)
        _get_nested_resources(network_client.list_service_gateways, OciServiceGw)

        tree.append(vcn)


def _get_bv_resources(tree, region):
    """
    retrieve block volumes

    :param tree: compartment subtree
    :param region: current region
    """

    try:
        ilist = oci.pagination.list_call_get_all_results(bv_client.list_volumes, compartment_id=tree['id'])

        for i in ilist.data:
            bv = OciBlockVolume(i, bv_client)

            tree.setdefault(bv.resource_type, []).append(bv)
    except Exception as e:
        logging.error('error while retrieving Block Volume resources')


def _get_lb_resources(tree, region):
    """
    retrieve: vcn, subnet, gateways, secury list, route tables

    :param tree: compartment subtree
    :param region: current region
    """

    ilist = oci.pagination.list_call_get_all_results(lb_client.list_load_balancers, compartment_id=tree['id'])


    for i in ilist.data:
        lb = OciLoadBalancer(i, lb_client)

        tree.append(lb)



