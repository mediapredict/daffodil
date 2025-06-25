import sys, importlib
sys.path.append('/usr/lib/python3/dist-packages')
sys.modules['distutils'] = importlib.import_module('setuptools._distutils')
from setuptools import setup, Extension
from Cython.Build import cythonize

exts_c = [
    Extension('daffodil.predicate', ['daffodil/predicate.c']),
    Extension('daffodil.hstore_predicate', ['daffodil/hstore_predicate.c']),
    Extension('daffodil.key_expectation_delegate', ['daffodil/key_expectation_delegate.c']),
    Extension('daffodil.simulation_delegate', ['daffodil/simulation_delegate.c']),
    Extension('daffodil.exceptions', ['daffodil/exceptions.c']),
    Extension('daffodil.pretty_print', ['daffodil/pretty_print.c']),
    Extension('daffodil.parser', ['daffodil/parser.c']),
]

cy_exts = cythonize([Extension('daffodil.elasticsearch_predicate', ['daffodil/elasticsearch_predicate.pyx'])], language_level=3)

setup(name='daffodil_local', ext_modules=exts_c + cy_exts)
