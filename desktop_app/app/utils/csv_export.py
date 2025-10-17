from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, MutableSequence, Sequence, Tuple, Union

HeaderSpec = Union[str, Tuple[str, str]]
RowFilter = Callable[[Mapping[str, Any]], bool]
ValueFilter = Callable[[Any], Any]

__all__ = [
    "generate_csv",
    "export_csv",
]


def _normalise_headers(headers: Sequence[HeaderSpec]) -> Tuple[Tuple[str, str], ...]:
    normalised: MutableSequence[Tuple[str, str]] = []
    for header in headers:
        if isinstance(header, tuple):
            key, label = header
        else:
            key, label = header, header
        normalised.append((str(key), str(label)))
    return tuple(normalised)


def generate_csv(
    rows: Iterable[Mapping[str, Any]],
    headers: Sequence[HeaderSpec],
    *,
    row_filter: RowFilter | None = None,
    value_filters: Mapping[str, ValueFilter] | None = None,
    delimiter: str = ",",
) -> str:
    """Generate a CSV document from a sequence of dictionaries."""

    header_pairs = _normalise_headers(headers)
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=delimiter)
    writer.writerow([label for _, label in header_pairs])

    for row in rows:
        if row_filter and not row_filter(row):
            continue

        values: list[Any] = []
        for key, _ in header_pairs:
            value = row.get(key, "")
            if value_filters and key in value_filters:
                value = value_filters[key](value)
            values.append(value)
        writer.writerow(values)

    return buffer.getvalue()


def export_csv(
    path: Union[str, Path],
    rows: Iterable[Mapping[str, Any]],
    headers: Sequence[HeaderSpec],
    *,
    encoding: str = "utf-8",
    newline: str = "",
    row_filter: RowFilter | None = None,
    value_filters: Mapping[str, ValueFilter] | None = None,
    delimiter: str = ",",
) -> Path:
    """Write the CSV output to the provided ``path`` and return it as :class:`Path`."""

    content = generate_csv(
        rows,
        headers,
        row_filter=row_filter,
        value_filters=value_filters,
        delimiter=delimiter,
    )

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding=encoding, newline=newline)
    return path
