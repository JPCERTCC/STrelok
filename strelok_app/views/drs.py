from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.db.models import Q

from ..models import *
from ..forms import *
import json

def viz_drs(request):
    user = None
    verified = False
    if request.user.is_authenticated():
        user = request.user
    if request.user.is_verified():
        verified = True
    c = {
        "user":user,
        "vefified":verified,
        "tsform":TypeSelectForm(),
    }
    return render(request, "drs_viz.html", c)

def data_drs(request):
    tsform = TypeSelectForm()
    nodes = []
    edges = []
    icon = True
    drs = None
    if request.method == "POST":
        tsform = TypeSelectForm(request.POST)
        if tsform.is_valid():
            types = tsform.cleaned_data["types"]
            rels = tsform.cleaned_data["relation"]
            icon = tsform.cleaned_data["icon"]
            drs = DefinedRelationship.objects.filter(
                Q(source__in=types)|Q(target__in=types),
            ).filter(
                type__in=rels
            )
    else:
        drs = DefinedRelationship.objects.all()
            
    for dr in drs:
        for sot in (dr.source, dr.target):
            node = {
                'id': sot.name,
                'label': sot.name,
                'group': sot.name,
                'font': {'strokeWidth': 2, 'strokeColor': 'white'},
            }
            if not node in nodes:
                nodes.append(node)
        edge = {
            'from': dr.source.name,
            'to': dr.target.name,
            'label': dr.type.name,
            'font': {'strokeWidth': 2, 'strokeColor': 'white'},
        }
        if not edge in edges:
            edges.append(edge)
    dataset = {
        'nodes': nodes,
        'edges': edges,
        'icon': icon,
    }
    return JsonResponse(dataset)
