"""Dataset models matching original SQLAlchemy models."""

from django.db import models


class Dataset(models.Model):
    """Dataset metadata stored after file upload."""

    name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=10)
    row_count = models.IntegerField(default=0)
    column_count = models.IntegerField(default=0)
    column_names = models.TextField(null=True, blank=True)
    uploaded_by = models.ForeignKey("authentication.User", on_delete=models.SET_NULL, null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default="PENDING")

    class Meta:
        db_table = "datasets"

    def __str__(self):
        return self.name


class DatasetFile(models.Model):
    """Physical file associated with a dataset."""

    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name="files")
    file_path = models.CharField(max_length=500)
    original_filename = models.CharField(max_length=255)

    class Meta:
        db_table = "dataset_files"
