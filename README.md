# libmorse

Convert timed signals into alphabet.


## Installation

For this project, we're gonna use Python 2 version.

#### Install Python interpreter and pip:

*Linux*

```bash
$ sudo apt update && sudo apt install --upgrade python python-dev python-setuptools
$ sudo -H easy_install -U pip
```

*Windows*
- download and install desired version from here: https://www.python.org/downloads/
- download and run get-pip script: https://pip.pypa.io/en/stable/installing/

Make sure that you're using the correct version of pip, by running
`pip --version`. It should use the Python 2 version, if not, try with *pip2*.

#### Clone repository and install package:

```bash
$ https://github.com/cmin764/libmorse.git
$ cd libmorse
$ sudo -H ./setup.sh    # setup.bat on Windows
```


## Usage

#### Run CLI and explore the library commands:

*Linux*

```bash
$ libmorse --help
```

If you have trouble with file permissions (libmorse.log), don't forget to
remove them with `sudo` first. Or simply run `git clean -fdx` to clean-up the
project directory.

*Windows*

```bat
> python bin\libmorse --help
```

#### Within CLI:

*Windows*

*\<test GUI coming soon\>*

*Linux*

Same commands, just directly execute the `libmorse` script without the need to
supply paths, like in the top example above.

#### Within module:

You can also import **libmorse** as a normal python module/library and use it
accordingly in your Python scripts/projects.

*\<details coming soon\>*


## Development

If you want to develop **libmorse**, do the following:

#### Optionally install virtualenv:

*Linux*

```bash
$ sudo -H pip install -U virtualenv virtualenvwrapper
$ echo "export WORKON_HOME=~/Envs" >>~/.bashrc
$ source ~/.bashrc
$ mkdir -p $WORKON_HOME
$ echo "source /usr/local/bin/virtualenvwrapper.sh" >>~/.bashrc
$ source ~/.bashrc
$ mkvirtualenv morseus
```

*Windows*

Make sure that you have added your Python *Scripts* path to the system
path already (https://www.howtogeek.com/118594/how-to-edit-your-system-path-for-easy-command-line-access/).
The path you need to add is usually: `C:\Python27\Scripts`.

Now install the necessary pip packages and create your first virtual environment.

```bat
> pip install -U virtualenv virtualenvwrapper virtualenvwrapper-win
> mkvirtualenv morseus
```

Use `workon morseus` command to activate the virtual environment every time you
want to work through it and `deactivate` for leaving it.

#### Install requirements, develop and test:

Don't forget to uninstall the package first (if installed):

```bash
$ pip uninstall libmorse
```

Then:

```bash
$ pip install -Ur requirements/develop.txt
$ python setup.py develop
$ python setup.py test
```

Don't forget to run with `sudo -H` if you're working outside the virtualenv.

#### Run tests, create and serve documentation:

```bash
$ nosetests
$ cd doc && make html
$ cd build/html && python -m SimpleHTTPServer
```

Enter http://localhost:8000 to view documentation.

----

* Homepage: https://cosminpoieana.wordpress.com/
* Documentation: https://libmorse.readthedocs.io/
* Source: https://github.com/cmin764/libmorse.git
* License: MIT
* Authors:
    + Cosmin Poieana <cmin764@gmail.com>
