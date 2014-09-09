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
      version = '1.03',
      author = 'Joel Koenka',
      author_email = 'yoelk@tx.technion.ac.il',
      description = 'Instrumentino is an open-source modular graphical user interface framework for controlling Arduino based experimental instruments.\n'+
                    'It expands the control capability of Arduino by allowing instruments builders to easily create a custom user interface program running on an attached personal computer.\n'+
                    'It enables the definition of operation sequences and their automated running without user intervention.\n'+
                    'Acquired experimental data and a usage log are automatically saved on the computer for further processing.\n'+
                    'Complex devices, which are difficult to control using an Arduino, may be integrated as well by incorporating third party application programming interfaces (APIs) into the Instrumentino framework.'+
                    '\n'
                    'When using Instrumentino for a scientific publication, please cite the release article:\n'+
                    'http://www.sciencedirect.com/science/article/pii/S0010465514002112'+
                    'Get the code at: https://github.com/yoelk/instrumentino',
      license = 'GPLv3',
      keywords = 'Instrumentino, Arduino',
      url = 'http://www.chemie.unibas.ch/~hauser/open-source-lab/instrumentino/index.html',
      # could also include long_description, download_url, classifiers, etc.
      )