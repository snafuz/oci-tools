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

[Here](docs/ol_linux_setup.md) the Oracle Linux OCI instance setup

* Prepare configuration file:

```bash
    cd config
    cp config_template config
```
see also: [how-to setup configuration file](config/configuration_file.md) 

## Usage

#### Training toolkit

Training toolkit 
- scan the tenancy and retrieve all the resources 
- clean-up the tenancy (all reosurces in tenancy or in a specific compartment)

Run the server
```bash
    #enter in virtualenv
    $ . venv_oci-tools/bin/activate

    (venv_oci-tools) $ python3 oci-tools.py resource-manager 
```

To refer to a specific configuration profile, use

```bash
    (venv_oci-tools) $ python3 oci-tools.py resource-manager --profile <PROFILE_NAME> 
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










