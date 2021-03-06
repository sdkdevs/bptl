from unittest.mock import patch

from django.conf import settings
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from bptl.tasks.models import TaskMapping
from bptl.utils.constants import Statuses

from ..models import ServiceTask
from .utils import TokenAuthMixin


class WorkUnitTestCase(TokenAuthMixin, APITestCase):
    @patch(
        "bptl.work_units.zgw.tasks.zaak.CreateZaakTask.create_zaak",
        return_value={"url": "zaak_url", "identificatie": "foo"},
    )
    @patch("bptl.work_units.zgw.tasks.zaak.CreateZaakTask.create_status")
    def test_post_workunit(self, *mocks):
        TaskMapping.objects.create(
            topic_name="zaak-initialize",
            callback="bptl.work_units.zgw.tasks.zaak.CreateZaakTask",
        )

        data = {"topic": "zaak-initialize", "vars": {"someOtherVar": 123}}
        url = reverse("work-unit", args=(settings.REST_FRAMEWORK["DEFAULT_VERSION"],))

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        service_task = ServiceTask.objects.get()

        self.assertEqual(service_task.topic_name, "zaak-initialize")
        self.assertEqual(service_task.status, Statuses.performed)
        self.assertEqual(service_task.variables, {"someOtherVar": 123})

        data_response = response.json()
        expected_response = data.copy()
        expected_response["resultVars"] = {
            "zaak": {"url": "zaak_url", "identificatie": "foo"},
            "zaakUrl": "zaak_url",
            "zaakIdentificatie": "foo",
        }
        self.assertEqual(data_response, expected_response)

    @patch("bptl.activiti.api.views.execute", side_effect=Exception("This is fine"))
    def test_post_workunit_fail_execute(self, m):
        data = {"topic": "zaak-initialize", "vars": {"someOtherVar": 123}}
        url = reverse("work-unit", args=(settings.REST_FRAMEWORK["DEFAULT_VERSION"]))

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        data = response.json()

        self.assertTrue(data["non_field_errors"].strip().endswith("This is fine"))
