# OCI Tools

## Introduction

Python Tenancy Manager

## Installation

* Setup a virtualenv and install the dependencies.

```bash
    $ git clone https://github.com/snafuz/oci-tools.git
    $ cd oci-tools

    $ pip install virtualenv
    $ virtualenv venv_oci-tools
    $ . venv_oci-tools/bin/activate

    (venv_oci-tools) $ pip install -r requirements.txt

```

* Prepare configuration file:

```bash
    cd config
    cp config_template config
```

## Usage

#### Training toolkit

Training toolkit 
- scan the tenancy and retrieve all the resources 
- clean-up the tenancy (all reosurces in tenancy or in a specific compartment)

Run the server
```bash
    #enter in virtual env
    $ . venv_oci-tools/bin/activate

    (venv_oci-tools) $ python oci-tools.py 
```










