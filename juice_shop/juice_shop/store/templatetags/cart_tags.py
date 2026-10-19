from django import template
from ..cart import Cart

register = template.Library()


@register.simple_tag
def cart_quantity(request):
    cart = Cart(request)
    return len(cart)


@register.filter
def multiply(value, arg):
    return value * arg


@register.filter
def currency(value):
    return f"${value:.2f}"
