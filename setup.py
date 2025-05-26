from setuptools import setup
from Cython.Build import cythonize
import Cython.Compiler.Options

Cython.Compiler.Options.cimport_from_pyx = True

extra_kwargs = {
    "ext_modules": cythonize(
        "daffodil/*.pyx",
        compiler_directives={
            "language_level": "3",

            # controls extensions which allow cprofile to see cython functions but
            # has a small performance penalty
            "profile": False,
        }
    )
}

# The setup() call itself becomes much simpler!
# It will automatically read name, version, etc. from pyproject.toml's [project] table.
setup(
    packages=["daffodil"], # Still need to tell it where your package code is
    # You might also need this if your project is not in a 'src' layout
    # package_dir={'': '.'}, # If daffodil/ is directly in root
    **extra_kwargs
)