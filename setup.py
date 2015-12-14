from setuptools import setup

setup(
    name='daffodil',
    version='0.3.6',
    author='James Robert',
    description='A Super-simple DSL for filtering datasets',
    license='MIT',
    keywords='data filtering',
    url='https://github.com/mediapredict/daffodil',
    packages=['daffodil'],
    install_requires=[
        "parsimonious",
    ],
    long_description='A Super-simple DSL for filtering datasets',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Topic :: Utilities'
    ]
)
