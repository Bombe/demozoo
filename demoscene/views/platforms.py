from demoscene.shortcuts import *
from demoscene.models import Platform

def index(request):
	platforms = Platform.objects.order_by('name')
	return render(request, 'platforms/index.html', {
		'platforms': platforms,
	})

def show(request, platform_id):
	platform = Platform.objects.get(id = platform_id)
	return render(request, 'platforms/show.html', {
		'platform': platform,
		'active_groups': platform.random_active_groups()[:],
		'productions': platform.productions.filter(release_date_date__isnull=False).order_by('-release_date_date')[0:30],
	})
