from decimal import Decimal, InvalidOperation

from django import template
from django.templatetags.static import static

from bikes.models import Bike

register = template.Library()


@register.filter
def euro(value):
    try:
        amount = Decimal(value)
    except (InvalidOperation, TypeError):
        return value
    formatted = f"{amount:.2f}".replace(".", ",")
    return f"{formatted} €"


@register.simple_tag
def bike_photo_url(bike):
    if bike.image:
        return bike.image.url
    if bike.bike_type == Bike.BikeType.ELECTRIC:
        return static("bikes/electric-bike.png")
    return static("bikes/city-bike.png")
