"""Catalogue operations.

The manager owns the in-memory list of books and keeps the storage backend in
step with it. Nothing in this module prints: every failure is raised as a
:class:`~library.errors.LibraryError` so the caller decides how to report it.
"""

from collections import namedtuple

from library.config import DEFAULT_LOAN_DAYS, data_file_path
from library.errors import (
	AlreadyBorrowedError,
	BookNotFoundError,
	DuplicateISBNError,
	NotBorrowedError,
	ValidationError,
)
from library.models import SEARCH_FIELDS, Book, parse_date, today
from library.storage import JsonBookStorage

#: Result of :meth:`LibraryManager.return_book`.
ReturnReceipt = namedtuple('ReturnReceipt', 'book due_date days_overdue')


def _normalise_isbn(isbn):
	text = '' if isbn is None else str(isbn).strip()
	if not text:
		raise ValidationError('ISBN cannot be empty.')
	return text


class LibraryManager:
	"""Add, search, lend and take back books.

	Args:
		storage: Any object exposing ``load``/``save``/``location``. Defaults
			to a :class:`~library.storage.JsonBookStorage` at the configured
			catalogue path.
		loan_days: Length of the loan period in days.
	"""

	def __init__(self, storage=None, loan_days=DEFAULT_LOAN_DAYS):
		if loan_days <= 0:
			raise ValidationError(f'Loan period must be at least one day, got {loan_days}.')
		self.storage = JsonBookStorage(data_file_path()) if storage is None else storage
		self.loan_days = loan_days
		self.books = self.storage.load()

	# -- catalogue ---------------------------------------------------------

	def __len__(self):
		return len(self.books)

	def __iter__(self):
		return iter(self.books)

	def save(self):
		"""Persist the current catalogue."""
		self.storage.save(self.books)

	def reload(self):
		"""Discard the in-memory catalogue and read it back from storage."""
		self.books = self.storage.load()
		return self.books

	def find_book(self, isbn):
		"""Return the book with this ISBN, or ``None``."""
		isbn = _normalise_isbn(isbn)
		for book in self.books:
			if book.isbn == isbn:
				return book
		return None

	def get_book(self, isbn):
		"""Return the book with this ISBN.

		Raises:
			BookNotFoundError: if no book matches.
		"""
		book = self.find_book(isbn)
		if book is None:
			raise BookNotFoundError(_normalise_isbn(isbn))
		return book

	def add_book(self, title, author, year, isbn):
		"""Add a book and save the catalogue.

		Raises:
			ValidationError: if any field is empty or the year is not a number.
			DuplicateISBNError: if the ISBN is already in the catalogue.
		"""
		book = Book(title, author, year, isbn)
		if self.find_book(book.isbn) is not None:
			raise DuplicateISBNError(book.isbn)
		self.books.append(book)
		self.save()
		return book

	def remove_book(self, isbn):
		"""Remove a book from the catalogue and save.

		Raises:
			BookNotFoundError: if no book matches the ISBN.
		"""
		book = self.get_book(isbn)
		self.books.remove(book)
		self.save()
		return book

	def search_books(self, keyword, field):
		"""Return every book whose ``field`` contains ``keyword``.

		The match is case-insensitive and matches on substrings, so searching
		authors for ``orw`` finds ``Orwell``.

		Raises:
			ValidationError: if the field is unknown or the keyword is empty.
		"""
		if field not in SEARCH_FIELDS:
			raise ValidationError(
				f"Cannot search by {field!r}; choose one of {', '.join(SEARCH_FIELDS)}."
			)
		keyword = '' if keyword is None else str(keyword).strip()
		if not keyword:
			raise ValidationError('Search keyword cannot be empty.')
		return [book for book in self.books if book.matches(keyword, field)]

	# -- lending -----------------------------------------------------------

	def borrow_book(self, isbn, current_date=None):
		"""Lend a book out and save the catalogue.

		Returns:
			Book: the borrowed book, whose ``due_date(loan_days)`` is the date
			it must come back.

		Raises:
			BookNotFoundError: if no book matches the ISBN.
			AlreadyBorrowedError: if the book is already on loan.
		"""
		book = self.get_book(isbn)
		if book.borrowed:
			raise AlreadyBorrowedError(book.isbn)
		book.borrow(parse_date(current_date) or today())
		self.save()
		return book

	def return_book(self, isbn, current_date=None):
		"""Take a book back and save the catalogue.

		Returns:
			ReturnReceipt: the book, the date it was due and how many days
			late it was (``0`` when it came back on time).

		Raises:
			BookNotFoundError: if no book matches the ISBN.
			NotBorrowedError: if the book is not on loan.
		"""
		book = self.get_book(isbn)
		if not book.borrowed:
			raise NotBorrowedError(book.isbn)
		current_date = parse_date(current_date) or today()
		due_date = book.due_date(self.loan_days)
		days_overdue = book.days_overdue(current_date, self.loan_days)
		book.give_back()
		self.save()
		return ReturnReceipt(book, due_date, days_overdue)

	def due_date_for(self, book):
		"""Return the due date of a borrowed book under this loan period."""
		return book.due_date(self.loan_days)

	# -- views -------------------------------------------------------------

	def available_books(self):
		"""Books currently on the shelf."""
		return [book for book in self.books if not book.borrowed]

	def borrowed_books(self):
		"""Books currently on loan."""
		return [book for book in self.books if book.borrowed]

	def overdue_books(self, current_date=None):
		"""Borrowed books whose loan period has elapsed, most overdue first."""
		current_date = parse_date(current_date) or today()
		overdue = [
			book for book in self.books if book.is_overdue(current_date, self.loan_days)
		]
		overdue.sort(
			key=lambda book: book.days_overdue(current_date, self.loan_days), reverse=True
		)
		return overdue

	def summary(self, current_date=None):
		"""Return catalogue counts: total, available, borrowed and overdue."""
		current_date = parse_date(current_date) or today()
		return {
			'total': len(self.books),
			'available': len(self.available_books()),
			'borrowed': len(self.borrowed_books()),
			'overdue': len(self.overdue_books(current_date)),
		}
