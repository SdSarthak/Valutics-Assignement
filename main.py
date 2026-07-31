"""Entry point for the Library Management System.

Run it with ``python main.py``. All of the behaviour lives in the ``library``
package so it can be imported and tested on its own.
"""

import sys

from library.cli import main

if __name__ == '__main__':
	sys.exit(main())
