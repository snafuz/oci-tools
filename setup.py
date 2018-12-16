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
    #packages=find_packages(),
    install_requires=[
    ],
    scripts=['oci-tools.py']
)
