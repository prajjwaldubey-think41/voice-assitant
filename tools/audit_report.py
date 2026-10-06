from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


class AuditReportGenerator:
    """Render a completed transaction's audit entries as a PDF report."""

    def __init__(self, output_dir: str | Path = "reports") -> None:
        self.output_dir = Path(output_dir)

    def generate(
        self,
        entries: list[dict[str, Any]],
        transaction_id: str,
        query: str = "",
        ledger: dict[str, Any] | None = None,
    ) -> Path:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        path = self.output_dir / f"audit_report_{transaction_id}.pdf"
        styles = getSampleStyleSheet()
        story: list[Any] = [
            Paragraph("Audit Report", styles["Title"]),
            Paragraph(f"Transaction: {escape(transaction_id)}", styles["Normal"]),
            Paragraph(
                f"Generated: {datetime.now(timezone.utc).isoformat()}", styles["Normal"]
            ),
            Paragraph(f"Request: {escape(query)}", styles["Normal"]),
            Spacer(1, 12),
            Paragraph(f"Operations ({len(entries)})", styles["Heading2"]),
        ]
        rows = [["#", "Timestamp", "Operation", "Input", "Output"]]
        for index, entry in enumerate(entries, start=1):
            rows.append(
                [
                    str(index),
                    Paragraph(escape(str(entry["timestamp"])), styles["BodyText"]),
                    Paragraph(escape(str(entry["operation"])), styles["BodyText"]),
                    Paragraph(escape(self._format(entry["input"])), styles["BodyText"]),
                    Paragraph(escape(self._format(entry["output"])), styles["BodyText"]),
                ]
            )
        table = Table(rows, colWidths=[20, 100, 70, 150, 150], repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        story.append(table)
        if ledger:
            story += [Spacer(1, 12), Paragraph("Final Ledger State", styles["Heading2"])]
            ledger_rows = [["Variable", "Value"]] + [
                [Paragraph(escape(str(k)), styles["BodyText"]), Paragraph(escape(self._format(v)), styles["BodyText"])]
                for k, v in ledger.items()
            ]
            ledger_table = Table(ledger_rows, colWidths=[150, 340])
            ledger_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ]
                )
            )
            story.append(ledger_table)
        SimpleDocTemplate(str(path), pagesize=A4, title="Audit Report").build(story)
        return path

    @staticmethod
    def _format(value: Any) -> str:
        return json.dumps(value, default=str, sort_keys=True)
