from django.conf import settings


def city_context(request):
    relevant_settings = [
        "SITE_META",
        "FOOTER_CREDITS",
        "CITY_COUNCIL_NAME",
        "CITY_NAME",
        "CITY_NAME_SHORT",
        "CITY_VOCAB",
        "SEARCH_PLACEHOLDER_TEXT",
        "LEGISLATION_TYPE_DESCRIPTIONS",
        "LEGISTAR_URL",
        "DISQUS_SHORTNAME",
        "IMAGES",
        "MAP_CONFIG",
        "ANALYTICS_TRACKING_CODE",
        "ABOUT_BLURBS",
        "USING_NOTIFICATIONS",
        "GOOGLE_API_KEY",
    ]

    return {s: getattr(settings, s, None) for s in relevant_settings}


def recaptcha_public_key(request):
    # See: https://developers.google.com/recaptcha/docs/faq
    recaptcha_dev_key = "6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI"
    return {
        "recaptcha_public_key": getattr(
            settings, "RECAPTCHA_PUBLIC_KEY", recaptcha_dev_key
        )
    }
