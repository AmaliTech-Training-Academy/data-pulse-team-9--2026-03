"""Dataset upload router - IMPLEMENTED."""

import os
import uuid

from datapulse.exceptions import InvalidFileException
from datasets.models import Dataset, DatasetFile
from datasets.serializers import DatasetListSerializer, DatasetResponseSerializer
from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView


class DatasetUploadView(APIView):
    """Upload a CSV or JSON file and store dataset metadata."""

    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        request={
            "multipart/form-data": {
                "type": "object",
                "properties": {"file": {"type": "string", "format": "binary"}},
            }
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

        dataset = Dataset.objects.create(
            name=filename.rsplit(".", 1)[0],
            file_type=ext,
            row_count=0,
            column_count=0,
            column_names=None,
            uploaded_by=request.user if request.user and request.user.is_authenticated else None,
            status="PROCESSING",
        )

        DatasetFile.objects.create(dataset=dataset, file_path=file_path, original_filename=filename)

        # Trigger Celery Task asynchronously
        from datasets.tasks import parse_dataset_file_task

        parse_dataset_file_task.delay(dataset.id)

        return Response(DatasetResponseSerializer(dataset).data, status=status.HTTP_201_CREATED)


from rest_framework import generics  # noqa: E402


class DatasetListView(generics.ListAPIView):
    """List all datasets."""

    serializer_class = DatasetResponseSerializer

    @extend_schema(
        responses={200: DatasetListSerializer},
        tags=["Datasets"],
        summary="List previously uploaded datasets",
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        queryset = Dataset.objects.all().order_by("-uploaded_at")

        # Admin can filter by uploader
        if getattr(self.request.user, "role", "USER") == "ADMIN":
            uploaded_by = self.request.query_params.get("uploaded_by")
            if uploaded_by:
                queryset = queryset.filter(uploaded_by_id=uploaded_by)
            return queryset

        # Standard user only sees their own
        return queryset.filter(uploaded_by=self.request.user)


class DatasetDetailView(generics.RetrieveAPIView):
    """Retrieve a single dataset by ID (use to poll processing status)."""

    serializer_class = DatasetResponseSerializer

    @extend_schema(
        responses={200: DatasetResponseSerializer},
        tags=["Datasets"],
        summary="Get dataset details by ID",
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        if getattr(self.request.user, "role", "USER") == "ADMIN":
            return Dataset.objects.all()
        return Dataset.objects.filter(uploaded_by=self.request.user)
