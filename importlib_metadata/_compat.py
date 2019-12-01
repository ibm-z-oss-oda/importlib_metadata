from __future__ import absolute_import

import io
import abc
import sys
import email


if sys.version_info > (3,):  # pragma: nocover
    import builtins
    from configparser import ConfigParser
    from contextlib import suppress
    FileNotFoundError = builtins.FileNotFoundError
    IsADirectoryError = builtins.IsADirectoryError
    NotADirectoryError = builtins.NotADirectoryError
    PermissionError = builtins.PermissionError
    map = builtins.map
else:  # pragma: nocover
    from backports.configparser import ConfigParser
    from itertools import imap as map  # type: ignore
    from contextlib2 import suppress  # noqa
    FileNotFoundError = IOError, OSError
    IsADirectoryError = IOError, OSError
    NotADirectoryError = IOError, OSError
    PermissionError = IOError, OSError

if sys.version_info > (3, 5):  # pragma: nocover
    import pathlib
else:  # pragma: nocover
    import pathlib2 as pathlib

try:
    ModuleNotFoundError = builtins.FileNotFoundError
except (NameError, AttributeError):  # pragma: nocover
    ModuleNotFoundError = ImportError  # type: ignore


if sys.version_info >= (3,):  # pragma: nocover
    from importlib.abc import MetaPathFinder
else:  # pragma: nocover
    class MetaPathFinder(object):
        __metaclass__ = abc.ABCMeta


__metaclass__ = type
__all__ = [
    'install', 'NullFinder', 'MetaPathFinder', 'ModuleNotFoundError',
    'pathlib', 'ConfigParser', 'map', 'suppress', 'FileNotFoundError',
    'NotADirectoryError', 'email_message_from_string',
    ]


def install(cls):
    """
    Class decorator for installation on sys.meta_path.

    Adds the backport DistributionFinder to sys.meta_path and
    attempts to disable the finder functionality of the stdlib
    DistributionFinder.
    """
    sys.meta_path.append(cls())
    disable_stdlib_finder()
    return cls


def disable_stdlib_finder():
    """
    Give the backport primacy for discovering path-based distributions
    by monkey-patching the stdlib O_O.

    See #91 for more background for rationale on this sketchy
    behavior.
    """
    def matches(finder):
        return (
            finder.__module__ == '_frozen_importlib_external'
            and hasattr(finder, 'find_distributions')
            )
    for finder in filter(matches, sys.meta_path):  # pragma: nocover
        del finder.find_distributions


class NullFinder:
    """
    A "Finder" (aka "MetaClassFinder") that never finds any modules,
    but may find distributions.
    """
    @staticmethod
    def find_spec(*args, **kwargs):
        return None

    # In Python 2, the import system requires finders
    # to have a find_module() method, but this usage
    # is deprecated in Python 3 in favor of find_spec().
    # For the purposes of this finder (i.e. being present
    # on sys.meta_path but having no other import
    # system functionality), the two methods are identical.
    find_module = find_spec


def py2_message_from_string(text):  # nocoverpy3
    # Work around https://bugs.python.org/issue25545 where
    # email.message_from_string cannot handle Unicode on Python 2.
    io_buffer = io.StringIO(text)
    return email.message_from_file(io_buffer)


email_message_from_string = (
    py2_message_from_string
    if sys.version_info < (3,) else
    email.message_from_string
    )

# https://bitbucket.org/pypy/pypy/issues/3021/ioopen-directory-leaks-a-file-descriptor
PYPY_OPEN_BUG = getattr(sys, 'pypy_version_info', (9, 9, 9))[:3] <= (7, 1, 1)


class PyPy_repr:
    """
    Override repr for EntryPoint objects on PyPy2 to avoid __iter__ access.
    Ref #97.
    """
    affected = (
        hasattr(sys, 'pypy_version_info') and
        sys.version_info < (3,)
        )

    def __compat_repr__(self):  # pragma: nocover
        def make_param(name):
            value = getattr(self, name)
            return '{name}={value!r}'.format(**locals())
        params = ', '.join(map(make_param, self._fields))
        return 'EntryPoint({params})'.format(**locals())

    if affected:  # pragma: nocover
        __repr__ = __compat_repr__
    del affected
