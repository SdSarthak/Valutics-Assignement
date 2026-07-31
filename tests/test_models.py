"""Tests for the Book record and the loan arithmetic."""

import datetime

import pytest

from library.errors import ValidationError
from library.models import Book, format_date, parse_date

from tests.conftest import TODAY


def make_book(**overrides):
	fields = {
		'title': 'Dune',
		'author': 'Frank Herbert',
		'year': 1965,
		'isbn': 'ISBN-003',
	}
	fields.update(overrides)
	return Book(**fields)


class TestValidation:
	def test_fields_are_stripped(self):
		book = make_book(title='  Dune  ', author='\tFrank Herbert\n', isbn=' ISBN-003 ')
		assert book.title == 'Dune'
		assert book.author == 'Frank Herbert'
		assert book.isbn == 'ISBN-003'

	@pytest.mark.parametrize('field', ['title', 'author', 'isbn'])
	def test_blank_text_field_is_rejected(self, field):
		with pytest.raises(ValidationError):
			make_book(**{field: '   '})

	@pytest.mark.parametrize('bad_year', ['nineteen', '', None, 0, -5, True])
	def test_bad_year_is_rejected(self, bad_year):
		with pytest.raises(ValidationError):
			make_book(year=bad_year)

	def test_numeric_string_year_is_coerced(self):
		assert make_book(year=' 1965 ').year == 1965


class TestSerialisation:
	def test_round_trip(self):
		book = make_book(borrowed=True, borrowed_date='2025-06-01')
		restored = Book.from_dict(book.to_dict())
		assert restored == book
		assert restored.borrowed_date == datetime.date(2025, 6, 1)

	def test_dates_serialise_as_strings(self):
		book = make_book(borrowed=True, borrowed_date=datetime.date(2025, 6, 1))
		assert book.to_dict()['borrowed_date'] == '2025-06-01'

	def test_available_book_has_no_borrow_date(self):
		# A stale loan date on a returned book would make it look overdue.
		book = make_book(borrowed=False, borrowed_date='2025-06-01')
		assert book.borrowed_date is None
		assert book.to_dict()['borrowed_date'] is None

	def test_missing_field_is_reported(self):
		with pytest.raises(ValidationError) as exc:
			Book.from_dict({'title': 'Dune', 'author': 'Frank Herbert'})
		assert 'year' in str(exc.value)
		assert 'isbn' in str(exc.value)

	def test_non_mapping_is_rejected(self):
		with pytest.raises(ValidationError):
			Book.from_dict(['Dune'])

	def test_bad_date_is_rejected(self):
		with pytest.raises(ValidationError):
			make_book(borrowed=True, borrowed_date='15-06-2025')


class TestDateHelpers:
	def test_parse_date_accepts_none_and_blank(self):
		assert parse_date(None) is None
		assert parse_date('') is None

	def test_parse_date_passes_through_dates(self):
		day = datetime.date(2025, 6, 1)
		assert parse_date(day) == day
		assert parse_date(datetime.datetime(2025, 6, 1, 13, 30)) == day

	def test_format_date_handles_none(self):
		assert format_date(None) is None


class TestLoanArithmetic:
	def test_available_book_has_no_due_date(self):
		assert make_book().due_date(14) is None

	def test_due_date_is_borrow_date_plus_loan_period(self):
		book = make_book(borrowed=True, borrowed_date='2025-06-01')
		assert book.due_date(14) == datetime.date(2025, 6, 15)
		assert book.due_date(7) == datetime.date(2025, 6, 8)

	def test_book_is_not_overdue_on_the_due_date(self):
		book = make_book(borrowed=True, borrowed_date='2025-06-01')
		assert book.days_overdue(TODAY, 14) == 0
		assert book.is_overdue(TODAY, 14) is False

	def test_overdue_days_counted_from_the_day_after(self):
		book = make_book(borrowed=True, borrowed_date='2025-06-01')
		assert book.days_overdue(datetime.date(2025, 6, 16), 14) == 1
		assert book.days_overdue(datetime.date(2025, 6, 25), 14) == 10

	def test_available_book_is_never_overdue(self):
		assert make_book().days_overdue(datetime.date(2030, 1, 1), 14) == 0

	@pytest.mark.parametrize(
		'borrowed,borrow_date,current,expected',
		[
			(False, None, TODAY, 'Available'),
			(True, '2025-06-10', TODAY, 'Borrowed'),
			(True, '2025-05-01', TODAY, 'Overdue'),
		],
	)
	def test_status_label(self, borrowed, borrow_date, current, expected):
		book = make_book(borrowed=borrowed, borrowed_date=borrow_date)
		assert book.status(current, 14) == expected

	def test_borrow_then_give_back_clears_the_loan(self):
		book = make_book()
		book.borrow(TODAY)
		assert book.borrowed is True
		assert book.borrowed_date == TODAY
		book.give_back()
		assert book.borrowed is False
		assert book.borrowed_date is None


class TestMatching:
	def test_match_is_case_insensitive_substring(self):
		book = make_book()
		assert book.matches('DUN', 'title') is True
		assert book.matches('herbert', 'author') is True
		assert book.matches('tolkien', 'author') is False

	def test_year_is_searchable_as_text(self):
		assert make_book().matches('196', 'year') is True

	def test_unknown_field_is_rejected(self):
		with pytest.raises(ValidationError):
			make_book().matches('x', 'publisher')
