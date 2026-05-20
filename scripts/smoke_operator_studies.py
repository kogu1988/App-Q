from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="appq-studies-") as tmp_dir:
        os.environ["APP_MODEL_PROVIDER"] = "mock"
        os.environ["APP_Q_STUDIES_DIR"] = tmp_dir
        os.environ["APP_Q_DISABLE_PDF_EXPORT"] = "1"
        app = AppTest.from_file(str(ROOT / "apps" / "operator" / "streamlit_app.py"), default_timeout=30)
        app.run()

        save_buttons = [button for button in app.button if button.label == "Kaydet"]
        assert save_buttons, "Kaydet button not found"
        save_buttons[0].click().run()

        studies = [item for item in Path(tmp_dir).iterdir() if item.is_dir()]
        assert len(studies) == 1, f"Expected one saved study, found {len(studies)}"
        metadata = json.loads((studies[0] / "metadata.json").read_text(encoding="utf-8"))
        assert metadata["has_report"] is False

    with tempfile.TemporaryDirectory(prefix="appq-studies-run-") as tmp_dir:
        os.environ["APP_MODEL_PROVIDER"] = "mock"
        os.environ["APP_Q_STUDIES_DIR"] = tmp_dir
        os.environ["APP_Q_DISABLE_PDF_EXPORT"] = "1"
        app = AppTest.from_file(str(ROOT / "apps" / "operator" / "streamlit_app.py"), default_timeout=60)
        app.run()

        run_buttons = [button for button in app.button if button.label == "Araştırmayı Çalıştır"]
        assert run_buttons, "Araştırmayı Çalıştır button not found"
        run_buttons[0].set_value(True).run(timeout=60)

        studies_after_run = [item for item in Path(tmp_dir).iterdir() if item.is_dir()]
        report_studies = [
            item
            for item in studies_after_run
            if json.loads((item / "metadata.json").read_text(encoding="utf-8")).get("has_report")
        ]
        assert report_studies, f"Expected a study with report output, found {len(studies_after_run)} studies"
        report_study = report_studies[0]
        metadata = json.loads((report_study / "metadata.json").read_text(encoding="utf-8"))
        assert (report_study / "report.html").exists(), "report.html not generated"
        assert (report_study / "report.md").exists(), "report.md not generated"
        assert (report_study / "report.json").exists(), "report.json not generated"
        if metadata.get("pdf_status") == "generated":
            assert (report_study / "report.pdf").exists(), "report.pdf metadata says generated but file is missing"

        print(f"Study smoke test passed: {report_study.name} / pdf_status={metadata.get('pdf_status')}")


if __name__ == "__main__":
    main()
