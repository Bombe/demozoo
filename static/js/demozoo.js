function htmlEncode(str) {
	return str.replace(/&/g,'&amp;').replace(/>/g,'&gt;').replace(/</g,'&lt;').replace(/"/g,'&quot;');
}
	
$(function() {
	$('ul.messages li').animate({'backgroundColor': 'white'}, 5000);
	
	$('.spawning_formset').each(function() {
		var formset = this;
		var totalFormsInput = $("input[type='hidden'][name$='TOTAL_FORMS']", this);
		var fieldPrefix = totalFormsInput.attr('name').replace(/TOTAL_FORMS$/, '');
		
		function deleteForm(li) {
			$('.delete input:checkbox', li).attr('checked', true);
			$('> *', li).fadeOut(); /* fading out the LI itself is borked on Webkit (as of 2010-06-01) */
		}
		
		$('> ul > li', this).each(function() {
			var li = this;
			var deleteButton = $('<a href="javascript:void(0);" class="delete_button" title="delete">delete</a>');
			deleteButton.click(function() {
				deleteForm(li);
			});
			$('.delete', li).hide().after(deleteButton);
		});
		var lastElement = $('> ul > li:last', this);
		var newFormTemplate = lastElement.clone();
		var newFormInitialIndex = totalFormsInput.val() - 1;
		
		if (totalFormsInput.val() > 1 || $(this).hasClass('initially_hidden')) {
			lastElement.remove();
			totalFormsInput.val(totalFormsInput.val() - 1);
		}
		
		var addButton = $('<a href="javascript:void(0);" class="add_button">add</a>');
		var addLi = $('<li></li>');
		addLi.append(addButton);
		addButton.click(function() {
			var newForm = newFormTemplate.clone();
			addLi.before(newForm);
			var newIndex = parseInt(totalFormsInput.val());
			totalFormsInput.val(newIndex + 1);
			$(":input[name^='" + fieldPrefix + "']", newForm).each(function() {
				this.name = this.name.replace(fieldPrefix + newFormInitialIndex, fieldPrefix + newIndex);
			})
			$(":input[id^='id_" + fieldPrefix + "']", newForm).each(function() {
				this.id = this.id.replace('id_' + fieldPrefix + newFormInitialIndex, 'id_' + fieldPrefix + newIndex);
			})
			$("label[for^='id_" + fieldPrefix + "']", newForm).each(function() {
				this.htmlFor = this.htmlFor.replace('id_' + fieldPrefix + newFormInitialIndex, 'id_' + fieldPrefix + newIndex);
			})
			$('a.delete_button', newForm).click(function() {
				deleteForm(newForm);
			});
			newForm.hide().slideDown('fast');
			$(":input", newForm).focus();
		})
		$('> ul', this).append(addLi);
	})
	
	function addAutocompleteRule(selector, url, idField, useNickId) {
		$(selector).autocomplete(url, {
			autoFill: true,
			formatItem: function(row) {return htmlEncode(decodeURIComponent(row[2]))},
			formatResult: function(row) {return decodeURIComponent(row[3])},
			selectFirst: true,
			matchSubset: false,
			matchCase: true,
			extraParams: {'new_option': true}
		}).result(function(evt, result) {
			$(idField).val(result[useNickId ? 1 : 0]);
		});
	}
	/* TODO: instead of hard-coding hidden field IDs, derive them from the text field ID (thus supporting prefixes -> multiple forms per page) */
	addAutocompleteRule('input.group_autocomplete', '/groups/autocomplete/', 'input#id_group_id');
	addAutocompleteRule('input.scener_autocomplete', '/sceners/autocomplete/', 'input#id_scener_id');
	addAutocompleteRule('input.nick_autocomplete', '/releasers/autocomplete/', 'input#id_nick_id', true);
	addAutocompleteRule('input.production_autocomplete', '/productions/autocomplete/', 'input#id_production_id');
	
	function parseAutocompleteResults(data) {
		var results = [];
		var resultLines = data.split(/\n/);
		for (var i = 0; i < resultLines.length; i++) {
			var resultFields = resultLines[i].split('|');
			if (resultFields.length > 1) {
				results.push({
					'id': resultFields[1], // use nick ID, not releaser ID
					'label': decodeURIComponent(resultFields[2]),
					'name': decodeURIComponent(resultFields[3]),
					'score': parseInt(resultFields[4]),
					'icon': resultFields[5]
				})
			}
		}
		return results;
	}
	
	var previousAuthorSuggestions = {}
	function getAuthorSuggestions(name, groups, callback) {
		if (previousAuthorSuggestions[name] && previousAuthorSuggestions[name][groups]) {
			callback(previousAuthorSuggestions[name][groups]);
		} else {
			$.get('/releasers/autocomplete/', {
				'q': name, 'group': groups, 'exact': 'true', 'new_option': 'true'
			}, function(data) {
				var results = parseAutocompleteResults(data);
				if (!previousAuthorSuggestions[name]) previousAuthorSuggestions[name] = {};
				previousAuthorSuggestions[name][groups] = results;
				callback(results);
			})
		}
	}
	
	var previousGroupSuggestions = {}
	function getGroupSuggestions(name, members, callback) {
		if (previousGroupSuggestions[name] && previousGroupSuggestions[name][members]) {
			callback(previousGroupSuggestions[name][members]);
		} else {
			$.get('/groups/autocomplete/', {
				'q': name, 'member': members, 'exact': 'true', 'new_option': 'true'
			}, function(data) {
				var results = parseAutocompleteResults(data);
				if (!previousGroupSuggestions[name]) previousGroupSuggestions[name] = {};
				previousGroupSuggestions[name][members] = results;
				callback(results);
			})
		}
	}
	
	function suggestionsHaveTopResult(results) {
		if (results.length == 0) return false;
		if (results[0].score < 0) return false;
		if (results.length == 1) return true;
		return (results[0].score > results[1].score);
	}
	
	function buildSuggestionLink(result, authorIdInput, authorNameInput, selectedResult, selectedResultInner) {
		var suggestionA = $('<a href="javascript:void(0)"></a>');
		suggestionA.text(result.label).addClass('icon_' + result.icon);
		suggestionA.click(function() {
			authorIdInput.val(result.id);
			authorNameInput.val(result.name);
			selectedResult.removeClass().addClass("selected_result icon_" + result.icon);
			selectedResultInner.text(result.name);
		})
		return suggestionA;
	}
	
	function buildAuthorMatchElement(author, results, container, basename, index) {
		var authorIdInput = $('<input type="hidden" />').attr('name', basename + '-' + index + '-nick_id');
		var authorNameInput = $('<input type="hidden" />').attr('name', basename + '-' + index + '-name');
		
		container.append(authorIdInput, authorNameInput);
		
		if (suggestionsHaveTopResult(results)) {
			var selectedResult = $('<a href="javascript:void(0)" class="selected_result"></a>');
			var selectedResultInner = $('<span></span>');
			selectedResult.append(selectedResultInner);
			selectedResult.addClass('icon_' + results[0].icon);
			selectedResultInner.text(results[0].label);
			authorIdInput.val(results[0].id);
			authorNameInput.val(results[0].name);
		} else {
			var selectedResult = $('<a href="javascript:void(0)" class="selected_result icon_error"></a>');
			var selectedResultInner = $('<span></span>');
			selectedResult.append(selectedResultInner);
			selectedResultInner.text(author);
			authorIdInput.val('error'); /* TODO: JS (and server-side?) validation for presence of these */
			authorNameInput.val('');
		}
		container.append(selectedResult);
		var suggestionsUl = $('<ul class="suggestions"></ul>');
		for (var i = 0; i < results.length; i++) {
			var suggestionLi = $('<li></li>');
			var suggestionA = buildSuggestionLink(results[i], authorIdInput, authorNameInput, selectedResult, selectedResultInner);
			suggestionLi.append(suggestionA);
			suggestionsUl.append(suggestionLi);
		}
		/* TODO: fake a selector bar that moves with up/down arrow keys, to make the list
		keyboard accessible */
		container.append(suggestionsUl);
		suggestionsUl.hide();
		selectedResult.click(function() {
			if (selectedResult.is('.active')) {
				selectedResult.blur();
			} else {
				selectedResult.focus();
			}
			return false;
		}).focus(function() {
			selectedResult.addClass('active');
			suggestionsUl.show();
		}).blur(function() {
			
			setTimeout(function() {
				selectedResult.removeClass('active');
				suggestionsUl.hide();
			}, 100);
		})
	}
	
	var lastByline;
	function parseByline(input, matchedNamesContainer) {
		var byline = $(input).val();
		if (byline == lastByline) return;
		lastByline = byline;
		/* try to split on the first '/' into authors and affiliations */
		var match = byline.match(/^(.+?)\/(.*)/)
		if (match) {
			/* split author / affiliation lists on standard separators: / + ^ , & */
			var rawAuthors = match[1].split(/[\/\+\^\,\&]/);
			var rawAffiliations = match[2].split(/[\/\+\^\,\&]/);
		} else {
			/* treat the entire thing as a list of authors */
			var rawAuthors = byline.split(/[\/\+\^\,\&]/);
			var rawAffiliations = [];
		}
		/* clean up list - strip leading/trailing whitespace and remove blank entries */
		var authors = [];
		var affiliations = [];
		for (var i = 0; i < rawAuthors.length; i++) {
			var author = rawAuthors[i].replace(/^\s+/, '').replace(/\s+$/, '')
			if (author != '') authors.push(author);
		}
		for (var i = 0; i < rawAffiliations.length; i++) {
			var affiliation = rawAffiliations[i].replace(/^\s+/, '').replace(/\s+$/, '')
			if (affiliation != '') affiliations.push(affiliation);
		}
		
		$(matchedNamesContainer).empty();
		var authorsTotalForms = $('<input type="hidden" name="authors-TOTAL_FORMS" />').val(authors.length);
		var affiliationsTotalForms = $('<input type="hidden" name="affiliations-TOTAL_FORMS" />').val(affiliations.length);
		
		$(matchedNamesContainer).append(
			authorsTotalForms,
			'<input type="hidden" name="authors-INITIAL_FORMS" value="0" />',
			'<input type="hidden" name="authors-MAX_NUM_FORMS" value="" />',
			affiliationsTotalForms,
			'<input type="hidden" name="affiliations-INITIAL_FORMS" value="0" />',
			'<input type="hidden" name="affiliations-MAX_NUM_FORMS" value="" />'
		);
		
		/* TODO: detect if focus is on one of the elements being deleted, and prevent it from
		sending the tab index into outer space */
		if (authors.length || affiliations.length) {
			var matchedAuthorsUl = $('<ul></ul>');
			var matchedGroupsUl = $('<ul></ul>');
			$(matchedNamesContainer).append(
				'Matched names:',
				matchedAuthorsUl,
				matchedGroupsUl)
			
			$.each(authors, function(i, author) {
				var authorLi = $('<li class="matched_name"></li>');
				matchedAuthorsUl.append(authorLi);
				getAuthorSuggestions(author, affiliations, function(results) {
					buildAuthorMatchElement(author, results, authorLi, 'authors', i);
				});
			});
			$.each(affiliations, function(i, affiliation) {
				var groupLi = $('<li class="matched_name"></li>');
				matchedGroupsUl.append(groupLi);
				getGroupSuggestions(affiliation, authors, function(results) {
					buildAuthorMatchElement(affiliation, results, groupLi, 'affiliations', i);
				});
			});
		}
	}
	$('input.byline_autocomplete').each(function() {
		var matchedNamesContainer = $('#' + this.id + '_matched_names');
		$(this).blur(function() {
			parseByline(this, matchedNamesContainer);
		});
	})
	
	$('input.date').each(function() {
		var opts = {dateFormat: 'd M yy'};
		$(this).datepicker(opts);
	});
})
