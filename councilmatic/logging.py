def before_send(event, hint):
    """
    Log 400 Bad Request errors with the same custom fingerprint so that we can
    group them and ignore them all together. See:
    https://github.com/getsentry/sentry-python/issues/149#issuecomment-434448781
    """

    # Don't log errors from /rss/ paths
    path = event.get("request", {}).get("url", "")
    is_rss_path = "/rss/" in path
    if is_rss_path:
        return None

    log_record = hint.get("log_record")
    if log_record and hasattr(log_record, "name"):
        if log_record.name == "django.security.DisallowedHost":
            event["fingerprint"] = ["disallowed-host"]
    return event
