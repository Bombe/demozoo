from django.conf.urls.defaults import *

urlpatterns = patterns('maintenance.views',
	(r'^$', 'index', {}, 'maintenance_index'),
	(r'^prods_without_screenshots$', 'prods_without_screenshots', {}, 'maintenance_prods_without_screenshots'),
	(r'^prods_without_external_links$', 'prods_without_external_links', {}, 'maintenance_prods_without_external_links'),
	(r'^prods_without_release_date$', 'prods_without_release_date', {}, 'maintenance_prods_without_release_date'),
	(r'^prods_without_release_date_with_placement$', 'prods_without_release_date_with_placement', {}, 'maintenance_prods_without_release_date_with_placement'),
	(r'^prod_soundtracks_without_release_date$', 'prod_soundtracks_without_release_date', {}, 'maintenance_prod_soundtracks_without_release_date'),
	(r'^group_nicks_with_brackets$', 'group_nicks_with_brackets', {}, 'maintenance_group_nicks_with_brackets'),
	(r'^ambiguous_groups_with_no_differentiators$', 'ambiguous_groups_with_no_differentiators', {}, 'maintenance_ambiguous_groups_with_no_differentiators'),
	(r'^non_standard_credits$', 'non_standard_credits', {}, 'maintenance_non_standard_credits'),
	(r'^replace_credit_role$', 'replace_credit_role', {}, 'maintenance_replace_credit_role'),
	(r'^prods_with_release_date_outside_party$', 'prods_with_release_date_outside_party', {}, 'maintenance_prods_with_release_date_outside_party'),
	(r'^fix_release_dates$', 'fix_release_dates', {}, 'maintenance_fix_release_dates'),
	(r'^exclude$', 'exclude', {}, 'maintenance_exclude'),
	(r'^prods_with_same_named_credits$', 'prods_with_same_named_credits', {}, 'maintenance_prods_with_same_named_credits'),
	(r'^same_named_prods_by_same_releaser$', 'same_named_prods_by_same_releaser', {}, 'maintenance_same_named_prods_by_same_releaser'),
)
