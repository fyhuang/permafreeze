permafreeze
===========

Automatic incremental backup to Amazon Glacier and S3.

Progress
========

At the moment, permafreeze only implements file consistency checking. To install, simply clone this repository and `python setup.py install`. Use the `sample-config.ini` as a base for your own configuration file. If your configuration file is named `config.ini`, run:

    freeze -c config.ini

To hash all the files in your targets. Use:

    freeze -c config.ini check

To check the consistency of all unmodified files in your targets.

Targets
=======
