Configuration File
==================

This README describes the configuration file format used by permafreeze. Look at `sample-config.ini` (included with the source distribution) for a barebones configuration file. The configuration file uses a standard .ini file format, with the following sections and options:

# options

`site-name`: name the collection of files you are archiving. Typically the hostname of the computer or some variant.

`s3-bucket-name`: the Amazon S3 bucket where archived trees will be stored.

`glacier-vault-name`: the Glacier vault where data will be stored.

`dont-archive`: (boolean [f]) if true, don't store any data, but hash files and store a tree (for consistency checking).

`ignore-dotfiles`: (boolean [f]) if true, ignore any files and directories starting with a period (`.`).

`ignore-config`: (boolean [t]) if true, ignore permafreeze's own configuration files (e.g. if you freeze your home directory).

# targets

In this section, list your targets and their filesystem paths as key-value pairs. For example:

~~~
myfiles=/path/to/files
music=/home/user/Music
~~~

Defines two targets: one called `myfiles` (whose root path on the filesystem is `/path/to/files`), and the other called `music` (with filesystem path `/home/user/Music`).

# Target sections

For each target you define in the `targets` section above, you can optionally add a separate target section for it. For example, a target section for the `music` target looks like:

~~~
[music]
; Paths are relative to root, so the following
; excludes /home/user/Music/iTunes
exclude-paths=/iTunes
~~~

`exclude-paths`: don't archive or check these paths. Paths are relative to the root of the *target*.

# auth

`accessKeyId`: Amazon access key ID

`secretAccessKey`: Amazon secret access key