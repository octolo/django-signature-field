## Assistant Guidelines

This file provides general guidelines for the AI assistant working on this project.

For detailed information, refer to:
- `AI.md` - Condensed reference guide for AI assistants (start here)
- `purpose.md` - Project purpose and goals
- `structure.md` - Project structure and module organization
- `development.md` - Development guidelines and best practices

### Quick Reference

- Always use `./service.py dev <command>` or `python service.py dev <command>` for project tooling when available
- Always use `./service.py quality <command>` or `python service.py quality <command>` for quality checks when available
- Always use `./service.py django <command>` or `python service.py django <command>` for Django commands when available
- Maintain clean module organization and separation of concerns
- Default to English for all code artifacts (comments, docstrings, logging, error strings, documentation snippets, etc.)
- Follow Python best practices and quality standards
- Keep dependencies minimal and prefer standard library
- Ensure all public APIs have type hints and docstrings
- Write tests for new functionality
- Source code in `src/` directory

### Django Signature Field Guidelines

- **Field factory**: `SignatureField(field_type="blob")` or `field_type="image"`
- **Default mode**: Blob storage
- **Image mode**: Requires `upload_to`
- **Input formats**: bytes, base64, and data URLs

### Field Implementation Checklist

When working with SignatureField:

- [ ] `field_type` is `"blob"` or `"image"`
- [ ] Blob mode uses `BinaryField` storage
- [ ] Image mode uses `ImageField` with `upload_to`
- [ ] Data URLs and base64 input are decoded before save
- [ ] `deconstruct()` points to `signature.fields.SignatureField`
