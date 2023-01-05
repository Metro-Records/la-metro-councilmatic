from django.conf import settings


def recaptcha_public_key(request):
    # See: https://developers.google.com/recaptcha/docs/faq
    recaptcha_dev_key = "6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI"
    return {
        "recaptcha_public_key": getattr(
            settings, "RECAPTCHA_PUBLIC_KEY", recaptcha_dev_key
        )
    }
