from django import forms
from django.utils.safestring import mark_safe
from demoscene.models import Production
from submit_button_field import SubmitButtonInput
from django.core.exceptions import ValidationError
import datetime
from byline_field import BylineField, BylineWidget

# A value encapsulating the state of the ProductionWidget.
# Used as the cleaned value of a ProductionField
# and the value ProductionWidget returns from value_from_datadict.

class ProductionSelection():
	def __init__(self, id = None, title = None, byline_lookup = None, types_to_set = []):
		self.id = id
		self.types_to_set = types_to_set
		if self.id:
			self.production = Production.objects.get(id = self.id)
			self.title = self.production.title
			self.byline = self.production.byline()
			self.byline_lookup = None
		else:
			self.production = None
			self.title = title
			self.byline_lookup = byline_lookup
	
	def commit(self):
		if not self.production:
			self.production = Production(
				title = self.title,
				updated_at = datetime.datetime.now(),
			)
			# Ugh. We really ought to come up with a nice way of setting supertype
			# in advance of setting types, rather than having to save a second time
			# once the types are in place...
			self.production.save()
			self.production.types = self.types_to_set
			self.production.save()
			self.byline.commit(self.production)
		return self.production
	
	def __str__(self):
		return "ProductionSelection: %s - %s" % (self.id, self.title)
	
	@staticmethod
	def from_value(value, types_to_set = []):
		# value can be:
		# a Production
		# None
		# an integer (will be used as an ID)
		# an existing ProductionSelection
		if not value:
			return ProductionSelection()
		elif isinstance(value, ProductionSelection):
			return ProductionSelection(id = value.id, title = value.title, byline_lookup = value.byline_lookup, types_to_set = types_to_set)
		elif isinstance(value, int):
			return ProductionSelection(id = value)
		elif isinstance(value, Production):
			return ProductionSelection(id = value.id)
		else:
			raise Exception("Don't know how to convert %s to a ProductionSelection!" % repr(value))
		
class ProductionWidget(forms.Widget):
	def __init__(self, attrs = None, types_to_set = [], supertype = None):
		self.id_widget = forms.HiddenInput()
		self.title_widget = forms.TextInput()
		self.byline_widget = BylineWidget()
		self.types_to_set = types_to_set
		self.supertype = supertype
		super(ProductionWidget, self).__init__(attrs = attrs)
	
	def value_from_datadict(self, data, files, name):
		id = self.id_widget.value_from_datadict(data, files, name + '_id')
		title = self.title_widget.value_from_datadict(data, files, name + '_title')
		byline_lookup = self.byline_widget.value_from_datadict(data, files, name + '_byline')
		if id or title:
			return ProductionSelection(
				id = id,
				title = title,
				byline_lookup = byline_lookup,
				types_to_set = self.types_to_set,
			)
		else:
			return None
	
	def render(self, name, value, attrs=None):
		production_selection = ProductionSelection.from_value(value, types_to_set = self.types_to_set)
		production_id = production_selection.id
		
		if production_id:
			byline_text = production_selection.production.byline().__unicode__()
			if byline_text:
				static_view = [
					# FIXME: HTMLencode
					"<b>%s</b> by %s" % (production_selection.production.title, byline_text)
				]
			else:
				static_view = [
					"<b>%s</b>" % production_selection.production.title
				]
		else:
			static_view = []
		
		title_attrs = self.build_attrs(attrs)
		title_attrs['class'] = 'title_field'
		if self.supertype:
			title_attrs['data-supertype'] = self.supertype
		byline_attrs = self.build_attrs(attrs)
		byline_attrs['id'] += '_byline'
		
		output = [
			'<div class="production_field">',
			'<div class="static_view">',
			'<div class="static_view_text">',
			u''.join(static_view),
			'</div>',
			'</div>',
			'<div class="form_view">',
			self.id_widget.render(name + '_id', production_id),
			self.title_widget.render(name + '_title', '', attrs = title_attrs),
			' <label for="%s">by</label> ' % self.byline_widget.id_for_label('id_' + name + '_byline'),
			self.byline_widget.render(name + '_byline', '', attrs = byline_attrs),
			'</div>',
			'</div>',
		]
		return mark_safe(u''.join(output))

class ProductionField(forms.Field):
	def __init__(self, *args, **kwargs):
		self.types_to_set = kwargs.pop('types_to_set', [])
		self.byline_field = BylineField(required = False)
		supertype = kwargs.pop('supertype', None)
		self.widget = ProductionWidget(types_to_set = self.types_to_set, supertype = supertype)
		
		super(ProductionField, self).__init__(*args, **kwargs)
	
	def clean(self, value):
		if not value:
			value = None
		else:
			value = ProductionSelection.from_value(value, types_to_set = self.types_to_set)
			value.byline = self.byline_field.clean(value.byline_lookup)
		
		return super(ProductionField, self).clean(value)
