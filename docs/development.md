## Development Guidelines

### General Rules

- Always execute project tooling through `./service.py <service> <command>` or `python service.py <service> <command>` when available.
- Default to English for all code artifacts (comments, docstrings, logging, error strings, documentation snippets, etc.) regardless of the language used in discussions.
- Keep comments minimal and only when they clarify non-obvious logic.
- Avoid reiterating what the code already states clearly.
- Add comments only when they resolve likely ambiguity or uncertainty.

### Simplicity and Dependencies

- **Keep functions simple**: Always write the simplest possible functions. Avoid unnecessary complexity unless it's clearly evident or necessary.
- **Minimize dependencies**: Limit dependencies to the absolute minimum. Only add new dependencies when they provide essential functionality that cannot be reasonably implemented otherwise.
- **Prefer standard library**: Use Python standard library whenever possible before adding external dependencies.
- **Avoid over-engineering**: Don't add abstractions, patterns, or layers unless they solve a real problem or are clearly needed.

### Code Quality

- **Testing**: Use pytest for all tests. Place tests in `tests/` directory.
- **Type Hints**: All public functions and methods must have complete type hints.
- **Docstrings**: Use Google-style docstrings for all public classes, methods, and functions.
- **Linting**: Follow PEP 8 and use the configured linters (ruff, mypy, etc.).
- **Formatting**: Use the configured formatter (ruff format, etc.).

### Module Organization

- Keep related functionality grouped together in logical modules
- Maintain clear separation of concerns between modules
- Use `__init__.py` to define clean public APIs
- Avoid circular dependencies
- Source code in `src/` directory

### Field Development

- **Field factory**: Use `SignatureField(field_type="blob")` or `field_type="image"`
- **Default mode**: Blob storage via `BinaryField`
- **Image mode**: Requires `upload_to` and uses `ImageField`
- **Input parsing**: Accept bytes, base64 text, and data URLs through `parse_signature_data`
- **Optional signatures**: Fields default to `blank=True`

### Error Handling

- Always handle errors gracefully
- Provide clear, actionable error messages
- Use appropriate exception types
- Document exceptions in docstrings
- Handle API failures with proper error handling when appropriate

### Configuration and Secrets

- Never hardcode API keys, credentials, or sensitive information
- Use environment variables or Django settings for configuration
- Provide clear documentation on required configuration
- Use Django settings for configuration data when appropriate

### Versioning

- Follow semantic versioning (SemVer)
- Update version numbers appropriately for changes
- Document breaking changes clearly
