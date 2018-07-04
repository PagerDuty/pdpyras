from setuptools import setup, find_packages
from pdpyras import __version__

setup(
    name='pdpyras',
    description="A REST API client for PagerDuty based on Requests' Session",
    py_modules=['pdpyras'],
    version=__version__,
    license='MIT',
    url='https://github.com/PagerDuty/python-rest-sessions',
    download_url='https://github.com/PagerDuty/python-rest-sessions/archive/master.tar.gz',
    install_requires=['requests', 'urllib3']
)

