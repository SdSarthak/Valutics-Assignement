"""Library Management System.

A small catalogue manager for a personal or classroom library: add books,
search them, lend them out for a fixed loan period and track overdue returns.

The package is deliberately split so the rules can be tested without a
terminal attached:

* :mod:`library.models`  - the :class:`~library.models.Book` record and the
  loan arithmetic (due dates, overdue days).
* :mod:`library.storage` - reading and writing the JSON catalogue on disk.
* :mod:`library.manager` - catalogue operations, raising errors instead of
  printing them.
* :mod:`library.cli`     - the interactive menu, the only layer that does I/O.
"""

from library.errors import (
	AlreadyBorrowedError,
	BookNotFoundError,
	DuplicateISBNError,
	LibraryError,
	NotBorrowedError,
	StorageError,
	ValidationError,
)
from library.manager import LibraryManager
from library.models import Book
from library.storage import JsonBookStorage, MemoryBookStorage

__version__ = '1.0.0'

__all__ = [
	'AlreadyBorrowedError',
	'Book',
	'BookNotFoundError',
	'DuplicateISBNError',
	'JsonBookStorage',
	'LibraryError',
	'LibraryManager',
	'MemoryBookStorage',
	'NotBorrowedError',
	'StorageError',
	'ValidationError',
	'__version__',
]
