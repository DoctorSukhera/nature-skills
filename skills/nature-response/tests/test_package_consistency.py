from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "check_package_consistency.py"
SPEC = importlib.util.spec_from_file_location("check_package_consistency", SCRIPT)
assert SPEC and SPEC.loader
CHECKER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = CHECKER
SPEC.loader.exec_module(CHECKER)


MANUSCRIPT_TEXT = r"""
\section{Methods}
The calibration procedure uses an independent validation split and reports the
selected threshold before evaluation on the held-out test set.
"""

RESPONSE_TEXT = r"""
\ReviewerComment{Please clarify how model calibration was performed.}
\AuthorResponse{We have clarified the calibration procedure in the Methods.}
\RevisedExcerpt{The calibration procedure uses an independent validation split and reports the
selected threshold before evaluation on the held-out test set.}
"""


class PackageConsistencyTests(unittest.TestCase):
    def write(self, root: Path, name: str, content: str) -> Path:
        path = root / name
        path.write_text(content, encoding="utf-8")
        return path

    def test_consistent_package_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manuscript = self.write(root, "main.tex", MANUSCRIPT_TEXT)
            response = self.write(root, "response.tex", RESPONSE_TEXT)
            clean = self.write(root, "clean.tex", MANUSCRIPT_TEXT)
            marked = self.write(
                root,
                "marked.tex",
                MANUSCRIPT_TEXT.replace(
                    "The calibration procedure",
                    r"\revised{The calibration procedure}",
                ),
            )

            findings = CHECKER.run_checks(manuscript, response, clean, marked)

        self.assertEqual([], findings)

    def test_quote_mismatch_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manuscript = self.write(root, "main.tex", MANUSCRIPT_TEXT)
            response = self.write(
                root,
                "response.tex",
                RESPONSE_TEXT.replace("independent validation split", "five-fold cross-validation"),
            )

            findings = CHECKER.run_checks(manuscript, response)

        self.assertIn("QUOTE_NOT_IN_MANUSCRIPT", {item.code for item in findings})

    def test_comment_response_count_mismatch_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manuscript = self.write(root, "main.tex", MANUSCRIPT_TEXT)
            response = self.write(
                root,
                "response.tex",
                RESPONSE_TEXT + r"\ReviewerComment{Please report the software version.}",
            )

            findings = CHECKER.run_checks(manuscript, response)

        self.assertIn("COMMENT_RESPONSE_COUNT_MISMATCH", {item.code for item in findings})

    def test_clean_marked_content_drift_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manuscript = self.write(root, "main.tex", MANUSCRIPT_TEXT)
            response = self.write(root, "response.tex", RESPONSE_TEXT)
            clean = self.write(root, "clean.tex", MANUSCRIPT_TEXT)
            marked = self.write(
                root,
                "marked.tex",
                MANUSCRIPT_TEXT.replace("held-out test set", "training set"),
            )

            findings = CHECKER.run_checks(manuscript, response, clean, marked)

        self.assertIn("CLEAN_MARKED_TEXT_MISMATCH", {item.code for item in findings})


if __name__ == "__main__":
    unittest.main()
