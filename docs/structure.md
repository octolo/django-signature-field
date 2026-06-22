## Project Structure

Django Signature Field follows a standard Python package structure with source code in `src/`.

### General Structure

```
django-signature-field/
├── src/
│   └── signature/           # Main package directory
│       ├── __init__.py      # Package exports
│       └── fields.py        # SignatureField and implementations
├── tests/                   # Test suite
│   ├── settings.py          # Django test settings
│   └── app/                 # Test application
│       ├── models.py        # Test models
│       └── ...
├── docs/                    # Documentation
├── manage.py                # Django management script
├── pyproject.toml           # Project configuration
└── README.md                # Project README
```

### Module Organization Principles

- **Single Responsibility**: Each module has a clear, single purpose
- **Separation of Concerns**: Keep different concerns in separate modules
- **Clear Exports**: Use `__init__.py` to define public API
- **Logical Grouping**: Organize related functionality together
- **Source Layout**: All source code in `src/` directory

### Field Organization

The `fields.py` module provides:

- **`SignatureField`**: Factory for blob or image storage
- **`SignatureBlobField`**: Binary storage field
- **`SignatureImageField`**: Image file storage field
- **`parse_signature_data`**: Decode canvas output

### Package Exports

The public API is defined in `src/signature/__init__.py`:

- **Fields**: `SignatureField`, `SignatureBlobField`, `SignatureImageField`
