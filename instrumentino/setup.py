#!/usr/bin/env python
import ez_setup
ez_setup.use_setuptools()
from setuptools import setup, find_packages

setup(install_requires = ['wxPython', 'pyserial', 'matplotlib', 'numpy'],
      packages=find_packages(),
      package_data={'': ['*.png', '*.xrc', '*.dll']},
      zip_safe=True,

      # metadata for upload to PyPI
      name='instrumentino',
      version = '1.08',
      author = 'Joel Koenka',
      author_email = 'yoelk@tx.technion.ac.il',
      description = 'Open-source modular GUI framework for controlling Arduino based instruments',
      long_description = 
'''
Instrumentino is an open-source modular graphical user interface framework for controlling Arduino based experimental instruments.
It expands the control capability of Arduino by allowing instruments builders to easily create a custom user interface program running on an attached personal computer.It enables the definition of operation sequences and their automated running without user intervention.

Acquired experimental data and a usage log are automatically saved on the computer for further processing.

Complex devices, which are difficult to control using an Arduino, may be integrated as well by incorporating third party application programming interfaces (APIs) into the Instrumentino framework.

It consists of two separate programs:

  * *instrumentino*: which is run on a PC and provides the graphical user interface.

  * *controlino*:    which is the program running on the Arduino controller itself, and is used to communicate with instrumentino.
    
    Get it at: https://github.com/yoelk/Instrumentino/blob/master/controlino/controlino.cpp
    
    On the top of the controlino sketch, there are define statements to adjust it to different Arduino boards. **Please make sure you set them correctly**.

The official Instrumentino website is:
http://www.chemie.unibas.ch/~hauser/open-source-lab/instrumentino/index.html

Get the code at: https://github.com/yoelk/instrumentino

We are looking forward for contributors.
There is lots of potential for Instrumentino to grow!

Please contact me if you want to add features and make Instrumentino better.
yoelk_at_tx.technion.ac.il

When using Instrumentino for a scientific publication, please cite the release article:

http://www.sciencedirect.com/science/article/pii/S0010465514002112
''',
      license = 'GPLv3',
      keywords = 'Instrumentino, Arduino',
      url = 'http://www.chemie.unibas.ch/~hauser/open-source-lab/instrumentino/index.html',
      # could also include long_description, download_url, classifiers, etc.
      ) 