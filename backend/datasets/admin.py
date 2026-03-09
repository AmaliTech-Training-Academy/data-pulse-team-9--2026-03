from django.contrib import admin
from .models import Dataset, DatasetFile

@admin.register(Dataset)
class DatasetAdmin(admin.ModelAdmin):
    list_display = ('name', 'file_type', 'uploaded_by', 'status', 'row_count', 'uploaded_at')
    list_filter = ('file_type', 'status')
    search_fields = ('name', 'uploaded_by__email')
    ordering = ('-uploaded_at',)

@admin.register(DatasetFile)
class DatasetFileAdmin(admin.ModelAdmin):
    list_display = ('dataset', 'original_filename', 'file_path')
    search_fields = ('original_filename', 'dataset__name')
