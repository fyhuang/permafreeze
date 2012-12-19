permafreeze
===========

Automatic incremental backup to Amazon Glacier and S3.

Usage
=====

To install, simply clone this repository and `python setup.py install`. Permafreeze reads the configuration file from `~/.config/permafreeze/config.ini`; use the `sample-config.ini` as a starting point for your own configuration file. If you would like to use a different config file, pass the `-c` switch (e.g. `freeze -c ./myconfig.ini`).

At the moment, permafreeze only supports two operations:

* Performing consistency checking on files
* Backing up data to S3 and Glacier

### Consistency checking

Generate a tree (containing hashes of all your files) using the `freeze` command with `-H` switch:

    freeze -H
    # the default action is 'freeze':
    freeze -H freeze

At a later time, you can check the consistency of all your files with the command:

    freeze check

Currently, to prevent excessive warnings, permafreeze will not try to check a file which has a newer modified timestamp than the one stored in the tree. This makes consistency checking mainly useful for guarding against hardware failures.

### Backing up data

Simply type:

    freeze

permafreeze will automatically scan all your targets (see Configuration File) and backup any files which have been changed since the most recent backup. The resulting tree will be stored to S3, and the actual file data will be stored in Amazon Glacier.

Requirements
============

Currently:

* Python 2.7
* Boto 2.6.0-dev or higher (2.6.0 stable doesn't have full Glacier support)
* An Amazon AWS account

Configuration File
==================

Permafreeze determines which of your local files to backup by reading the configuration file. A barebones sample configuration file can be found in `sample-config.ini`. The various options and their values are described in `README-CONFIG.md`.
