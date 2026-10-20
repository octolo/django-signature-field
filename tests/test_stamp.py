"""Tests for localized signature timestamps."""

from datetime import datetime, timezone

import pytest
from django.utils.formats import date_format
from django.utils.translation import override

from signature.stamp import format_signature_timestamp


@pytest.mark.parametrize(
    ('language', 'expected_prefix'),
    [
        ('fr', 'Signé le : '),
        ('fr-fr', 'Signé le : '),
        ('en-us', 'Signed: '),
    ],
)
def test_signature_timestamp_uses_active_language(
    language: str,
    expected_prefix: str,
) -> None:
    when = datetime(2026, 10, 20, 8, 46, tzinfo=timezone.utc)

    with override(language):
        expected_date = date_format(when, 'SHORT_DATETIME_FORMAT')
        label = format_signature_timestamp(when)

    assert label == f'{expected_prefix}{expected_date}'
