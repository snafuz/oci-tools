### Run OCI Resource Manager script on Oracle Linux 7 OCI instance

````bash
$ sudo yum install -y oracle-epel-release-el7
$ sudo yum install -y git python36

$ wget https://bootstrap.pypa.io/get-pip.py
$ sudo -H python36 ./get-pip.py
$ sudo -H /usr/local/bin/pip3 install virtualenv

$ virtualenv venv_oci-tools
$ . venv_oci-tools/bin/activate
(venv_oci-tools)$ pip3 install -r requirements.txt
(venv_oci-tools)$ python3 oci-tools.py training
````