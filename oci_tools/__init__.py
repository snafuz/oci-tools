__author__ = "amarchesini"
__copyright__ = ""
__credits__ = ["Andrea Marchesini"]
__license__ = ""
__version__='0.1.0'
__maintainer__ = "amarchesini"
__email__ = "andrea.marchesini@oracle.com"
__status__ = "dev"
__description__=""

#################################################

from collections import namedtuple

RESOURCE = namedtuple('RESOURCES',
                       'VCN '
                       'INSTANCE '
                       'COMPARTMENT '
                       'VNIC '
                       'BLOCKVOLUME '
                       'VNIC_ATTACHMENT '
                       'SUBNET '
                       'IGW '
                       'NATGW '
                       'DRG '
                       'SERVICEGW '
                       'SEC_LIST '
                       'ROUTE_TABLE '
                       'LPEERINGGW')\
    ('vcn',
     'instance',
     'compartment',
     'vnic',
     'bv',
     'vnic_attachment',
     'subnet',
     'igw',
     'natgw',
     'drg',
     'sgw',
     'sl',
     'rt',
     'lpg')

LIFECYCLE_KO_STATUS =['TERMINATED',
                      'TERMINATING',
                      'DETACHED',
                      'DELETED']

