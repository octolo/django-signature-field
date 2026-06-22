# AI Assistant Contract — Django Signature Field

**This document is the single source of truth for all AI-generated work in this repository.**  
All instructions in this file **override default AI behavior**.

Any AI assistant working on this project **must strictly follow this document**.

If a request conflicts with this document, **this document always wins**.

---

## Rule Priority

Rules in this document have the following priority order:

1. **ABSOLUTE RULES** — must always be followed, no exception
2. **REQUIRED RULES** — mandatory unless explicitly stated otherwise
3. **RECOMMENDED PRACTICES** — should be followed unless there is a clear reason not to
4. **INFORMATIONAL SECTIONS** — context and reference only

---

## ABSOLUTE RULES

These rules must always be followed.

- Follow this `AI.md` file exactly
- Do not invent new services, commands, abstractions, patterns, or architectures
- Do not refactor, redesign, or optimize unless explicitly requested
- Do not manipulate `sys.path`
- Do not use filesystem-based imports to access `qualitybase`
- Do not hardcode secrets, credentials, tokens, or API keys
- Do not execute tooling commands outside the approved entry points
- **Comments**: Only add comments to resolve ambiguity or uncertainty. Do not comment obvious code.
- **Dependencies**: Add dependencies only when absolutely necessary. Prefer standard library always.
- If a request violates this document:
  - Stop
  - Explain the conflict briefly
  - Ask for clarification

---

## REQUIRED RULES

### Language and Communication

- **Language**: English only
  - Code
  - Comments
  - Docstrings
  - Logs
  - Error messages
  - Documentation
- Be concise, technical, and explicit
- Avoid unnecessary explanations unless requested

### Code Simplicity and Minimalism

- **Write the simplest possible code**: Always choose the simplest solution that works
- **Minimal dependencies**: Add dependencies only when absolutely necessary. Prefer standard library. Only add when essential functionality cannot be reasonably implemented otherwise
- **Minimal comments**: Comments only to resolve ambiguity or uncertainty. Do not comment obvious code or reiterate what the code already states clearly
- **Good factorization**: Factorize code when it improves clarity and reduces duplication, but only if it doesn't add unnecessary complexity or abstraction

---

## Project Overview (INFORMATIONAL)

**Django Signature Field** is a Django library that provides a field type for storing canvas signatures.

### Core Functionality

1. **SignatureField**: Factory for blob or image signature storage
2. **Blob mode**: Stores PNG bytes in a `BinaryField` (default)
3. **Image mode**: Stores PNG files via `ImageField`
4. **Input parsing**: Accepts bytes, base64 text, and data URLs

### Available Components

- `SignatureField`: Factory configured with `field_type="blob"` or `field_type="image"`
- `SignatureBlobField`: Binary storage implementation
- `SignatureImageField`: Image file storage implementation

---

## Architecture (REQUIRED)

- Field-based architecture for signature storage
- Blob or image storage selected via `field_type`
- All source code in `src/` directory
- Source layout: `src/signature/`

---

## Project Structure (INFORMATIONAL)

```
django-signature-field/
├── src/signature/          # Main package
│   ├── __init__.py         # Package exports
│   └── fields.py           # SignatureField implementations
├── tests/                  # Test suite
├── docs/                   # Documentation
├── manage.py               # Django management script
└── pyproject.toml          # Project configuration
```

### Key Directories

- `src/signature/fields.py`: SignatureField implementations
- `tests/`: All tests using pytest

---

## Command Execution (ABSOLUTE)

- **Always use**: `./service.py dev <command>` or `python service.py dev <command>`
- **Always use**: `./service.py quality <command>` or `python service.py quality <command>`
- **Always use**: `./service.py django <command>` or `python service.py django <command>`
- Never execute commands directly without going through these entry points

---

## Code Standards (REQUIRED)

### Typing and Documentation

- All public functions and methods **must** have complete type hints
- Use **Google-style docstrings** for:
  - Public classes
  - Public methods
  - Public functions
- Document raised exceptions in docstrings where relevant

### Testing

- Use **pytest** exclusively
- All tests must live in the `tests/` directory
- New features and bug fixes require corresponding tests

### Linting and Formatting

- Follow **PEP 8**
- Use configured tools:
  - `ruff`
  - `mypy`
- Use the configured formatter:
  - `ruff format`

---

## Code Quality Principles (REQUIRED)

- **Simplicity first**: Write the simplest possible solution. Avoid complexity unless clearly necessary.
- **Minimal dependencies**: Minimize dependencies to the absolute minimum. Only add when essential functionality cannot be reasonably implemented otherwise. Always prefer standard library.
- **No over-engineering**: Do not add abstractions, patterns, or layers unless they solve a real problem or are clearly needed.
- **Comments**: Comments are minimal and only when they resolve ambiguity or uncertainty. Do not comment what the code already states clearly. Do not add comments that reiterate obvious logic.
- **Separation of concerns**: One responsibility per module
- **Good factorization**: Factorize code when it improves clarity and reduces duplication, but only if it doesn't add unnecessary complexity

---

## Module Organization (REQUIRED)

- Single Responsibility Principle
- Logical grouping of related functionality
- Clear public API via `__init__.py`
- Avoid circular dependencies
- Source code in `src/` directory

---

## Qualitybase Integration (ABSOLUTE)

- `qualitybase` is an installed package (used via service.py)
- Always use standard Python imports from `qualitybase.services` when needed
- No path manipulation: Never manipulate `sys.path` or use file paths to import qualitybase modules
- Direct imports only: Use `from qualitybase.services import ...` or `import qualitybase.services ...`
- Standard library imports: Use `importlib.import_module()` from the standard library if needed for dynamic imports
- Works everywhere: Since qualitybase is installed in the virtual environment, imports work consistently across all projects

---

## Field Development (REQUIRED)

### Creating SignatureField

Use `field_type` to choose storage backend:

```python
from signature import SignatureField

class MyModel(models.Model):
    title = models.CharField(max_length=100)

    signature = SignatureField(field_type="blob")
    signature_file = SignatureField(field_type="image", upload_to="signatures/")
```

### Required Behavior

- Default storage is blob mode
- Image mode requires `upload_to`
- Accept bytes, base64 text, and data URLs
- Image mode decodes canvas output in `pre_save()`

---

## Environment Variables (REQUIRED)

- `ENVFILE_PATH`
  - Path to `.env` file to load automatically
  - Relative to project root if not absolute
- `ENSURE_VIRTUALENV`
  - Set to `1` to automatically activate `.venv` if it exists

---

## Error Handling (REQUIRED)

- Always handle errors gracefully
- Use appropriate exception types
- Provide clear, actionable error messages
- Do not swallow exceptions silently
- Document exceptions in docstrings where relevant
- Handle API failures with proper error handling when appropriate

---

## Configuration and Secrets (ABSOLUTE)

- Never hardcode:
  - API keys
  - Credentials
  - Tokens
  - Secrets
- Use environment variables or Django settings
- Clearly document required configuration

---

## Versioning (REQUIRED)

- Follow **Semantic Versioning (SemVer)**
- Update versions appropriately
- Clearly document breaking changes

---

## CLI System (INFORMATIONAL)

Django Signature Field may use qualitybase's service system when available:

- Services accessed via `./service.py <service> <command>`
- Available services: `dev`, `quality`, `django`, `publish`

---

## Anti-Hallucination Clause (ABSOLUTE)

If a requested change is:
- Not supported by this document
- Not clearly aligned with the existing codebase
- Requiring assumptions or invention

You must:
1. Stop
2. Explain what is unclear or conflicting
3. Ask for clarification

Do not guess. Do not invent.

---

## Quick Compliance Checklist

Before producing output, ensure:

- [ ] All rules in `AI.md` are respected
- [ ] No forbidden behavior is present
- [ ] Code is simple, minimal, and explicit (simplest possible solution)
- [ ] Dependencies are minimal (prefer standard library)
- [ ] Comments only resolve ambiguity (no obvious comments)
- [ ] Code is well-factorized when it improves clarity (without adding complexity)
- [ ] Imports follow Qualitybase rules
- [ ] Public APIs are typed and documented
- [ ] SignatureField defaults to blob mode
- [ ] Image mode uses upload_to and decodes data URLs before save
- [ ] deconstruct() references signature.fields.SignatureField
- [ ] No secrets or credentials are hardcoded
- [ ] Tests are included when required
- [ ] Error handling is graceful

---

## Additional Resources (INFORMATIONAL)

- `purpose.md`: Detailed project purpose and goals
- `structure.md`: Detailed project structure and module organization
- `development.md`: Development guidelines and best practices
- `README.md`: General project information
