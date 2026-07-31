"""Runtime configuration.

Nothing here is secret, but the catalogue location and the loan period are the
two things that change between machines, so both are read from the
environment with sensible fallbacks. See ``.env.example``.
"""

import os
from pathlib import Path

from library.errors import ValidationError

#: Number of days a book may be kept before it counts as overdue.
DEFAULT_LOAN_DAYS = 14

#: Serialisation format for borrow dates in the catalogue file.
DATE_FORMAT = '%Y-%m-%d'

#: Environment variable holding the path of the catalogue file.
ENV_DATA_FILE = 'LIBRARY_DATA_FILE'

#: Environment variable overriding :data:`DEFAULT_LOAN_DAYS`.
ENV_LOAN_DAYS = 'LIBRARY_LOAN_DAYS'

#: Catalogue file name used when the environment does not say otherwise.
DEFAULT_DATA_FILE_NAME = 'books.txt'

#: Optional file of ``KEY=VALUE`` settings loaded at start-up.
DOTENV_FILE_NAME = '.env'


def project_root():
	"""Return the directory that contains the ``library`` package."""
	return Path(__file__).resolve().parent.parent


def load_dotenv(path=None, env=None):
	"""Copy ``KEY=VALUE`` lines from a ``.env`` file into the environment.

	Values already present in the environment win, so an explicit export on
	the command line always beats the file. Blank lines and ``#`` comments are
	ignored, and a missing file is not an error. Returns the keys that were
	set, which keeps the behaviour easy to assert in tests.
	"""
	env = os.environ if env is None else env
	path = project_root() / DOTENV_FILE_NAME if path is None else Path(path)
	if not path.is_file():
		return []
	applied = []
	for line in path.read_text(encoding='utf-8').splitlines():
		line = line.strip()
		if not line or line.startswith('#') or '=' not in line:
			continue
		key, _, value = line.partition('=')
		key = key.strip()
		value = value.strip().strip('"').strip("'")
		if key and key not in env:
			env[key] = value
			applied.append(key)
	return applied


def data_file_path(env=None):
	"""Resolve the catalogue path.

	``LIBRARY_DATA_FILE`` wins when set; otherwise the catalogue lives next to
	the project so the program behaves the same no matter which directory it
	was started from.
	"""
	env = os.environ if env is None else env
	configured = (env.get(ENV_DATA_FILE) or '').strip()
	if configured:
		return Path(configured).expanduser()
	return project_root() / DEFAULT_DATA_FILE_NAME


def loan_days(env=None):
	"""Resolve the loan period in days.

	Raises:
		ValidationError: if ``LIBRARY_LOAN_DAYS`` is set to something that is
			not a positive whole number.
	"""
	env = os.environ if env is None else env
	configured = (env.get(ENV_LOAN_DAYS) or '').strip()
	if not configured:
		return DEFAULT_LOAN_DAYS
	try:
		days = int(configured)
	except ValueError:
		raise ValidationError(
			f'{ENV_LOAN_DAYS} must be a whole number of days, got {configured!r}.'
		) from None
	if days <= 0:
		raise ValidationError(f'{ENV_LOAN_DAYS} must be greater than zero, got {days}.')
	return days
