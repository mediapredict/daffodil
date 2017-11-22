from distutils.core import setup

cython_installed = False
try:
    import Cython
    cython_installed = True
except ImportError:
    pass

extra_kwargs = {}

if cython_installed:
    from Cython.Build import cythonize
    import Cython.Compiler.Options

    Cython.Compiler.Options.cimport_from_pyx = True

    # TODO: in the future distribute c sources instead of pyx files
    #   https://stackoverflow.com/questions/4505747/how-should-i-structure-a-python-package-that-contains-cython-code
    extra_kwargs['ext_modules'] = cythonize(
        'daffodil/*.pyx',
        compiler_directives={
            'language_level': "3",

            # controls extensions which allow cprofile to see cython functions but
            # has a small performance penalty
            'profile': False,
        }
    )


setup(
    name='daffodil',
    version='0.5.4',
    author='James Robert',
    description='A Super-simple DSL for filtering datasets',
    license='MIT',
    keywords='data filtering',
    url='https://github.com/mediapredict/daffodil',
    packages=['daffodil'],
    install_requires=['cython'],
    long_description='A Super-simple DSL for filtering datasets',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Topic :: Utilities'
    ],
    **extra_kwargs
)
