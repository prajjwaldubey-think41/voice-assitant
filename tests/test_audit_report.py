from tools import AuditReportGenerator, AuditTrail


def test_generate_creates_pdf_with_entries_and_ledger(tmp_path) -> None:
    trail = AuditTrail()
    trail.record("ledger_create", {"name": "a", "value": 1}, 1)
    trail.record("calculate", {"code": "a <b> 2"}, 2)
    path = AuditReportGenerator(tmp_path / "out").generate(
        trail.retrieve(), "tx1", "make <stuff> & more", {"a": 1}
    )
    assert path.name == "audit_report_tx1.pdf"
    assert path.read_bytes().startswith(b"%PDF")


def test_generate_handles_empty_entries(tmp_path) -> None:
    path = AuditReportGenerator(tmp_path).generate([], "empty")
    assert path.exists()
