"""
A setuptools based setup module.
"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()

# Get the long description from the README file
#long_description = (here / 'README.md').read_text(encoding='utf-8')

# Arguments marked as "Required" below must be included for upload to PyPI.
# Fields marked as "Optional" may be commented out.

setup(

    name='flakyreporter', 
    version='1.0.0', 
    description='Automatically detect Randomness in flaky pytest functions', 
    url='https://github.com/JesperMjornman/FlakyReporter',  
    author='D. Mastell & J. Mjörnman',  # Optional
    author_email='jesmj855@student.liu.se',  # Optional
    classifiers=[
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 4 - Beta',

        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',

        'License :: OSI Approved :: MIT License',

        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3 :: Only',
    ],
    keywords='sample, setuptools, development',  
    package_dir={'': 'src'}, 
    packages=find_packages(where='src'), 
    python_requires='>=3.6, <4',
    setup_requires=['wheel'],
    install_requires=['pytest', 'py-cpuinfo', 'pytest-cov', 'numpy'],
    
    package_data={  
        'flakyreporter': ['keywords.dat'],
    },
    include_package_data=True,

    entry_points={  
        'console_scripts': [
            'flakyreporter=flakyreporter:main',
        ],
    },

    #project_urls={ 
    #    'Bug Reports': 'https://github.com/pypa/sampleproject/issues',
    #    'Funding': 'https://donate.pypi.org',
    #    'Say Thanks!': 'http://saythanks.io/to/example',
    #    'Source': 'https://github.com/pypa/sampleproject/',
    #},
)
