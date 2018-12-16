import oci
import logging
from pprint import pformat

from .oci_config import OCIConfig
from .oci_resources import *


def scan_tenancy(config:OCIConfig):
    compartment_list(config)
    #traverse(data,0)
    resource_list(config)
    logging.info('{}'.format(pformat(config.compartments_tree)))


def compartment_list(conf:OCIConfig):
    """
    list all compartments
    """
    compartment_tree = {}

    for r in conf.regions:
        conf.workon_region=r
        compartment_tree[r]=compartment_tree_build(conf)
        logging.info('_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-')
        logging.info('Compartment tree')
        logging.info('Region: {}\n{}'.format(r,pformat(compartment_tree[r])))
        logging.info('_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-')

    conf.compartments_tree = compartment_tree


def compartment_tree_build(conf:OCIConfig):
    """
    build a full compartment tree
    """
    identity_client=oci.identity.IdentityClient(conf.config)
    elems=[]
    
    clist_paged = identity_client.list_compartments(compartment_id=conf.tenancy,compartment_id_in_subtree=True)
    elems += clist_paged.data
    while clist_paged.next_page:
        clist_paged = identity_client.list_compartments(compartment_id=conf.tenancy,page=clist_paged.next_page)
        elems += clist_paged.data

    elem_with_children = {}

    def _build_children_sub_tree(parent,name):
          cur_dict = {
              'name': name,
              'id': parent,
          }
          if parent in elem_with_children.keys():
              cur_dict["nested"] = [_build_children_sub_tree(cid[0],cid[1]) for cid in elem_with_children[parent]]
          return cur_dict

    for item in elems:
          cid = item.id
          name = item.name
          pid = item.compartment_id
          elem_with_children.setdefault(pid, []).append([cid,name])

    res = _build_children_sub_tree(conf.tenancy,'tenancy')
    return res


def resource_list(conf:OCIConfig):
    """
    recursively visit all  compartments in all regions and retrieve resources
    """
    def _retrieve_resources_in_compartment(tree, traverse_level=0):
        
        logging.info('{} {}'.format('__'*traverse_level, tree['name']))
        if 'nested' in tree:
            for nested_item in tree['nested']:
                traverse_level += 1
                _retrieve_resources_in_compartment(nested_item, traverse_level)
                traverse_level -= 1
        _get_instance_resources(compute_client, tree)
        _get_network_resources(network_client, tree)

    for r in conf._compartments_tree.keys():
        #logging.info(r)
        conf.workon_region = r
        logging.info("visit compartments in {} region".format(r))

        compute_client = oci.core.ComputeClient(conf.config)

        network_client = oci.core.VirtualNetworkClient(conf.config)
        
        _retrieve_resources_in_compartment(conf._compartments_tree[r])


def _get_instance_resources(compute_client,tree):
    """
    retrieve instances and vnics
    """
    ilist = compute_client.list_instances(compartment_id=tree['id'])
    for i in ilist.data:
        instance = OCI_Instance(i)
        vnics_list = compute_client.list_vnic_attachments(compartment_id=tree['id'], instance_id = i.id)
        for v in vnics_list.data:
            rv=OCI_Vnic(v)
            instance[rv.resource_type]= rv
        tree.setdefault(instance.resource_type,[]).append(instance)


def _get_network_resources(network_client,tree):
    """
    retrieve: vcn, subnet, gateways, secury list, route tables
    """
    ilist = network_client.list_vcns(compartment_id=tree['id'])
    for i in ilist.data:
        vcn = OCI_VCN(i)
        #Subnet
        subnet = network_client.list_subnets(compartment_id=tree['id'], vcn_id = vcn.id)
        for v in subnet.data:
            rv=OCI_Subnet(v)
            vcn[rv.resource_type]= rv
        #Internet Gateway
        ig = network_client.list_internet_gateways(compartment_id=tree['id'], vcn_id = vcn.id)
        for v in ig.data:
            rv = OCI_IG(v)
            vcn[rv.resource_type] = rv
        #Nat Gateway
        ng = network_client.list_nat_gateways(compartment_id=tree['id'], vcn_id = vcn.id)
        for v in ng.data:
            rv = OCI_NatGateway(v)
            vcn[rv.resource_type] = rv
        #Security List
        sl = network_client.list_security_lists(compartment_id=tree['id'], vcn_id = vcn.id)
        for v in sl.data:
            rv = OCI_SecurityList(v)
            vcn[rv.resource_type] = rv
        #Route Table
        rt = network_client.list_route_tables(compartment_id=tree['id'], vcn_id=vcn.id)
        for v in rt.data:
            rv = OCI_RouteTable(v)
            vcn[rv.resource_type] = rv
        #ServiceGateway
        sg = network_client.list_service_gateways(compartment_id=tree['id'], vcn_id=vcn.id)
        for v in sg.data:
            rv = OCI_ServiceGateway(v)
            vcn[rv.resource_type] = rv
        #Local Peering
        lp = network_client.list_local_peering_gateways(compartment_id=tree['id'], vcn_id=vcn.id)
        for v in lp.data:
            rv = OCI_LocalPeeringGw(v)
            vcn[rv.resource_type] = rv
        tree.setdefault(vcn.resource_type, []).append(vcn)



def _get_bv_resorces(bv_client,tree):
    """
    retrieve block volumes
    """
    pass


def _get_lb_resources(tree):
    """
    retrieve loadbalancer, backaned set and listner
    """
    pass

'''
test recursive function
'''
'''
data = {'count': 2,
    'text': '1',
    'kids': [{'count': 3,
                'text': '1.1',
                'kids': [{'count': 1,
                        'text': '1.1.1',
                        'kids': [{'count':0,
                                    'text': '1.1.1.1',
                                    'kids': []}]},
                        {'count': 0,
                        'text': '1.1.2',
                        'kids': [{'count':0,
                                    'text': '1.1.2.1',
                                    'kids': []}]},
                        {'count': 0,
                        'text': '1.1.3',
                        'kids': []}]},
                {'count': 0,
                'text': '1.2',
                'kids': []}]}


def traverse(data, traverse_level):
    
    for kid in data['kids']:
        traverse_level += 1
        traverse(kid, traverse_level)
        traverse_level -= 1    
    print (' ' * traverse_level + data['text'])
'''
