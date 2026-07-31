"""Interactive menu for the library.

This is the only module that reads from stdin or writes to stdout. Everything
it shows comes from :class:`~library.manager.LibraryManager`, so the rules can
be exercised in tests without a terminal.
"""

import sys

from library import config
from library.errors import LibraryError, StorageError, ValidationError
from library.manager import LibraryManager
from library.models import SEARCH_FIELDS, format_date, today
from library.storage import JsonBookStorage

MENU = '''
Library Book Manager
----------------------
1. Add New Book
2. List All Books
3. Search for Books
4. Borrow a Book
5. Return a Book
6. Remove a Book
7. Show Overdue Books
8. Exit
'''

SEARCH_MENU_FIELDS = ('title', 'author', 'year', 'isbn')


class Quit(Exception):
	"""Raised internally when the user chooses to leave or closes stdin."""


# -- input helpers ---------------------------------------------------------


def ask(prompt):
	"""Read one stripped line, treating end-of-input as a request to quit."""
	try:
		return input(prompt).strip()
	except EOFError:
		print()
		raise Quit() from None


def ask_nonempty(prompt):
	"""Keep asking until the user types something."""
	while True:
		value = ask(prompt)
		if value:
			return value
		print('Input cannot be empty.')


def ask_year(prompt):
	"""Keep asking until the user types a positive whole number."""
	while True:
		value = ask(prompt)
		if value.isdigit() and int(value) > 0:
			return int(value)
		print('Year must be a positive whole number, for example 1949.')


# -- formatting ------------------------------------------------------------


def describe(book, loan_days, current_date=None):
	"""Return a single catalogue line for a book."""
	status = book.status(current_date, loan_days)
	line = f'{book.title} | {book.author} | {book.year} | ISBN: {book.isbn} | {status}'
	due = book.due_date(loan_days)
	if due is not None:
		line += f' | borrowed {format_date(book.borrowed_date)}, due {format_date(due)}'
		overdue = book.days_overdue(current_date, loan_days)
		if overdue:
			line += f' ({overdue} day(s) late)'
	elif book.borrowed:
		line += ' | borrow date unknown'
	return line


def show_books(books, loan_days, heading, current_date=None, empty_message='No books to show.'):
	"""Print a numbered list of books under a heading."""
	if not books:
		print(empty_message)
		return
	print(f'\n{heading}')
	for index, book in enumerate(books, 1):
		print(f'{index}. {describe(book, loan_days, current_date)}')


# -- actions ---------------------------------------------------------------


def add_book(manager):
	title = ask_nonempty('Enter book title: ')
	author = ask_nonempty('Enter author: ')
	year = ask_year('Enter publication year: ')
	isbn = ask_nonempty('Enter ISBN: ')
	book = manager.add_book(title, author, year, isbn)
	print(f'Added "{book.title}" by {book.author}.')


def list_books(manager):
	summary = manager.summary()
	show_books(
		manager.books,
		manager.loan_days,
		'Library Collection:',
		empty_message='No books in the library yet.',
	)
	if summary['total']:
		print(
			f"\n{summary['total']} book(s): {summary['available']} available, "
			f"{summary['borrowed']} on loan, {summary['overdue']} overdue."
		)


def search_books(manager):
	print('Search by: ' + '  '.join(
		f'{index}. {field.title()}' for index, field in enumerate(SEARCH_MENU_FIELDS, 1)
	))
	choice = ask(f'Choose field (1-{len(SEARCH_MENU_FIELDS)}): ')
	if not choice.isdigit() or not 1 <= int(choice) <= len(SEARCH_MENU_FIELDS):
		print('Invalid field.')
		return
	field = SEARCH_MENU_FIELDS[int(choice) - 1]
	keyword = ask_nonempty(f'Enter {field} to search for: ')
	results = manager.search_books(keyword, field)
	show_books(
		results,
		manager.loan_days,
		f"Search results ({field} contains '{keyword}'):",
		empty_message='No matching books found.',
	)


def borrow_book(manager):
	isbn = ask_nonempty('Enter ISBN to borrow: ')
	book = manager.borrow_book(isbn)
	due = manager.due_date_for(book)
	print(f'Borrowed "{book.title}". Please return it by {format_date(due)}.')


def return_book(manager):
	isbn = ask_nonempty('Enter ISBN to return: ')
	receipt = manager.return_book(isbn)
	if receipt.days_overdue:
		print(
			f'Returned "{receipt.book.title}". It was due on '
			f'{format_date(receipt.due_date)} and is {receipt.days_overdue} day(s) overdue.'
		)
	elif receipt.due_date is not None:
		print(f'Returned "{receipt.book.title}" on time (due {format_date(receipt.due_date)}).')
	else:
		print(f'Returned "{receipt.book.title}".')


def remove_book(manager):
	isbn = ask_nonempty('Enter ISBN to remove: ')
	book = manager.get_book(isbn)
	if book.borrowed:
		print('That book is currently on loan; take it back before removing it.')
		return
	confirm = ask(f'Remove "{book.title}" from the catalogue? (y/N): ').lower()
	if confirm not in ('y', 'yes'):
		print('Nothing removed.')
		return
	manager.remove_book(isbn)
	print(f'Removed "{book.title}".')


def show_overdue(manager):
	overdue = manager.overdue_books()
	show_books(
		overdue,
		manager.loan_days,
		'Overdue books:',
		empty_message='Nothing is overdue.',
	)


ACTIONS = {
	'1': add_book,
	'2': list_books,
	'3': search_books,
	'4': borrow_book,
	'5': return_book,
	'6': remove_book,
	'7': show_overdue,
}


# -- wiring ----------------------------------------------------------------


def build_manager(path=None, loan_days=None):
	"""Create a manager, moving an unreadable catalogue aside if needed."""
	storage = JsonBookStorage(path if path is not None else config.data_file_path())
	days = config.loan_days() if loan_days is None else loan_days
	try:
		return LibraryManager(storage, days)
	except StorageError as exc:
		print(f'Warning: {exc}')
		backup = storage.quarantine()
		if backup is not None:
			print(f'The existing catalogue was kept as {backup}.')
		print('Starting with an empty catalogue.')
		return LibraryManager(storage, days)


def run(manager):
	"""Drive the menu loop until the user exits."""
	print(f'Catalogue: {manager.storage.location}')
	print(f'Loan period: {manager.loan_days} day(s). Today is {format_date(today())}.')
	while True:
		print(MENU)
		try:
			choice = ask('Select an option (1-8): ')
			if choice == '8':
				print('Exiting Library Book Manager. Goodbye!')
				return 0
			action = ACTIONS.get(choice)
			if action is None:
				print('Invalid option. Please select 1-8.')
				continue
			action(manager)
		except Quit:
			print('Exiting Library Book Manager. Goodbye!')
			return 0
		except LibraryError as exc:
			print(f'Error: {exc}')


def main(argv=None):
	"""Entry point. Returns the process exit code."""
	argv = sys.argv[1:] if argv is None else list(argv)
	if argv and argv[0] in ('-h', '--help'):
		print(__doc__.strip())
		print(
			f'\nConfiguration:\n'
			f'  {config.ENV_DATA_FILE}  path to the catalogue JSON file\n'
			f'  {config.ENV_LOAN_DAYS}  loan period in days '
			f'(default {config.DEFAULT_LOAN_DAYS})\n'
			f'\nSearchable fields: {", ".join(SEARCH_FIELDS)}'
		)
		return 0
	config.load_dotenv()
	try:
		manager = build_manager()
	except (ValidationError, StorageError) as exc:
		print(f'Error: {exc}')
		return 1
	try:
		return run(manager)
	except KeyboardInterrupt:
		print('\nInterrupted. Goodbye!')
		return 130


if __name__ == '__main__':  # pragma: no cover
	sys.exit(main())
