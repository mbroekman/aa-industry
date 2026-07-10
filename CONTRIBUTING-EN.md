# Contributing to this Project

Thank you for taking the time to contribute to Alliance Auth Industry Reforged! Collaboration makes the project more stable, faster, and better for everyone.

Below you will find the guidelines and steps to effectively contribute to the codebase.

______________________________________________________________________

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
1. [How Can I Contribute?](#how-can-i-contribute)
   - [Reporting Bugs](#reporting-bugs)
   - [Suggesting Features](#suggesting-features)
   - [Contributing Code](#contributing-code)
1. [Setting Up a Local Development Environment](#setting-up-a-local-development-environment)
1. [Style and Quality Guidelines](#style-and-quality-guidelines)
1. [The Pull Request Process](#the-pull-request-process)
1. [Communication and Feedback](#communication-and-feedback)

______________________________________________________________________

## 1. Code of Conduct

We strive for an open, welcoming, and respectful community. We expect all contributors to communicate professionally and provide constructive feedback, both within issues and pull requests, and on the connected communication channels.

## 2. How Can I Contribute?

### Reporting Bugs

Found a bug or unexpected behavior? Please check the existing **Issues** first to see if the problem has already been reported. If not, open a new issue containing the following information:

- A clear, descriptive title.
- Exact steps to reproduce the issue.
- Expected behavior versus actual behavior.
- Relevant log files, tracebacks, and environment details (Python version, OS, specific Django/Alliance Auth plugin versions if applicable).

### Suggesting Features

Suggestions for new functionalities are highly appreciated! Open an issue and describe:

- The desired functionality.
- Why it is valuable for the project (the concrete use-case).
- Any ideas regarding the technical architecture or implementation.

### Contributing Code

Want to directly fix a bug or implement a feature?

1. Find an existing issue or open one first to discuss your plans.
1. Fork the repository and create a new dedicated branch for your changes.

______________________________________________________________________

## 3. Setting Up a Local Development Environment

Follow these steps to set up a clean and working development environment:

1. **Clone the repository:**

   ```bash
   git clone https://github.com/mbroekman/aa-industry.git
   cd aa-industry
   ```

1. **Create and activate a virtual environment:**

   ```bash
   python -m venv venv

   # On Linux/macOS:
   source venv/bin/activate

   # On Windows (Command Prompt):
   venv\Scripts\activate

   # On Windows (PowerShell):
   .\venv\Scripts\Activate.ps1
   ```

1. **Install the dependencies (including development tools):**

   ```bash
   pip install --upgrade pip
   pip install -e .
   pip install tox pre-commit
   pre-commit install
   ```

1. **Verify that the test suite runs successfully:**

   ```bash
   make tox_tests
   ```

______________________________________________________________________

## 4. Style and Quality Guidelines

To keep the codebase organized and maintainable, we enforce strict standards:

- **Python Code Style:** We closely follow the **PEP 8** guidelines.
- **Formatting & Linting:** We use automated tools to ensure code consistency. Always run these tools before making a commit:
  ```bash
  # Run all configured pre-commit hooks (Ruff, Black, etc)
  make pre-commit-checks
  ```
- **Docstrings & Type Hinting:** Write clear docstrings (preferably following Google or NumPy style) for new functions, methods, and classes. Use type hinting where possible to optimize readability and tooling support.
- **Database Migrations:** If you make changes to data models (for example, within Django apps), do not forget to generate the corresponding migration files and include them in your commit:
  ```bash
  python manage.py makemigrations industry_reforged
  ```

______________________________________________________________________

## 5. The Pull Request Process

When your code is ready to be reviewed, follow these steps:

1. **Keep branches focused:** Ensure your branch addresses only one specific issue or functionality.
1. **Write tests:** Ensure new code is covered by unit tests and existing integration tests still pass completely.
1. **Update documentation:** Adjust any READMEs, inline documentation, or docstrings if you change functionality or configurations.
1. **Commit messages:** Write clear, active commit messages based on conventions (e.g., `feat: add push-mechanism via Kafka` or `fix: resolve validation error in models`).
1. **Push and open a PR:** Push your branch to the remote repository and open a Pull Request (PR) to the `develop` or `main` branch.
1. **Code Review:** At least one core developer will review your code. Constructively process any feedback.

______________________________________________________________________

## 6. Communication and Feedback

If you have questions, want to brainstorm about the architecture, or need direct feedback:

- Utilize the discussion options in GitHub Issues or within the Pull Request itself.
- For real-time consultation and community feedback, you can visit the project's Discord channel.

Thank you for your contribution! This project grows and improves thanks to developers like you.
