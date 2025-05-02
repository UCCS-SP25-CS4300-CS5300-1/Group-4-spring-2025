"""
This file contains the filters for the jobs app.
"""

from django import template
import html
import ast

register = template.Library()

@register.filter(name='format_field')
def format_field(value):
    """
    This function formats the field value.
    """

    if value is None:
        return None

    processed_value = value

    if isinstance(value, str) and value.startswith('[') and value.endswith(']'):
        try:
            list_val = ast.literal_eval(value)
            if isinstance(list_val, list) and len(list_val) > 0:
                processed_value = list_val[0]
            elif isinstance(list_val, list):
                processed_value = ''
        except (ValueError, SyntaxError):
            processed_value = value.strip('\'"[] ')

    if isinstance(processed_value, str):
        processed_value = html.unescape(processed_value)
        if processed_value:
            processed_value = processed_value.replace('_', ' ').replace('-', ' ').title()
        return processed_value
    else:
        return processed_value
    