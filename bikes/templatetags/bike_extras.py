from decimal import Decimal, InvalidOperation

from django import template

register = template.Library()


@register.filter
def euro(value):
    try:
        amount = Decimal(value)
    except (InvalidOperation, TypeError):
        return value
    formatted = f"{amount:.2f}".replace(".", ",")
    return f"{formatted} €"
