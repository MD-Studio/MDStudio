from setuptools import setup

setup(
    name='MDStudio',
    version='0.1.0',
    description='',
    license='Apache-2.0',
    url='https://github.com/MD-Studio/MDStudio',
    author=['Marc van dijk', 'Paul Visscher',  'Felipe Zapata'],
    author_email='m4.van.dijkatvu.nl',
    keywords='biochemistry docking molecular-dynamics toxicology',
    packages=[],
    classifiers=[
        'development status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: Apache Software License'
        'programming language :: python',
        'Topic :: Scientific/Engineering :: Bio-Informatics'
    ],
    install_requires=[],
    extras_require={'test': ['nose', 'coverage']},
    scripts=[]
)
