__version__ = '0.1'

import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
CHANGES = open(os.path.join(here, 'CHANGES.rst')).read()

setup(name='zilch',
      version=__version__,
      description='ZeroMQ-based reporting and collector',
      long_description=README + '\n\n' +  CHANGES,
      classifiers=[
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        ],
      keywords='zeromq exceptions errors reporter collector',
      author="Ben Bangert",
      author_email="ben@groovie.org",
      url="",
      license="MIT",
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      tests_require = ['pkginfo', 'Mock>=0.7', 'nose'],
      install_requires=[
          "pyzmq>=2.1",
          "simplejson>=2.1",
          "cmdln>=1.1.2",
      ],
      entry_points="""
      [console_scripts]
      zilch-collector = zilch.script:main
      """
)
