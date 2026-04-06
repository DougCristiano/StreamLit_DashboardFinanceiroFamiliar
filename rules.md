# Project Rules & Guidelines

## Code Standards

### Python Style
- Follow PEP 8 guidelines
- Use type hints for all public functions
- Docstrings in Google style format for all functions and modules
- Maximum line length: 100 characters
- Use black for formatting: `black .`
- Lint with flake8: `flake8 .`

### File Organization
- `app.py` — Main entry point
- `utils/` — Reusable functions and logic
- `ui/` — Streamlit components and layout
- `styles/` — CSS and visual theming

### Naming Conventions
- Variables and functions: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Classes: `PascalCase`
- Private functions: prefix with `_`

## Development Workflow

### Before Committing
1. Run `black .` to format code
2. Run `flake8 .` to check style issues
3. Run `mypy .` to validate types
4. Run `pytest` to ensure tests pass

### Adding New Features
1. Create a branch from `main`
2. Write tests for new functionality
3. Update docstrings and type hints
4. Update README if needed
5. Ensure all checks pass before PR

## Data & Privacy
- Do NOT commit `.venv/`, `__pycache__/`, or `.pytest_cache/`
- JSON files (`membros.json`, `categorias.json`) contain local data only
- For production use, consider database storage and authentication

