import os

def load_template(template_name):
    template_path = os.path.join('email_templates', template_name)
    with open(template_path, 'r') as file:
        return file.read()

def populate_template(template, replacements):
    for placeholder, value in replacements.items():
        template = template.replace('{{' + placeholder + '}}', value)
    return template

def str_to_bool(s: str) -> bool:
    """
    Convert a string to a boolean.

    Args:
        s (str): The string to convert.

    Returns:
        bool: The converted boolean value.
    """
    if s.lower() in ('true', 'yes', '1'):
        return True
    elif s.lower() in ('false', 'no', '0'):
        return False
    else:
        raise ValueError(f"Cannot convert {s} to boolean")
 