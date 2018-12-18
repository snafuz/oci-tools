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
        'asn1crypto>=0.24.0',
        'certifi>=2018.11.29',
        'cffi>=1.11.5',
        'configparser>=3.5.0',
        'cryptography>=2.4.2',
        'idna==2.8',
        'oci>=2.1.2',
        'pycparser>=2.19',
        'pyOpenSSL>=17.4.0',
        'python-dateutil>=2.7.3',
        'pytz>=2018.7',
        'rope>=0.11.0',
        'six>=1.12.0',
    ],
    scripts=['oci-tools.py']
)
