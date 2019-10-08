# -*- coding: utf-8 -*-
# taken from requests library: https://github.com/kennethreitz/requests
import sys

# -------
# Pythons
# -------

# Syntax sugar.
_ver = sys.version_info

#: Python 2.x?
is_py2 = (_ver[0] == 2)

#: Python 3.x?
is_py3 = (_ver[0] == 3)

#: Python 3.0.x
is_py30 = (is_py3 and _ver[1] == 0)

#: Python 3.1.x
is_py31 = (is_py3 and _ver[1] == 1)

#: Python 3.2.x
is_py32 = (is_py3 and _ver[1] == 2)

#: Python 3.3.x
is_py33 = (is_py3 and _ver[1] == 3)

#: Python 3.4.x
is_py34 = (is_py3 and _ver[1] == 4)

#: Python 2.7.x
is_py27 = (is_py2 and _ver[1] == 7)

#: Python 2.6.x
is_py26 = (is_py2 and _ver[1] == 6)

#: Python 2.5.x
is_py25 = (is_py2 and _ver[1] == 5)

# ---------
# Platforms
# ---------
# Syntax sugar.
_ver = sys.version.lower()

is_pypy = ('pypy' in _ver)
is_jython = ('jython' in _ver)
is_ironpython = ('iron' in _ver)

# Assume CPython, if nothing else.
is_cpython = not any((is_pypy, is_jython, is_ironpython))

# Windows-based system.
is_windows = 'win32' in str(sys.platform).lower()

# Standard Linux 2+ system.
is_linux = ('linux' in str(sys.platform).lower())
is_osx = ('darwin' in str(sys.platform).lower())
is_hpux = ('hpux' in str(sys.platform).lower())   # Complete guess.
is_solaris = ('solar==' in str(sys.platform).lower())   # Complete guess.


# ---------
# Specifics
# ---------
if is_py2:
    import thread
    bytes = str
    str = unicode
    basestring = basestring

elif is_py3:
    import _thread as thread
    str = str
    bytes = bytes
    basestring = (str, bytes)

