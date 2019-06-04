var SmartLogic = {
  getToken: function(refresh=false) {
    console.log('getToken fired');
    if ( refresh || !window.localStorage.getItem('ses_token') ) {
      console.log('refresh ' + refresh);
      $.get('/ses-token/')
        .then(function(response) {
          window.localStorage.setItem('ses_token', response.access_token);
        });
    };
    return window.localStorage.getItem('ses_token');
  },
  buildServiceUrl: function(query) {
    return 'https://cloud.smartlogic.com/svc/0ef5d755-1f43-4a7e-8b06-7591bed8d453/ses/CombinedModel/hints/' + query + '.json';
  }
};

/* Attaches autocomplete to the input div specified by the id passed */
function autocompleteSearchBar(element) {
  $(element).autocomplete({
    serviceUrl: SmartLogic.buildServiceUrl,
    ajaxSettings: {
      beforeSend: function (xhr) {
        xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded; charset=UTF-8');
        xhr.setRequestHeader('Authorization', 'Bearer ' + window.localStorage.getItem('ses_token'));
      },
      statusCode: {
        403: function (xhr, textStatus, errorThrown) {
          console.log('status 403');
          SmartLogic.getToken(refresh=true);
          $.ajax(this);
        }
      },
      data: {}
    },
    paramName: '',
    transformResult: function(response) {
      var res = JSON.parse(response);
      if (res.status_code == 500 || res.termHints.length < 1) {
        return {
          suggestions: ['No topics found']
        };
      } else {
        return {
          suggestions: $.map(res.termHints, function(d) {
              /* If the search term is an acronym, displays that as a part of the suggestion */
              var nature = '';
              if (d.values[0]['nature'] == 'NPT') {
                nature = d.values[0]['value'];
                nature = ' (' + nature + ')';
              }
              return {'value': d.name + nature, 'data': d.id};
            }
          )
        };
      }
    },
    onSelect: function(suggestion) {
      $.when(
        $.get('/topic/', { 'guid': suggestion.data }))
          .then(function(response) {
            if (response.status_code == 200) {
              var base = '/search/?selected_facets=topics_exact%3A';
              var url = base + response.subject_safe;
              window.location.href = url;
            }
          })
        },
    onSearchError: function (query, jqXHR, textStatus, errorThrown) {
      console.log('error')
    }
  )
};
