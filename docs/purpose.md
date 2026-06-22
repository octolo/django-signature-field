## Project Purpose

**Django Signature Field** is a Django library that provides a field type for storing canvas signatures.

### Core Functionality

The library enables you to:

1. **Store signatures as binary data** (default):
   - Accept data URLs, base64 strings, or raw bytes
   - Persist PNG content in a `BinaryField`

2. **Store signatures as image files**:
   - Accept the same input formats
   - Persist PNG content via `ImageField` and `upload_to`

3. **SignatureField factory**:
   - Configure storage with `SignatureField(field_type="blob")` or `field_type="image"`
   - Blob mode is the default

### Architecture

The library provides:

- **`SignatureField`**: Factory that returns the appropriate concrete field
- **`SignatureBlobField`**: Binary storage implementation
- **`SignatureImageField`**: Image file storage implementation
- **`parse_signature_data`**: Shared decoder for canvas output

### Use Cases

- Sign contracts or forms in the browser
- Choose compact blob storage or file-based storage depending on deployment
- Reuse the same input format regardless of storage backend
