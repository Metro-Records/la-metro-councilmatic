var SmartLogic = {
  getToken: function () {
    tokenNeeded = !window.localStorage.getItem('ses_token')

    msInDay = 86400000
    tokenExpired = (Date.now() - window.localStorage.getItem('ses_issued')) / msInDay >= 3

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
  buildServiceUrl: function (query) {
    return 'https://cloud.smartlogic.com/svc/0ef5d755-1f43-4a7e-8b06-7591bed8d453/ses/CombinedModel/concepts/' + query.term + '.json?FILTER=AT=System:%20Legistar&stop_cm_after_stage=3&maxResultCount=10';
  },
  transformResponse: function (data, params) {
    var results = data.terms
      ? $.map(data.terms, function(d) {
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
                if (el.field.name.toLowerCase() == params.term.toLowerCase()) {
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

        return {'text': '<strong>' + d.term.name + nptLabel + '</strong>', 'id': d.term.id};
      })
      : [];

    return {
      'results': results,
      'pagination': {'more': false}
    };
  }
};
