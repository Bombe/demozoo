from django import forms
from django.utils.safestring import mark_safe
from demoscene.models import Nick, NickVariant, Releaser
import datetime

# A variant of RadioFieldRenderer which accepts 4-tuples as choices, using the third element
# as a classname for the <li> and fourth element as a data-name attribute
class RadioFieldWithClassnameRenderer(forms.widgets.RadioFieldRenderer):
	def render(self):
		from django.utils.encoding import force_unicode
		list_items = []
		for i, choice in enumerate(self.choices):
			widget = forms.widgets.RadioInput(self.name, self.value, self.attrs.copy(), choice, i);
			list_items.append(
				u'<li class="%s" data-name="%s">%s</li>' % (choice[2], choice[3], force_unicode(widget))
			)
		return mark_safe(u'<ul>\n%s\n</ul>' % u'\n'.join(list_items))

class MatchedNickWidget(forms.Widget):
	def __init__(self, search_term, attrs = None,
		sceners_only = False, groups_only = False,
		group_names = [], member_names = []):
		self.search_term = search_term
		
		choices = []
		self.nick_variants = NickVariant.autocompletion_search(
			search_term, exact = True,
			sceners_only = sceners_only, groups_only = groups_only,
			groups = group_names, members = member_names)
		for nv in self.nick_variants:
			icon = 'group' if nv.nick.releaser.is_group else 'scener'
			if nv.nick.name == nv.name:
				choices.append((nv.nick_id, nv.nick.name_with_affiliations(), icon, nv.nick.name))
			else:
				label = "%s (%s)" % (nv.nick.name_with_affiliations(), nv.name)
				choices.append((nv.nick_id, label, icon, nv.nick.name))
		
		# see if there's a unique top choice in self.nick_variants;
		# if so, store that in self.top_choice for possible use later
		# if we render this widget with no initial value specified
		if self.nick_variants.count() == 0:
			self.top_choice = None
		elif self.nick_variants.count() == 1:
			self.top_choice = self.nick_variants[0]
		elif self.nick_variants[0].score > self.nick_variants[1].score:
			self.top_choice = self.nick_variants[0]
		else:
			self.top_choice = None
		
		if not groups_only:
			choices.append( ('newscener', "Add a new scener named '%s'" % search_term, "add_scener", search_term) )
		if not sceners_only:
			choices.append( ('newgroup', "Add a new group named '%s'" % search_term, "add_group", search_term) )
		
		self.select_widget = forms.RadioSelect(renderer = RadioFieldWithClassnameRenderer,
			choices = choices, attrs = attrs)
		self.name_widget = forms.HiddenInput()
		
		super(MatchedNickWidget, self).__init__(attrs = attrs)
	
	def value_from_datadict(self, data, files, name):
		nick_id = self.select_widget.value_from_datadict(data, files, name + '_id')
		nick_name = self.name_widget.value_from_datadict(data, files, name + '_name')
		if nick_id:
			if nick_id == 'newscener':
				return Nick(name = nick_name, releaser__is_group = False)
			elif nick_id == 'newgroup':
				return Nick(name = nick_name, releaser__is_group = True)
			else:
				return Nick.objects.get(id = nick_id)
		else:
			return None
	
	def id_for_label(self, id_):
		if id_:
			id_ += '_id'
		return id_
	id_for_label = classmethod(id_for_label)
	
	def render(self, name, value, attrs=None):
		selected_id = (value and value.id) or (self.top_choice and self.top_choice.nick_id)
		output = [
			self.select_widget.render(
				name + '_id',
				selected_id,
				attrs = attrs),
			self.name_widget.render(name + '_name', self.search_term, attrs = attrs)
		]
		return mark_safe(u'<div class="nick_match">' + u''.join(output) + u'</div>')

class MatchedNickField(forms.Field):
	def __init__(self, search_term, *args, **kwargs):
		
		matched_nick_widget_opts = {
			'sceners_only': kwargs.pop('sceners_only', False),
			'groups_only': kwargs.pop('groups_only', False),
			'group_names': kwargs.pop('group_names', []),
			'member_names': kwargs.pop('member_names', [])
		}
		self.widget = MatchedNickWidget(search_term, **matched_nick_widget_opts)
		
		self.search_term = search_term
		
		nick_variants = self.widget.nick_variants
		if nick_variants.count() == 0:
			self.best_match = None
		elif nick_variants.count() == 1:
			self.best_match = nick_variants[0].nick
		elif nick_variants[0].score > nick_variants[1].score:
			self.best_match = nick_variants[0].nick
		else:
			self.best_match = None
		
		super(MatchedNickField, self).__init__(*args, **kwargs)
	
	def clean(self, value):
		if not value:
			value = self.best_match
		elif isinstance(value, Nick):
			# check that it's a valid selection given the available choices
			if value.id: # nick is an existing database entry
				if value not in [nv.nick for nv in self.widget.nick_variants]: # invalid...
					value = self.best_match # ...so start a fresh match
			else:
				if value.name.lower() != self.search_term.lower(): # invalid...
					value = self.best_match # ...so start a fresh match
		
		if isinstance(value, Nick) or value == None:
			return super(MatchedNickField, self).clean(value)
		else:
			raise Exception("Don't know how to clean %s" % repr(value))
