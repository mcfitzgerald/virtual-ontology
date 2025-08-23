"""
Database management endpoints

Provides API for database maintenance, backups, and monitoring
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import Dict, Any
from pathlib import Path
from datetime import datetime
import shutil
from sqlmodel import select, func, Session

from database.dependencies import SessionDep, ManagerDep
from database.schemas import DatabaseStats, CleanupRequest, BackupRequest, BackupResponse, OperationResponse
from database.models import (
    HistoricalMESData,
    TwinRun,
    SimulationData,
    EquipmentConfig,
    ProductConfig,
    Experiment,
    DiscoveredPattern,
    ParameterRecommendation,
)


router = APIRouter()


# Table categories for cleanup
TABLE_CATEGORIES = {
    "historical": ["historical_mes_data"],
    "simulation": ["simulation_data", "twin_runs"],
    "optimization": ["optimization_results", "parameter_recommendations"],
    "experiments": ["experiments", "discovered_patterns"],
    "configuration": ["equipment_config", "product_config"],
}


@router.get("/status")
async def database_status(manager: ManagerDep, session: SessionDep) -> Dict[str, Any]:
    """
    Get current database status

    Returns:
    - Connection status
    - Ontology version
    - Manifest version
    - Table counts
    """

    try:
        # Get versions
        ontology_version = manager.get_ontology_version()
        manifest_version = manager.get_manifest_version()

        # Get table counts
        table_counts = {
            "historical_mes_data": session.exec(select(func.count(HistoricalMESData.id))).one(),  # type: ignore[arg-type]  # type: ignore[arg-type]
            "twin_runs": session.exec(select(func.count(TwinRun.run_id))).one(),  # type: ignore[arg-type]  # type: ignore[arg-type]
            "simulation_data": session.exec(select(func.count(SimulationData.id))).one(),  # type: ignore[arg-type]  # type: ignore[arg-type]
            "equipment_config": session.exec(select(func.count(EquipmentConfig.equipment_id))).one(),  # type: ignore[arg-type]  # type: ignore[arg-type]
            "product_config": session.exec(select(func.count(ProductConfig.product_id))).one(),  # type: ignore[arg-type]  # type: ignore[arg-type]
            "experiments": session.exec(select(func.count(Experiment.experiment_id))).one(),  # type: ignore[arg-type]  # type: ignore[arg-type]
            "patterns": session.exec(select(func.count(DiscoveredPattern.pattern_id))).one(),  # type: ignore[arg-type]
        }

        return {
            "status": "connected",
            "database_path": str(manager.db_path),
            "ontology_version": ontology_version,
            "manifest_version": manifest_version,
            "table_counts": table_counts,
            "total_records": sum(table_counts.values()),
        }

    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.get("/stats", response_model=DatabaseStats)
async def database_statistics(manager: ManagerDep, session: SessionDep) -> DatabaseStats:
    """
    Get comprehensive database statistics

    Returns detailed information about:
    - Database file size
    - Table record counts
    - Data categories
    - Versions
    """

    # Get file size
    file_size_mb = 0.0
    if manager.db_path.exists():
        file_size_mb = manager.db_path.stat().st_size / (1024 * 1024)

    # Get table counts
    tables = {
        "historical_mes_data": session.exec(select(func.count(HistoricalMESData.id))).one(),  # type: ignore[arg-type]
        "twin_runs": session.exec(select(func.count(TwinRun.run_id))).one(),  # type: ignore[arg-type]
        "simulation_data": session.exec(select(func.count(SimulationData.id))).one(),  # type: ignore[arg-type]
        "equipment_config": session.exec(select(func.count(EquipmentConfig.equipment_id))).one(),  # type: ignore[arg-type]
        "product_config": session.exec(select(func.count(ProductConfig.product_id))).one(),  # type: ignore[arg-type]
        "experiments": session.exec(select(func.count(Experiment.experiment_id))).one(),  # type: ignore[arg-type]
        "discovered_patterns": session.exec(select(func.count(DiscoveredPattern.pattern_id))).one(),  # type: ignore[arg-type]
        "parameter_recommendations": session.exec(select(func.count(ParameterRecommendation.recommendation_id))).one(),  # type: ignore[arg-type]
    }

    # Group by categories
    categories = {}
    for category, table_list in TABLE_CATEGORIES.items():
        category_count = sum(tables.get(t, 0) for t in table_list)
        if category_count > 0:
            categories[category] = {"tables": table_list, "total_records": category_count}

    return DatabaseStats(
        database_path=str(manager.db_path),
        file_size_mb=round(file_size_mb, 2),
        total_tables=len(tables),
        total_records=sum(tables.values()),
        tables=tables,
        ontology_version=manager.get_ontology_version(),
        manifest_version=manager.get_manifest_version(),
        categories=categories,
    )


@router.post("/sync-manifests", response_model=OperationResponse)
async def sync_manifests(manager: ManagerDep) -> OperationResponse:
    """
    Sync configurations from YAML manifest files

    Updates equipment and product configurations
    from the manifest YAML files
    """

    try:
        manager.sync_configurations_from_manifests()

        return OperationResponse(
            success=True,
            message="Configurations synced from manifests",
            details={
                "manifest_version": manager.get_manifest_version(),
                "manifests_synced": ["equipment_manifest", "production_manifest"],
            },
        )

    except Exception as e:
        return OperationResponse(success=False, message=f"Sync failed: {str(e)}")


@router.post("/import-historical")
async def import_historical_data(manager: ManagerDep, csv_file: UploadFile = File(...)) -> OperationResponse:
    """
    Import historical MES data from CSV file
    """

    try:
        # Save uploaded file temporarily
        temp_path = Path(f"/tmp/{csv_file.filename}")
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(csv_file.file, buffer)

        # Import data
        manager.import_historical_data(temp_path)

        # Clean up temp file
        temp_path.unlink()

        return OperationResponse(success=True, message=f"Historical data imported from {csv_file.filename}")

    except Exception as e:
        return OperationResponse(success=False, message=f"Import failed: {str(e)}")


@router.post("/backup", response_model=BackupResponse)
async def create_backup(request: BackupRequest, manager: ManagerDep) -> BackupResponse:
    """
    Create a database backup

    Creates a timestamped backup of the database file
    with optional compression
    """

    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = Path("backups")
        backup_dir.mkdir(exist_ok=True)

        backup_name = f"twin_db_backup_{timestamp}.db"
        backup_path = backup_dir / backup_name

        # Copy database file
        shutil.copy2(manager.db_path, backup_path)

        # Compress if requested
        if request.compress:
            import gzip

            compressed_path = backup_path.with_suffix(".db.gz")
            with open(backup_path, "rb") as f_in:
                with gzip.open(compressed_path, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)
            backup_path.unlink()  # Remove uncompressed file
            backup_path = compressed_path

        # Get backup stats
        size_mb = backup_path.stat().st_size / (1024 * 1024)

        # Get record counts
        with Session(manager.engine) as session:
            total_records = (
                session.exec(select(func.count(HistoricalMESData.id))).one()  # type: ignore[arg-type]
                + session.exec(select(func.count(SimulationData.id))).one()  # type: ignore[arg-type]
                + session.exec(select(func.count(TwinRun.run_id))).one()  # type: ignore[arg-type]
            )

        return BackupResponse(
            backup_path=str(backup_path),
            size_mb=round(size_mb, 2),
            tables_backed_up=8,  # Approximate
            records_backed_up=total_records,
            created_at=datetime.now(),
            compressed=request.compress,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backup failed: {str(e)}")


@router.post("/restore")
async def restore_backup(manager: ManagerDep, backup_file: UploadFile = File(...)) -> OperationResponse:
    """
    Restore database from a backup file

    WARNING: This will replace the current database
    """

    try:
        # Create backup of current database first
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pre_restore_backup = manager.db_path.with_suffix(f".pre_restore_{timestamp}.db")
        shutil.copy2(manager.db_path, pre_restore_backup)

        # Save uploaded file
        temp_path = Path(f"/tmp/{backup_file.filename}")
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(backup_file.file, buffer)

        # Decompress if needed
        if backup_file.filename and backup_file.filename.endswith(".gz"):
            import gzip

            decompressed_path = temp_path.with_suffix("")
            with gzip.open(temp_path, "rb") as f_in:
                with open(decompressed_path, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)
            temp_path.unlink()
            temp_path = decompressed_path

        # Replace database file
        shutil.move(str(temp_path), str(manager.db_path))

        return OperationResponse(
            success=True,
            message=f"Database restored from {backup_file.filename}",
            details={"pre_restore_backup": str(pre_restore_backup)},
        )

    except Exception as e:
        return OperationResponse(success=False, message=f"Restore failed: {str(e)}")


@router.post("/clean", response_model=OperationResponse)
async def clean_database(request: CleanupRequest, session: SessionDep) -> OperationResponse:
    """
    Clean database tables

    Options:
    - Clean by category
    - Clean specific tables
    - Clean data older than N days
    - Preserve specific tables
    """

    try:
        tables_cleaned = []
        records_removed = 0

        # Determine tables to clean
        if request.category:
            if request.category not in TABLE_CATEGORIES:
                return OperationResponse(
                    success=False,
                    message=f"Unknown category: {request.category}",
                    details={"available_categories": list(TABLE_CATEGORIES.keys())},
                )
            tables_to_clean = TABLE_CATEGORIES[request.category]
        elif request.tables:
            tables_to_clean = request.tables
        else:
            return OperationResponse(success=False, message="Must specify either category or tables to clean")

        # Remove preserved tables
        tables_to_clean = [t for t in tables_to_clean if t not in request.preserve]

        # Clean each table
        for table_name in tables_to_clean:
            if table_name == "historical_mes_data":
                records = session.exec(select(HistoricalMESData)).all()
                for record in records:
                    session.delete(record)
                records_removed += len(records)

            elif table_name == "simulation_data":
                sim_records = session.exec(select(SimulationData)).all()
                for sim_record in sim_records:
                    session.delete(sim_record)
                records_removed += len(sim_records)

            elif table_name == "twin_runs":
                twin_records = session.exec(select(TwinRun)).all()
                for twin_record in twin_records:
                    session.delete(twin_record)
                records_removed += len(twin_records)

            tables_cleaned.append(table_name)

        session.commit()

        return OperationResponse(
            success=True,
            message=f"Cleaned {len(tables_cleaned)} tables",
            details={"tables_cleaned": tables_cleaned, "records_removed": records_removed},
        )

    except Exception as e:
        session.rollback()
        return OperationResponse(success=False, message=f"Cleanup failed: {str(e)}")


@router.post("/reset", response_model=OperationResponse)
async def reset_database(manager: ManagerDep, keep_configurations: bool = True) -> OperationResponse:
    """
    Reset database to initial state

    Options:
    - keep_configurations: Preserve equipment/product configs
    """

    try:
        # Create backup first
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = manager.db_path.with_suffix(f".pre_reset_{timestamp}.db")
        shutil.copy2(manager.db_path, backup_path)

        # Drop and recreate tables
        manager.create_all_tables()

        # Re-sync configurations if requested
        if keep_configurations:
            manager.sync_configurations_from_manifests()

        return OperationResponse(
            success=True,
            message="Database reset to initial state",
            details={"backup_created": str(backup_path), "configurations_preserved": keep_configurations},
        )

    except Exception as e:
        return OperationResponse(success=False, message=f"Reset failed: {str(e)}")
