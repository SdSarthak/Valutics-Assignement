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


def project_root():
	"""Return the directory that contains the ``library`` package."""
	return Path(__file__).resolve().parent.parent


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
