import json
from celery import shared_task
from django.db import transaction
import structlog

from datasets.models import Dataset, DatasetFile
from datasets.services.file_parser import parse_csv, parse_json

logger = structlog.get_logger(__name__)

@shared_task
def parse_dataset_file_task(dataset_id: int):
    """
    Asynchronously parses a previously uploaded dataset file.
    Extracts row count, column count, and column names, then marks the dataset as PENDING.
    """
    logger.info("parse_dataset.started", dataset_id=dataset_id)
    try:
        dataset = Dataset.objects.get(id=dataset_id)
        dataset_file = DatasetFile.objects.filter(dataset=dataset).first()
        
        if not dataset_file:
            logger.error("parse_dataset.no_file", dataset_id=dataset_id)
            dataset.status = "ERROR"
            dataset.save()
            return
            
        file_path = dataset_file.file_path
        ext = dataset.file_type
        
        logger.info("parse_dataset.parsing", dataset_id=dataset_id, file_path=file_path)
        metadata = parse_csv(file_path) if ext == "csv" else parse_json(file_path)
        
        with transaction.atomic():
            dataset.row_count = metadata["row_count"]
            dataset.column_count = metadata["column_count"]
            dataset.column_names = json.dumps(metadata["column_names"])
            dataset.status = "PENDING"
            dataset.save()
            
        logger.info("parse_dataset.success", dataset_id=dataset_id, rows=metadata["row_count"])
    except Exception as e:
        logger.exception("parse_dataset.failed", dataset_id=dataset_id, error=str(e))
        try:
            dataset = Dataset.objects.get(id=dataset_id)
            dataset.status = "ERROR"
            dataset.save()
        except:
            pass
