# AI-Devtools-Zoomcamp-HW

This repository contains homework projects for the AI Dev Tools Zoomcamp 2025.

## Project Structure

- **01-todo**: [Django TODO Application](01-todo/)
  - Create, edit, and delete TODO items
  - Assign due dates to tasks with calendar picker
  - Mark todos as resolved/unresolved with toggle
  - Bulk select and delete multiple todos
  - Vibrant pastel UI with gradient buttons, shadows, and animations
  - 133 comprehensive tests with 100% passing rate
  - Fully responsive Bootstrap 5 design

### References

- [AI Dev Tools Zoomcamp - Homework 1](https://github.com/DataTalksClub/ai-dev-tools-zoomcamp/blob/main/cohorts/2025/01-overview/homework.md)

## Getting Started

Each project folder contains its own Django setup. To run a project:

```bash
cd 01-todo
python3 manage.py runserver 8001
```

Then visit: http://localhost:8001/todos/

### Running Tests

To run all tests for the TODO application:

```bash
cd 01-todo
python3 manage.py test todos.tests -v 2
```

This will run 133 comprehensive tests covering:
- **Models**: Data validation, field constraints, ordering
- **Views**: CRUD operations, redirects, error handling
- **Forms**: Input validation, special characters, date handling
- **Integration**: Complete user workflows, data persistence
- **Edge Cases**: Boundary conditions, special characters, concurrent operations
