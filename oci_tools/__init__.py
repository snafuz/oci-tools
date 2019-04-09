__author__ = "amarchesini"
__copyright__ = ""
__credits__ = ["Andrea Marchesini"]
__license__ = ""
__version__='0.1.4'
__maintainer__ = "amarchesini"
__email__ = "andrea.marchesini@oracle.com"
__status__ = "dev"
__description__=""

#################################################

from collections import namedtuple

REGIONS = ['ca-toronto-1',
           'us-ashburn-1',
           'us-phoenix-1',
           'ca-toronto-1',
           'eu-frankfurt-1',
           'uk-london-1']

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
                       'AUTONOMOUS_DB'
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
     'db_home',
     'autonomous_db')


LIFECYCLE_KO_STATUS =['TERMINATED',
                      'DETACHED',
                      'DELETED']

LIFECYCLE_INACTIVE_STATUS = ['TERMINATING',
                             'DELETING'] + LIFECYCLE_KO_STATUS


