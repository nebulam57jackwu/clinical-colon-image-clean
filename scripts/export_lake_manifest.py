"""Export a read-only, pseudonymous candidate manifest from the image lake."""

from __future__ import annotations

import argparse
import csv
import os
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LAKE_ROOT = Path(
    os.environ.get("CLINICAL_IMAGE_LAKE_ROOT", str(REPO_ROOT.parent / "clinical-image-lake"))
).expanduser().resolve()
SCHEMA_VERSION = "0.1"
COLUMNS = (
    "schema_version", "image_id", "patient_key", "image_path", "source_id",
    "content_sha256", "width", "height", "blur_score", "blur_is_usable",
    "blur_qc_method",
)


def _resolve_lake_image_path(lake_root: Path, image_path: str, image_id: str) -> Path:
    """Validate a DB-relative image path and reject symlink escapes."""
    relative_path = Path(image_path)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise ValueError(f"Unsafe image path for {image_id}")

    root = lake_root.expanduser().resolve()
    candidate = root / relative_path
    if not candidate.is_file():
        raise FileNotFoundError(candidate)

    resolved = candidate.resolve(strict=True)
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"Image path escapes lake root for {image_id}") from exc
    return resolved


def export_manifest(
    db_path: Path,
    output_path: Path,
    source_id: str,
    limit: int | None = None,
    lake_root: Path = DEFAULT_LAKE_ROOT,
) -> int:
    if not source_id.strip():
        raise ValueError("source_id must not be empty")
    if limit is not None and limit <= 0:
        raise ValueError("limit must be positive")
    output_path = output_path.expanduser().resolve()
    lake_root = lake_root.expanduser().resolve()
    if output_path.exists():
        raise FileExistsError(f"Refusing to overwrite existing output: {output_path}")
    if not db_path.is_file():
        raise FileNotFoundError(db_path)

    # Import lazily so local safety tests and --help work without the data-connected
    # DuckDB dependency installed. The actual export still requires DuckDB.
    try:
        import duckdb
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "DuckDB is required for export; install requirements.txt or use the lake environment"
        ) from exc

    output_path.parent.mkdir(parents=True, exist_ok=True)
    connection = duckdb.connect(str(db_path), read_only=True)
    try:
        query = """
            SELECT m.image_id, m.patient_key, m.file_path, m.source_id,
                   m.content_sha256, m.width, m.height, q.blur_score,
                   q.is_usable, q.qc_method
            FROM images_master AS m
            LEFT JOIN image_quality_qc AS q USING (image_id)
            WHERE m.source_id = ?
            ORDER BY m.image_id
        """
        if limit is not None:
            query += " LIMIT ?"
            rows = connection.execute(query, [source_id, limit]).fetchall()
        else:
            rows = connection.execute(query, [source_id]).fetchall()
    finally:
        connection.close()
    if not rows:
        raise ValueError(f"No images found for source_id={source_id!r}")
    for row in rows:
        if not row[1] or not row[2]:
            raise ValueError(f"Missing patient_key or image path for {row[0]}")
        _resolve_lake_image_path(lake_root, row[2], row[0])

    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            dir=output_path.parent,
            prefix=f".{output_path.name}.",
            suffix=".tmp",
            delete=False,
            newline="",
            encoding="utf-8",
        ) as handle:
            temporary_path = Path(handle.name)
            writer = csv.writer(handle)
            writer.writerow(COLUMNS)
            writer.writerows((SCHEMA_VERSION, *row) for row in rows)
            handle.flush()
            os.fsync(handle.fileno())

        # Hard-linking the completed temp file gives us an atomic no-overwrite
        # publication on the same filesystem. A concurrent writer cannot replace it.
        try:
            os.link(temporary_path, output_path)
        except FileExistsError as exc:
            raise FileExistsError(
                f"Refusing to overwrite existing output: {output_path}"
            ) from exc
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-id", required=True)
    parser.add_argument(
        "--lake-root",
        type=Path,
        default=DEFAULT_LAKE_ROOT,
        help="clinical-image-lake checkout containing shared_image_lake/ (or set CLINICAL_IMAGE_LAKE_ROOT)",
    )
    parser.add_argument("--db", type=Path, help="override the lake DuckDB path")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    lake_root = args.lake_root.expanduser().resolve()
    db_path = args.db.expanduser().resolve() if args.db else lake_root / "shared_image_lake/metadata/dataset_metadata.duckdb"
    count = export_manifest(db_path, args.output, args.source_id, args.limit, lake_root)
    print(f"Exported {count} pseudonymous candidates to {args.output}")


if __name__ == "__main__":
    main()
