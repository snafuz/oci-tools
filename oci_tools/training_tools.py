
from pprint import pformat

from .oci_resources import *

from oci_tools import RESOURCE as R
from oci_tools import REGIONS

from oci.exceptions import ServiceError

compute_client: oci.core.ComputeClient = None
network_client: oci.core.VirtualNetworkClient = None
bv_client: oci.core.BlockstorageClient = None
identity_client: oci.identity.IdentityClient = None
lb_client: oci.load_balancer.LoadBalancerClient = None
db_client: oci.database.DatabaseClient = None


def _init_api_client(conf: OCIConfig):
    global compute_client
    global network_client
    global bv_client
    global lb_client
    global db_client

    lb_client = oci.load_balancer.LoadBalancerClient(conf.config)
    network_client = oci.core.VirtualNetworkClient(conf.config)
    compute_client = oci.core.ComputeClient(conf.config)
    bv_client = oci.core.BlockstorageClient(conf.config)
    db_client = oci.database.DatabaseClient(conf.config)


def run(config: OCIConfig):

    get_regions(config)

    scan_tenancy(config)
    # currently cleanup and terminate-all are equivalent
    if config.operation == 'terminate-all':
        cleanup(config)
    elif config.operation == 'cleanup':
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
            tree.cleanup(config=config, force=force)


def get_regions(conf: OCIConfig):
    """
    discover subscribed regions and home region.

    :param conf: OCI configuration
    :return:
    """

    global identity_client
    # loop over the full list of regions as we don't know in advance what are the subscribed regions
    for r in REGIONS:
        conf.workon_region = r
        identity_client = oci.identity.IdentityClient(conf.config)
        try:
            rs = identity_client.list_region_subscriptions(conf.tenancy)
            conf.region_subscriptions = rs.data
            break
        except ServiceError as se:
            continue
    logging.info('Home region: {}'.format(conf.home_region))
    logging.info('Regions: {}'.format(conf.region_subscriptions))


def compartment_list(conf: OCIConfig):
    """
    list all compartments

    :param conf: OCIConfig object
    """
    region_tree = {}
    for r in conf.region_subscriptions:
        conf.workon_region = r.region_name
        # TODO: implement copy function to avoid scanning compartment for each region
        region_tree[r.region_name] = compartment_tree_build(conf)
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

    def _get_nested_resources(api_list_call: identity_client.list_compartments, id: str, tree: []):

        elems = oci.pagination.list_call_get_all_results(api_list_call, id,compartment_id_in_subtree=False)
        for item in elems.data:
            compartment = OciCompartment(item, identity_client)
            if (conf.preserve_compartments and compartment.name in conf.preserve_compartments or
                    (conf.skip_scan_preserved_resources and compartment.check_tags(conf.preserve_tags))):
                continue
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
    def _retrieve_resources_in_compartment(tree, region, traverse_level=1, scan_resources=False):        
        logging.info('{} {}'.format('__'*traverse_level, tree['name']))
        items = tree.get(R.COMPARTMENT)
        for nested_item in [] if not items else items:
            traverse_level += 1
            scan = scan_resources or not bool(conf.compartment_filter) or nested_item.name in conf.compartment_filter
            _retrieve_resources_in_compartment(nested_item, region, traverse_level, scan_resources=scan)
            traverse_level -= 1
        if scan_resources:
            _get_network_resources(tree, conf)
            _get_bv_resources(tree, conf)
            _get_instance_resources(tree, conf)
            _get_lb_resources(tree, conf)
            _get_db_resources(tree, conf)
            _get_autonomous_resources(tree, conf)

    for r in conf.compartments_tree.keys():
        # logging.info(r)
        conf.workon_region = r
        logging.info("Resource discovery - visit compartments in {} region".format(r))
        _init_api_client(conf)

        # bv_client.list_volumes('').data
        for tree in conf.compartments_tree[r]:
            scan = not bool(conf.compartment_filter) or tree.name in conf.compartment_filter
            _retrieve_resources_in_compartment(tree, r, scan_resources=scan)


def _get_instance_resources(tree: OciResource, conf: OCIConfig):
    """
    retrieve instances and vnics

    :param tree: compartment subtree
    """
    ilist = oci.pagination.list_call_get_all_results(compute_client.list_instances, compartment_id=tree['id'])

    def _get_nested_resources(api_list_call, res: OciResource):
        try:
            rlist = oci.pagination.list_call_get_all_results(api_list_call,
                                                             compartment_id=tree['id'],
                                                             instance_id=i.id)
            for r in rlist.data:
                res_obj = res(r, compute_client)
                if conf.skip_scan_preserved_resources and res_obj.check_tags(conf.preserve_tags):
                    continue
                if not res_obj or not res_obj.is_active():
                    continue
                res_obj.append(res_obj)
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
            logging.error('unable to retrieve {} Instance {}'.format(res.resource_type, i.id))

    for i in ilist.data:
        instance = OciInstance(i, compute_client)
        if not instance.is_active():
            continue
        _get_nested_resources(compute_client.list_vnic_attachments, OciVnicAttachment)

        tree.append(instance)


def _get_network_resources(tree, conf: OCIConfig):
    """
    retrieve: vcn, subnet, gateways, secury list, route tables

    :param tree: compartment subtree
    """

    ilist = oci.pagination.list_call_get_all_results(network_client.list_vcns, compartment_id=tree['id'])

    def _get_nested_resources(api_list_call, res: OciResource, **kwargs):
        try:
            if 'vcn_id' in kwargs:
                rlist = oci.pagination.list_call_get_all_results(api_list_call,
                                                                 compartment_id=tree['id'],
                                                                 vcn_id=kwargs.get('vcn_id'))
            else:
                rlist = oci.pagination.list_call_get_all_results(api_list_call,
                                                                 compartment_id=tree['id'])
            if not rlist.data:
                return None
            for r in rlist.data or []:
                res_obj = res(r, network_client)
                if conf.skip_scan_preserved_resources and res_obj.check_tags(conf.preserve_tags):
                    continue
                if not res_obj or not res_obj.is_active():
                    continue
                return res_obj
        except oci.exceptions.ServiceError as se:
            logging.error('unable to retrieve {}  VCN {}'.format(res.resource_type, vcn.id))
            return None

    for i in ilist.data:
        vcn = OciVcn(i, network_client)
        vcn.append(_get_nested_resources(network_client.list_subnets, OciSubnet, vcn_id=vcn.id))
        vcn.append(_get_nested_resources(network_client.list_internet_gateways, OciInternetGw, vcn_id=vcn.id))
        vcn.append(_get_nested_resources(network_client.list_nat_gateways, OciNatGw, vcn_id=vcn.id))
        vcn.append(_get_nested_resources(network_client.list_security_lists, OciSecurityList, vcn_id=vcn.id))
        vcn.append(_get_nested_resources(network_client.list_route_tables, OciRouteTable, vcn_id=vcn.id))
        vcn.append(_get_nested_resources(network_client.list_local_peering_gateways, OciLocalPeeringGw, vcn_id=vcn.id))
        vcn.append(_get_nested_resources(network_client.list_service_gateways, OciServiceGw, vcn_id=vcn.id))

        tree.append(vcn)

    tree.append(_get_nested_resources(network_client.list_drgs, OciDRG))
    tree.append(_get_nested_resources(network_client.list_cpes, OciCPE))
    tree.append(_get_nested_resources(network_client.list_drg_attachments, OciDRGAttachment))
    tree.append(_get_nested_resources(network_client.list_remote_peering_connections, OciRPC))
    tree.append(_get_nested_resources(network_client.list_ip_sec_connections, OciVPN))


def _get_bv_resources(tree, conf: OCIConfig):
    """
    retrieve block volumes

    :param tree: compartment subtree
    """

    try:
        ilist = oci.pagination.list_call_get_all_results(bv_client.list_volumes, compartment_id=tree['id'])

        for i in ilist.data:
            res_obj = OciBlockVolume(i, bv_client)
            if (conf.skip_scan_preserved_resources and res_obj.check_tags(
                    conf.preserve_tags)) or not res_obj.is_active():
                continue
            tree.append(res_obj)
    except Exception as e:
        logging.error('error while retrieving Block Volume resources')


def _get_lb_resources(tree, conf: OCIConfig):
    """
    retrieve: lb resources

    :param tree: compartment subtree
    """

    ilist = oci.pagination.list_call_get_all_results(lb_client.list_load_balancers, compartment_id=tree['id'])

    for i in ilist.data:
        res_obj = OciLoadBalancer(i, lb_client)
        if (conf.skip_scan_preserved_resources and res_obj.check_tags(conf.preserve_tags)) or not res_obj.is_active():
            continue
        tree.append(res_obj)


def _get_db_resources(tree, conf: OCIConfig):
    """
    retrieve: db_system resources

    :param tree: compartment subtree
    """

    ilist = oci.pagination.list_call_get_all_results(db_client.list_db_systems, compartment_id=tree['id'])

    for i in ilist.data:
        res_obj = OciDbSystem(i, db_client)
        if (conf.skip_scan_preserved_resources and res_obj.check_tags(conf.preserve_tags)) or not res_obj.is_active():
            continue
        dbhomes = db_client.list_db_homes(tree['id'], res_obj.id)
        if dbhomes and dbhomes.data:
            for dbh in dbhomes.data:
                res_obj.append(OciDBHome(dbh, db_client))
        tree.append(res_obj)

    ilist = oci.pagination.list_call_get_all_results(db_client.list_backups, compartment_id=tree['id'])

    for i in ilist.data:
        res_obj = OciDbBackup(i, db_client)
        if (conf.skip_scan_preserved_resources and res_obj.check_tags(conf.preserve_tags)) or not res_obj.is_active():
            continue
        tree.append(res_obj)


def _get_autonomous_resources(tree, conf: OCIConfig):
    """
    retrieve: autonomous db resources

    :param tree: compartment subtree
    """

    ilist = oci.pagination.list_call_get_all_results(db_client.list_autonomous_databases, compartment_id=tree['id'])
    for i in ilist.data:
        res_obj = OciAutonomousDB(i, db_client)
        if (conf.skip_scan_preserved_resources and res_obj.check_tags(conf.preserve_tags)) or not res_obj.is_active():
            continue
        tree.append(res_obj)
