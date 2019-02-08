#!/usr/bin/env python


from oci_tools import  __version__
from oci_tools import oci_config, training_tools
import sys, argparse, logging


def print_help(args):

    parser.print_help()


def training(args):
    """
    Entry point for the oci training toolkit
    """
    conf = oci_config.OCIConfig(args.config, regions=args.regions)

    training_tools.run(conf)

def resource_manager(args):
    """
        Entry point for the oci resource manager
        """
    conf = oci_config.OCIConfig(args.config, regions=args.regions)

    training_tools.run(conf)



def setup_log(args):
    """
    setup log
    """

    log_handlers = []

    if args.log == 'console' or args.log == 'all':
        sh = logging.StreamHandler()
        sh.setFormatter(logging.Formatter("%(message)s"))
        log_handlers.append(sh)
    if args.log == 'file' or args.log == 'all':
        log_handlers.append(logging.FileHandler("{0}".format(args.log_output)))

    logging.basicConfig(
        level=logging.getLevelName(args.log_level.upper()),
        format="%(asctime)s [%(levelname)-5.5s]  %(message)s",
        handlers=log_handlers,
    )

    if args.log_level.upper() != 'DEBUG':
        logging.getLogger("oci").setLevel(logging.WARNING)


#########################
# command line parser init
parser = argparse.ArgumentParser(description="OCI Toolkit")
parser.set_defaults(func=print_help)
parser.add_argument('--log',
                    dest='log',
                    choices=['console', 'file', 'all', 'none'],
                    default='console')
parser.add_argument('--log-level',
                    dest='log_level',
                    choices=['debug', 'info', 'warn'],
                    default='info')
parser.add_argument('--log-output',
                    dest='log_output',
                    default='log/oci-tools.log')


sub01 = parser.add_subparsers(help="OCI toolkit")
training_parser = sub01.add_parser('training',
                                   help="utility to manage training environments")
training_parser.set_defaults(func=training)
training_parser.add_argument('--config',
                             help='OCI configuration file',
                             dest='config',
                             default='./config/config')
training_parser.add_argument('--regions',
                             help='comma separated list of regions',
                             dest='regions')
    
resource_manager_parser = sub01.add_parser('resource-manager',
                                   help="utility to manage oci environments")
resource_manager_parser.set_defaults(func=resource_manager)
resource_manager_parser.add_argument('--config',
                             help='OCI configuration file',
                             dest='config',
                             default='./config/config')
# WARNING below parameters are not yet managed in the code
# USE CONFIG FILE
resource_manager_parser.add_argument('-o', '--operation',
                             dest='operation',
                             default='list',
                             choices=['list', 'delete'])
resource_manager_parser.add_argument('--regions',
                             help='comma separated list of regions',
                             dest='regions')
resource_manager_parser.add_argument('-f', '--force',
                             help='force the delete operation without asking for confirmation',
                             default=False,
                             dest='clean_force')


def main():
    import sys
    if sys.version_info[0] < 3:
        raise Exception("I'm sorry, you're Python version must be >= 3.6")
    print(' ** oci-tools v.{} **'.format(__version__))
    args=parser.parse_args()
    setup_log(args)
    args.func(args)


if __name__ == '__main__':
    main()