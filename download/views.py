from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from download.models import Download
import os, uuid
import cooperhewitt.api.client
import json

access_token = os.environ['CH_API_KEY']
hostname = os.environ['CH_API_HOST']

def index(request):
	context = {}
	return render(request, 'download/index.html', context)
	
def about(request):
	context = {}
	return render(request, 'download/about.html', context)

def search(request):	
	try:
		query = request.POST['query']
	except (KeyError, Download.DoesNotExist):
		return redirect('/')
	else:
		results = search_objects(query)
		objects = results['objects']
		context = {'objects':objects, 'query':query}
		return render(request, 'download/search.html', context)
	
def thanks(request):
	try:
		search_terms = request.POST['search_terms']
		object_ids = request.POST['object_ids']
	except (KeyError, Download.DoesNotExist):
		return redirect('/')
	else:
		event_id = uuid.uuid4()
		event_id = str(event_id)

		event = {
			'event_id': event_id,
			'action': 'download_tool',
			'email': request.user.email,
			'object_ids': object_ids,
			'search_terms': search_terms
		}
		
		events = json.dumps([event])
		
		# write the search to the db...
		e = Download(user=request.user, search_terms=search_terms)
		e.save()
		
		api = cooperhewitt.api.client.OAuth2(access_token, hostname=hostname)
		method = 'millerfox.eventserver.registerEvents'
		args = { 'events': events }
		
		rsp = api.call(method, **args)
	
		context = {}
		return render(request, 'download/thanks.html', context)	

def account(request):
	searches = Download.objects.filter(user=request.user)
	context = {'searches':searches}
	return render(request, 'download/account.html', context)

def login_page(request):
	context = {}
	
	if request.method == 'POST':
		username = request.POST['username']
		password = request.POST['password']
	
		user = authenticate(username=username, password=password)
	
		if user is not None:
			if user.is_active:
				login(request, user)
				return render(request, 'download/index.html', context)
		else:
			return render(request, 'download/login.html', context)
	
	return render(request, 'download/login.html', context)

def logout_page(request):
	context = {}
	logout(request)	
	
	return render(request, 'download/logout.html', context)

def search_objects(query):
	api = cooperhewitt.api.client.OAuth2(access_token, hostname=hostname)
	method = 'cooperhewitt.search.objects'
	args = { 'query': query, 'has_images': 'yes' }

	rsp = api.call(method, **args)
	
	return rsp
	
	