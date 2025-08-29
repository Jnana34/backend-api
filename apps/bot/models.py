import uuid
from django.db import models
from pgvector.django import VectorField   # pip install django-pgvector


class SchemaEmbedding(models.Model):
    """
    Stores embeddings of table/column definitions.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    object_name = models.CharField(max_length=255)   # e.g., "cart_items.quantity"
    definition = models.TextField()
    embedding = VectorField(dimensions=768)          # text-embedding-004 → 768 dims

    def __str__(self):
        return self.object_name


class FAQCache(models.Model):
    """
    Stores frequently asked questions with responses for quick lookup.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.TextField()
    embedding = VectorField(dimensions=768)
    response = models.JSONField()
    hits = models.PositiveIntegerField(default=0)
    last_used = models.DateTimeField(auto_now=True)


class QueryLog(models.Model):
    """
    Logs user queries, generated SQL, and results for retraining.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(null=True, blank=True)
    question = models.TextField()
    question_embedding = VectorField(dimensions=768, null=True)
    generated_sql = models.TextField(null=True, blank=True)
    sql_result = models.JSONField(null=True, blank=True)
    model_name = models.CharField(max_length=100, default="gemini-embedding-001")
    created_at = models.DateTimeField(auto_now_add=True)
