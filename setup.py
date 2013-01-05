from setuptools import setup, Extension

hasher_module = Extension('libpf',
        sources=[
            'libpf/hasher.cpp',
            'libpf/snappyfd.cpp',
            'libpf/crc32c.c',
            'blake/blake512.c',
        ],

        libraries=[
            'snappy',
        ],
        
        extra_compile_args=[],
        )

setup(name='permafreeze',
      version='0.1',
      description='Automatic incremental backup to Amazon Glacier and S3',
      author='Yifeng Huang',
      author_email='me@nongraphical.com',
      url='https://github.com/fyhuang/permafreeze',

      packages=['permafreeze'],
      entry_points={
          'console_scripts': [
              'freeze = permafreeze:main',
              ],
          },

      install_requires=[
          'boto',
          ],

      ext_modules=[hasher_module],
      )
