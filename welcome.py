def make_welcome_text():
    return (
        "Вітаємо у ASPA-бот!\n"
        "Ми допоможемо знайти автозапчастини за VIN або фото техпаспорта.\n"
        "Оберіть мову для спілкування нижче 👇"
    )

def get_profile_fields():
    # Какие поля будут в карточке клиента
    return ["last_name", "first_name", "middle_name", "phone", "city", "np_office"]
