from django import template
import html
import ast

register = template.Library()

@register.filter(name='format_field')
def format_field(value):
    
    if value is None:
        return '' 

    if not isinstance(value, str):
        return value

    processed_value = value
    
    if value.startswith('[') and value.endswith(']'):
        try:
            list_val = ast.literal_eval(value)
            if isinstance(list_val, list) and len(list_val) > 0:
                processed_value = format_field(list_val[0])
            else:
                 processed_value = '' 
        except (ValueError, SyntaxError):
             processed_value = value.strip('[]"\' ')
             if processed_value == value:
                 processed_value = value 
             else:
                 processed_value = format_field(processed_value)
                 
    if isinstance(processed_value, str):
        current_str = html.unescape(processed_value)
        
        if current_str:
            formatted_str = current_str.replace('_', ' ').replace('-', ' ').title()
        else:
            formatted_str = ''
            
        return formatted_str
    else:
        return processed_value

# Ensure the directory structure is: myproject/home/templatetags/__init__.py 