# django-signature-field

Django field for storing canvas signatures as binary data or image files.

## Purpose

Store signature pad output in the database either as a binary blob (default) or as an uploaded PNG file.

## Installation

```bash
pip install django-signature-field
```

## Quick Start

```python
from django.db import models
from signature import SignatureField


class Contract(models.Model):
    title = models.CharField(max_length=100)

    # Default: binary storage
    signature = SignatureField()

    # Or explicitly as blob
    signature_blob = SignatureField(field_type="blob")

    # Or as image file
    signature_image = SignatureField(field_type="image", upload_to="signatures/")
```

## Input formats

The field accepts:

- Raw bytes
- Base64 text
- Data URLs (`data:image/png;base64,...`)

## Field modes

| `field_type` | Storage | Django field |
|--------------|---------|--------------|
| `"blob"` (default) | Raw PNG bytes in database | `BinaryField` |
| `"image"` | PNG file on storage | `ImageField` |

## Development

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT
