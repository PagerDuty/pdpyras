from setuptools import setup

__version__ = '5.3.0'

if __name__ == '__main__':
    setup(
        name='pdpyras',
        description="PagerDuty Python REST API Sessions",
        long_description="A basic REST API client for PagerDuty based on Requests' Session class",
        py_modules=['pdpyras'],
        version=__version__,
        license='MIT',
        url='https://pagerduty.github.io/pdpyras',
        download_url='https://pypi.org/project/pdpyras/',
        install_requires=['requests', 'urllib3'],
        author='PagerDuty',
        author_email='support@pagerduty.com',
        python_requires='>=3.6'
    )
