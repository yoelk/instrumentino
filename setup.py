#!/usr/bin/env python
import ez_setup
ez_setup.use_setuptools()
from setuptools import setup, find_packages

setup(install_requires = ['wxPython', 'pyserial', 'matplotlib'], #, 'pylab', 'mpl_toolkits'
      packages=find_packages(),
      package_data={'': ['*.png', '*.xrc', '*.dll']},
      zip_safe=True,

      # metadata for upload to PyPI
      name='instrumentino',
      version = '1.0',
      author = 'Joel Koenka',
      author_email = 'yoelk@tx.technion.ac.il',
      description = 'Instrumentino is a GUI framework for instruments based Arduino controllers. Extensions for other controllers exist a well.\n'+
                    'When using Instrumentino for a scientific publication, please cite the release article:\n'+
                    'http://www.sciencedirect.com/science/article/pii/S0010465514002112',
      license = 'GPLv3',
      keywords = 'Instrumentino, Arduino',
      url = 'http://www.chemie.unibas.ch/~hauser/index.html',
      # could also include long_description, download_url, classifiers, etc.
      )