from typing import Dict, List, Optional, Union
import pandas as pd
from pathlib import Path
import json
import logging
from datetime import datetime
import pyarrow as pa
import pyarrow.parquet as pq
from enum import Enum

logger = logging.getLogger(__name__)


class ExportFormat(str, Enum):
    """Supported export formats."""

    CSV = "csv"
    PARQUET = "parquet"
    FEATHER = "feather"
    JSON = "json"
    PICKLE = "pickle"


class DataExporter:
    """Export data in various formats with compression and partitioning."""

    def __init__(
        self,
        export_dir: Union[str, Path],
        format: ExportFormat = ExportFormat.PARQUET,
        compression: Optional[str] = "snappy",
        partition_cols: Optional[List[str]] = None,
    ):
        """Initialize the exporter.

        Args:
            export_dir: Directory for exported files
            format: Export format
            compression: Compression method (if supported)
            partition_cols: Columns to partition by
        """
        self.export_dir = Path(export_dir)
        self.format = format
        self.compression = compression
        self.partition_cols = partition_cols or []

        self.export_dir.mkdir(parents=True, exist_ok=True)

    def export_data(
        self, df: pd.DataFrame, name: str, metadata: Optional[Dict] = None
    ) -> Path:
        """Export data to specified format.

        Args:
            df: DataFrame to export
            name: Base name for export file
            metadata: Optional metadata to include

        Returns:
            Path to exported file/directory
        """
        # Add export timestamp to metadata
        metadata = metadata or {}
        metadata["export_timestamp"] = datetime.now().isoformat()
        metadata["rows"] = len(df)
        metadata["columns"] = list(df.columns)

        # Create export path
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"{name}_{timestamp}"

        if self.format == ExportFormat.PARQUET:
            return self._export_parquet(df, base_name, metadata)
        elif self.format == ExportFormat.FEATHER:
            return self._export_feather(df, base_name, metadata)
        elif self.format == ExportFormat.CSV:
            return self._export_csv(df, base_name, metadata)
        elif self.format == ExportFormat.JSON:
            return self._export_json(df, base_name, metadata)
        else:  # PICKLE
            return self._export_pickle(df, base_name, metadata)

    def _export_parquet(self, df: pd.DataFrame, name: str, metadata: Dict) -> Path:
        """Export to Parquet format."""
        export_path = self.export_dir / f"{name}.parquet"

        # Convert DataFrame to PyArrow Table
        table = pa.Table.from_pandas(df)

        # Add metadata
        metadata_bytes = json.dumps(metadata).encode("utf-8")

        if self.partition_cols:
            # Partitioned write
            pq.write_to_dataset(
                table,
                self.export_dir / name,
                partition_cols=self.partition_cols,
                compression=self.compression,
                metadata={"metadata": metadata_bytes},
            )
            return self.export_dir / name
        else:
            # Single file write
            pq.write_table(
                table,
                export_path,
                compression=self.compression,
                metadata={"metadata": metadata_bytes},
            )
            return export_path

    def _export_feather(self, df: pd.DataFrame, name: str, metadata: Dict) -> Path:
        """Export to Feather format."""
        export_path = self.export_dir / f"{name}.feather"

        # Convert to PyArrow and write
        table = pa.Table.from_pandas(df)

        # Add metadata
        metadata_bytes = json.dumps(metadata).encode("utf-8")
        table = table.replace_schema_metadata({"metadata": metadata_bytes})

        with pa.OSFile(str(export_path), "wb") as f:
            with pa.RecordBatchFileWriter(f, table.schema) as writer:
                writer.write_table(table)

        return export_path

    def _export_csv(self, df: pd.DataFrame, name: str, metadata: Dict) -> Path:
        """Export to CSV format."""
        export_path = self.export_dir / f"{name}.csv"
        metadata_path = self.export_dir / f"{name}_metadata.json"

        # Export data
        df.to_csv(export_path, index=True, compression=self.compression)

        # Export metadata separately
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

        return export_path

    def _export_json(self, df: pd.DataFrame, name: str, metadata: Dict) -> Path:
        """Export to JSON format."""
        export_path = self.export_dir / f"{name}.json"

        # Combine data and metadata
        data = {"metadata": metadata, "data": df.to_dict(orient="records")}

        with open(export_path, "w") as f:
            json.dump(data, f, indent=2)

        return export_path

    def _export_pickle(self, df: pd.DataFrame, name: str, metadata: Dict) -> Path:
        """Export to Pickle format."""
        export_path = self.export_dir / f"{name}.pkl"

        # Create dict with data and metadata
        combined_data = {"metadata": metadata, "data": df}
        pd.to_pickle(combined_data, export_path, compression=self.compression)
        return export_path

    @staticmethod
    def read_exported_data(
        path: Union[str, Path], format: Optional[ExportFormat] = None
    ) -> tuple[pd.DataFrame, Dict]:
        """Read exported data and metadata.

        Args:
            path: Path to exported file
            format: Format override (if not inferred from extension)

        Returns:
            Tuple of (DataFrame, metadata dict)
        """
        path = Path(path)

        if format is None:
            format = ExportFormat(path.suffix[1:])  # Remove leading dot

        if format == ExportFormat.PARQUET:
            table = pq.read_table(path)
            df = table.to_pandas()
            metadata = json.loads(table.schema.metadata[b"metadata"].decode("utf-8"))

        elif format == ExportFormat.FEATHER:
            with pa.memory_map(str(path), "r") as source:
                table = pa.ipc.open_file(source).read_all()
            df = table.to_pandas()
            metadata = json.loads(table.schema.metadata[b"metadata"].decode("utf-8"))

        elif format == ExportFormat.CSV:
            df = pd.read_csv(path, index_col=0)
            metadata_path = path.with_suffix(".json")
            with open(metadata_path, "r") as f:
                metadata = json.load(f)

        elif format == ExportFormat.JSON:
            with open(path, "r") as f:
                data = json.load(f)
            df = pd.DataFrame.from_records(data["data"])
            metadata = data["metadata"]

        else:  # PICKLE
            data = pd.read_pickle(path)
            df = data["data"]
            metadata = data["metadata"]

        return df, metadata
