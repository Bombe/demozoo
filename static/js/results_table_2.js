function Event() {
	var self = {};
	var listeners = [];
	
	self.bind = function(callback) {
		listeners.push(callback);
	}
	self.unbind = function(callback) {
		for (var i = listeners.length - 1; i >= 0; i--) {
			if (listeners[i] == callback) listeners.splice(i, 1);
		}
	}
	self.trigger = function() {
		var args = arguments;
		for (var i = 0; i < listeners.length; i++) {
			listeners[i].apply(null, args);
		};
	}
	
	return self;
}

function Property(initialValue) {
	var self = {};
	
	self._value = initialValue;
	
	self.change = Event();
	self.get = function() {
		return self._value;
	}
	self.set = function(newValue) {
		if (newValue === self._value) return;
		self._value = newValue;
		self.change.trigger(self._value);
	}
	
	return self;
}

function EditableGrid(elem) {
	var self = {};
	
	var $elem = $(elem);
	var gridElem = $elem.get(0);
	$elem.addClass('editable_grid');
	
	var cursorX = 0, cursorY = 0;
	var rows = [];
	var isFocused = false;
	
	function elementIsInGrid(childElem) {
		return $.contains(gridElem, childElem);
	}
	
	/* return the index of the GridRow object whose DOM element is, or contains, childElem,
		or null if childElement is not contained in a row of this grid
	*/
	function rowIndexForElement(childElem) {
		/* walk up childElem's parent elements until we find an immediate child of
			the grid element */
		var elemToTest = childElem;
		while (elemToTest.parentElement && elemToTest.parentElement != gridElem) {
			elemToTest = elemToTest.parentElement;
		}
		if (elemToTest.parentElement) {
			/* check each row in turn to see if its element is the one we've found */
			for (var i = 0; i < rows.length; i++) {
				if (rows[i].elem == elemToTest) return i;
			}
		}
	}
	/* return the coordinates of the grid cell whose DOM element is, or contains, childElem,
		or null if childElem is not contained in a cell of this grid
	*/
	function coordsForElement(childElem) {
		var y = rowIndexForElement(childElem);
		if (y != null) {
			var x = rows[y].cellIndexForElement(childElem);
			if (x != null) return [x,y];
		}
	}
	
	function keydown(event) {
		/* current cell, if any, gets first dibs on handling events */
		var cell = getCell(cursorX, cursorY);
		if (cell) {
			var result = cell.keydown(event);
			/* cell's keydown handler can return:
				- null to let grid handle the event
				- false to terminate event handling immediately
				- true to pass control to the browser's default handlers */
			if (result != null) return result;
		}
		
		switch (event.which) {
			case 9: /* tab */
				if (event.shiftKey) {
					if (cursorX > 0) {
						self.setCursor(cursorX - 1, cursorY);
						return false;
					} else {
						/* scan backwards to previous row with cells */
						for (var newY = cursorY - 1; newY >= 0; newY--) {
							var cellCount = rows[newY].getCellCount();
							if (cellCount) {
								self.setCursor(cellCount - 1, newY);
								return false;
							}
						}
						/* no previous cell; allow tab to escape the grid */
						blur();
						return;
					}
				} else {
					if (cursorX + 1 < rows[cursorY].getCellCount()) {
						self.setCursor(cursorX + 1, cursorY);
						return false;
					} else {
						/* scan forwards to next row with cells */
						for (var newY = cursorY + 1; newY < rows.length; newY++) {
							var cellCount = rows[newY].getCellCount();
							if (cellCount) {
								self.setCursor(0, newY);
								return false;
							}
						}
						/* no next cell; allow tab to escape the grid */
						blur();
						return;
					}
				}
			case 37: /* cursor left */
				setCursorIfInRange(cursorX - 1, cursorY);
				//resultsTable.focus();
				return false;
			case 38: /* cursor up */
				setCursorIfInRange(cursorX, cursorY - 1);
				//resultsTable.focus();
				return false;
			case 39: /* cursor right */
				setCursorIfInRange(cursorX + 1, cursorY);
				//resultsTable.focus();
				return false;
			case 40: /* cursor down */
				setCursorIfInRange(cursorX, cursorY + 1);
				//resultsTable.focus();
				return false;
		}
	}
	/*
	function keypress(event) {
	}
	*/
	
	if ($elem.attr('tabindex') == null) {
		$elem.attr('tabindex', 0);
	}
	self.focus = function() {
		$elem.focus();
	}
	$elem.focus(function() {
		if (!isFocused) {
			isFocused = true;
			$(this).addClass('focused');
			$(document).bind('keydown', keydown);
			// $(document).bind('keypress', keypress);
			
			/* It isn't guaranteed that the cell at cursor position has
				been given the 'cursor' class (e.g. upon initial load,
				when cell (0,0) is created *after* the cursor is already
				set to 0,0) so do that now */
			var cell = getCell(cursorX, cursorY);
			if (cell) cell.receiveCursor();
		}
	})
	function blur() {
		isFocused = false;
		$elem.removeClass('focused');
		/* TODO: also propagate blur event to the current GridRow */
		$(document).unbind('keydown', keydown);
		// $(document).unbind('keypress', keypress);
	}
	
	function setCursorIfInRange(x, y) {
		var row = rows[y];
		if (!row || !row.getCell(x)) return;
		self.setCursor(x,y);
	}
	
	/* set cursor to position x,y */
	self.setCursor = function(x, y) {
		var oldCell = getCell(cursorX, cursorY);
		if (oldCell) oldCell.loseCursor();
		
		cursorX = x; cursorY = y;
		getCell(cursorX, cursorY).receiveCursor();
		/* TODO: possibly scroll page if cursor not in view */
	}
	
	$(document).mousedown(function(event) {
		var coords = coordsForElement(event.target);
		if (coords) {
			if (coords[0] == cursorX && coords[1] == cursorY) {
				return; /* continue editing if cursor is already here */
			}
			$elem.focus();
			/* notify existing cell, if any, of losing focus */
			var cell = getCell(cursorX, cursorY);
			if (cell) cell.blur();
			self.setCursor(coords[0], coords[1]);
		}
	}).click(function(event) {
		if (elementIsInGrid(event.target)) {
			$elem.focus();
		} else {
			blur();
		}
	});
	
	var headerRowUl = $('<ul class="fields"></ul>')
	var headerRow = $('<li class="header_row"></li>').append(headerRowUl, '<div style="clear: both;"></div>');
	$elem.prepend(headerRow);
	
	self.onAddRow = Event() /* Fired when adding a row via the insert / add buttons.
		NOT fired when calling addRow from code */
	
	var insertButton = $('<input type="button" class="add" value="Add row" />');
	var insertButtonDiv = $('<div class="editable_grid_insert"></div>');
	insertButtonDiv.append(insertButton);
	$elem.after(insertButtonDiv);
	insertButton.click(function() {
		/* set timeout so that button acquires focus before we revert focus to the table */
		setTimeout(function() {
			var row = self.addRow(null, true);
			self.onAddRow.trigger(row);
		}, 10);
	})
	
	self.addHeader = function(title, className) {
		var li = $('<li></li>').attr('class', className).append(
			$('<div class="show"></div>').text(title)
		);
		headerRowUl.append(li);
	}
	
	self.addRow = function(index, animate) {
		if (index == null || index >= rows.length) {
			index = rows.length;
			var row = GridRow(index);
			$elem.append(row.elem);
			rows.push(row);
		} else {
			/* bump up all row indexes below this one */
			for (var i = index; i < rows.length; i++) {
				rows[i].index.set(i+1);
			}
			/* also bump up cursor position */
			if (cursorY >= index) cursorY++;
			
			var row = GridRow(index);
			$(row.elem).insertBefore(rows[index].elem);
			rows.splice(index, 0, row);
		}
		
		row.prependInsertLink(function() {
			var newRow = self.addRow(row.index.get(), true);
			self.onAddRow.trigger(newRow);
		})
		
		row.onDelete.bind(function() {
			var index = row.index.get();
			for (var i = index + 1; i < rows.length; i++) {
				rows[i].index.set(i-1);
			}
			rows.splice(index, 1);
			
			if (cursorY > index) {
				cursorY--;
			} else if (cursorY == index) {
				if (rows.length == 0) {
					/* cursorY remains at 0,0 even if there's no cell to highlight there */
				} else if (cursorY == rows.length) {
					self.setCursor(cursorX, cursorY - 1);
				} else {
					self.setCursor(cursorX, cursorY);
				}
			}
		})
		
		if (animate) {
			row.slideDown();
		}
		
		return row;
	}
	
	getRow = function(index) {
		return rows[index];
	}
	getCell = function(x,y) {
		var row = getRow(y);
		if (row) return row.getCell(x);
	}
	
	$elem.sortable({
		'axis': 'y',
		'distance': 1,
		'items': 'li.data_row',
		'cancel': ':input,option,.byline_match_container', /* TODO: make into a config option to pass to EditableGrid */
		'update': function(event, ui) {
			var rowElem = ui.item[0];
			var row, oldIndex;
			for (var i = 0; i < rows.length; i++) {
				if (rows[i].elem == rowElem) {
					oldIndex = i;
					row = rows[i];
					break;
				}
			}
			var newIndex = $elem.find('> li.data_row').index(rowElem);
			
			rows.splice(oldIndex, 1);
			rows.splice(newIndex, 0, row);
			if (oldIndex < newIndex) {
				/* moving down */
				for (var i = oldIndex; i < newIndex; i++) {
					rows[i].index.set(i);
				}
				rows[newIndex].index.set(newIndex);
				
				if (cursorY == oldIndex) {
					cursorY = newIndex;
				} else if (cursorY > oldIndex && cursorY <= newIndex) {
					cursorY--;
				}
				
			} else {
				/* moving up */
				for (var i = newIndex+1; i <= oldIndex; i++) {
					rows[i].index.set(i);
				}
				rows[newIndex].index.set(newIndex);
				
				if (cursorY == oldIndex) {
					cursorY = newIndex;
				} else if (cursorY >= newIndex && cursorY < oldIndex) {
					cursorY++;
				}
			}
			
		}
	});
	
	return self;
}

function GridRow(index) {
	var self = {};
	
	self.index = Property(index);
	
	var cells = [];
	
	var $elem = $('<li class="data_row"></li>');
	self.elem = $elem.get(0);
	var fieldsUl = $('<ul class="fields"></ul>');
	var fieldsUlElem = fieldsUl.get(0);
	var deleteLink = $('<a href="javascript:void(0)" tabindex="-1" class="delete" title="Delete this row">Delete</a>');
	$elem.append(fieldsUl, deleteLink, '<div style="clear: both;"></div>');
	
	self.addCell = function(cell) {
		cells.push(cell);
		fieldsUl.append(cell.elem);
	}
	self.getCell = function(index) {
		return cells[index];
	}
	self.getCellCount = function() {
		return cells.length;
	}
	
	/* return the index of the GridCell object whose DOM element is, or contains, childElem,
		or null if childElement is not contained in a cell of this row
	*/
	self.cellIndexForElement = function(childElem) {
		/* walk up childElem's parent elements until we find an immediate child of
			the fieldsUlElem element */
		var elemToTest = childElem;
		while (elemToTest.parentElement && elemToTest.parentElement != fieldsUlElem) {
			elemToTest = elemToTest.parentElement;
		}
		if (elemToTest.parentElement) {
			/* check each cell in turn to see if its element is the one we've found */
			for (var i = 0; i < cells.length; i++) {
				if (cells[i].elem == elemToTest) return i;
			}
		}
	}
	
	self.slideDown = function() {
		$elem.css({'height': '0'}).animate({'height': '20px'}, {
			'duration': 'fast',
			'complete': function() {
				$elem.css({'height': 'auto'});
				//appendDeleteLink(row);
			}
		});
	}
	
	self.prependInsertLink = function(clickAction) {
		var insertLink = $('<a class="insert" tabindex="-1" title="Insert row here" href="javascript:void(0)">insert &rarr;</a>');
		$elem.prepend(insertLink);
		insertLink.click(clickAction);
	}
	
	self.onDelete = Event();
	deleteLink.click(function() {
		self.onDelete.trigger();
		/* TODO: what happens if we're in edit mode? */
		$elem.fadeOut('fast', function() {
			$elem.remove();
		})
	})
	
	return self;
}

function GridCell(opts) {
	if (!opts) opts = {};
	var self = {};
	
	var $elem = $('<li></li>')
	self.elem = $elem.get(0);
	if (opts['class']) $elem.addClass(opts['class']);
	
	self.value = Property(opts.value);
	
	var showElem = $('<div class="show"></div>')
	showElem.text(opts.value);
	$elem.append(showElem);
	
	var input = $('<input type="text" />');
	input.val(opts.value);
	var editElem = $('<div class="edit"></div>');
	editElem.append(input);
	$elem.append(editElem);
	editElem.hide();
	
	self.value.change.bind(function(newValue) {
		showElem.text(newValue);
		input.val(newValue);
	})
	
	self.receiveCursor = function() {
		$elem.addClass('cursor');
	}
	self.loseCursor = function() {
		$elem.removeClass('cursor');
	}
	
	/* edit modes:
		null = not editing
		'capturedText' = do not select on focus; cursor keys move caret
		'uncapturedText' = select on focus; cursor keys move cell
	*/
	var editMode = null;
	function finishEdit() {
		self.value.set(input.val());
		editElem.hide();
		showElem.show();
		editMode = null;
	}
	function startEdit(newMode) {
		showElem.hide();
		editElem.show();
		input.focus();
		editMode = newMode;
	}
	
	self.keydown = function(event) {
		switch (editMode) {
			case null:
				switch (event.which) {
					case 13:
						startEdit('capturedText');
						return false;
				}
				break;
			case 'capturedText':
				switch(event.which) {
					case 13: /* enter */
						finishEdit();
						return false;
					case 37: /* cursors */
					case 38:
					case 39:
					case 40:
						return true; /* override grid event handler, defer to browser's own */
				}
				break;
		}
	}
	self.blur = function() {
		if (editMode) finishEdit();
	}
	
	return self;
}

function ResultsTable(elem, opts) {
	var grid = EditableGrid(elem);
	grid.addHeader('Placing', 'placing_field');
	grid.addHeader('Title', 'title_field');
	grid.addHeader('By', 'by_field');
	grid.addHeader('Platform', 'platform_field');
	grid.addHeader('Type', 'type_field');
	grid.addHeader('Score', 'score_field');
	
	if (opts.competitionPlacings.length) {
		for (var i = 0; i < opts.competitionPlacings.length; i++) {
			var row = grid.addRow();
			var competitionPlacing = CompetitionPlacing(opts.competitionPlacings[i], row);
		}
	} else {
		/* add an initial empty row */
		var row = grid.addRow();
		var competitionPlacing = CompetitionPlacing(null, row);
	}
	
	grid.onAddRow.bind(function(row) {
		var competitionPlacing = CompetitionPlacing(null, row);
		grid.setCursor(1, row.index.get());
		grid.focus();
	})
}

function CompetitionPlacing(data, row) {
	if (!data) data = {};
	if (!data.production) data.production = {};
	if (!data.production.byline) data.production.byline = {};
	
	var self = {};
	self.row = row;
	
	var cellOrder = ['placing', 'title', 'by', 'platform', 'type', 'score'];
	var cells = {
		'placing': GridCell({'class': 'placing_field', 'value': data.ranking}),
		'title': GridCell({'class': 'title_field', 'value': data.production.title}),
		'by': GridCell({'class': 'by_field', 'value': data.production.byline.search_term}),
		'platform': GridCell({'class': 'platform_field'}),
		'type': GridCell({'class': 'type_field'}),
		'score': GridCell({'class': 'score_field', 'value': data.score})
	}
	for (var i = 0; i < cellOrder.length; i++) {
		self.row.addCell(cells[cellOrder[i]]);
	}
	
	return self;
}
