from setuptools import setup, find_packages

__version__ = '4.4.0'

if __name__ == '__main__':
    setup(
        name='pdpyras',
        description="PagerDuty REST API client",
        long_description="A basic REST API client for PagerDuty based on Requests' Session class",
        py_modules=['pdpyras'],
        version=__version__,
        license='MIT',
        url='https://pagerduty.github.io/pdpyras',
        download_url='https://pypi.org/project/pdpyras/',
        install_requires=['requests', 'urllib3'],
        author='Demitri Morgan',
        author_email='demitri@pagerduty.com',
        python_requires='>=3.5'
    )
