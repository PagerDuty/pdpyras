from setuptools import setup, find_packages
from pdpyras import __version__

setup(
    name='pdpyras',
    description="PagerDuty REST API client",
    long_description="A basic REST API client for PagerDuty based on Requests' Session class",
    py_modules=['pdpyras'],
    version=__version__,
    license='MIT',
    url='https://github.com/PagerDuty/pdpyras',
    download_url='https://github.com/PagerDuty/pdpyras/archive/master.tar.gz',
    install_requires=['requests', 'urllib3'],
    author='Demitri Morgan',
    author_email='demitri@pagerduty.com',
    python_requires='>=2.7.10, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*'
)

