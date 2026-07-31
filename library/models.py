"""The :class:`Book` record and the loan arithmetic that goes with it.

All date handling lives here so that due dates and overdue counts are computed
in exactly one place. Every method that needs "today" takes it as an argument,
which keeps the behaviour deterministic and testable.
"""

import datetime

from library.config import DATE_FORMAT, DEFAULT_LOAN_DAYS
from library.errors import ValidationError

#: Fields a catalogue search may be run against.
SEARCH_FIELDS = ('title', 'author', 'year', 'isbn')


def parse_date(value):
	"""Parse a ``YYYY-MM-DD`` string into a :class:`datetime.date`.

	``None`` and empty strings map to ``None``; :class:`datetime.date` and
	:class:`datetime.datetime` values are passed through.

	Raises:
		ValidationError: if the string is not a valid date.
	"""
	if value is None or value == '':
		return None
	if isinstance(value, datetime.datetime):
		return value.date()
	if isinstance(value, datetime.date):
		return value
	if not isinstance(value, str):
		raise ValidationError(f'Expected a date string, got {value!r}.')
	try:
		return datetime.datetime.strptime(value.strip(), DATE_FORMAT).date()
	except ValueError:
		raise ValidationError(
			f'Invalid date {value!r}; expected the format YYYY-MM-DD.'
		) from None


def format_date(value):
	"""Render a date as ``YYYY-MM-DD``, or ``None`` if there is no date."""
	if value is None:
		return None
	return value.strftime(DATE_FORMAT)


def today():
	"""Return the current local date. Wrapped so tests can pass their own."""
	return datetime.date.today()


def _clean_text(value, field):
	if value is None:
		raise ValidationError(f'{field.title()} cannot be empty.')
	text = str(value).strip()
	if not text:
		raise ValidationError(f'{field.title()} cannot be empty.')
	return text


def _clean_year(value):
	if isinstance(value, bool):
		raise ValidationError('Year must be a whole number.')
	if isinstance(value, int):
		year = value
	else:
		text = str(value).strip()
		if not text:
			raise ValidationError('Year cannot be empty.')
		try:
			year = int(text)
		except ValueError:
			raise ValidationError(f'Year must be a whole number, got {value!r}.') from None
	if year <= 0:
		raise ValidationError(f'Year must be greater than zero, got {year}.')
	return year


class Book:
	"""A single catalogue entry.

	Args:
		title: Book title, must be non-empty.
		author: Author name, must be non-empty.
		year: Publication year, a positive whole number.
		isbn: Catalogue identifier, must be non-empty and unique per library.
		borrowed_date: Date the book left the shelf, or ``None``.
		borrowed: Whether the book is currently on loan.
	"""

	__slots__ = ('title', 'author', 'year', 'isbn', 'borrowed', 'borrowed_date')

	def __init__(self, title, author, year, isbn, borrowed_date=None, borrowed=False):
		self.title = _clean_text(title, 'title')
		self.author = _clean_text(author, 'author')
		self.year = _clean_year(year)
		self.isbn = _clean_text(isbn, 'isbn')
		self.borrowed = bool(borrowed)
		borrowed_date = parse_date(borrowed_date)
		# A book that is on the shelf never keeps a loan date, which keeps the
		# saved catalogue from drifting into a contradictory state.
		self.borrowed_date = borrowed_date if self.borrowed else None

	def to_dict(self):
		"""Return the JSON-serialisable form written to the catalogue file."""
		return {
			'title': self.title,
			'author': self.author,
			'year': self.year,
			'isbn': self.isbn,
			'borrowed_date': format_date(self.borrowed_date),
			'borrowed': self.borrowed,
		}

	@staticmethod
	def from_dict(data):
		"""Rebuild a book from its :meth:`to_dict` form.

		Raises:
			ValidationError: if the record is not a mapping or a field is
				missing or malformed.
		"""
		if not isinstance(data, dict):
			raise ValidationError(f'Expected a book object, got {type(data).__name__}.')
		missing = [key for key in ('title', 'author', 'year', 'isbn') if key not in data]
		if missing:
			raise ValidationError(f"Book record is missing field(s): {', '.join(missing)}.")
		return Book(
			data['title'],
			data['author'],
			data['year'],
			data['isbn'],
			data.get('borrowed_date'),
			data.get('borrowed', False),
		)

	def due_date(self, loan_days=DEFAULT_LOAN_DAYS):
		"""Return the date this loan falls due, or ``None`` if not on loan."""
		if not self.borrowed or self.borrowed_date is None:
			return None
		return self.borrowed_date + datetime.timedelta(days=loan_days)

	def days_overdue(self, current_date=None, loan_days=DEFAULT_LOAN_DAYS):
		"""Return how many days past the due date the book is (``0`` if not)."""
		due = self.due_date(loan_days)
		if due is None:
			return 0
		current_date = parse_date(current_date) or today()
		overdue = (current_date - due).days
		return overdue if overdue > 0 else 0

	def is_overdue(self, current_date=None, loan_days=DEFAULT_LOAN_DAYS):
		"""Return ``True`` when the loan period has elapsed."""
		return self.days_overdue(current_date, loan_days) > 0

	def borrow(self, current_date=None):
		"""Mark the book as on loan from ``current_date`` (default: today)."""
		self.borrowed = True
		self.borrowed_date = parse_date(current_date) or today()
		return self

	def give_back(self):
		"""Mark the book as returned and clear the loan date."""
		self.borrowed = False
		self.borrowed_date = None
		return self

	def status(self, current_date=None, loan_days=DEFAULT_LOAN_DAYS):
		"""Return ``Available``, ``Borrowed`` or ``Overdue``."""
		if not self.borrowed:
			return 'Available'
		if self.is_overdue(current_date, loan_days):
			return 'Overdue'
		return 'Borrowed'

	def matches(self, keyword, field):
		"""Return ``True`` if ``keyword`` appears in the given field.

		Raises:
			ValidationError: if ``field`` is not one of :data:`SEARCH_FIELDS`.
		"""
		if field not in SEARCH_FIELDS:
			raise ValidationError(
				f"Cannot search by {field!r}; choose one of {', '.join(SEARCH_FIELDS)}."
			)
		return str(keyword).strip().lower() in str(getattr(self, field)).lower()

	def __eq__(self, other):
		if not isinstance(other, Book):
			return NotImplemented
		return self.to_dict() == other.to_dict()

	def __hash__(self):
		return hash(self.isbn)

	def __repr__(self):
		return (
			f'Book(title={self.title!r}, author={self.author!r}, year={self.year!r}, '
			f'isbn={self.isbn!r}, borrowed={self.borrowed!r}, '
			f'borrowed_date={format_date(self.borrowed_date)!r})'
		)
