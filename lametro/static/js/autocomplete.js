/* Attaches autocomplete to the input div specified by the id passed */
function autocompleteSearchBar(element) {
  $(element).autocomplete({
    serviceUrl: '/autocomplete/',
    paramName: 'query',
    transformResult: function(response) {
      var res = JSON.parse(response);
      console.log(response)
      if (res.status_code == 500 || res.termHints.length < 1) {
        return {
          suggestions: [{'value': 'No topics found', 'data': 'na'}]
        };
      } else {
        return {
          suggestions: $.map(res.termHints, function(d) {
              return {'value': d.name, 'data': d.id};
            }
          )
        };
      }
    },
    onSearchError: function(query, jqXHR, textStatus, errorThrown) {
      return textStatus + ' : ' + errorThrown;
    },
    onSelect: function(suggestion) {
      $.when(
        $.get('/topic/', { 'guid': suggestion.data }))
          .then(function(response) {
            console.log(response)
            if (response.status_code == 200) {
              var base = '/search/?selected_facets=topics_exact%3A';
              var url = base + response.subject_safe;
              window.location.href = url;
            }
          })
        }
    })
};
