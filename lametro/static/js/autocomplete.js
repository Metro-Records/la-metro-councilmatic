var SmartLogic = {
  query: {},
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
    return 'https://cloud.smartlogic.com/svc/0dcee7c7-1667-4164-81e5-c16e46f2f74c/ses/CombinedModel/concepts/' + query.term + '.json?FILTER=AT=System:%20Legistar&stop_cm_after_stage=3&maxResultCount=10';
  },
  transformResponse: function (data, params) {
    SmartLogic.query = params;
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

        return {'text': d.term.name + nptLabel, 'id': d.term.name};
      })
      : [];

    return {
      'results': results,
      'pagination': {'more': false}
    };
  },
  highlightResult: function (result) {
    var term = SmartLogic.query.term.trim();

    var escapeRegex = function (string) {
      return string.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&');
    }

    var match = new RegExp('(' + escapeRegex(term) + ')', "ig");
    var highlightedResult = result.text.replace(match, '<strong class="match-group">$1</strong>');

    return $('<span></span>')
      .append(highlightedResult)
      .attr('data-name', result.id);
  }
};

function initAutocomplete (formElement, inputElement) {
    var $form = $(formElement);
    var $input = $(inputElement);

    SmartLogic.getToken();

    $input.select2({
        tags: true,
        ajax: {
            url: SmartLogic.buildServiceUrl,
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Authorization': 'Bearer ' + window.localStorage.getItem('ses_token')
            },
            processResults: SmartLogic.transformResponse
        },
        templateResult: function (state) {
          return state.loading
            ? state.text
            : SmartLogic.highlightResult(state);
        },
        containerCssClass: 'input-lg form-control form-lg autocomplete-search',
        minimumInputLength: 3,
        language: {
          inputTooShort: function (args) {
            return 'Enter 3 or more characters to view suggestions.'
          }
        }
    });

    $form.on('submit', function handleSubmit (e) {
        e.preventDefault();

        var terms = $('#search-bar')
          .select2('data')
          .map(function (el) {return el.id});

        var queryString = terms.join(' AND ');

        var corpusString = $(this).find('input[name="search-all"]')[0].checked
          ? 'search-all=on'
          : 'search-reports=on';

        var extraParams = []

        $.each($(e.target).find('input[type="hidden"]'), function (_, el) {
          var param = $(el).attr('name') + '=' + $(el).attr('value');
          extraParams.push(param);
        });

        var searchUrl = '/search/?q=' + queryString + '&' + corpusString;

        if ( extraParams.length > 0 ) {
          extraParamString = extraParams.join('&');
          searchUrl = searchUrl + '&' + extraParamString;
        }

        window.location.href = searchUrl;
    });

    // Select option and execute search on enter
    // https://github.com/select2/select2/issues/1456#issuecomment-265457102
    var submitOnEnter = function (e) {
        if (e.keyCode === 13) {
          $form.submit();
        }
    };

    $input.on('select2:select', function (e) {
        $form.off('keyup', '.select2-selection', submitOnEnter);
    });

    $input.on('select2:opening', function (e) {
        $form.on('keyup', '.select2-selection', submitOnEnter);
    });
}
