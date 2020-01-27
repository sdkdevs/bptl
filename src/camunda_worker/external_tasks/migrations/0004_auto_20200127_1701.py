# Generated by Django 2.2.9 on 2020-01-27 16:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("external_tasks", "0003_auto_20200116_1432"),
    ]

    operations = [
        migrations.AlterField(
            model_name="fetchedtask",
            name="status",
            field=models.CharField(
                choices=[
                    ("initial", "Initial"),
                    ("in_progress", "In progress"),
                    ("performed", "The task is performed, but not sent to Camunda"),
                    ("failed", "Failed"),
                    ("completed", "Completed"),
                ],
                default="initial",
                help_text="The current status of task processing",
                max_length=50,
                verbose_name="status",
            ),
        ),
    ]
