"""Shared fixtures for the CSV Reader test suite.

The app runs headless (Qt "offscreen" platform). Every test gets its own
temporary QSettings file so recent-files / last-viewed-file entries never
touch the user's real settings, and modal dialogs are stubbed so a stray
error box fails the test instead of hanging it.
"""
import datetime
import importlib.util
import os
import sys
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))  # for icon_loader

openpyxl = pytest.importorskip("openpyxl")
from openpyxl.styles import Font  # noqa: E402
from openpyxl.worksheet.formula import ArrayFormula  # noqa: E402
from PyQt6.QtCore import QSettings  # noqa: E402
from PyQt6.QtWidgets import QApplication, QMessageBox  # noqa: E402


@pytest.fixture(scope="session")
def app_module():
    """csv-reader.py has a hyphen in its name, so import it by path"""
    spec = importlib.util.spec_from_file_location("csv_reader_app", REPO_ROOT / "csv-reader.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def qapp():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def dialog_errors(monkeypatch):
    """Collect error dialogs instead of showing them"""
    errors = []
    monkeypatch.setattr(QMessageBox, "critical",
                        staticmethod(lambda parent, title, text, *a, **k: errors.append(text)))
    monkeypatch.setattr(QMessageBox, "warning",
                        staticmethod(lambda parent, title, text, *a, **k: errors.append(text)))
    return errors


@pytest.fixture
def window(app_module, qapp, tmp_path, monkeypatch, dialog_errors):
    """A fresh main window with isolated settings. Fails the test if any
    error dialog was raised."""
    settings_file = str(tmp_path / "settings.ini")
    monkeypatch.setattr(app_module, "QSettings",
                        lambda *a, **k: QSettings(settings_file, QSettings.Format.IniFormat))
    w = app_module.CSVReaderApp()
    w.show()
    yield w
    w.is_modified = False  # skip the unsaved-changes prompt on close
    w.close()
    w.deleteLater()
    assert not dialog_errors, f"unexpected error dialog(s): {dialog_errors}"


# ---------------------------------------------------------------- workbooks

@pytest.fixture
def orders_xlsx(tmp_path):
    """Three sheets; the first has typed values, formulas and formatting"""
    path = tmp_path / "orders.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Orders"
    ws.append(["ID", "Qty", "Price", "Date", "Zip", "Total"])
    ws.append([1, 5, 2.5, datetime.datetime(2026, 1, 2), "01234", "=B2*C2"])
    ws.append([2, 3, 4.0, datetime.datetime(2026, 2, 3), "55401", "=B3*C3"])
    ws.append([3, 7, 1.25, datetime.datetime(2026, 3, 4), "60601", "=B4*C4"])
    ws["A1"].font = Font(bold=True)
    ws.column_dimensions["D"].width = 22
    ws["C2"].number_format = "$#,##0.00"
    customers = wb.create_sheet("Customers")
    customers.append(["Name", "City"])
    customers.append(["Ann", "Austin"])
    customers.append(["Bo", "Boise"])
    wb.create_sheet("Notes")["A1"] = "keep me"
    wb.save(path)
    return path


@pytest.fixture
def mixed_sheets_xlsx(tmp_path):
    """Sheets that are normal, empty and headers-only"""
    path = tmp_path / "mixed.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Orders"
    ws.append(["ID", "Qty", "Total"])
    for i, qty in enumerate([5, 3, 4], start=2):
        ws.append([i - 1, qty, f"=B{i}*2"])
    c = wb.create_sheet("Customers")
    c.append(["Name", "City"])
    c.append(["Ann", "Austin"])
    c.append(["Bo", "Boise"])
    wb.create_sheet("Empty")
    wb.create_sheet("HeadersOnly").append(["A", "B"])
    wb.save(path)
    return path


@pytest.fixture
def formulas_xlsx(tmp_path):
    """Formulas (plain and array), a literal string starting with '=', and
    sheet names that collide once made filename-safe"""
    path = tmp_path / "formulas.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Calc"
    ws.append(["Qty", "Price", "Total", "Note"])
    ws.append([2, 3, "=A2*B2", None])
    ws.append([4, 5, "=A3*B3", "x"])
    ws["D3"] = ArrayFormula("D3", "=A3:A3*2")
    q = wb.create_sheet("Q1 Q2")
    q.append(["k", "v"])
    q.append(["a", 1])
    wb.create_sheet("Blank")
    q2 = wb.create_sheet("Q1_Q2")
    q2.append(["dup", "name"])
    q2.append([1, 2])
    wb.save(path)
    # A literal text cell starting with "=" (string type, not a formula)
    wb = openpyxl.load_workbook(path)
    wb["Calc"]["D2"].value = "=literal?"
    wb["Calc"]["D2"].data_type = "s"
    wb.save(path)
    return path


@pytest.fixture
def sample_csv(tmp_path):
    path = tmp_path / "sample.csv"
    path.write_text("Name,City,Zip\nAnn,Austin,01234\nBo,Boise,83702\n", encoding="utf-8")
    return path
