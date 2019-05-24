# OCI Tools

## Introduction

Python OCI Resource Manager

## Installation 

* Setup a virtualenv and install the dependencies.
* ***The script requires python 3.6 or above***

```bash
    $ git clone https://github.com/snafuz/oci-tools.git
    $ cd oci-tools

    $ pip3 install virtualenv
    $ virtualenv venv_oci-tools
    $ . venv_oci-tools/bin/activate

    (venv_oci-tools) $ pip3 install -r requirements.txt

```
> Depending on the amount of resources and your nework connection speed the process can take several minutes to complete. To experience better performance you should run it from inside OCI tenancy.  
[Here](docs/ol_linux_setup.md) the Oracle Linux OCI instance setup



## Usage

#### Prepare configuration file:

```bash
    cd config
    cp config_template config
```
see also: [how-to setup configuration file](config/configuration_file.md) 

#### Run the process

Supported operation:
- ___list___: scan the tenancy and retrieve all the resources (Default) 
- ___cleanup___: terminate all reosurces in tenancy or in a specific compartment, but top level compartments
- ___dryrun___: emulate _cleanup_ without affecting any resource


```bash
    #enter in virtualenv
    $ . venv_oci-tools/bin/activate

    (venv_oci-tools) $ python3 oci-tools.py resource-manager --config <CONFIG_FILE_PATH>
```
If no configuration file is provided, the process will load `./config/config`

Operation can be provided as command line argument or in the config file.

```bash
    (venv_oci-tools) $ python3 oci-tools.py resource-manager --operation [list|dryrun|cleanup]
```

To refer to a specific configuration profile, use

```bash
    (venv_oci-tools) $ python3 oci-tools.py resource-manager --profile <PROFILE_NAME> 
```

By default the structure is printed out in json format. If you want it to be in yaml

```bash
    (venv_oci-tools) $ python3 oci-tools.py resource-manager --yaml 
```

To store the structure in a file
```bash
    (venv_oci-tools) $ python3 oci-tools.py resource-manager --output <FILE_PATH> 

    # or

     (venv_oci-tools) $ python3 oci-tools.py resource-manager --yaml --output <FILE_PATH> 
```

### Caveats
* The script supports the below resources
    * Compute
    * VCN (subnet, security list, route table, internet gateway, NAT gateway, local peering gateway, service gateway)
    * Block volume
    * Load Balancer
    * DRG, Remote Peering Connection, IPSec Connection, CPE
    * Database, Database Backup, Dataguard association (tested on VM only)
    * Autonomous DB (ATP, ADW)
    
* Compartment can only be deleted from the home region
* The cleanup process currently doesn't support cross-compartment dependencies










