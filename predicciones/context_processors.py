from django.conf import settings


def entorno(request):
    return {"es_produccion": not settings.DEBUG, "requiere_login": settings.REQUIRE_LOGIN}
