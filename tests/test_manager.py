"""Tests for catalogue operations and lending rules."""

import datetime

import pytest

from library.errors import (
	AlreadyBorrowedError,
	BookNotFoundError,
	DuplicateISBNError,
	NotBorrowedError,
	ValidationError,
)
from library.manager import LibraryManager
from library.storage import MemoryBookStorage

from tests.conftest import TODAY


class TestAddAndRemove:
	def test_add_book_persists_immediately(self, manager, storage):
		manager.add_book('Dune', 'Frank Herbert', 1965, 'ISBN-003')
		assert [b.isbn for b in storage.load()] == ['ISBN-003']

	def test_duplicate_isbn_is_rejected(self, stocked):
		with pytest.raises(DuplicateISBNError):
			stocked.add_book('Other', 'Someone', 2001, 'ISBN-001')
		assert len(stocked) == 3

	def test_duplicate_check_ignores_surrounding_space(self, stocked):
		with pytest.raises(DuplicateISBNError):
			stocked.add_book('Other', 'Someone', 2001, '  ISBN-001  ')

	def test_invalid_book_is_not_added(self, manager):
		with pytest.raises(ValidationError):
			manager.add_book('', 'Someone', 2001, 'ISBN-009')
		assert len(manager) == 0

	def test_remove_book(self, stocked):
		removed = stocked.remove_book('ISBN-002')
		assert removed.title == 'Animal Farm'
		assert [b.isbn for b in stocked.reload()] == ['ISBN-001', 'ISBN-003']

	def test_remove_missing_book(self, stocked):
		with pytest.raises(BookNotFoundError):
			stocked.remove_book('nope')

	def test_blank_isbn_is_rejected(self, stocked):
		with pytest.raises(ValidationError):
			stocked.find_book('   ')


class TestSearch:
	def test_search_by_author_returns_every_match(self, stocked):
		results = stocked.search_books('orwell', 'author')
		assert {b.title for b in results} == {'Nineteen Eighty-Four', 'Animal Farm'}

	def test_search_by_title_is_partial(self, stocked):
		assert [b.isbn for b in stocked.search_books('dun', 'title')] == ['ISBN-003']

	def test_search_by_year(self, stocked):
		assert [b.isbn for b in stocked.search_books('1945', 'year')] == ['ISBN-002']

	def test_search_by_isbn(self, stocked):
		assert [b.title for b in stocked.search_books('ISBN-003', 'isbn')] == ['Dune']

	def test_no_match_returns_empty_list(self, stocked):
		assert stocked.search_books('tolkien', 'author') == []

	def test_unknown_field_is_rejected(self, stocked):
		with pytest.raises(ValidationError):
			stocked.search_books('x', 'publisher')

	def test_blank_keyword_is_rejected(self, stocked):
		with pytest.raises(ValidationError):
			stocked.search_books('   ', 'title')


class TestLending:
	def test_borrow_sets_date_and_due_date(self, stocked):
		book = stocked.borrow_book('ISBN-001', current_date=TODAY)
		assert book.borrowed is True
		assert book.borrowed_date == TODAY
		assert stocked.due_date_for(book) == datetime.date(2025, 6, 29)

	def test_borrow_is_persisted(self, stocked, storage):
		stocked.borrow_book('ISBN-001', current_date=TODAY)
		stored = {b.isbn: b for b in storage.load()}
		assert stored['ISBN-001'].borrowed is True
		assert stored['ISBN-001'].borrowed_date == TODAY

	def test_borrowing_twice_is_rejected(self, stocked):
		stocked.borrow_book('ISBN-001', current_date=TODAY)
		with pytest.raises(AlreadyBorrowedError):
			stocked.borrow_book('ISBN-001', current_date=TODAY)

	def test_borrow_unknown_isbn(self, stocked):
		with pytest.raises(BookNotFoundError):
			stocked.borrow_book('ISBN-404')

	def test_return_on_time_reports_no_overdue_days(self, stocked):
		stocked.borrow_book('ISBN-001', current_date=TODAY)
		receipt = stocked.return_book('ISBN-001', current_date=datetime.date(2025, 6, 20))
		assert receipt.days_overdue == 0
		assert receipt.due_date == datetime.date(2025, 6, 29)
		assert receipt.book.borrowed is False
		assert receipt.book.borrowed_date is None

	def test_return_on_the_due_date_is_on_time(self, stocked):
		stocked.borrow_book('ISBN-001', current_date=TODAY)
		receipt = stocked.return_book('ISBN-001', current_date=datetime.date(2025, 6, 29))
		assert receipt.days_overdue == 0

	def test_late_return_counts_the_days(self, stocked):
		stocked.borrow_book('ISBN-001', current_date=TODAY)
		receipt = stocked.return_book('ISBN-001', current_date=datetime.date(2025, 7, 4))
		assert receipt.days_overdue == 5

	def test_returning_a_shelved_book_is_rejected(self, stocked):
		with pytest.raises(NotBorrowedError):
			stocked.return_book('ISBN-001')

	def test_return_clears_the_loan_on_disk(self, stocked, storage):
		stocked.borrow_book('ISBN-001', current_date=TODAY)
		stocked.return_book('ISBN-001', current_date=TODAY)
		stored = {b.isbn: b for b in storage.load()}
		assert stored['ISBN-001'].borrowed is False
		assert stored['ISBN-001'].borrowed_date is None

	def test_a_book_can_be_borrowed_again_after_return(self, stocked):
		stocked.borrow_book('ISBN-001', current_date=datetime.date(2025, 5, 1))
		stocked.return_book('ISBN-001', current_date=TODAY)
		book = stocked.borrow_book('ISBN-001', current_date=TODAY)
		assert book.borrowed_date == TODAY


class TestViews:
	def test_overdue_books_sorted_most_late_first(self, stocked):
		stocked.borrow_book('ISBN-001', current_date=datetime.date(2025, 5, 1))
		stocked.borrow_book('ISBN-002', current_date=datetime.date(2025, 5, 20))
		stocked.borrow_book('ISBN-003', current_date=TODAY)
		overdue = stocked.overdue_books(current_date=TODAY)
		assert [b.isbn for b in overdue] == ['ISBN-001', 'ISBN-002']

	def test_available_and_borrowed_split(self, stocked):
		stocked.borrow_book('ISBN-001', current_date=TODAY)
		assert [b.isbn for b in stocked.borrowed_books()] == ['ISBN-001']
		assert [b.isbn for b in stocked.available_books()] == ['ISBN-002', 'ISBN-003']

	def test_summary_counts(self, stocked):
		stocked.borrow_book('ISBN-001', current_date=datetime.date(2025, 5, 1))
		stocked.borrow_book('ISBN-002', current_date=TODAY)
		assert stocked.summary(current_date=TODAY) == {
			'total': 3,
			'available': 1,
			'borrowed': 2,
			'overdue': 1,
		}


class TestLoanPeriod:
	def test_custom_loan_period_moves_the_due_date(self):
		manager = LibraryManager(MemoryBookStorage(), loan_days=7)
		manager.add_book('Dune', 'Frank Herbert', 1965, 'ISBN-003')
		book = manager.borrow_book('ISBN-003', current_date=TODAY)
		assert manager.due_date_for(book) == datetime.date(2025, 6, 22)

	def test_non_positive_loan_period_is_rejected(self):
		with pytest.raises(ValidationError):
			LibraryManager(MemoryBookStorage(), loan_days=0)
