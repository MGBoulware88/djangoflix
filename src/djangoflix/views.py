from django.shortcuts import render
from django.views import generic
from django.http import HttpResponse, HttpResponseRedirect


def index(request):
    return HttpResponse("Hello, World!")


def home(request):
    return HttpResponse("Hello, Home!")


def browse(request):
    return HttpResponse("Hello, browse!")


def movies(request):
    return HttpResponse("Hello, movies!")


def tv(request):
    return HttpResponse("Hello, tv!")


def search(request):
    return HttpResponse("Hello, search!")
