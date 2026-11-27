"""Formula cells are read-only; Save As .csv on a multi-sheet workbook is an export."""
import csv
import os

import openpyxl
import pytest
from PyQt6.QtCore import Qt


class FakeSheet:
    def __init__(self, rows):
        self.rows = rows

    def iter_rows(self, **kwargs):
        return iter(self.rows)


# ------------------------------------------------------------------ formulas

def test_formula_detection(window, formulas_xlsx):
    window.loadDataFile(str(formulas_xlsx))
    state = window.xlsx_source["sheets"][0]
    assert state["formulas"] == {2: {2: "=A2*B2"}, 3: {2: "=A3*B3", 3: "=A3:A3*2"}}
    # D2 is a literal string starting with "=", not a formula
    assert window.csv_data[0][3] == "=literal?"
    # openpyxl-written file has no cached results: formula text is shown
    assert window.csv_data[0][2] == "=A2*B2"


def test_cached_value_shown_when_present(app_module):
    state = app_module.CSVReaderApp._newSheetState("x")
    app_module.CSVReaderApp._fillSheetState(
        state, FakeSheet([("h",), ("=A1*2",)]), lambda: FakeSheet([("h",), (6,)]))
    assert state["data"] == [["6"]]
    assert state["formulas"] == {2: {0: "=A1*2"}}
    assert state["raw"][1] == (6,)


def test_formula_free_sheet_reads_once(app_module):
    state = app_module.CSVReaderApp._newSheetState("x")

    def fail():
        raise AssertionError("cached-value pass should be skipped")

    app_module.CSVReaderApp._fillSheetState(state, FakeSheet([("h",), (1,)]), fail)
    assert state["data"] == [["1"]]


def test_formula_cells_read_only_in_table(window, formulas_xlsx):
    window.loadDataFile(str(formulas_xlsx))
    window.switchToTableView()
    formula_item = window.table_view.item(0, 2)
    assert not formula_item.flags() & Qt.ItemFlag.ItemIsEditable
    assert "=A2*B2" in formula_item.toolTip()
    assert formula_item.font().italic()
    assert window.table_view.item(0, 0).flags() & Qt.ItemFlag.ItemIsEditable


def test_formula_cells_read_only_in_record_edit_mode(window, formulas_xlsx):
    window.loadDataFile(str(formulas_xlsx))
    window._toggleRecordEditMode()
    editors = window.record_view.field_editors
    assert not editors[2].isEnabled()
    assert "=A2*B2" in editors[2].toolTip()
    assert editors[0].isEnabled()
    editors[0].setText("7")
    window._commitRecordEdits()
    assert window.dirty_cells == {(2, 0)}  # the formula cell is not touched

    window.saveFile()
    calc = openpyxl.load_workbook(formulas_xlsx)["Calc"]
    assert calc["A2"].value == 7
    assert calc["C2"].value == "=A2*B2"


def test_formula_locks_follow_header_reassignment(window, formulas_xlsx):
    window.loadDataFile(str(formulas_xlsx))
    window.reassignHeaderRow(1)  # sheet row 3 becomes the header
    assert set(window._lockedCells()) == {(1, 2)}  # sheet row 2 is now data row 1


# ---------------------------------------------------------------- CSV export

@pytest.mark.parametrize("names, expected", [
    (["Orders"], ["r_Orders.csv"]),
    (["Q1 Q2", "Q1_Q2"], ["r_Q1_Q2.csv", "r_Q1_Q2_2.csv"]),
    (['a:b*c?"d"'], ["r_a_b_c_d.csv"]),
    (["..."], ["r_Sheet.csv"]),
])
def test_per_sheet_csv_paths(app_module, tmp_path, names, expected):
    paths = app_module.CSVReaderApp._perSheetCSVPaths(str(tmp_path / "r.csv"), names)
    assert [os.path.basename(p) for p in paths] == expected


@pytest.fixture
def save_as(window, app_module, monkeypatch):
    """Run File > Save As with a chosen path and export answer"""
    def run(path, mode):
        monkeypatch.setattr(app_module.QFileDialog, "getSaveFileName",
                            staticmethod(lambda *a, **k: (str(path), "")))
        monkeypatch.setattr(window, "_askCSVExportMode", lambda count, name: mode)
        window.saveFileAs()
    return run


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.reader(f))


def test_export_current_sheet(window, formulas_xlsx, save_as, tmp_path):
    window.loadDataFile(str(formulas_xlsx))
    window.switchSheet(1)
    window._onTableCellEdited(0, 1, "99")
    out = tmp_path / "export.csv"
    save_as(out, "current")

    assert read_csv(out) == [["k", "v"], ["a", "99"]]
    # The workbook stays open and its edits stay unsaved
    assert window.current_file_path == str(formulas_xlsx)
    assert window.is_modified
    assert window.windowTitle().endswith("*")


def test_export_one_file_per_sheet(window, formulas_xlsx, save_as, monkeypatch, tmp_path):
    window.loadDataFile(str(formulas_xlsx))
    window.switchSheet(1)
    window._onTableCellEdited(0, 1, "99")  # unsaved edit is included in the export
    existing = tmp_path / "export_Calc.csv"
    existing.write_text("old", encoding="utf-8")
    asked = []
    monkeypatch.setattr(window, "_confirmOverwrite", lambda paths: asked.append(paths) or True)

    save_as(tmp_path / "export.csv", "each")

    assert sorted(p.name for p in tmp_path.glob("export_*.csv")) == \
        ["export_Calc.csv", "export_Q1_Q2.csv", "export_Q1_Q2_2.csv"]
    assert asked == [[str(existing)]]
    assert read_csv(tmp_path / "export_Q1_Q2.csv")[1] == ["a", "99"]
    assert read_csv(existing)[0] == ["Qty", "Price", "Total", "Note"]
    assert "1 empty sheet skipped" in window.statusBar().currentMessage()
    assert window.current_file_path == str(formulas_xlsx)


def test_declining_overwrite_writes_nothing(window, formulas_xlsx, save_as, monkeypatch, tmp_path):
    window.loadDataFile(str(formulas_xlsx))
    existing = tmp_path / "export_Calc.csv"
    existing.write_text("old", encoding="utf-8")
    monkeypatch.setattr(window, "_confirmOverwrite", lambda paths: False)
    save_as(tmp_path / "export.csv", "each")
    assert existing.read_text(encoding="utf-8") == "old"
    assert not (tmp_path / "export_Q1_Q2.csv").exists()


def test_cancel_export_writes_nothing(window, formulas_xlsx, save_as, tmp_path):
    window.loadDataFile(str(formulas_xlsx))
    save_as(tmp_path / "export.csv", None)
    assert not list(tmp_path.glob("export*.csv"))


def test_single_sheet_save_as_csv_switches_file(window, save_as, tmp_path):
    single = tmp_path / "one.xlsx"
    wb = openpyxl.Workbook()
    wb.active.append(["a"])
    wb.active.append([1])
    wb.save(single)
    window.loadDataFile(str(single))
    out = tmp_path / "one.csv"
    save_as(out, "should-not-be-asked")
    assert read_csv(out) == [["a"], ["1"]]
    assert window.current_file_path == str(out)
