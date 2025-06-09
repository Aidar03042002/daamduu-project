# core/pipeline.py

from social_core.exceptions import AuthForbidden

def check_email_domain(strategy, details, backend, *args, **kwargs):
    """
    Проверка, что email оканчивается на @manas.edu.kg
    """
    email = details.get("email")
    if email and not email.endswith("@manas.edu.kg"):
        raise AuthForbidden(backend, "Доступ разрешён только для @manas.edu.kg")

def get_username_and_names(strategy, details, backend, *args, **kwargs):
    """
    Устанавливает username, first_name и last_name, если они отсутствуют
    """
    email = details.get("email")
    if email:
        username = email.split('@')[0]
        details['username'] = username

    # Автозаполнение имени и фамилии только для нового пользователя
    user = kwargs.get('user')

    if user is None:
        # Если пользователь создаётся — берем из details
        first_name = details.get("first_name") or ""
        last_name = details.get("last_name") or ""

        details["first_name"] = first_name
        details["last_name"] = last_name
