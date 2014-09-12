from setuptools import setup

setup(name = 'astron', version = '0.0', license = 'BSD',
      description = 'A Python implementation of the application-side of the Astron protocol.',
      url = 'http://github.com/Astron/astron.libpython',
      packages = ['astron'],
      install_requires = ['bamboo'],
      platforms = 'any',
      classifiers = [
        'Programming Language :: Python',
        'Development Status :: 2 - Pre-Alpha',
        'Natural Language :: English',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries :: Python Modules',
      ])
