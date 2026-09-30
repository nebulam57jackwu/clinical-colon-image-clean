import csv
import importlib.util
import os
import tempfile
import unittest
from pathlib import Path

from scripts import export_lake_manifest


class ExporterSafetyTests(unittest.TestCase):
    def test_refuses_to_overwrite_before_opening_database(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "candidates.csv"
            output.write_text("sentinel\n", encoding="utf-8")

            with self.assertRaises(FileExistsError):
                export_lake_manifest.export_manifest(
                    root / "missing.duckdb",
                    output,
                    "source",
                    lake_root=root,
                )

            self.assertEqual(output.read_text(encoding="utf-8"), "sentinel\n")

    def test_rejects_parent_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(ValueError):
                export_lake_manifest._resolve_lake_image_path(
                    root, "../outside.png", "IMG-1"
                )

    def test_rejects_symlink_escape(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "lake"
            outside = Path(directory) / "outside.png"
            image_dir = root / "shared_image_lake" / "images"
            image_dir.mkdir(parents=True)
            outside.write_bytes(b"not a clinical image")
            os.symlink(outside, image_dir / "escape.png")

            with self.assertRaises(ValueError):
                export_lake_manifest._resolve_lake_image_path(
                    root, "shared_image_lake/images/escape.png", "IMG-2"
                )

    @unittest.skipUnless(
        importlib.util.find_spec("duckdb"),
        "DuckDB is optional for local synthetic safety tests",
    )
    def test_exports_sorted_rows_with_read_only_database(self) -> None:
        import duckdb

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            lake_root = root / "lake"
            image_dir = lake_root / "shared_image_lake" / "images"
            image_dir.mkdir(parents=True)
            for name in ("a.png", "b.png"):
                (image_dir / name).write_bytes(b"synthetic")

            db_path = root / "dataset_metadata.duckdb"
            connection = duckdb.connect(str(db_path))
            try:
                connection.execute(
                    "CREATE TABLE images_master ("
                    "image_id VARCHAR, patient_key VARCHAR, file_path VARCHAR, "
                    "source_id VARCHAR, content_sha256 VARCHAR, width INTEGER, height INTEGER)"
                )
                connection.execute(
                    "CREATE TABLE image_quality_qc ("
                    "image_id VARCHAR, blur_score DOUBLE, is_usable BOOLEAN, qc_method VARCHAR)"
                )
                connection.executemany(
                    "INSERT INTO images_master VALUES (?, ?, ?, ?, ?, ?, ?)",
                    [
                        (
                            "IMG-B",
                            "PAT-B",
                            "shared_image_lake/images/b.png",
                            "source",
                            "b" * 64,
                            2,
                            2,
                        ),
                        (
                            "IMG-A",
                            "PAT-A",
                            "shared_image_lake/images/a.png",
                            "source",
                            "a" * 64,
                            1,
                            1,
                        ),
                    ],
                )
                connection.execute(
                    "INSERT INTO image_quality_qc VALUES "
                    "('IMG-A', 0.1, true, 'synthetic'), "
                    "('IMG-B', 0.2, false, 'synthetic')"
                )
            finally:
                connection.close()

            output = root / "out" / "candidates.csv"
            count = export_lake_manifest.export_manifest(
                db_path, output, "source", lake_root=lake_root
            )

            self.assertEqual(count, 2)
            with output.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual([row["image_id"] for row in rows], ["IMG-A", "IMG-B"])
            self.assertEqual(rows[0]["blur_is_usable"], "True")
            self.assertEqual(rows[1]["blur_is_usable"], "False")


if __name__ == "__main__":
    unittest.main()
