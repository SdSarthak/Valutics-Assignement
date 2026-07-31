"""Shared fixtures. Every test runs against synthetic data in a temp dir."""

import datetime

import pytest

from library.manager import LibraryManager
from library.storage import JsonBookStorage, MemoryBookStorage

#: Fixed "today" so overdue arithmetic never depends on the wall clock.
TODAY = datetime.date(2025, 6, 15)


@pytest.fixture
def catalogue_path(tmp_path):
	return tmp_path / 'books.txt'


@pytest.fixture
def storage(catalogue_path):
	return JsonBookStorage(catalogue_path)


@pytest.fixture
def manager(storage):
	return LibraryManager(storage, loan_days=14)


@pytest.fixture
def memory_manager():
	return LibraryManager(MemoryBookStorage(), loan_days=14)


@pytest.fixture
def stocked(manager):
	"""A manager holding three books, none of them on loan."""
	manager.add_book('Nineteen Eighty-Four', 'George Orwell', 1949, 'ISBN-001')
	manager.add_book('Animal Farm', 'George Orwell', 1945, 'ISBN-002')
	manager.add_book('Dune', 'Frank Herbert', 1965, 'ISBN-003')
	return manager
