from django.utils import timezone

from zgw_consumers.constants import APITypes

from bptl.tasks.registry import register

from .base import ZGWWorkUnit


@register
class CreateStatusTask(ZGWWorkUnit):
    """
    Create a new STATUS for the ZAAK in the process.

    **Required process variables**

    * ``zaak``: full URL of the ZAAK to create a new status for
    * ``statustype``: full URL of the STATUSTYPE to set
    * ``services``: JSON Object of connection details for ZGW services:

        .. code-block:: json

          {
              "<zrc alias>": {"jwt": "Bearer <JWT value>"},
              "<ztc alias>": {"jwt": "Bearer <JWT value>"}
          }

    **Optional process variables (Camunda exclusive)**

    * ``callbackUrl``: send an empty POST request to this URL to signal completion

    **Sets the process variables**

    * ``status``: the full URL of the created STATUS
    """

    def create_status(self) -> dict:
        variables = self.task.get_variables()
        zrc_client = self.get_client(APITypes.zrc)
        data = {
            "zaak": variables["zaak"],
            "statustype": variables["statustype"],
            "datumStatusGezet": timezone.now().isoformat(),
        }
        status = zrc_client.create("status", data)
        return status

    def perform(self):
        status = self.create_status()
        return {"status": status["url"]}
