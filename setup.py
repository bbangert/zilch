__version__ = '0.1.3'

import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
CHANGES = open(os.path.join(here, 'CHANGES.rst')).read()

setup(name='zilch',
      version=__version__,
      description='Error/Exception collector and reporter',
      long_description=README + '\n\n' +  CHANGES,
      classifiers=[
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        ],
      keywords='zeromq exceptions errors reporter collector sqlalchemy',
      author="Ben Bangert",
      author_email="ben@groovie.org",
      url="https://github.com/bbangert/zilch",
      license="MIT",
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      tests_require = ['pkginfo', 'Mock>=0.7', 'nose', 'SQLAlchemy>=0.7'],
      install_requires=[
          "simplejson>=2.1", "weberror>=0.10.3",
      ],
      entry_points="""
      [console_scripts]
      zilch-recorder = zilch.script:zilch_recorder
      zilch-web = zilch.script:zilch_web
      
      [paste.filter_app_factory]
      middleware = zilch.middleware:make_error_middleware
      """
)
