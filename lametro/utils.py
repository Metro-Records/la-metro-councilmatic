# Parse the subject line from ocr_full_text
def format_full_text(full_text):
    results = ''

    if full_text:
        txt_as_array = full_text.split("..")
        for item in txt_as_array:
            if 'SUBJECT:' in item:
                array_with_subject = item.split('\n\n')
                for item in array_with_subject:
                    if 'SUBJECT:' in item:
                        results = item.replace('\n', '')
    return results

# Isolate text after 'SUBJECT'
def parse_subject(text):
    if text:
        before_keyword, keyword, after_keyword = text.partition('SUBJECT:')
        if after_keyword:
            if '[PROJECT OR SERVICE NAME]' not in after_keyword and '[DESCRIPTION]' not in after_keyword and '[CONTRACT NUMBER]' not in after_keyword:
                return after_keyword.strip()

    return None