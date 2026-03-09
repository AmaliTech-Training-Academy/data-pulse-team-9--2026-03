from datasets.models import Dataset
from rest_framework import serializers


class DatasetResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dataset
        fields = ["id", "name", "file_type", "row_count", "column_count", "column_names", "status", "uploaded_at"]


class DatasetListSerializer(serializers.Serializer):
    datasets = DatasetResponseSerializer(many=True)
    total = serializers.IntegerField()
