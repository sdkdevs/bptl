from django.contrib import admin

from polymorphic.admin import PolymorphicChildModelFilter, PolymorphicParentModelAdmin

from bptl.activiti.models import ServiceTask
from bptl.camunda.models import ExternalTask
from bptl.work_units.zgw.models import DefaultService

from .forms import AdminTaskMappingForm
from .models import BaseTask, TaskMapping


class DefaultServiceInline(admin.TabularInline):
    model = DefaultService
    extra = 1


@admin.register(TaskMapping)
class TaskMappingAdmin(admin.ModelAdmin):
    list_display = ("__str__", "active")
    list_filter = ("active",)
    search_fields = ("topic_name", "callback")
    form = AdminTaskMappingForm
    inlines = (DefaultServiceInline,)


@admin.register(BaseTask)
class BaseTaskAdmin(PolymorphicParentModelAdmin):
    child_models = (ExternalTask, ServiceTask)
    list_filter = (PolymorphicChildModelFilter, "status")
