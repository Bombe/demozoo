from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

def render(request, template, context={}, **kwargs):
	return render_to_response(template, context, context_instance=RequestContext(request), **kwargs)

# TODO: see if we can (largely) replace this with get_absolute_url
def redirect(*args, **kwargs):
	return HttpResponseRedirect(reverse(*args, **kwargs))
