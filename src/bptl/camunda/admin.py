from django.contrib import admin

from polymorphic.admin import PolymorphicChildModelAdmin

from .models import ExternalTask


@admin.register(ExternalTask)
class ExternalTaskAdmin(PolymorphicChildModelAdmin):
    list_display = ("__str__", "priority", "is_expired", "status")
    list_filter = ("topic_name", "lock_expires_at", "status")
    search_fields = ("task_id", "worker_id")

    def is_expired(self, obj) -> bool:
        return obj.expired

    is_expired.boolean = True
