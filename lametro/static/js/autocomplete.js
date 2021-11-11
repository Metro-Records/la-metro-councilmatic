var SmartLogic = {
  query: {},
  baseUrl: 'https://cloud.smartlogic.com/svc/0dcee7c7-1667-4164-81e5-c16e46f2f74c/ses/CombinedModel/concepts/',
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
    var stop = query.stop_cm_after_stage ? query.stop_cm_after_stage : '3';
    var maxResults = query.maxResultCount ? query.maxResultCount : '10';

    return '/subjects/?term=' + query.term
        + '&stop_cm_after_stage=' + stop
        + '&maxResultCount=' + maxResults
        + '&FILTER=AT=System:%20Legistar';
  },
  transformResponse: function (data, params) {
    SmartLogic.query = params;

    var results = $.map(data.subjects, function(result) {
        return {text: result.display_name, id: result.name}
    });

    // Only show the suggested group if there are suggestions
    var groupedResults = results.length > 0
      ? [{
        'text': 'Suggested query terms',
        'children': results
      }]
      : [];

    return {
      'results': groupedResults,
      'pagination': {'more': false}
    };
  },
  highlightResult: function (result) {
    // Return the first result with a set prefix, no highlight
    if ( result.newTag === true ) {
      return $('<span></span>')
        .append('<strong>What you typed: </strong>' + result.text)
        .attr('data-name', result.id)
    };

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
    var currentQuery;

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
        },
        createTag: function (params) {
          var term = $.trim(params.term);

          if (term === '') {
            return null;
          }

          return {
            id: term,
            text: term,
            newTag: true
          }
        }
    }).on('select2:closing', function(e) {
        /* By default, Select2 clears input when the user clicks inside the
           search bar or the input loses focus. We want to retain that input.
           I adapted this solution from this comment:
           https://github.com/select2/select2/issues/3902#issuecomment-206658823 */

        // Grab the input value before closing the menu.
        currentQuery = $('.select2-search input').prop('value');
    }).on('select2:close', function(e) {
        // Once the menu has closed, add back the input value.
        $('.select2-search input').val(currentQuery).trigger('change');
    }).on('select2:open', function(e) {
        // When the menu reopens (or regains focus), initialize a search with
        // the input value.
        $('.select2-search input').trigger('input');
    }).on('select2:select', function(e) {
        // When a user selects a value, clear the existing input value. (This
        // basically preserves normal select behavior with the above measures
        // to preserve pending input between selections.)
        $('.select2-search input').val('').trigger('change');
    });

    function handleSubmit(e) {
        var terms = $('#search-bar')
          .select2('data')
          .map(function (el) {return el.id});

        // Grab the input text
        var pendingTerm = $('.select2-search input').prop('value');

        // If there's a pending term, add it to the query
        if ( pendingTerm !== '' ) {
          terms.push(pendingTerm);
        };

        var queryString = terms.join(' AND ');

        var corpusString = $(e.target).find('input[name="search-all"]')[0].checked
          ? 'search-all=on'
          : 'search-reports=on';

        var extraParams = [];

        $.each($(e.target).find('input[type="hidden"]'), function (_, el) {
          var param = $(el).attr('name') + '=' + $(el).attr('value');
          extraParams.push(param);
        });

        var searchUrl = '/search/?q=' + queryString + '&' + corpusString;

        if ( extraParams.length > 0 ) {
          extraParamString = extraParams.join('&');
          searchUrl = searchUrl + '&' + extraParamString;
        };

        window.location.href = searchUrl;
    };

    // Store handleSubmit in the global namespace so it can be referenced in
    // the reCAPTCHA callback
    window.handleSubmit = handleSubmit;

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

function showRelatedTerms (termArray) {
    if ( termArray.length === 0 ) {
        return;
    };

    var relatedTerms = [];

    // Execute all Ajax requests before proceeding:
    // https://stackoverflow.com/a/5627301/7142170
    $.when.apply(
        $, termArray.map(getRelatedTerms)
    ).then(function () {
        // arguments is a magic variable containing all arguments passed to
        // this function. This is helpful, because we have an indeterminate
        // number of Ajax requests to deal with.
        //
        // If there is only one request, then args is an array with three items:
        // the response, status, and Ajax object. If there is more than one,
        // then args is an array of these arrays.
        if ( termArray.length === 1 ) {
            var response = arguments[0];
            relatedTerms = parseRelatedTerms(response);
        } else {
            $.each(arguments, function (_, arg) {
                var response = arg[0];
                relatedTerms = relatedTerms.concat(parseRelatedTerms(response));
            });
        };

        $.when(
            getSubjectsFromTerms(relatedTerms)
        ).then(function (response) {
            renderRelatedTerms(response);
        });
    })
}

function getRelatedTerms (term) {
    console.log('Retrieving terms related to ' + term);

    var url = SmartLogic.buildServiceUrl({
        'term': term,
        'stop_cm_after_stage': 1,
        'maxResultCount': 5,
    });

    return $.ajax({
        url: url,
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': 'Bearer ' + window.localStorage.getItem('ses_token')
        }
    });
}

function parseRelatedTerms (response) {
    if ( response.total === '1' ) {
        // If there is only one term, then the supplied term exactly
        // matches a term in SES. Display associated terms, if any.
        return response.terms[0].term.associated.length
            ? response.terms[0].term.associated[0].fields.map(function (el) {
                return {'name': el.field.name, 'id': el.field.id}
            })
            : [];
    } else {
        // If there is more than one term, then the supplied term
        // does not exactly match a term in SES. Display all results
        // (limited to at most 5 by our query.)
        return response.terms.map(function (el) {
            return {'name': el.term.name, 'id': el.term.id}
        });
    };
}

function getSubjectsFromTerms (terms, objectAttr) {
    var objectAttr = objectAttr? objectAttr : 'id';
    var termNames = terms.map(function(el) {return el[objectAttr]});

    return $.ajax({
        url: '/subjects/',
        data: {guids: termNames}
    });
}

function renderRelatedTerms (response) {
    if ( response.status_code == 200 && response.subjects.length > 0 ) {
        $('#related-terms').removeClass('hidden');

        $.each(response.subjects, function (idx, subject) {
            var link = $('<a />').attr('href', '/search/?q=' + subject.name).text(subject.name);
            $('#related-terms').append(link).append('<br />');
        });
    };
}
