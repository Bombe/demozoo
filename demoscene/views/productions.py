from demoscene.shortcuts import *
from demoscene.models import Production, Nick, Credit, DownloadLink, Screenshot, ProductionType
from demoscene.forms.production import *

from django.contrib.auth.decorators import login_required
import datetime

def productions_index(request):
	queryset = Production.objects.exclude(types__in = ProductionType.music_types()).\
		exclude(types__in = ProductionType.graphic_types())
	
	production_page = get_page(
		queryset.extra(
			select={'lower_title': 'lower(demoscene_production.title)'}
		).order_by('lower_title'),
		request.GET.get('page', '1') )
	
	return render(request, 'productions/index.html', {
		'production_page': production_page,
	})

def show(request, production_id, edit_mode = False):
	production = get_object_or_404(Production, id = production_id)
	if production.supertype != 'production':
		return HttpResponseRedirect(production.get_absolute_url())
	
	edit_mode = edit_mode or sticky_editing_active(request.user)
	
	return render(request, 'productions/show.html', {
		'production': production,
		'credits': production.credits.order_by('nick__name'),
		'screenshots': production.screenshots.order_by('id'),
		'download_links': production.ordered_download_links(),
		'soundtracks': [
			link.soundtrack for link in
			production.soundtrack_links.order_by('position').select_related('soundtrack')
		],
		'editing': edit_mode,
		'editing_as_admin': edit_mode and request.user.is_staff,
	})
	

@login_required
def edit(request, production_id):
	set_edit_mode_active(True, request.user)
	return show(request, production_id, edit_mode = True)

def edit_done(request, production_id):
	production = get_object_or_404(Production, id = production_id)
	set_edit_mode_active(False, request.user)
	return HttpResponseRedirect(production.get_absolute_url())
	
@login_required
def edit_core_details(request, production_id):
	production = get_object_or_404(Production, id = production_id)
	if request.method == 'POST':
		form = ProductionEditCoreDetailsForm(request.POST, instance = production)
		production_type_formset = ProductionTypeFormSet(request.POST, prefix = 'prod_type')
		production_platform_formset = ProductionPlatformFormSet(request.POST, prefix = 'prod_platform')
		
		if (
			form.is_valid() and production_type_formset.is_valid()
			and production_platform_formset.is_valid()
			):
			production.updated_at = datetime.datetime.now()
			form.save()
			production.types = production_type_formset.get_production_types()
			production.platforms = production_platform_formset.get_production_platforms()
			return HttpResponseRedirect(production.get_absolute_edit_url())
	else:
		form = ProductionEditCoreDetailsForm(instance = production)
		production_type_formset = ProductionTypeFormSet(prefix = 'prod_type',
			initial = [{'production_type': typ.id} for typ in production.types.all()])
		production_platform_formset = ProductionPlatformFormSet(prefix = 'prod_platform',
			initial = [{'platform': platform.id} for platform in production.platforms.all()])
	
	return ajaxable_render(request, 'productions/edit_core_details.html', {
		'production': production,
		'form': form,
		'production_type_formset': production_type_formset,
		'production_platform_formset': production_platform_formset,
	})

@login_required
def edit_notes(request, production_id):
	production = get_object_or_404(Production, id = production_id)
	if not request.user.is_staff:
		return HttpResponseRedirect(production.get_absolute_edit_url())
	return simple_ajax_form(request, 'production_edit_notes', production, ProductionEditNotesForm,
		title = 'Editing notes for %s:' % production.title,
		update_datestamp = True)

@login_required
def edit_external_links(request, production_id):
	production = get_object_or_404(Production, id = production_id)
	if not request.user.is_staff:
		return HttpResponseRedirect(production.get_absolute_edit_url())
	return simple_ajax_form(request, 'production_edit_external_links', production, ProductionEditExternalLinksForm,
		title = 'Editing external links for %s:' % production.title,
		update_datestamp = True)

@login_required
def add_download_link(request, production_id):
	production = get_object_or_404(Production, id = production_id)
	download_link = DownloadLink(production = production)
	if request.method == 'POST':
		form = ProductionDownloadLinkForm(request.POST, instance = download_link)
		if form.is_valid():
			production.updated_at = datetime.datetime.now()
			production.save()
			form.save()
			return HttpResponseRedirect(production.get_absolute_edit_url())
	else:
		form = ProductionDownloadLinkForm(instance = download_link)
	return ajaxable_render(request, 'shared/simple_form.html', {
		'form': form,
		'title': "Adding download link for %s:" % production.title,
		'action_url': reverse('production_add_download_link', args=[production.id]),
	})

@login_required
def edit_download_link(request, production_id, download_link_id):
	production = get_object_or_404(Production, id = production_id)
	download_link = get_object_or_404(DownloadLink, id = download_link_id, production = production)
	if request.method == 'POST':
		form = ProductionDownloadLinkForm(request.POST, instance = download_link)
		if form.is_valid():
			production.updated_at = datetime.datetime.now()
			production.save()
			form.save()
			return HttpResponseRedirect(production.get_absolute_edit_url())
	else:
		form = ProductionDownloadLinkForm(instance = download_link)
	return ajaxable_render(request, 'productions/edit_download_link.html', {
		'form': form,
		'production': production,
		'download_link': download_link,
	})

@login_required
def delete_download_link(request, production_id, download_link_id):
	production = get_object_or_404(Production, id = production_id)
	download_link = get_object_or_404(DownloadLink, id = download_link_id, production = production)
	if request.method == 'POST':
		if request.POST.get('yes'):
			download_link.delete()
			production.updated_at = datetime.datetime.now()
			production.save()
		return HttpResponseRedirect(production.get_absolute_edit_url())
	else:
		return simple_ajax_confirmation(request,
			reverse('production_delete_download_link', args = [production_id, download_link_id]),
			"Are you sure you want to delete this download link for %s?" % production.title )

@login_required
def screenshots(request, production_id):
	production = get_object_or_404(Production, id = production_id)
	return render(request, 'productions/screenshots.html', {
		'production': production,
		'screenshots': production.screenshots.order_by('id'),
	})

@login_required
def add_screenshot(request, production_id):
	production = get_object_or_404(Production, id = production_id)
	if request.method == 'POST':
		formset = ProductionAddScreenshotFormset(request.POST, request.FILES)
		if formset.is_valid():
			for form in formset.forms:
				screenshot = form.save(commit = False)
				if screenshot.original:
					screenshot.production = production
					screenshot.save()
			production.updated_at = datetime.datetime.now()
			production.save()
			return HttpResponseRedirect(production.get_absolute_edit_url())
	else:
		formset = ProductionAddScreenshotFormset()
	return ajaxable_render(request, 'productions/add_screenshot.html', {
		'production': production,
		'formset': formset,
	})

@login_required
def delete_screenshot(request, production_id, screenshot_id):
	production = get_object_or_404(Production, id = production_id)
	screenshot = get_object_or_404(Screenshot, id = screenshot_id, production = production)
	if request.method == 'POST':
		if request.POST.get('yes'):
			screenshot.delete()
			production.updated_at = datetime.datetime.now()
			production.save()
		return HttpResponseRedirect(reverse('production_screenshots', args=[production.id]))
	else:
		return simple_ajax_confirmation(request,
			reverse('production_delete_screenshot', args = [production_id, screenshot_id]),
			"Are you sure you want to delete this screenshot for %s?" % production.title )

@login_required
def create(request):
	if request.method == 'POST':
		production = Production(updated_at = datetime.datetime.now())
		form = CreateProductionForm(request.POST, instance = production)
		production_type_formset = ProductionTypeFormSet(request.POST, prefix = 'prod_type')
		production_platform_formset = ProductionPlatformFormSet(request.POST, prefix = 'prod_platform')
		download_link_formset = DownloadLinkFormSet(request.POST, instance = production)
		if (
			form.is_valid() and production_type_formset.is_valid()
			and production_platform_formset.is_valid() and download_link_formset.is_valid()
			):
			form.save()
			download_link_formset.save()
			production.types = production_type_formset.get_production_types()
			production.platforms = production_platform_formset.get_production_platforms()
			return HttpResponseRedirect(production.get_absolute_edit_url())
	else:
		form = CreateProductionForm()
		production_type_formset = ProductionTypeFormSet(prefix = 'prod_type')
		production_platform_formset = ProductionPlatformFormSet(prefix = 'prod_platform')
		download_link_formset = DownloadLinkFormSet()
	return ajaxable_render(request, 'productions/create.html', {
		'form': form,
		'production_type_formset': production_type_formset,
		'production_platform_formset': production_platform_formset,
		'download_link_formset': download_link_formset,
	})

@login_required
def add_credit(request, production_id):
	production = get_object_or_404(Production, id = production_id)
	credit = Credit(production = production)
	if request.method == 'POST':
		form = ProductionCreditForm(request.POST, instance = credit)
		if form.is_valid():
			form.save()
			production.updated_at = datetime.datetime.now()
			production.save()
			return HttpResponseRedirect(production.get_absolute_edit_url())
	else:
		form = ProductionCreditForm(instance = credit)
	return ajaxable_render(request, 'productions/add_credit.html', {
		'production': production,
		'form': form,
	})

@login_required
def edit_credit(request, production_id, credit_id):
	production = get_object_or_404(Production, id = production_id)
	credit = get_object_or_404(Credit, production = production, id = credit_id)
	if request.method == 'POST':
		form = ProductionCreditForm(request.POST, instance = credit)
		if form.is_valid():
			form.save()
			production.updated_at = datetime.datetime.now()
			production.save()
			return HttpResponseRedirect(production.get_absolute_edit_url())
	else:
		form = ProductionCreditForm(instance = credit)
	return ajaxable_render(request, 'productions/edit_credit.html', {
		'production': production,
		'credit': credit,
		'form': form,
	})

@login_required
def delete_credit(request, production_id, credit_id):
	production = get_object_or_404(Production, id = production_id)
	credit = get_object_or_404(Credit, production = production, id = credit_id)
	if request.method == 'POST':
		if request.POST.get('yes'):
			credit.delete()
			production.updated_at = datetime.datetime.now()
			production.save()
		return HttpResponseRedirect(production.get_absolute_edit_url())
	else:
		return simple_ajax_confirmation(request,
			reverse('production_delete_credit', args = [production_id, credit_id]),
			"Are you sure you want to delete %s's credit from %s?" % (credit.nick.name, production.title) )

@login_required
def edit_soundtracks(request, production_id):
	production = get_object_or_404(Production, id = production_id)
	if request.method == 'POST':
		formset = ProductionSoundtrackLinkFormset(request.POST, instance = production)
		if formset.is_valid():
			sorted_forms = sorted(formset.forms, key = lambda form: (form.cleaned_data['ORDER'] or 9999))
			for (i, form) in enumerate(sorted_forms):
				form.instance.position = i+1
				form.instance.save()
			formset.save()
			return HttpResponseRedirect(production.get_absolute_edit_url())
	else:
		formset = ProductionSoundtrackLinkFormset(instance = production)
	return ajaxable_render(request, 'productions/edit_soundtracks.html', {
		'production': production,
		'formset': formset,
	})

def autocomplete(request):
	query = request.GET.get('q')
	productions = Production.objects.filter(title__istartswith = query)[:10]
	return render(request, 'productions/autocomplete.txt', {
		'query': query,
		'productions': productions,
	}, mimetype = 'text/plain')
