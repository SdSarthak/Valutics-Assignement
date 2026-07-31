"""Tests for the presentation layer, driven through fake stdin."""

import datetime

import pytest

from library import cli
from library.storage import JsonBookStorage

from tests.conftest import TODAY


def feed(monkeypatch, answers):
	"""Replace ``input`` with a scripted sequence of answers."""
	queue = list(answers)

	def fake_input(prompt=''):
		if not queue:
			raise EOFError
		return queue.pop(0)

	monkeypatch.setattr('builtins.input', fake_input)


class TestDescribe:
	def test_available_book_line(self, stocked):
		line = cli.describe(stocked.get_book('ISBN-003'), 14, TODAY)
		assert line == 'Dune | Frank Herbert | 1965 | ISBN: ISBN-003 | Available'

	def test_borrowed_book_shows_due_date(self, stocked):
		stocked.borrow_book('ISBN-003', current_date=TODAY)
		line = cli.describe(stocked.get_book('ISBN-003'), 14, TODAY)
		assert 'Borrowed' in line
		assert 'borrowed 2025-06-15, due 2025-06-29' in line
		assert 'late' not in line

	def test_overdue_book_shows_the_lateness(self, stocked):
		stocked.borrow_book('ISBN-003', current_date=datetime.date(2025, 5, 1))
		line = cli.describe(stocked.get_book('ISBN-003'), 14, TODAY)
		assert 'Overdue' in line
		assert '31 day(s) late' in line


class TestMenuLoop:
	def test_option_eight_exits_cleanly(self, stocked, monkeypatch, capsys):
		feed(monkeypatch, ['8'])
		assert cli.run(stocked) == 0
		assert 'Goodbye' in capsys.readouterr().out

	def test_end_of_input_exits_cleanly(self, stocked, monkeypatch):
		feed(monkeypatch, [])
		assert cli.run(stocked) == 0

	def test_invalid_option_is_reported_and_loop_continues(
		self, stocked, monkeypatch, capsys
	):
		feed(monkeypatch, ['99', '8'])
		cli.run(stocked)
		assert 'Invalid option' in capsys.readouterr().out

	def test_add_book_through_the_menu(self, manager, monkeypatch, capsys):
		feed(monkeypatch, ['1', 'Dune', 'Frank Herbert', '1965', 'ISBN-003', '8'])
		cli.run(manager)
		assert 'Added "Dune"' in capsys.readouterr().out
		assert manager.find_book('ISBN-003') is not None

	def test_add_book_reprompts_on_a_bad_year(self, manager, monkeypatch, capsys):
		feed(monkeypatch, ['1', 'Dune', 'Frank Herbert', 'soon', '1965', 'ISBN-003', '8'])
		cli.run(manager)
		assert 'Year must be a positive whole number' in capsys.readouterr().out
		assert manager.get_book('ISBN-003').year == 1965

	def test_duplicate_isbn_is_reported_without_crashing(
		self, stocked, monkeypatch, capsys
	):
		feed(monkeypatch, ['1', 'Copy', 'Someone', '2001', 'ISBN-001', '8'])
		cli.run(stocked)
		assert 'already exists' in capsys.readouterr().out
		assert len(stocked) == 3

	def test_search_by_author(self, stocked, monkeypatch, capsys):
		feed(monkeypatch, ['3', '2', 'orwell', '8'])
		cli.run(stocked)
		out = capsys.readouterr().out
		assert 'Animal Farm' in out
		assert 'Dune' not in out

	def test_search_with_no_results(self, stocked, monkeypatch, capsys):
		feed(monkeypatch, ['3', '1', 'tolkien', '8'])
		cli.run(stocked)
		assert 'No matching books found.' in capsys.readouterr().out

	def test_borrow_then_return(self, stocked, monkeypatch, capsys):
		feed(monkeypatch, ['4', 'ISBN-001', '5', 'ISBN-001', '8'])
		cli.run(stocked)
		out = capsys.readouterr().out
		assert 'Please return it by' in out
		assert 'on time' in out
		assert stocked.get_book('ISBN-001').borrowed is False

	def test_returning_a_shelved_book_is_reported(self, stocked, monkeypatch, capsys):
		feed(monkeypatch, ['5', 'ISBN-001', '8'])
		cli.run(stocked)
		assert 'not currently borrowed' in capsys.readouterr().out

	def test_remove_requires_confirmation(self, stocked, monkeypatch, capsys):
		feed(monkeypatch, ['6', 'ISBN-002', 'n', '8'])
		cli.run(stocked)
		assert 'Nothing removed.' in capsys.readouterr().out
		assert len(stocked) == 3

	def test_remove_confirmed(self, stocked, monkeypatch, capsys):
		feed(monkeypatch, ['6', 'ISBN-002', 'y', '8'])
		cli.run(stocked)
		assert 'Removed "Animal Farm"' in capsys.readouterr().out
		assert stocked.find_book('ISBN-002') is None

	def test_borrowed_book_cannot_be_removed(self, stocked, monkeypatch, capsys):
		stocked.borrow_book('ISBN-002', current_date=TODAY)
		feed(monkeypatch, ['6', 'ISBN-002', '8'])
		cli.run(stocked)
		assert 'currently on loan' in capsys.readouterr().out
		assert len(stocked) == 3

	def test_overdue_view(self, stocked, monkeypatch, capsys):
		stocked.borrow_book('ISBN-001', current_date=datetime.date(2020, 1, 1))
		feed(monkeypatch, ['7', '8'])
		cli.run(stocked)
		assert 'Nineteen Eighty-Four' in capsys.readouterr().out

	def test_list_shows_a_summary(self, stocked, monkeypatch, capsys):
		feed(monkeypatch, ['2', '8'])
		cli.run(stocked)
		assert '3 book(s): 3 available' in capsys.readouterr().out

	def test_empty_library_message(self, manager, monkeypatch, capsys):
		feed(monkeypatch, ['2', '8'])
		cli.run(manager)
		assert 'No books in the library yet.' in capsys.readouterr().out


class TestBuildManager:
	def test_reads_an_existing_catalogue(self, catalogue_path, stocked):
		built = cli.build_manager(path=catalogue_path, loan_days=14)
		assert len(built) == 3

	def test_corrupt_catalogue_is_kept_aside(self, catalogue_path, capsys):
		catalogue_path.write_text('{not json', encoding='utf-8')
		built = cli.build_manager(path=catalogue_path, loan_days=14)
		assert len(built) == 0
		out = capsys.readouterr().out
		assert 'Warning' in out
		assert 'kept as' in out
		backups = list(catalogue_path.parent.glob('*.bak'))
		assert len(backups) == 1
		assert backups[0].read_text(encoding='utf-8') == '{not json'


class TestMain:
	def test_help_flag(self, capsys):
		assert cli.main(['--help']) == 0
		assert 'LIBRARY_DATA_FILE' in capsys.readouterr().out

	def test_bad_loan_days_environment_exits_with_an_error(
		self, monkeypatch, tmp_path, capsys
	):
		monkeypatch.setenv('LIBRARY_DATA_FILE', str(tmp_path / 'books.txt'))
		monkeypatch.setenv('LIBRARY_LOAN_DAYS', 'soon')
		assert cli.main([]) == 1
		assert 'Error:' in capsys.readouterr().out

	def test_run_from_main_with_environment_catalogue(
		self, monkeypatch, tmp_path, capsys
	):
		monkeypatch.setenv('LIBRARY_DATA_FILE', str(tmp_path / 'books.txt'))
		monkeypatch.setenv('LIBRARY_LOAN_DAYS', '7')
		feed(monkeypatch, ['1', 'Dune', 'Frank Herbert', '1965', 'ISBN-003', '8'])
		assert cli.main([]) == 0
		assert 'Loan period: 7 day(s)' in capsys.readouterr().out
		assert len(JsonBookStorage(tmp_path / 'books.txt').load()) == 1


@pytest.mark.parametrize('answer,expected', [('  Dune ', 'Dune')])
def test_ask_nonempty_reprompts(monkeypatch, capsys, answer, expected):
	feed(monkeypatch, ['', '   ', answer])
	assert cli.ask_nonempty('> ') == expected
	assert capsys.readouterr().out.count('Input cannot be empty.') == 2


def test_ask_raises_quit_at_end_of_input(monkeypatch):
	feed(monkeypatch, [])
	with pytest.raises(cli.Quit):
		cli.ask('> ')
