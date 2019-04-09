from distutils.core import setup
import oci_tools
setup(
    name='oci-tools',
    version=oci_tools.__version__,
    packages=['oci-tools'],
    url='',
    license=oci_tools.__license__,
    author=oci_tools.__author__,
    author_email=oci_tools.__email__,
    description=oci_tools.__description__,
    # packages=find_packages(),
    install_requires=[
        'asn1crypto>=0.24.0'
        'certifi>=2019.3.9'
        'cffi>=1.12.2'
        'configparser>=3.7.4'
        'cryptography>=2.6.1'
        'entrypoints>=0.3'
        'idna>=2.8'
        'mccabe>=0.6.1'
        'oci>=2.2.5'
        'pycodestyle>=2.5.0'
        'pycparser>=2.19'
        'pyflakes>=2.1.1'
        'pyOpenSSL>=19.0.0'
        'python-dateutil>=2.8.0'
        'pytz>=2018.9'
        'rope>=0.14.0'
        'six>=1.12.0'
    ],
    scripts=['oci-tools.py']
)
