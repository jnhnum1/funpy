"""
FunPy is an implementation of FUNctional programming features in the Python
Programming Language, using the MacroPy language.
"""

from distutils.core import setup
import setuptools

setup(name='FunPy',
      version='0.1.0',
      description='Functional Programming for Python: Algebraic Data Types, Pattern Matching, Tail Call Optimization, and more!',
      long_description=__doc__,
      license='BSD',
      author='Justin Holmgren, Li Haoyi',
      author_email='justin.holmgren@gmail.com, haoyi.sg@gmail.com',
      url='https://github.com/jnhnum1/funpy',
      packages=['funpy', 'funpy.adt', 'funpy.pattern', 'funpy.tco', 'funpy.tests'],
      install_requires=['macropy'],
      classifiers=['Programming Language :: Python :: 2.7']
     )
