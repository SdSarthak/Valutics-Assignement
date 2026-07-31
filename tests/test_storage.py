"""Tests for reading and writing the catalogue file, plus configuration."""

import json

import pytest

from library import config
from library.errors import StorageError, ValidationError
from library.models import Book
from library.storage import JsonBookStorage


def sample_books():
	return [
		Book('Dune', 'Frank Herbert', 1965, 'ISBN-003'),
		Book('Animal Farm', 'George Orwell', 1945, 'ISBN-002', '2025-06-01', True),
	]


class TestJsonBookStorage:
	def test_missing_file_loads_as_empty(self, storage):
		assert storage.load() == []

	def test_empty_file_loads_as_empty(self, catalogue_path, storage):
		catalogue_path.write_text('   ', encoding='utf-8')
		assert storage.load() == []

	def test_round_trip(self, storage):
		books = sample_books()
		storage.save(books)
		assert storage.load() == books

	def test_saved_file_is_readable_json(self, catalogue_path, storage):
		storage.save(sample_books())
		data = json.loads(catalogue_path.read_text(encoding='utf-8'))
		assert [record['isbn'] for record in data] == ['ISBN-003', 'ISBN-002']

	def test_save_creates_missing_directories(self, tmp_path):
		storage = JsonBookStorage(tmp_path / 'nested' / 'deeper' / 'books.txt')
		storage.save(sample_books())
		assert len(storage.load()) == 2

	def test_save_leaves_no_temp_file_behind(self, tmp_path, catalogue_path, storage):
		storage.save(sample_books())
		assert [p.name for p in tmp_path.iterdir()] == [catalogue_path.name]

	def test_malformed_json_raises(self, catalogue_path, storage):
		catalogue_path.write_text('{not json', encoding='utf-8')
		with pytest.raises(StorageError):
			storage.load()

	def test_non_list_payload_raises(self, catalogue_path, storage):
		catalogue_path.write_text('{"title": "Dune"}', encoding='utf-8')
		with pytest.raises(StorageError):
			storage.load()

	def test_bad_record_names_its_position(self, catalogue_path, storage):
		catalogue_path.write_text(
			json.dumps([sample_books()[0].to_dict(), {'title': 'Broken'}]), encoding='utf-8'
		)
		with pytest.raises(StorageError) as exc:
			storage.load()
		assert 'Book #2' in str(exc.value)

	def test_corrupt_file_is_kept_when_quarantined(self, catalogue_path, storage):
		catalogue_path.write_text('{not json', encoding='utf-8')
		backup = storage.quarantine()
		assert backup is not None
		assert backup.read_text(encoding='utf-8') == '{not json'
		assert not catalogue_path.exists()
		assert storage.load() == []

	def test_quarantine_without_a_file_is_a_no_op(self, storage):
		assert storage.quarantine() is None


class TestConfig:
	def test_data_file_defaults_next_to_the_project(self):
		path = config.data_file_path(env={})
		assert path.name == config.DEFAULT_DATA_FILE_NAME
		assert path.parent == config.project_root()

	def test_data_file_honours_the_environment(self, tmp_path):
		target = tmp_path / 'catalogue.json'
		assert config.data_file_path(env={config.ENV_DATA_FILE: str(target)}) == target

	def test_blank_environment_value_falls_back(self):
		path = config.data_file_path(env={config.ENV_DATA_FILE: '   '})
		assert path.parent == config.project_root()

	def test_loan_days_default(self):
		assert config.loan_days(env={}) == config.DEFAULT_LOAN_DAYS

	def test_loan_days_from_environment(self):
		assert config.loan_days(env={config.ENV_LOAN_DAYS: '21'}) == 21

	@pytest.mark.parametrize('value', ['soon', '0', '-3', '1.5'])
	def test_bad_loan_days_are_rejected(self, value):
		with pytest.raises(ValidationError):
			config.loan_days(env={config.ENV_LOAN_DAYS: value})


class TestDotenv:
	def write(self, tmp_path, text):
		path = tmp_path / '.env'
		path.write_text(text, encoding='utf-8')
		return path

	def test_missing_file_is_not_an_error(self, tmp_path):
		assert config.load_dotenv(path=tmp_path / '.env', env={}) == []

	def test_values_are_loaded(self, tmp_path):
		path = self.write(tmp_path, 'LIBRARY_LOAN_DAYS=21\nLIBRARY_DATA_FILE="/tmp/books.txt"\n')
		env = {}
		assert sorted(config.load_dotenv(path=path, env=env)) == [
			'LIBRARY_DATA_FILE',
			'LIBRARY_LOAN_DAYS',
		]
		assert env['LIBRARY_LOAN_DAYS'] == '21'
		assert env['LIBRARY_DATA_FILE'] == '/tmp/books.txt'

	def test_comments_and_blank_lines_are_skipped(self, tmp_path):
		path = self.write(tmp_path, '# a comment\n\nnot-a-pair\nLIBRARY_LOAN_DAYS=7\n')
		env = {}
		assert config.load_dotenv(path=path, env=env) == ['LIBRARY_LOAN_DAYS']
		assert env == {'LIBRARY_LOAN_DAYS': '7'}

	def test_existing_environment_wins(self, tmp_path):
		path = self.write(tmp_path, 'LIBRARY_LOAN_DAYS=21\n')
		env = {'LIBRARY_LOAN_DAYS': '3'}
		assert config.load_dotenv(path=path, env=env) == []
		assert env['LIBRARY_LOAN_DAYS'] == '3'
