import json


def test_fetch_subjects_from_related_terms(client, metro_subject):
    subject = metro_subject.build()

    dummy_terms = [subject.name, 'some other subject']

    response = client.get('/subjects/', {'related_terms[]': [subject.name, 'some other subject']})
    response = json.loads(response.content.decode('utf-8'))

    assert response['status_code'] == 200
    assert response['related_terms'] == dummy_terms
    assert response['subjects'] == [subject.name]
