from setuptools import setup

setup(
    name='tiny-eda',
    version='0.1.0',
    description='Very tiny and fast framework for building event driven microservices',
    url='https://github.com/CthUlhUzzz/tiny-eda',
    author='CthUlhUzzz',
    license='LGPL v3',
    keywords='framework eda microservice',
    packages=['tiny_eda',
              'tiny_eda.brokers'],
    install_requires=['aioredis'],
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Internet',
        'Topic :: Framework',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6']
)
