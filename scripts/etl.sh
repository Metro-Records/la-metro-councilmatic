#!/bin/bash -x

# Location of manage.py in container
MANAGE_PY="python /app/manage.py"

$MANAGE_PY refresh_pic
$MANAGE_PY compile_pdfs
$MANAGE_PY convert_attachment_text
$MANAGE_PY update_index --batch-size=50
$MANAGE_PY data_integrity
