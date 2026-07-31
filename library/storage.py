"""Persistence for the catalogue.

The on-disk format is a JSON array of book records (the file keeps its
historical ``books.txt`` name). Writes go through a temporary file and an
atomic replace so an interrupted save cannot leave a half-written catalogue
behind, and a file that cannot be parsed is moved aside rather than silently
overwritten.
"""

import datetime
import json
import os
from pathlib import Path

from library.errors import StorageError, ValidationError
from library.models import Book


class MemoryBookStorage:
	"""In-memory catalogue, used by tests and by ``--no-save`` style runs."""

	def __init__(self, books=None):
		self._records = [b.to_dict() for b in (books or [])]

	@property
	def location(self):
		return '(memory)'

	def load(self):
		return [Book.from_dict(record) for record in self._records]

	def save(self, books):
		self._records = [b.to_dict() for b in books]

	def quarantine(self):  # pragma: no cover - nothing to move aside
		return None


class JsonBookStorage:
	"""Reads and writes the catalogue as a JSON file on disk."""

	def __init__(self, path):
		self.path = Path(path)

	@property
	def location(self):
		return str(self.path)

	def load(self):
		"""Return the stored books, or an empty list if the file is absent.

		Raises:
			StorageError: if the file exists but cannot be read or parsed.
		"""
		if not self.path.exists():
			return []
		try:
			text = self.path.read_text(encoding='utf-8')
		except OSError as exc:
			raise StorageError(f'Could not read {self.path}: {exc}') from exc
		if not text.strip():
			return []
		try:
			data = json.loads(text)
		except json.JSONDecodeError as exc:
			raise StorageError(
				f'{self.path} is not valid JSON (line {exc.lineno}, column {exc.colno}).'
			) from exc
		if not isinstance(data, list):
			raise StorageError(
				f'{self.path} should contain a list of books, found {type(data).__name__}.'
			)
		books = []
		for index, record in enumerate(data, 1):
			try:
				books.append(Book.from_dict(record))
			except ValidationError as exc:
				raise StorageError(f'Book #{index} in {self.path} is invalid: {exc}') from exc
		return books

	def save(self, books):
		"""Write ``books`` to disk atomically.

		Raises:
			StorageError: if the catalogue could not be written.
		"""
		payload = json.dumps([b.to_dict() for b in books], indent=2)
		tmp_path = self.path.with_name(self.path.name + '.tmp')
		try:
			self.path.parent.mkdir(parents=True, exist_ok=True)
			with open(tmp_path, 'w', encoding='utf-8') as handle:
				handle.write(payload)
				handle.flush()
				os.fsync(handle.fileno())
			os.replace(tmp_path, self.path)
		except OSError as exc:
			raise StorageError(f'Could not write {self.path}: {exc}') from exc
		finally:
			if tmp_path.exists():
				try:
					tmp_path.unlink()
				except OSError:  # pragma: no cover - best effort cleanup
					pass

	def quarantine(self):
		"""Move an unreadable catalogue aside and return the backup path.

		Called when :meth:`load` fails, so a corrupt file is preserved instead
		of being overwritten by the next save.
		"""
		if not self.path.exists():
			return None
		stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
		backup = self.path.with_name(f'{self.path.name}.corrupt-{stamp}.bak')
		counter = 1
		while backup.exists():
			backup = self.path.with_name(f'{self.path.name}.corrupt-{stamp}-{counter}.bak')
			counter += 1
		try:
			os.replace(self.path, backup)
		except OSError as exc:
			raise StorageError(f'Could not move {self.path} aside: {exc}') from exc
		return backup
