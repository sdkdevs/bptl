from datetime import date
from typing import Any, Dict

from django.utils import timezone

from zgw_consumers.constants import APITypes

from bptl.tasks.registry import register

from ..nlx import get_nlx_headers
from .base import ZGWWorkUnit
from .resultaat import CreateResultaatTask


@register
class CreateZaakTask(ZGWWorkUnit):
    """
    Create a ZAAK in the configured Zaken API and set the initial status.

    The initial status is the STATUSTYPE with ``volgnummer`` equal to 1 for the
    ZAAKTYPE.

    **Required process variables**

    * ``zaaktype``: the full URL of the ZAAKTYPE
    * ``organisatieRSIN``: RSIN of the organisation
    * ``services``: JSON Object of connection details for ZGW services:

        .. code-block:: json

          {
              "<zrc alias>": {"jwt": "Bearer <JWT value>"},
              "<ztc alias>": {"jwt": "Bearer <JWT value>"}
          }

    **Optional process variables**

    * ``NLXProcessId``: a process id for purpose registration ("doelbinding")
    * ``NLXSubjectIdentifier``: a subject identifier for purpose registration ("doelbinding")

    **Optional process variables (Camunda exclusive)**

    * ``callbackUrl``: send an empty POST request to this URL to signal completion

    **Sets the process variables**

    * ``zaak``: the JSON response of the created ZAAK
    * ``zaakUrl``: the full URL of the created ZAAK
    * ``zaakIdentificatie``: the identificatie of the created ZAAK
    """

    def create_zaak(self) -> dict:
        variables = self.task.get_variables()

        client_zrc = self.get_client(APITypes.zrc)
        today = date.today().strftime("%Y-%m-%d")
        data = {
            "zaaktype": variables["zaaktype"],
            "vertrouwelijkheidaanduiding": "openbaar",
            "bronorganisatie": variables["organisatieRSIN"],
            "verantwoordelijkeOrganisatie": variables["organisatieRSIN"],
            "registratiedatum": today,
            "startdatum": today,
        }

        headers = get_nlx_headers(variables)
        zaak = client_zrc.create("zaak", data, request_kwargs={"headers": headers})
        return zaak

    def create_status(self, zaak: dict) -> dict:
        variables = self.task.get_variables()

        # get statustype for initial status
        ztc_client = self.get_client(APITypes.ztc)
        statustypen = ztc_client.list(
            "statustype", {"zaaktype": variables["zaaktype"]}
        )["results"]
        statustype = next(filter(lambda x: x["volgnummer"] == 1, statustypen))

        # create status
        zrc_client = self.get_client(APITypes.zrc)
        data = {
            "zaak": zaak["url"],
            "statustype": statustype["url"],
            "datumStatusGezet": timezone.now().isoformat(),
        }
        status = zrc_client.create("status", data)
        return status

    def perform(self) -> Dict[str, Any]:
        zaak = self.create_zaak()
        self.create_status(zaak)
        return {
            "zaak": zaak,
            "zaakUrl": zaak["url"],
            "zaakIdentificatie": zaak["identificatie"],
        }


@register
class CloseZaakTask(ZGWWorkUnit):
    """
    Close the ZAAK by setting the final STATUS.

    A ZAAK is required to have a RESULTAAT.

    **Required process variables**

    * ``zaak``: full URL of the ZAAK
    * ``services``: JSON Object of connection details for ZGW services:

        .. code-block:: json

          {
              "<zrc alias>": {"jwt": "Bearer <JWT value>"},
              "<ztc alias>": {"jwt": "Bearer <JWT value>"}
          }

    **Optional process variables**

    * ``resultaattype``: full URL of the RESULTAATTYPE to set.
      If provided the RESULTAAT is created before the ZAAK is closed

    **Optional process variables (Camunda exclusive)**

    * ``callbackUrl``: send an empty POST request to this URL to signal completion

    **Sets the process variables**

    * ``einddatum``: date of closing the zaak
    * ``archiefnominatie``: shows if the zaak should be destroyed or stored permanently
    * ``archiefactiedatum``: date when the archived zaak should be destroyed or transferred to the archive
    """

    def create_resultaat(self):
        resultaattype = self.task.get_variables().get("resultaattype")

        if not resultaattype:
            return

        create_resultaat_work_unit = CreateResultaatTask(self.task)
        create_resultaat_work_unit.create_resultaat()

    def close_zaak(self) -> dict:
        # build clients
        zrc_client = self.get_client(APITypes.zrc)
        ztc_client = self.get_client(APITypes.ztc)

        # get statustype to close zaak
        zaak = self.task.get_variables()["zaak"]
        zaaktype = zrc_client.retrieve("zaak", zaak)["zaaktype"]
        statustypen = ztc_client.list("statustype", {"zaaktype": zaaktype})["results"]
        statustype = next(filter(lambda x: x["isEindstatus"] is True, statustypen))

        # create status to close zaak
        data = {
            "zaak": zaak,
            "statustype": statustype["url"],
            "datumStatusGezet": timezone.now().isoformat(),
        }
        zrc_client.create("status", data)

        # get zaak to receive calculated variables
        zaak_closed = zrc_client.retrieve("zaak", zaak)
        return zaak_closed

    def perform(self):
        self.create_resultaat()
        resultaat = self.close_zaak()

        return {
            "einddatum": resultaat["einddatum"],
            "archiefnominatie": resultaat["archiefnominatie"],
            "archiefactiedatum": resultaat["archiefactiedatum"],
        }
