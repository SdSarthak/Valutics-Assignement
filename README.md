# 📚 Celine Library Management System

A comprehensive, object-oriented library management system built in Python that demonstrates advanced OOP concepts and provides a complete command-line interface for managing books, authors, and library members.

## 🌟 Features

### 📖 Book Management
- **Add New Books**: Register new books with detailed metadata
- **Update Book Details**: Modify book information including title, genre, and author
- **Remove Books**: Safely remove books (only if no copies are borrowed)
- **Manage Copies**: Add or remove book copies from inventory
- **Track Availability**: Real-time tracking of available vs. borrowed copies

### ✍️ Author Management
- **Author Registration**: Add new authors with biographical information
- **Update Author Details**: Modify author name and nationality
- **Author-Book Relationships**: Automatic bidirectional linking between authors and their books
- **Author Statistics**: View book counts and author portfolios

### 👥 Member Management
- **Member Registration**: Register new library members with contact information
- **Member Profiles**: Update member details and manage account status
- **Account Status**: Activate/deactivate member accounts
- **Borrowing History**: Complete tracking of member borrowing patterns

### 📖 Borrowing & Returns
- **Book Borrowing**: Streamlined book checkout process
- **Book Returns**: Efficient return processing with automatic inventory updates
- **Borrowing Validation**: Comprehensive checks for member status and book availability
- **Transaction History**: Complete audit trail of all borrowing activities

### 🔍 Search & Browse
- **Multi-criteria Search**: Search by title, author name, or genre
- **Flexible Matching**: Case-insensitive partial text matching
- **Genre Browsing**: Browse books by category
- **Advanced Filtering**: Filter by availability status

### 📊 Reports & Statistics
- **Library Overview**: Comprehensive library statistics
- **Collection Analytics**: Book distribution by genre
- **Member Activity**: Active vs. inactive member counts
- **Inventory Status**: Total vs. available copies tracking

## 🏗️ Object-Oriented Design

### Core Classes

#### 1. **Author Class**
```python
class Author:
    # Encapsulation: Private attributes with controlled access
    # Composition: Contains list of associated books
    # Properties: Getter/setter methods for data validation
```

**Key OOP Concepts:**
- **Encapsulation**: Private attributes (`__author_id`, `__name`, etc.) with property decorators
- **Data Validation**: Setter methods with input validation
- **Composition**: Maintains relationships with Book objects
- **Method Polymorphism**: String representation methods (`__str__`, `__repr__`)

#### 2. **Book Class**
```python
class Book:
    # Encapsulation: Protected book data and borrowing information
    # Association: Bidirectional relationship with Author
    # State Management: Availability tracking and copy management
```

**Key OOP Concepts:**
- **Encapsulation**: Private book metadata and borrowing state
- **Association**: Automatic relationship management with Author class
- **State Management**: Dynamic availability calculation
- **Business Logic**: Borrowing/returning validation and processing

#### 3. **LibraryMember Class**
```python
class LibraryMember:
    # Encapsulation: Member data and borrowing history
    # Aggregation: References to borrowed Book objects
    # State Tracking: Active/inactive status management
```

**Key OOP Concepts:**
- **Encapsulation**: Private member information and borrowing records
- **Aggregation**: Collection of borrowed books without ownership
- **State Pattern**: Active/inactive member status management
- **History Tracking**: Comprehensive borrowing history maintenance

#### 4. **Library Class**
```python
class Library:
    # Composition: Contains and manages all system entities
    # Facade Pattern: Simplified interface for complex operations
    # Collection Management: Centralized data structure management
```

**Key OOP Concepts:**
- **Composition**: Owns and manages Books, Authors, and Members
- **Facade Pattern**: Provides simplified interface for complex operations
- **Factory Methods**: Centralized object creation and ID management
- **Collection Management**: Dictionary-based efficient data storage

#### 5. **LibraryManagementSystem Class**
```python
class LibraryManagementSystem:
    # Controller Pattern: Manages user interaction and system coordination
    # Command Pattern: Menu-driven operation handling
    # Separation of Concerns: UI logic separated from business logic
```

**Key OOP Concepts:**
- **Controller Pattern**: Coordinates between user interface and business logic
- **Command Pattern**: Menu options as discrete command handlers
- **Single Responsibility**: Each method handles one specific operation
- **Error Handling**: Comprehensive exception management

## 🚀 Getting Started

### Prerequisites
- Python 3.7 or higher
- Windows PowerShell (for Windows users)
- No external dependencies required (uses only Python standard library)

### Installation

1. **Clone or Download**: Get the project files to your local machine
2. **Navigate to Directory**: Open your terminal and navigate to the project folder
```powershell
cd "c:\Users\sarth\OneDrive\Desktop\Projects\Library Management System"
```

3. **Run the Application**:
```powershell
python main.py
```

### First Run

The system initializes with sample data including:
- **3 Authors**: J.K. Rowling, George Orwell, Jane Austen
- **3 Books**: Harry Potter, 1984, Pride and Prejudice
- **2 Members**: Alice Johnson, Bob Smith

## 💻 Usage Guide

### Main Menu Navigation
The system provides an intuitive menu-driven interface:

```
1. 📚 Book Management      - Add, update, remove books
2. ✍️  Author Management   - Manage author information
3. 👥 Member Management    - Handle library memberships
4. 📖 Borrowing & Returns  - Process loans and returns
5. 🔍 Search & Browse      - Find books and browse collection
6. 📊 Reports & Statistics - View library analytics
7. ℹ️  System Information  - System status and details
8. 🚪 Exit System         - Close the application
```

### Example Operations

#### Adding a New Book
1. Select "Book Management" → "Add New Book"
2. Choose from existing authors or add a new author first
3. Enter book details: title, ISBN, publication year, genre, copies
4. System automatically creates bidirectional author-book relationship

#### Borrowing a Book
1. Select "Borrowing & Returns" → "Borrow Book"
2. View available books and registered members
3. Enter member ID and book ID
4. System validates member status and book availability
5. Automatic inventory update and transaction recording

#### Searching for Books
1. Select "Search & Browse" → Choose search criteria
2. Enter search terms (supports partial matching)
3. View results with availability status
4. Navigate to detailed book information

## 🔧 Advanced Features

### Data Validation
- **Input Sanitization**: All user inputs are validated and sanitized
- **Type Checking**: Automatic type conversion with error handling
- **Business Rules**: Enforcement of library-specific rules and constraints

### Error Handling
- **Graceful Degradation**: System continues operation despite individual failures
- **User-Friendly Messages**: Clear error messages with suggested solutions
- **Recovery Options**: Multiple attempts allowed for invalid inputs

### Relationship Management
- **Bidirectional Links**: Automatic maintenance of object relationships
- **Referential Integrity**: Prevents orphaned records and inconsistent states
- **Cascade Operations**: Related updates propagate automatically

### Performance Optimization
- **Dictionary Lookups**: O(1) average-case search performance
- **Memory Efficiency**: Objects shared rather than duplicated
- **Lazy Loading**: Data loaded only when needed

## 🧩 System Architecture

### Layer Architecture
```
┌─────────────────────────────────────┐
│         Presentation Layer          │
│    (LibraryManagementSystem)        │
├─────────────────────────────────────┤
│          Business Layer             │
│     (Library + Core Classes)        │
├─────────────────────────────────────┤
│           Data Layer                │
│    (In-Memory Collections)          │
└─────────────────────────────────────┘
```

### Design Patterns Used

1. **Facade Pattern**: Library class provides simplified interface
2. **Factory Pattern**: Centralized object creation with ID management
3. **Observer Pattern**: Automatic relationship updates
4. **Command Pattern**: Menu operations as discrete commands
5. **State Pattern**: Member and book status management
6. **Composition Pattern**: Library contains all entities
7. **Template Method**: Consistent CRUD operations across entities

## 📈 Extensibility

The system is designed for easy extension:

### Adding New Features
```python
class SpecializedBook(Book):
    """Example: Extend Book class for special collections"""
    def __init__(self, *args, special_category=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.__special_category = special_category

class DigitalLibrary(Library):
    """Example: Extend Library for digital collections"""
    def add_digital_book(self, ...):
        # Implementation for digital book management
        pass
```

### Integration Points
- **Database Integration**: Replace in-memory storage with database
- **API Development**: Add REST API layer for web/mobile apps
- **Authentication**: Implement user authentication and authorization
- **Reporting**: Add advanced analytics and reporting features

## 🛡️ Data Security

### Encapsulation Benefits
- **Data Protection**: Private attributes prevent direct manipulation
- **Controlled Access**: All data access through validated methods
- **State Consistency**: Business rules enforced at object level

### Validation Layers
1. **Input Validation**: User input sanitization and type checking
2. **Business Rules**: Library-specific constraint enforcement
3. **State Validation**: Object state consistency maintenance

## 🚨 Error Scenarios Handled

- **Invalid User Input**: Type mismatches, empty values, out-of-range numbers
- **Business Rule Violations**: Borrowing unavailable books, inactive member access
- **Data Inconsistencies**: Missing relationships, orphaned records
- **System Interruptions**: Graceful handling of Ctrl+C and unexpected exits

## 🧪 Testing Approach

While no automated tests are included, the system supports manual testing through:

### Test Scenarios
1. **CRUD Operations**: Create, read, update, delete for all entities
2. **Relationship Testing**: Verify bidirectional relationships
3. **Business Logic**: Test borrowing rules and constraints
4. **Edge Cases**: Empty collections, boundary values, invalid operations
5. **User Workflow**: Complete user journeys from start to finish

### Validation Methods
- **Sample Data**: Pre-loaded data for immediate testing
- **Error Simulation**: Invalid inputs to test error handling
- **State Verification**: Check object states after operations
- **Relationship Integrity**: Verify relationship consistency

## 🤝 Contributing

To extend or modify the system:

1. **Follow OOP Principles**: Maintain encapsulation, inheritance, and polymorphism
2. **Add Documentation**: Comment all new methods and classes thoroughly
3. **Validate Inputs**: Implement proper input validation and error handling
4. **Test Thoroughly**: Verify all new functionality with edge cases
5. **Maintain Relationships**: Ensure bidirectional relationships remain consistent

## 📋 Future Enhancements

### Planned Features
- **Database Persistence**: SQLite integration for data persistence
- **Advanced Search**: Full-text search with ranking
- **Fine Management**: Overdue book tracking and fine calculation
- **Reservation System**: Book reservation and hold management
- **Multi-Library Support**: Support for library branches
- **Export/Import**: Data export to CSV/JSON formats
- **Email Notifications**: Automated reminders and notifications

### Technical Improvements
- **Unit Testing**: Comprehensive test suite with pytest
- **Configuration Management**: External configuration files
- **Logging System**: Detailed operation logging
- **Performance Monitoring**: Response time and memory usage tracking
- **API Development**: RESTful API for external integrations

## 🏆 Educational Value

This project demonstrates:

### Object-Oriented Programming Concepts
- **Encapsulation**: Data hiding and controlled access
- **Inheritance**: Class hierarchies and code reuse
- **Polymorphism**: Method overriding and duck typing
- **Abstraction**: Complex operations hidden behind simple interfaces

### Software Design Principles
- **Single Responsibility**: Each class has one primary purpose
- **Open/Closed**: Open for extension, closed for modification
- **Dependency Inversion**: High-level modules don't depend on low-level modules
- **Interface Segregation**: Focused, role-specific interfaces

### Real-World Programming Practices
- **Error Handling**: Comprehensive exception management
- **Input Validation**: User input sanitization and validation
- **Documentation**: Thorough code documentation and comments
- **User Experience**: Intuitive interface design and feedback

## 📞 Support

For questions, issues, or suggestions:

1. **Code Review**: Examine the thoroughly commented source code
2. **Menu System**: Use the built-in help and navigation
3. **Error Messages**: Follow the descriptive error messages and suggestions
4. **Documentation**: Refer to this comprehensive README

## 📄 License

This project is created for educational purposes and demonstrates Object-Oriented Programming concepts in Python. Feel free to use, modify, and extend for learning and development purposes.

---

**Built with ❤️ using Python and Object-Oriented Programming principles**

*Celine Library Management System - Where books meet modern software design!* 📚✨
