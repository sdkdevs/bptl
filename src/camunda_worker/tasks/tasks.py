from datetime import date

from django.utils import timezone

from zgw_consumers.models import APITypes, Service


class Task:
    def __init__(self, task):
        self.task = task

    def perform(self):
        raise NotImplementedError("subclasses of Task must provide a perform() method")


class CreateZaakTask(Task):
    def create_zaak(self) -> dict:
        zrc = Service.objects.filter(api_type=APITypes.zrc)
        client = zrc.build_client()
        variables = self.task.flat_variables()
        today = date.today().strftime("%Y-%m-%d")
        data = {
            "zaaktype": variables["zaaktype"],
            "vertrouwelijkheidaanduiding": "openbaar",
            "bronorganisatie": variables["organisatieRSIN"],
            "verantwoordelijkeOrganisatie": variables["organisatieRSIN"],
            "registratiedatum": today,
            "startdatum": today,
        }

        zaak = client.create("zaak", data)
        return zaak

    def create_status(self, zaak) -> dict:
        # get statustype for initial status
        ztc = Service.objects.filter(api_type=APITypes.ztc)
        ztc_client = ztc.build_client()
        statustypen = ztc_client.list(
            "status", {"zaaktype": self.task.flat_variables()["zaaktype"]}
        )
        statustype = next(filter(lambda x: x["statustypevolgnummer"] == 1, statustypen))

        # create status
        zrc = Service.objects.filter(api_type=APITypes.zrc)
        zrc_client = zrc.build_client()
        data = {
            "zaaK": zaak["url"],
            "statustype": statustype["url"],
            "datumStatusGezet": timezone.now().isoformat(),
        }
        status = zrc_client.create("status", data)
        return status

    def perform(self):
        zaak = self.create_zaak()
        self.create_status(zaak)
        return {"zaak": zaak["url"]}


# mapping of task topic and correspondent python class to perform the task
MAPPING = {
    "zaak-initialize": CreateZaakTask,
}
