"""Dataset upload router - IMPLEMENTED."""

import json
import os
import uuid

from datapulse.exceptions import InvalidFileException
from datasets.models import Dataset, DatasetFile
from datasets.serializers import DatasetListSerializer, DatasetResponseSerializer
from datasets.services.file_parser import parse_csv, parse_json
from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView


class DatasetUploadView(APIView):
    """Upload a CSV or JSON file and store dataset metadata."""

    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        request={
            "multipart/form-data": {"type": "object", "properties": {"file": {"type": "string", "format": "binary"}}}
        },
        responses={201: DatasetResponseSerializer},
        tags=["Datasets"],
        summary="Upload a CSV or JSON file",
    )
    def post(self, request):
        file = request.FILES.get("file")
        if not file:
            raise InvalidFileException("No file provided.")

        filename = file.name or ""
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext not in ("csv", "json"):
            raise InvalidFileException(f"Unsupported file type: {ext}")

        upload_dir = settings.UPLOAD_DIR
        os.makedirs(upload_dir, exist_ok=True)
        unique_name = f"{uuid.uuid4().hex}_{filename}"
        file_path = os.path.join(upload_dir, unique_name)

        content = file.read()
        if len(content) == 0:
            raise InvalidFileException("Uploaded file is empty.")
        with open(file_path, "wb") as fh:
            fh.write(content)

        try:
            metadata = parse_csv(file_path) if ext == "csv" else parse_json(file_path)
        except Exception as e:
            os.remove(file_path)
            raise InvalidFileException(f"Failed to parse: {e}")

        dataset = Dataset.objects.create(
            name=filename.rsplit(".", 1)[0],
            file_type=ext,
            row_count=metadata["row_count"],
            column_count=metadata["column_count"],
            column_names=json.dumps(metadata["column_names"]),
            uploaded_by=request.user,
            status="PENDING",
        )

        DatasetFile.objects.create(dataset=dataset, file_path=file_path, original_filename=filename)

        return Response(DatasetResponseSerializer(dataset).data, status=status.HTTP_201_CREATED)


class DatasetListView(generics.ListAPIView):
    """List all datasets with role-based access control."""

    serializer_class = DatasetResponseSerializer
    pagination_key = "datasets"

    @extend_schema(
        responses={200: DatasetListSerializer},
        tags=["Datasets"],
        summary="List all datasets",
    )
    def get(self, request, *args, **kwargs):
        # We override get to maintain the exact list serializer shape in docs
        # but generics.ListAPIView + our custom pagination handles the data
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        if getattr(self.request.user, "role", "USER") == "ADMIN":
            return Dataset.objects.all().order_by("-uploaded_at")
        return Dataset.objects.filter(uploaded_by=self.request.user).order_by("-uploaded_at")
