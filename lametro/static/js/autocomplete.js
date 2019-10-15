var SmartLogic = {
  getToken: function() {
    tokenNeeded = !window.localStorage.getItem('ses_token')

    msInDay = 86400000
    tokenExpired = (Date.now() - window.localStorage.getItem('ses_issued')) / msInDay >= 14

    if ( (tokenNeeded || tokenExpired) ) {
      return $.get(
        '/ses-token/'
      ).then(function(response) {
          window.localStorage.setItem('ses_token', response.access_token);
          window.localStorage.setItem('ses_issued', Date.now());
      }).fail(function() {
          console.log('Failed to retrieve token');
      });
    };
  },
  buildServiceUrl: function(query) {
    return 'https://cloud.smartlogic.com/svc/0ef5d755-1f43-4a7e-8b06-7591bed8d453/ses/CombinedModel/concepts/' + query + '.json?FILTER=AT=System:%20Legistar&stop_cm_after_stage=3&maxResultCount=10';
  }
};

/* Attaches autocomplete to the input div specified by the id passed */
function autocompleteSearchBar(element) {
  $(element).autocomplete({
    serviceUrl: SmartLogic.buildServiceUrl,
    ajaxSettings: {
      beforeSend: function (xhr) {
        SmartLogic.getToken();
        xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
        xhr.setRequestHeader('Authorization', 'Bearer ' + window.localStorage.getItem('ses_token'));
      },
      data: {}
    },
    paramName: '',
    transformResult: function(response, term) {
      var res = JSON.parse(response);
      var noneFoundText = "No suggestions found. Press enter to perform a keyword search."
      if (res.status_code == 500 || res.terms.length < 1) {
        return {suggestions: [noneFoundText]};
      } else {
        return {
          suggestions: $.map(res.terms, function(d) {
            /* d.term.equivalence is an array of objects. Each object contains
            a "fields" array, also an array of objects, containing alternative
            names for the concept. Identify whether our search term matches one
            of these labels, so we can include it in the suggestion. */
            var nptLabel = '';

            if ( d.term.equivalence !== undefined && d.term.equivalence.length > 0 ) {
              var npt;

              $.each(d.term.equivalence, function(idx, el) {
                npt = el.fields.reduce(function(inp, el) {
                  if (inp) {
                    return inp
                  } else {
                    if (el.field.name.toLowerCase() == term.toLowerCase()) {
                      return el.field.name;
                    }
                  }
                }, undefined);

                if ( npt ) {
                  nptLabel = ' (' + npt + ')';
                  return false; // Equivalent to "break"
                }
              });
            };

            return {'value': d.term.name + nptLabel, 'data': d.term.id};
          })
        };
      }
    },
    onSelect: function(suggestion) {
      $.when(
        $.get('/topic/', { 'guid': suggestion.data })
      ).then(function(response) {
        if (response.status_code == 200) {
          var base = '/search/?q=';
          var url = base + response.subject_safe;
          window.location.href = url;
        };
      });
    },
    deferRequestBy: 100,
    triggerSelectOnValidInput: false,
  });
};
