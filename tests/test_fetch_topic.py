import json


def test_fetch_single_topic(client, subject_guid):

    s_g = subject_guid.build()

    response = client.get('/topic/', { 'guid': s_g.guid })
    response = json.loads(response.content.decode('utf-8'))

    assert response['status_code'] == 200
    assert s_g.name == response['subject']

def test_fetch_no_topics(client, subject_guid):

    response = client.get('/topic/', { 'guid': '0000-5-0000' })
    response = json.loads(response.content.decode('utf-8'))

    assert response['status_code'] == 404
