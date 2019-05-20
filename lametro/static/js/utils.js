// Admin view: Helper functions for manually uploading event documents via a URL or PDF.
function full_text_doc_url_js(url, base_url) {
    encoded_url = encodeURIComponent(url)
    doc_url = base_url + '?filename=agenda&document_url=' + encoded_url

    return doc_url 
};

function previewPDF(input) {
    if (input.files && input.files[0]) {
        var reader = new FileReader();

        reader.onload = function (e) {
            // Show buttons and preview
            $('#pdf-form-message, #pdf-check-viewer-test, #pdf-form-cancel, #pdf-form-submit').removeClass('hidden');
            document.getElementById('pdf-check-viewer-test').src = e.target.result
        }

        reader.readAsDataURL(input.files[0]);
    }
};

var SmartLogic = {
    key: null,
    initialize: function(key) {
        SmartLogic.key = key;
    },
    generateToken: function() {
        $.ajax({
            type: 'POST',
            url: 'https://cloud.smartlogic.com/token',
            data: {
                'grant_type': 'apikey',
                'key': SmartLogic.key,
            }
        }).done(function (response) {
            window.localStorage.setItem('token', response.access_token);
        }).error(function (xhr, textStatus, errorThrown) {
            console.log('Could not generate SmartLogic token');
        });
    },
    hints: function(query) {
        if ( window.localStorage.token == undefined ) {
            SmartLogic.generateToken()
        };

        $.ajax({
            type: 'GET',
            // TO-DO: Figure out if this is the right URL
            url: 'https://cloud.smartlogic.com/svc/0ef5d755-1f43-4a7e-8b06-7591bed8d453/ses/CombinedModel/hints/' + query + '.json',
            beforeSend: function (xhr) {
                xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded; charset=UTF-8');
                xhr.setRequestHeader('Authorization', 'Bearer '+ window.localStorage.token);
            },
            statusCode: {
                403: function (xhr, textStatus, errorThrown) {
                    SmartLogic.generateToken();
                    $.ajax(this);
                }
            }
        }).done(function (response) {
            return response;
        }).error(function (xhr, textStatus, errorThrown) {
            console.log('Could not retrieve hints for term ' + query);
        });
    }
}
