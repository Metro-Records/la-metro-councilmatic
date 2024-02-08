import csv
import os
import re
import pytz

from django.conf import settings

from haystack.utils.highlighting import Highlighter

app_timezone = pytz.timezone(settings.TIME_ZONE)


class ExactHighlighter(Highlighter):
    """
    This class customizes the Haystack Highlighter to allow for
    highlighting multi-word strings.
    https://django-haystack.readthedocs.io/en/master/highlighting.html#highlighter
    https://github.com/django-haystack/django-haystack/blob/master/haystack/utils/highlighting.py

    Use this class to build custom filters in `search_result.html`.
    """

    def __init__(self, query, **kwargs):
        super(Highlighter, self).__init__()
        self.query_words = self.make_query_words(query)

    def make_query_words(self, query):
        query_words = set()
        if query.startswith('"') and query.endswith('"'):
            query_words.add(query.strip('"'))
        else:
            query_words = set(
                [
                    word.lower()
                    for word in query.split()
                    if not word.startswith("-") and len(word) > 3
                ]
            )

        return query_words


def format_full_text(full_text):
    """
    The search results and board report titles (on the BillDetail) should show
    the "SUBJECT:" header from the board report when present. The ocr_full_text
    contains this information. Some example snippets:

    # Subject header followed by two linebreaks.
    ..Subject\nSUBJECT:\tFOOD SERVICE OPERATOR\n\n..Action\nACTION:\tAWARD
    SERVICES CONTRACT\n\n..

    # Subject header followed by a return carriage and linebreak.
    ..Subject/Action\r\nSUBJECT: MONTHLY REPORT ON CRENSHAW/LAX SAFETY\r\nACTION:
    RECEIVE AND FILE\r\n

    # Subject header with a linebreak in the middle and without an ACTION header.
    ..Subject\nSUBJECT:    REVISED MOTION BY DIRECTORS HAHN, SOLIS, \nGARCIA,
    AND DUPONT-WALKER\n..Title\n
    """
    results = ""

    if full_text:
        clean_full_text = (
            full_text.replace("\n\n", "NEWLINE")
            .replace("\r\n", "NEWLINE")
            .replace("\n..", "NEWLINE")
            .replace("\n", " ")
        )
        match = re.search("(SUBJECT:)(.*?)(NEWLINE|ACTION:)", clean_full_text)
        if match:
            results = match.group(2)

    return results


def parse_subject(text):
    if (
        ("[PROJECT OR SERVICE NAME]" not in text)
        and ("[DESCRIPTION]" not in text)
        and ("[CONTRACT NUMBER]" not in text)
    ):
        return text.strip()


def get_identifier(obj_or_string):
    if isinstance(obj_or_string, str):
        return obj_or_string
    return obj_or_string.id


def get_list_from_csv(filename):
    file_directory = os.path.dirname(__file__)
    absolute_file_directory = os.path.abspath(file_directory)
    my_file = os.path.join(absolute_file_directory, "..", "data", filename)

    with open(my_file) as f:
        reader = csv.DictReader(f)

        new_fieldnames = []
        for field in reader.fieldnames:
            new_fieldname = field.lower().replace(" ", "_")
            new_fieldnames.append(new_fieldname)
        reader.fieldnames = new_fieldnames

        my_list = [row for row in reader]

    return my_list
