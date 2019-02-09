__author__ = "amarchesini"
__copyright__ = ""
__credits__ = ["Andrea Marchesini"]
__license__ = ""
__version__='0.1.3'
__maintainer__ = "amarchesini"
__email__ = "andrea.marchesini@oracle.com"
__status__ = "dev"
__description__=""

#################################################

from collections import namedtuple

# resource name identifier
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
                       'LPEERINGGW '
                       'LB '
                       'DB_SYSTEM '
                       'DB_BACKUP '
                       'CPE '
                       'RPC '
                       'VPN '
                       'DRG_ATTACHMENT '
                       'DB_HOME '
                        )\
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
     'lpg',
     'lb',
     'db_system',
     'db_backup',
     'cpe',
     'rpc',
     'vpn',
     'drg_attachment',
     'db_home')


LIFECYCLE_KO_STATUS =['TERMINATED',
                      'DETACHED',
                      'DELETED']

LIFECYCLE_INACTIVE_STATUS = ['TERMINATING',
                             'DELETING'] + LIFECYCLE_KO_STATUS


