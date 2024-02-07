from datetime import timedelta, datetime
import itertools
import json
import re
import urllib

from django import template
from django.utils import timezone

from councilmatic.settings_jurisdiction import legislation_types
from councilmatic.settings import PIC_BASE_URL
from councilmatic_core.models import Person, Bill

from lametro.models import app_timezone, Alert
from lametro.utils import ExactHighlighter, format_full_text, parse_subject


register = template.Library()


@register.filter
def call_link_html(person_id):
    person = Person.objects.get(id=person_id)
    url = person.link_html
    return url


@register.filter
def format_label(label):
    first_part = label.split(", ")[0]

    return first_part


@register.filter
def comma_to_line_break(text):
    return "<br />".join(text.split(", "))


@register.filter
def format_district(label):
    label_parts = label.split(", ")
    if "Mayor of the City" in label:
        formatted_label = "City of Los Angeles"
    else:
        formatted_label = label_parts[-1]
    return formatted_label


# Filter for legislation detail view
@register.filter
def prepare_title(full_text):
    formatted_text = format_full_text(full_text)

    if formatted_text:
        return parse_subject(formatted_text)


@register.filter
def full_text_doc_url(url):
    query = {"document_url": url, "filename": "agenda"}
    pic_query = {"file": PIC_BASE_URL + "?" + urllib.parse.urlencode(query)}

    return urllib.parse.urlencode(pic_query)


@register.filter
def appointment_label(label):
    """
    This filter converts the post title into a prose-style format with
    nomination info, e.g., "Appointee of Los Angeles County City Selection
    Committee, Southeast Long Beach sector" into "Appointee of [Committee],
    nominated by the [Subcommittee]".

    Some posts do not require modification, e.g., "Caltrans District 7 Director,
    Appointee of Governor of California."

    A full list of posts resides in the scraper.
    """
    if "District 7 Director" in label:
        return label

    elif "Chief Executive Officer" in label:
        return label

    elif label == "Mayor of the City of Los Angeles":
        return label

    full_label = label.replace("Appointee of", "Appointee of the")
    label_parts = full_label.split(", ")

    if len(label_parts) < 1:
        return full_label

    if "sector" in full_label:
        return ", nominated by the ".join(label_parts).replace("sector", "Subcommittee")
    else:
        return ", nominated by the ".join(label_parts) + " Subcommittee"


@register.filter
def clean_membership_extras(extras):
    if extras.get("acting"):
        return "Acting"
    else:
        return ""


@register.filter
def clean_role(role_list):
    if "Board Member" in role_list:
        role_list.remove("Board Member")

    return role_list[0]


@register.filter
def compare_time(event_date):
    if event_date < timezone.now():
        return True


@register.filter
def parse_agenda_item(text):
    if text:
        label, number = text.split(",")
        return number
    else:
        return ""


@register.filter
def short_topic_name(text):
    if len(text) > 50:
        blurb = text[:50]
        blurb = blurb[: blurb.rfind(" ")] + " ..."
        return blurb
    else:
        return text


@register.filter
def updates_made(event):
    """
    If an upcoming event has been updated in any way (changed time, address,
    document, agenda item, status, etc), in a four-day window before the
    event's scheduled start time.
    """
    four_days_before_meeting = event.start_time - timedelta(days=4)

    updates_made = False

    if (
        four_days_before_meeting
        <= app_timezone.localize(datetime.now())
        < event.start_time
    ):
        # Only check for an agenda (firing an additional query) if we're within
        # the update window.
        if event.documents.filter(note__icontains="agenda").exists():
            updates_made = (
                four_days_before_meeting <= event.updated_at < event.start_time
            )

    return updates_made


@register.filter
def find_agenda_url(all_documents):
    """
    This filter determines how to format the URL link, particularly, in the
    case of manually uploaded agenda.
    """
    valid_urls = [
        link.url
        for doc in all_documents
        if doc.note in ("Agenda", "Event Document - Manual upload URL")
        for link in doc.links.all()
    ]

    pdf_url = [
        ("static/" + link.url)
        for doc in all_documents
        if doc.note == "Event Document - Manual upload PDF"
        for link in doc.links.all()
    ]

    valid_urls += pdf_url

    return valid_urls[0]


@register.simple_tag(takes_context=True)
def get_highlighted_attachment_text(context, id):
    bill = Bill.objects.get(id=id)
    attachment_text = " ".join(
        d.extras["full_text"] for d in bill.documents.all() if d.extras.get("full_text")
    )

    highlight = ExactHighlighter(context["query"])

    return highlight.highlight(attachment_text)


@register.filter
def matches_query(tag, request):
    # request.GET['q'] looks like "token AND token AND token"
    terms = [
        token.lower().replace('"', "")
        for token in request.GET.get("q", "").split(" AND ")
        if token
    ]

    exactly_matches = tag.lower() in terms
    partially_matches = any(term in tag.lower() for term in terms)

    return exactly_matches or partially_matches


@register.filter
def matches_facet(tag, selected_facets):
    facet_values = []

    for values in selected_facets.values():
        facet_values += [v.lower() for v in values]

    exactly_matches = tag.lower() in facet_values
    partially_matches = any(value in tag.lower() for value in facet_values)

    return exactly_matches or partially_matches


@register.simple_tag(takes_context=True)
def hits_first(context, topics, selected_facets):
    """
    Return array of topics, such that topics matching a selected facet or the
    search term are returned first, followed by the remaining tags in ABC order.
    """
    if isinstance(topics, list):
        return topics

    topics = json.loads(topics)

    # context['query'] looks like "(token) AND (token) AND (token)". Sometimes,
    # tokens end with parentheses, e.g., "(Coronavirus (COVID-19))". Using a
    # solution like rstrip() removes both of the closing parentheses, which
    # interferes with hits. To strip the enclosing parentheses, but leave the
    # others in tact, remove the first opening parenthesis, reverse the string,
    # remove the first closing parenthesis, then put the string back in the
    # right order.
    terms = [
        token.replace("(", "", 1)[::-1].replace(")", "", 1)[::-1].replace('"', "")
        for token in re.split(" and ", context["query"], re.IGNORECASE)
        if token
    ]

    for _, values in selected_facets.items():
        terms += values

    hits_pattern = r"({})".format("|".join(re.escape(term) for term in terms))

    return list(
        itertools.chain(
            filter(
                lambda topic: re.match(hits_pattern, topic["name"], re.IGNORECASE),
                topics,
            ),
            filter(
                lambda topic: not re.match(hits_pattern, topic["name"], re.IGNORECASE),
                topics,
            ),
        )
    )


@register.filter
def all_have_extra(entities, extra):
    """
    Determine whether all entities in a given array have the designated value
    in their extras.
    """
    return all(e.extras.get(extra, None) for e in entities)


@register.filter
def get_list(querydict, key):
    return querydict.getlist(key)


@register.filter
def get_bill_type_link(bill_type):
    for legislation_type in legislation_types:
        if legislation_type["search_term"].upper() == bill_type.upper():
            return f'/about#{legislation_type["html_id"]}'

    return ""


@register.filter
def query_encode(query):
    return urllib.parse.quote_plus(query)


@register.filter
def group_by_classification(queryset):
    for group, members in itertools.groupby(
        queryset.order_by("classification"),
        lambda item: item.get_classification_display(),
    ):
        yield group, list(members)


@register.filter
def sort_topics(topics):
    """Sorts a board report's topics alphabetically."""

    return sorted(topics, key=lambda t: t.name)


@register.simple_tag
def get_alerts():
    return Alert.objects.all()
