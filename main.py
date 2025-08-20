
import json
import os

BOOKS_FILE = 'books.txt'

class Book:
	def __init__(self, title, author, year, isbn, borrowed=False):
		self.title = title
		self.author = author
		self.year = year
		self.isbn = isbn
		self.borrowed = borrowed

	def to_dict(self):
		return {
			'title': self.title,
			'author': self.author,
			'year': self.year,
			'isbn': self.isbn,
			'borrowed': self.borrowed
		}

	@staticmethod
	def from_dict(data):
		return Book(
			data['title'],
			data['author'],
			data['year'],
			data['isbn'],
			data.get('borrowed', False)
		)

class LibraryManager:
	def __init__(self):
		self.books = []
		self.load_books()

	def load_books(self):
		if os.path.exists(BOOKS_FILE):
			try:
				with open(BOOKS_FILE, 'r', encoding='utf-8') as f:
					data = json.load(f)
					self.books = [Book.from_dict(b) for b in data]
			except Exception:
				self.books = []
		else:
			self.books = []

	def save_books(self):
		with open(BOOKS_FILE, 'w', encoding='utf-8') as f:
			json.dump([b.to_dict() for b in self.books], f, indent=2)

	def add_book(self, title, author, year, isbn):
		if any(b.isbn == isbn for b in self.books):
			print('A book with this ISBN already exists.')
			return
		self.books.append(Book(title, author, year, isbn))
		self.save_books()
		print('Book added successfully.')

	def list_books(self):
		if not self.books:
			print('No books in the library.')
			return
		print('\nLibrary Collection:')
		for idx, b in enumerate(self.books, 1):
			status = 'Borrowed' if b.borrowed else 'Available'
			print(f"{idx}. {b.title} | {b.author} | {b.year} | ISBN: {b.isbn} | {status}")

	def search_books(self, keyword, field):
		results = []
		keyword = keyword.lower()
		for b in self.books:
			value = str(getattr(b, field, '')).lower()
			if keyword in value:
				results.append(b)
		if not results:
			print('No matching books found.')
		else:
			print(f"\nSearch Results ({field.title()} contains '{keyword}'):")
			for idx, b in enumerate(results, 1):
				status = 'Borrowed' if b.borrowed else 'Available'
				print(f"{idx}. {b.title} | {b.author} | {b.year} | ISBN: {b.isbn} | {status}")

	def borrow_book(self, isbn):
		for b in self.books:
			if b.isbn == isbn:
				if b.borrowed:
					print('This book is already borrowed.')
				else:
					b.borrowed = True
					self.save_books()
					print('Book borrowed successfully.')
				return
		print('Book not found.')

	def return_book(self, isbn):
		for b in self.books:
			if b.isbn == isbn:
				if not b.borrowed:
					print('This book is not currently borrowed.')
				else:
					b.borrowed = False
					self.save_books()
					print('Book returned successfully.')
				return
		print('Book not found.')

def input_nonempty(prompt):
	while True:
		val = input(prompt).strip()
		if val:
			return val
		print('Input cannot be empty.')

def main():
	manager = LibraryManager()
	menu = '''\nLibrary Book Manager\n----------------------\n1. Add New Book\n2. List All Books\n3. Search for Books\n4. Borrow a Book\n5. Return a Book\n6. Exit\n'''
	while True:
		print(menu)
		choice = input('Select an option (1-6): ').strip()
		if choice == '1':
			title = input_nonempty('Enter book title: ')
			author = input_nonempty('Enter author: ')
			while True:
				year = input('Enter publication year: ').strip()
				if year.isdigit():
					year = int(year)
					break
				print('Year must be a number.')
			isbn = input_nonempty('Enter ISBN: ')
			manager.add_book(title, author, year, isbn)
		elif choice == '2':
			manager.list_books()
		elif choice == '3':
			print('Search by: 1. Title  2. Author  3. Year')
			f = input('Choose field (1-3): ').strip()
			if f == '1':
				keyword = input_nonempty('Enter title keyword: ')
				manager.search_books(keyword, 'title')
			elif f == '2':
				keyword = input_nonempty('Enter author keyword: ')
				manager.search_books(keyword, 'author')
			elif f == '3':
				keyword = input_nonempty('Enter year: ')
				manager.search_books(keyword, 'year')
			else:
				print('Invalid field.')
		elif choice == '4':
			isbn = input_nonempty('Enter ISBN to borrow: ')
			manager.borrow_book(isbn)
		elif choice == '5':
			isbn = input_nonempty('Enter ISBN to return: ')
			manager.return_book(isbn)
		elif choice == '6':
			print('Exiting Library Book Manager. Goodbye!')
			break
		else:
			print('Invalid option. Please select 1-6.')

if __name__ == '__main__':
	main()
