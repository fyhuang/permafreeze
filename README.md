permafreeze
===========

Automatic incremental backup to Amazon Glacier and S3.

Usage
=====

At the moment, permafreeze only implements file consistency checking. To install, simply clone this repository and `python setup.py install`. Use the `sample-config.ini` as a base for your own configuration file. If your configuration file is named `config.ini`, run:

    freeze -c config.ini

To hash all the files in your targets. Use:

    freeze -c config.ini check

To check the consistency of all unmodified files in your targets.

Configuration File
==================

A barebones sample configuration file can be found in `sample-config.ini`. The various options and their values are described in `README-CONFIG.md`.
