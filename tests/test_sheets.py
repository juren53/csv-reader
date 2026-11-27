"""Multi-sheet workbooks: sheet tabs, per-sheet state and saving across sheets."""
import openpyxl


def test_tabs_and_lazy_loading(window, mixed_sheets_xlsx):
    window.loadDataFile(str(mixed_sheets_xlsx))
    assert window.sheet_tabs.isVisible()
    assert [window.sheet_tabs.tabText(i) for i in range(window.sheet_tabs.count())] == \
        ["Orders", "Customers", "Empty", "HeadersOnly"]
    assert [s["loaded"] for s in window.xlsx_source["sheets"]] == [True, False, False, False]
    assert window.windowTitle().endswith("[Orders]")
    assert window.next_sheet_action.isEnabled() and window.prev_sheet_action.isEnabled()


def test_switching_keeps_per_sheet_state(window, mixed_sheets_xlsx):
    window.loadDataFile(str(mixed_sheets_xlsx))
    window.nextRecord()
    window.nextRecord()
    window._onTableCellEdited(0, 1, "50")

    window.sheet_tabs.setCurrentIndex(1)  # like clicking the tab
    assert window.headers == ["Name", "City"]
    assert window.csv_data[1] == ["Bo", "Boise"]
    assert "Sheet 2/4: Customers" in window.statusBar().currentMessage()
    assert window.windowTitle().endswith("[Customers] *")

    window.switchSheetBy(-1)  # Ctrl+PgUp
    assert window.headers[0] == "ID"
    assert window.current_record_index == 2
    assert window.csv_data[0][1] == "50"


def test_switching_wraps_around(window, mixed_sheets_xlsx):
    window.loadDataFile(str(mixed_sheets_xlsx))
    window.switchSheetBy(-1)
    assert window.xlsx_source["active"] == 3
    window.switchSheetBy(1)
    assert window.xlsx_source["active"] == 0


def test_record_edit_committed_on_sheet_switch(window, mixed_sheets_xlsx):
    window.loadDataFile(str(mixed_sheets_xlsx))
    window.switchSheet(1)
    window._toggleRecordEditMode()
    window.record_view.field_editors[0].setText("Annie")
    window.switchSheet(0)
    assert not window.record_edit_mode
    assert window.xlsx_source["sheets"][1]["data"][0][0] == "Annie"


def test_empty_and_headers_only_sheets(window, mixed_sheets_xlsx):
    window.loadDataFile(str(mixed_sheets_xlsx))
    window.switchSheet(2)
    assert window.csv_data == []
    assert "no data rows" in window.nav_label.text().lower()
    window.switchToTableView()
    window.switchSheet(3)
    assert window.table_view.columnCount() == 2
    assert window.table_view.rowCount() == 0
    window.switchSheet(0)
    assert window.table_view.rowCount() == 3


def test_save_writes_edits_from_every_sheet(window, mixed_sheets_xlsx):
    window.loadDataFile(str(mixed_sheets_xlsx))
    window._onTableCellEdited(0, 1, "50")
    window.switchSheet(1)
    window._onTableCellEdited(1, 1, "Boston")
    window.switchSheet(0)
    window.saveFile()

    wb = openpyxl.load_workbook(mixed_sheets_xlsx)
    assert wb.sheetnames == ["Orders", "Customers", "Empty", "HeadersOnly"]
    assert wb["Orders"]["B2"].value == 50
    assert wb["Orders"]["C2"].value == "=B2*2"
    assert wb["Customers"]["B3"].value == "Boston"
    assert all(not s["dirty_cells"] for s in window.xlsx_source["sheets"])
    assert not window.is_modified

    # A second save on another sheet builds on the first
    window.switchSheet(1)
    window._onTableCellEdited(0, 1, "Paris")
    window.saveFile()
    wb = openpyxl.load_workbook(mixed_sheets_xlsx)
    assert wb["Customers"]["B2"].value == "Paris"
    assert wb["Orders"]["B2"].value == 50


def test_header_reassignment_on_second_sheet(window, mixed_sheets_xlsx):
    window.loadDataFile(str(mixed_sheets_xlsx))
    window.switchSheet(1)
    window.reassignHeaderRow(0)                # "Ann" row becomes the header
    window._onTableCellEdited(0, 0, "Nm")      # old header row (sheet row 1)
    window.saveFile()
    c = openpyxl.load_workbook(mixed_sheets_xlsx)["Customers"]
    assert c["A1"].value == "Nm"
    assert c["A2"].value == "Ann"


def test_tabs_hidden_for_csv_and_single_sheet(window, mixed_sheets_xlsx, sample_csv, tmp_path):
    window.loadDataFile(str(mixed_sheets_xlsx))
    window.loadDataFile(str(sample_csv))
    assert not window.sheet_tabs.isVisible()
    assert not window.next_sheet_action.isEnabled()
    assert "[" not in window.windowTitle()

    single = tmp_path / "one.xlsx"
    wb = openpyxl.Workbook()
    wb.active.append(["a"])
    wb.active.append([1])
    wb.save(single)
    window.loadDataFile(str(single))
    assert not window.sheet_tabs.isVisible()
    assert window.csv_data == [["1"]]


def test_trailing_blank_rows_are_dropped(window, tmp_path):
    path = tmp_path / "padded.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["a", "b"])
    ws.append([1, 2])
    ws["A50"].number_format = "0.00"  # formatting-only cell inflates max_row
    ws["A50"].value = None
    wb.save(path)
    window.loadDataFile(str(path))
    assert window.csv_data == [["1", "2"]]
