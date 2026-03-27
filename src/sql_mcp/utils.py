import csv
import io
import json
from typing import Any


def format_table(headers: list[str], rows: list[tuple[Any, ...]]) -> str:
    if not headers:
        return "(no columns)"
    if not rows:
        return "(no rows)"

    str_rows = []
    widths = [len(h) for h in headers]
    for row in rows:
        str_row = []
        for i, cell in enumerate(row):
            if cell is None:
                s = "NULL"
            elif isinstance(cell, bool):
                s = "true" if cell else "false"
            elif isinstance(cell, (bytes, bytearray)):
                s = "<binary>"
            else:
                s = str(cell)
            str_row.append(s)
            widths[i] = max(widths[i], len(s))
        str_rows.append(str_row)

    sep = " | "
    header_row = sep.join(h.ljust(widths[i]) for i, h in enumerate(headers))
    divider = "-+-".join("-" * w for w in widths)
    body = [sep.join(c.ljust(widths[i]) for i, c in enumerate(row)) for row in str_rows]
    return "\n".join([header_row, divider] + body)


def format_json(headers: list[str], rows: list[tuple[Any, ...]]) -> str:
    result = []
    for row in rows:
        obj: dict[str, Any] = {}
        for i, header in enumerate(headers):
            value = row[i] if i < len(row) else None
            if isinstance(value, (bytes, bytearray)):
                obj[header] = "<binary>"
            elif hasattr(value, "isoformat"):
                obj[header] = value.isoformat()
            else:
                obj[header] = value
        result.append(obj)
    return json.dumps(result, indent=2, default=str)


def format_csv(headers: list[str], rows: list[tuple[Any, ...]]) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    for row in rows:
        str_row = []
        for cell in row:
            if cell is None:
                str_row.append("")
            elif isinstance(cell, (bytes, bytearray)):
                str_row.append("<binary>")
            elif hasattr(cell, "isoformat"):
                str_row.append(cell.isoformat())
            else:
                str_row.append(str(cell))
        writer.writerow(str_row)
    return output.getvalue()


def result_summary(headers: list[str], rows: list[tuple[Any, ...]]) -> str:
    return f"{len(rows)} row(s), {len(headers)} column(s)"


def escape_sql_string(value: str) -> str:
    if not value:
        return "''"
    return f"'{value.replace(chr(39), chr(39) * 2)}'"
