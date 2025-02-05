from django.db import models
from users.models import User


class BaseModel(models.Model):
    created_at = models.DateTimeField(
        auto_now_add=True, blank=True, null=True, db_index=True
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        db_index=True,
        related_name="+",
    )
    updated_at = models.DateTimeField(
        auto_now=True, blank=True, null=True, db_index=True
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        db_index=True,
        related_name="+",
    )

    class Meta:
        abstract = True