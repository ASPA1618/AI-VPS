def make_welcome_text():
    return (
        "👋 Вітаємо в *ASPA-боті*!\n\n"
        "🚗 Тут ви зможете підібрати автозапчастини за VIN-кодом, "
        "фото техпаспорта або вручну по марці та моделі авто.\n"
        "⚡ Просто натисніть потрібну мову нижче 👇"
    )

def get_profile_fields():
    return ["last_name", "first_name", "middle_name", "phone", "city", "np_office"]

def make_choose_name(username, user_id):
    return (
        "📝 Як до вас звертатись?\n"
        f"(наприклад, @{username} або {user_id})"
    )
