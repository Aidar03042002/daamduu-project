# core/pipeline.py

def check_email_domain(strategy, details, backend, *args, **kwargs):
    email = details.get("email")
    if email and not email.endswith("@manas.edu.kg"):
        raise Exception("Доступ разрешён только для manas.edu.kg")

def get_username_and_names(strategy, details, backend, *args, **kwargs):
    email = details.get("email")
    if email:
        username = email.split('@')[0]
        details['username'] = username

    # Автозаполнение имени и фамилии
    first_name = details.get("first_name")
    last_name = details.get("last_name")

    # Only set names if user does not exist yet
    user = kwargs.get('user')
    if user is None or not user.first_name and not user.last_name:
        # This is a new user or user has no names set
        if first_name:
            details["first_name"] = first_name
        if last_name:
            details["last_name"] = last_name
    # If user exists and already has names, do not overwrite
    