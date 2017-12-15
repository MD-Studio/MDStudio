from setuptools import setup, find_packages

distribution_name = 'lie_echo'
setup(
    name=distribution_name,
    version='1.0.0',
    license='Apache Software License 2.0',
    description='Echo example component for the MDStudio application',
    author='Paul Visscher - Zefiros Software (www.zefiros.eu)',
    author_email='contact@zefiros.eu',
    url='https://github.com/MD-Studio/MDStudio',
    keywords='MDStudio Echo example',
    platforms=['Any'],
    packages=find_packages(),
    py_modules=[distribution_name],
    install_requires=[],
    test_suite="tests",
    include_package_data=True,
    zip_safe=True,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Topic :: Database',
        'Operating System :: OS Independent',
        'Intended Audience :: Science/Research',
    ],
)
