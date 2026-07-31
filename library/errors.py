"""Exceptions raised by the library package.

Every error carries a message that is safe to show straight to the user, so
the CLI can simply print ``str(exc)``.
"""


class LibraryError(Exception):
	"""Base class for every error raised by this package."""


class ValidationError(LibraryError):
	"""Input supplied by the caller is not usable."""


class StorageError(LibraryError):
	"""The catalogue file could not be read or written."""


class BookNotFoundError(LibraryError):
	"""No book in the catalogue matches the given ISBN."""

	def __init__(self, isbn):
		self.isbn = isbn
		super().__init__(f'No book found with ISBN {isbn}.')


class DuplicateISBNError(LibraryError):
	"""A book with the same ISBN is already in the catalogue."""

	def __init__(self, isbn):
		self.isbn = isbn
		super().__init__(f'A book with ISBN {isbn} already exists.')


class AlreadyBorrowedError(LibraryError):
	"""The book is already on loan."""

	def __init__(self, isbn):
		self.isbn = isbn
		super().__init__(f'The book with ISBN {isbn} is already borrowed.')


class NotBorrowedError(LibraryError):
	"""The book is on the shelf, so it cannot be returned."""

	def __init__(self, isbn):
		self.isbn = isbn
		super().__init__(f'The book with ISBN {isbn} is not currently borrowed.')
