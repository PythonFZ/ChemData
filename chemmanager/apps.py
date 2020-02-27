from django.apps import AppConfig


class ChemmanagerConfig(AppConfig):
    name = 'chemmanager'


# TODO Nutzer Gruppen/AK Zuweisen
# TODO Datenbank erweitern um mehr Funktionen
# TODO Bild für Chemikalien
# TODO Chemikalien Edit
# TODO login_required mit LoginRequiredMixin ersetzen
# TODO Delete chemical only for "staff" members or Person who created it!
# TODO Update Tooltip at stock!
