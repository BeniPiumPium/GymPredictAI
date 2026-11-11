from django import template

register = template.Library()


@register.filter
def pesos(value):
    if value is None:
        return "—"
    try:
        amount = float(value or 0)
    except (TypeError, ValueError):
        amount = 0
    return "$" + f"{amount:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")


@register.filter
def numero(value):
    if value is None:
        return "—"
    try:
        amount = float(value or 0)
    except (TypeError, ValueError):
        return "0"
    if amount.is_integer():
        return f"{int(amount):,}".replace(",", ".")
    return f"{amount:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".")
