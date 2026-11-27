"""Saving an XLSX patches only edited cells into the original workbook."""
import datetime
import os
import shutil
from pathlib import Path

import openpyxl
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


# ------------------------------------------------------------- unit: coercion

@pytest.mark.parametrize("text, original, expected", [
    ("9", 5, 9),
    ("2.75", 5, 2.75),
    ("1e3", 2.0, 1000.0),
    ("abc", 5, "abc"),                 # not a number: kept as text
    ("02134", "01234", "02134"),       # text cell keeps leading zero
    ("42", "x", "42"),                 # text cell stays text
    ("42", None, 42),                  # blank cell: plain numbers become numbers
    ("007", None, "007"),              # ...but leading zeros stay text
    ("", 5, None),                     # clearing empties the cell
    ("false", True, False),
    ("maybe", True, "maybe"),
    ("2026-05-06 00:00:00", datetime.datetime(2026, 1, 2), datetime.datetime(2026, 5, 6)),
    ("2026-05-06", datetime.date(2026, 1, 2), datetime.date(2026, 5, 6)),
    ("not a date", datetime.datetime(2026, 1, 2), "not a date"),
])
def test_coerce_cell_value(app_module, text, original, expected):
    result = app_module.coerce_cell_value(text, original)
    assert result == expected
    assert type(result) is type(expected)


# ------------------------------------------------------------ save round trip

def test_save_patches_only_edited_cells(window, orders_xlsx):
    window.loadDataFile(str(orders_xlsx))
    window._onTableCellEdited(1, 1, "9")                     # Qty: number
    window._onTableCellEdited(0, 4, "02134")                 # Zip: text with leading 0
    window._onTableCellEdited(0, 3, "2026-05-06 00:00:00")   # Date
    window._onTableCellEdited(2, 2, "")                      # clear a number
    window.saveFile()

    wb = openpyxl.load_workbook(orders_xlsx)
    o = wb["Orders"]
    assert wb.sheetnames == ["Orders", "Customers", "Notes"]
    assert o["B3"].value == 9
    assert o["E2"].value == "02134"
    assert o["D2"].value == datetime.datetime(2026, 5, 6)
    assert o["C4"].value is None
    # untouched content survives
    assert o["F2"].value == "=B2*C2" and o["F4"].value == "=B4*C4"
    assert o["C2"].value == 2.5 and o["A2"].value == 1
    assert o["A1"].font.b
    assert o.column_dimensions["D"].width == 22
    assert o["C2"].number_format == "$#,##0.00"
    assert wb["Customers"]["B2"].value == "Austin"
    assert wb["Notes"]["A1"].value == "keep me"
    assert not window.is_modified


def test_edits_after_header_reassignment_land_on_right_rows(window, orders_xlsx):
    window.loadDataFile(str(orders_xlsx))
    window.reassignHeaderRow(1)                # sheet row 3 becomes the header
    window._onTableCellEdited(2, 0, "333")     # data row 2 == sheet row 4
    window._onTableCellEdited(0, 4, "Zip!")    # data row 0 == old header, sheet row 1
    window.saveFile()

    o = openpyxl.load_workbook(orders_xlsx)["Orders"]
    assert o["A4"].value == 333
    assert o["A3"].value == 2
    assert o["E1"].value == "Zip!"
    # padded "ColumnN" header labels are never written
    assert not any(str(c.value or "").startswith("Column") for row in o.iter_rows() for c in row)


def test_save_as_xlsx_copies_whole_workbook(window, orders_xlsx, tmp_path):
    window.loadDataFile(str(orders_xlsx))
    window._onTableCellEdited(0, 1, "11")
    copy = tmp_path / "copy.xlsx"
    window.current_file_path = str(copy)
    window.saveFile()

    c = openpyxl.load_workbook(copy)
    assert c.sheetnames == ["Orders", "Customers", "Notes"]
    assert c["Orders"]["B2"].value == 11
    assert c["Orders"]["F2"].value == "=B2*C2"
    assert openpyxl.load_workbook(orders_xlsx)["Orders"]["B2"].value == 5  # original untouched

    # Later saves go to the copy and keep earlier edits
    window._onTableCellEdited(1, 1, "12")
    window.saveFile()
    c = openpyxl.load_workbook(copy)["Orders"]
    assert c["B2"].value == 11 and c["B3"].value == 12


def test_save_leaves_no_temp_files(window, orders_xlsx):
    window.loadDataFile(str(orders_xlsx))
    window._onTableCellEdited(0, 1, "8")
    window.saveFile()
    assert [f for f in os.listdir(orders_xlsx.parent) if f.endswith(".xlsx")] == ["orders.xlsx"]


def test_real_sample_round_trip_changes_one_cell(window, tmp_path):
    sample = tmp_path / "test5.xlsx"
    shutil.copy(REPO_ROOT / "xlsx-files" / "test5.xlsx", sample)

    def snapshot():
        return [[c.value for c in r] for r in openpyxl.load_workbook(sample).active.iter_rows()]

    before = snapshot()
    window.loadDataFile(str(sample))
    window._onTableCellEdited(3, 2, "zzz")
    window.saveFile()
    after = snapshot()
    diffs = [(i, j) for i, row in enumerate(before) for j, v in enumerate(row) if after[i][j] != v]
    assert diffs == [(4, 2)]


# ---------------------------------------------------------------------- CSV

def test_csv_edit_and_save(window, sample_csv):
    window.loadDataFile(str(sample_csv))
    window._onTableCellEdited(0, 0, "EDITED")
    window.saveFile()
    lines = sample_csv.read_text(encoding="utf-8").splitlines()
    assert lines[1] == "EDITED,Austin,01234"


def test_csv_save_as_xlsx_builds_new_workbook(window, sample_csv, tmp_path):
    window.loadDataFile(str(sample_csv))
    out = tmp_path / "from_csv.xlsx"
    window.current_file_path = str(out)
    window.saveFile()
    ws = openpyxl.load_workbook(out).active
    assert [c.value for c in ws[2]] == ["Ann", "Austin", "01234"]
    assert ws["C3"].value == 83702  # plain numbers become numbers
