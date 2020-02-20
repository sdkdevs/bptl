from django.core.management import BaseCommand, CommandError

from ...models import ExternalTask
from ...tasks import task_execute_and_complete


class Command(BaseCommand):
    help = "Execute and complete an External Camunda task."

    def add_arguments(self, parser):
        parser.add_argument(
            "task_id", type=int, help="ID of the External Task in the database"
        )

    def handle(self, **options):
        task_id = options["task_id"]
        task = ExternalTask.objects.filter(id=task_id).first()
        if task is None:
            raise CommandError("Could not find this task.")

        try:
            task_execute_and_complete(task_id)
        except Exception as exc:
            raise CommandError(exc) from exc
