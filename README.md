# Library Management System

A command-line catalogue for a small library. Add books, search them, lend them
out for a fixed loan period, take them back and see what is overdue. The whole
catalogue lives in a single JSON file, so there is no database to install and
no service to run.

Written for the Valutics assignment; kept as a working tool rather than a demo.

## Features

- Add books with title, author, publication year and ISBN, with the ISBN
  enforced as unique.
- List the catalogue with a live status for each book — `Available`,
  `Borrowed` or `Overdue` — plus the borrow and due dates.
- Case-insensitive substring search across title, author, year or ISBN.
- Borrow a book and get the due date; the loan period defaults to 14 days and
  is configurable.
- Return a book and be told whether it was on time, or by how many days it was
  late.
- Remove a book from the catalogue (blocked while it is on loan).
- A dedicated overdue report, sorted most overdue first.
- Crash-safe saves: the catalogue is written to a temporary file and swapped in
  atomically, and a catalogue that cannot be parsed is moved aside rather than
  overwritten.

## Requirements

Python 3.8 or newer. No third-party runtime dependencies.

## Setup

```bash
git clone https://github.com/SdSarthak/Valutics-Assignement.git
cd Valutics-Assignement

# optional but recommended
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements-dev.txt   # only needed to run the tests
```

## Usage

```bash
python main.py
```

You get a menu:

```
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
```

A short session:

```
Select an option (1-8): 1
Enter book title: Nineteen Eighty-Four
Enter author: George Orwell
Enter publication year: 1949
Enter ISBN: 9780451524935
Added "Nineteen Eighty-Four" by George Orwell.

Select an option (1-8): 4
Enter ISBN to borrow: 9780451524935
Borrowed "Nineteen Eighty-Four". Please return it by 2025-06-29.

Select an option (1-8): 2

Library Collection:
1. Nineteen Eighty-Four | George Orwell | 1949 | ISBN: 9780451524935 | Borrowed | borrowed 2025-06-15, due 2025-06-29

1 book(s): 0 available, 1 on loan, 0 overdue.
```

`python main.py --help` prints the configuration options and the searchable
fields.

## Where the data lives

There is no dataset to download — the catalogue is whatever you type in. It is
stored as a JSON array in `books.txt` next to `main.py`, and that file is
**gitignored** so a personal catalogue never lands in the repository. The file
is created on the first save; if it is missing, the program simply starts with
an empty library.

Each record looks like this:

```json
[
  {
    "title": "Nineteen Eighty-Four",
    "author": "George Orwell",
    "year": 1949,
    "isbn": "9780451524935",
    "borrowed_date": "2025-06-15",
    "borrowed": true
  }
]
```

If the file is ever corrupted, the program tells you, renames it to
`books.txt.corrupt-<timestamp>.bak` and carries on with an empty catalogue, so
nothing is lost silently.

## Configuration

Both settings are optional. Copy `.env.example` to `.env` (gitignored) or
export them in your shell; real environment variables take precedence over the
file.

| Variable | Default | Meaning |
| --- | --- | --- |
| `LIBRARY_DATA_FILE` | `books.txt` beside `main.py` | Path to the catalogue JSON file |
| `LIBRARY_LOAN_DAYS` | `14` | Days a book may be kept before it is overdue |

```bash
LIBRARY_DATA_FILE=~/library/books.json LIBRARY_LOAN_DAYS=21 python main.py
```

## Project layout

```
main.py                  thin entry point
library/
  config.py              environment settings and paths
  errors.py              exception types the CLI prints
  models.py              the Book record, due dates and overdue arithmetic
  storage.py             atomic JSON persistence
  manager.py             catalogue operations (raises, never prints)
  cli.py                 the interactive menu — the only I/O layer
tests/                   pytest suite, synthetic fixtures only
```

The split exists so the rules can be tested without a terminal: `manager` and
`models` raise `LibraryError` subclasses and `cli` is the only place that
prints.

## Using it as a library

```python
from library import LibraryManager, JsonBookStorage

manager = LibraryManager(JsonBookStorage('books.txt'), loan_days=14)
manager.add_book('Dune', 'Frank Herbert', 1965, 'ISBN-003')
book = manager.borrow_book('ISBN-003')
print(manager.due_date_for(book))

receipt = manager.return_book('ISBN-003')
print(receipt.days_overdue)          # 0 when returned on time
```

Every method that depends on the date accepts a `current_date` argument, which
is what makes the overdue logic testable.

## Tests

```bash
python -m pytest
```

111 tests covering validation, serialisation, the loan arithmetic, catalogue
operations, atomic and corrupt-file handling, configuration and the menu loop.
They use temporary directories and synthetic books only — no network, no
database and no reliance on today's date.
