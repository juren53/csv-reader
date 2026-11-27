"""Excel number formats: display, parsing edited text, and the save round trip."""
import datetime as dt

import openpyxl
import pytest

from cell_format import format_cell, parse_date, parse_number

ACCOUNTING = '_("$"* #,##0.00_);_("$"* \\(#,##0.00\\);_("$"* "-"??_);_(@_)'


@pytest.mark.parametrize("value, fmt, expected", [
    # numbers
    (12.5, r'\$#,##0.00', '$12.50'),
    (1250, '#,##0.00', '1,250.00'),
    (1234567.891, '#,##0', '1,234,568'),
    (0.256, '0%', '26%'),
    (0.256, '0.00%', '25.60%'),
    (-1234.5, '#,##0.00_);(#,##0.00)', '(1,234.50)'),
    (1234.5, '#,##0.00_);(#,##0.00)', '1,234.50'),
    (-5, '[Red]0;[Blue]-0', '-5'),
    (-5, '0', '-5'),
    (3.14159, '0.0#', '3.14'),
    (3.1, '0.0#', '3.1'),
    (0.5, '#.00', '.50'),
    (7, '000', '007'),
    (1500000, '#,##0,"K"', '1,500K'),
    (12.5, '[$€-407] #,##0.00', '€ 12.50'),
    (1234.5, ACCOUNTING, '$1,234.50'),
    (-1234.5, ACCOUNTING, '$(1,234.50)'),
    (0, ACCOUNTING, '$-'),
    (1.5e10, '0.00E+00', '1.50E+10'),
    (0, '#,##0', '0'),
    # General
    (42, 'General', '42'),
    (3.0, 'General', '3'),
    (0.1 + 0.2, 'General', '0.3'),
    (True, 'General', 'TRUE'),
    ('01234', '@', '01234'),
    (None, '0.00', ''),
    # dates and times
    (dt.datetime(2026, 9, 3), r'yyyy\-mm\-dd', '2026-09-03'),
    (dt.datetime(2026, 9, 3), 'mm-dd-yy', '9/3/2026'),          # builtin 14 = US short date
    (dt.datetime(2026, 9, 3), 'd-mmm-yy', '3-Sep-26'),
    (dt.datetime(2026, 9, 3), 'dddd, mmmm d, yyyy', 'Thursday, September 3, 2026'),
    (dt.datetime(2026, 9, 3), '[$-409]mmmm d, yyyy;@', 'September 3, 2026'),
    (dt.datetime(2026, 9, 3, 14, 5, 9), 'm/d/yy h:mm', '9/3/2026 14:05'),
    (dt.datetime(2026, 9, 3, 14, 5, 9), 'h:mm AM/PM', '2:05 PM'),
    (dt.datetime(2026, 1, 5, 8, 7), 'mm:ss', '07:00'),          # mm before ss = minutes
    (dt.time(9, 30), 'h:mm:ss', '9:30:00'),
    (dt.datetime(2026, 9, 3), 'General', '2026-09-03'),
    (dt.datetime(2026, 9, 3, 10, 30), 'General', '2026-09-03 10:30:00'),
])
def test_format_cell(value, fmt, expected):
    assert format_cell(value, fmt) == expected


@pytest.mark.parametrize("value, fmt", [
    (5, '000-0000'),        # literal inside digits: not supported
    (5, '# ?/?'),           # fractions
    ('text', '0.00'),       # text in a number format
])
def test_unsupported_formats_fall_back(value, fmt):
    assert format_cell(value, fmt) == str(value)


@pytest.mark.parametrize("text, expected", [
    ("$1,250.00", 1250.0),
    ("(5)", -5),
    ("12%", 0.12),
    ("-3", -3),
    ("13", 13),
    ("€ 12.50", 12.5),
    ("1.50E+10", 1.5e10),
    ("abc", None),
    ("1.2.3", None),
    ("", None),
])
def test_parse_number(text, expected):
    assert parse_number(text) == expected


@pytest.mark.parametrize("text, fmt, expected", [
    ("9/4/2026", "mm-dd-yy", dt.datetime(2026, 9, 4)),
    ("2026-09-04", r"yyyy\-mm\-dd", dt.datetime(2026, 9, 4)),
    ("4-Sep-26", "d-mmm-yy", dt.datetime(2026, 9, 4)),
    ("2:30 PM", "h:mm AM/PM", dt.datetime(1900, 1, 1, 14, 30)),
    ("2026-09-04 10:00", "General", dt.datetime(2026, 9, 4, 10)),   # ISO fallback
    ("Sept 4", "m/d/yyyy", None),
])
def test_parse_date(text, fmt, expected):
    assert parse_date(text, fmt) == expected


@pytest.mark.parametrize("text, original, fmt, expected", [
    ("$13.00", 12.5, r'\$#,##0.00', 13.0),
    ("13", 12.5, r'\$#,##0.00', 13),
    ("30%", 0.25, '0%', 0.3),
    ("9/4/2026", dt.datetime(2026, 9, 3), 'mm-dd-yy', dt.datetime(2026, 9, 4)),
    ("9/4/2026", dt.date(2026, 9, 3), 'mm-dd-yy', dt.date(2026, 9, 4)),
    ("$5", None, r'\$#,##0.00', 5),                  # blank cell with a currency format
    ("9/4/2026", None, 'm/d/yyyy', dt.datetime(2026, 9, 4)),
    ("007", None, None, "007"),                      # blank General cell keeps leading zeros
    ("TRUE", False, None, True),
])
def test_coerce_with_format(app_module, text, original, fmt, expected):
    result = app_module.coerce_cell_value(text, original, fmt)
    assert result == expected
    assert type(result) is type(expected)


# ------------------------------------------------------------- in the app

@pytest.fixture
def formatted_xlsx(tmp_path):
    path = tmp_path / "formatted.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["Item", "Price", "Date", "Share", "Count", "Blank $"])
    ws.append(["Mug", 12.5, dt.datetime(2026, 9, 3), 0.256, 1250, None])
    ws.append(["Tote", 1234.5, dt.datetime(2026, 10, 15), 0.5, 7, None])
    for r in (2, 3):
        ws[f"B{r}"].number_format = r'\$#,##0.00'
        ws[f"C{r}"].number_format = 'mm-dd-yy'
        ws[f"D{r}"].number_format = '0.0%'
        ws[f"E{r}"].number_format = '#,##0'
        ws[f"F{r}"].number_format = r'\$#,##0.00'
    wb.save(path)
    return path


def test_cells_display_with_excel_formats(window, formatted_xlsx):
    window.loadDataFile(str(formatted_xlsx))
    assert window.csv_data[0] == ["Mug", "$12.50", "9/3/2026", "25.6%", "1,250", ""]
    assert window.csv_data[1] == ["Tote", "$1,234.50", "10/15/2026", "50.0%", "7", ""]


def test_formatted_edits_save_as_typed_values(window, formatted_xlsx):
    window.loadDataFile(str(formatted_xlsx))
    window._onTableCellEdited(0, 1, "$13")          # price
    window._onTableCellEdited(0, 2, "9/4/2026")     # date in the cell's own format
    window._onTableCellEdited(0, 3, "30%")          # percentage
    window._onTableCellEdited(0, 4, "2,500")        # thousands separator
    window._onTableCellEdited(0, 5, "5")            # blank currency cell
    window.saveFile()

    ws = openpyxl.load_workbook(formatted_xlsx).active
    assert ws["B2"].value == 13
    assert ws["C2"].value == dt.datetime(2026, 9, 4)
    assert ws["D2"].value == pytest.approx(0.3)
    assert ws["E2"].value == 2500
    assert ws["F2"].value == 5
    assert ws["B2"].number_format == r'\$#,##0.00'   # formats are untouched
    # After saving, edited cells are shown in their Excel format
    assert window.csv_data[0] == ["Mug", "$13.00", "9/4/2026", "30.0%", "2,500", "$5.00"]


def test_unchanged_formatted_cells_are_not_rewritten(window, formatted_xlsx):
    window.loadDataFile(str(formatted_xlsx))
    window._onTableCellEdited(0, 0, "Big Mug")      # edit text only
    window.saveFile()
    ws = openpyxl.load_workbook(formatted_xlsx).active
    assert ws["B2"].value == 12.5                    # not re-parsed from "$12.50"
    assert ws["D2"].value == 0.256                   # not rounded to the shown 25.6%
