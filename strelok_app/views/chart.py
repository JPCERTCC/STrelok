from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.db.models import Q

from ..models import *
from ..forms import *
from collections import OrderedDict
import json, hashlib

def actor_chart(request, cnt_by='sector'):
    sights = Sighting.objects.all()
    tgt = Identity.objects.all()
    #tgt = Identity.objects.filter(object_id__in=sights.values("where_sighted_refs"))
    rels = Relationship.objects.all()
    data = cnt_actor_from_tgt(tgt, rels, sights, drilldown=True)
    dataset = []
    for d in data:
        dd = cnt_tgt_by_prop(tgt=d["tgt"], cnt_by=cnt_by, drilldown=False)
        drilldown = {
            "name": "Target categories of " + d["name"],
            "data": dd,
        }
        da = {
            "name":d["name"],
            "y":d["y"],
            "drilldown":drilldown,
        }
        dataset.append(da)
    dataset = json.dumps(dataset,indent=2)
    return HttpResponse(dataset,  content_type="application/json")

def cnt_actor_from_tgt(tgt, rels, sights, drilldown=False):
    data = {}
    for ta in ThreatActor.objects.all():
        data[ta.name] = []
    unidentified = []
    for t in tgt:
        l = []
        s = sights.filter(
            where_sighted_refs__object_id=t.object_id
        )
        l += s.values_list("sighting_of_ref",flat=True)
        r = rels.filter(
            target_ref=t.object_id
        )
        l += r.values_list("source_ref",flat=True)
        if l:
            at = Relationship.objects.filter(
                source_ref__in=list(set(l)),
                relationship_type__name="attributed-to",
                target_ref__object_id__startswith="threat-actor",
            )
            l += at.values_list("target_ref",flat=True)
            ta = ThreatActor.objects.filter(object_id__in=list(set(l)))
            if ta:
                for a in ta:
                    data[a.name].append(t)
            else:
                unidentified.append(t)
    dd = []
    for k, v in data.items():
        if v:
            ai = {
                "name": k,
                "y": len(v),
            }
            if drilldown:
                ai["tgt"] = v
            dd.append(ai)
    dd = sorted(
        dd,
        key=lambda kv: kv["y"],
        reverse=True
    )
    if unidentified:
        ai = {
            "name":"Unidentified",
            "y":len(unidentified),
        }
        if drilldown:
            ai["tgt"] = unidentified
        dd.append(ai)
    return dd

def target_chart(request, cnt_by="sector"):
    data = cnt_tgt_by_prop(cnt_by=cnt_by)
    return HttpResponse(json.dumps(data, indent=2),  content_type="application/json")

def chart_view(request, id, cnt_by="sector"):
    soid = STIXObjectID.objects.get(object_id=id)
    obj = get_obj_from_id(soid)
    dataset = []
    if obj.object_type.name == "threat-actor":
        dataset = cnt_tgt_by_prop(cnt_by=cnt_by, actor_name=obj.name)
    dataset = json.dumps(dataset,indent=2)
    return HttpResponse(dataset,  content_type="application/json")

def cnt_tgt_by_prop(cnt_by="sector", actor_name=None, drilldown=True, tgt=None):
    dataset = []
    sights = Sighting.objects.filter(
        where_sighted_refs__object_id__object_id__startswith="identity--",
        #sighting_of_ref__object_id__startswith="threat-actor--",
    )
    rels = Relationship.objects.filter(
        #source_ref__object_id__startswith='threat-actor--',
        relationship_type__name='targets',
        target_ref__object_id__startswith='identity--',
    )
    if actor_name:
        a = ThreatActor.objects.filter(name=actor_name)
        if a.count() == 1:
            oid = list(a.values_list("object_id", flat=True))
            at = Relationship.objects.filter(
                relationship_type__name="attributed-to",
                target_ref__in=oid,
            )
            oid += list(at.values_list("source_ref",flat=True))    
            sights = sights.filter(sighting_of_ref__in=oid)
            rels = rels.filter(source_ref__in=oid)
    if not tgt:
        tgt = Identity.objects.filter(
            Q(object_id__in=sights.values_list("where_sighted_refs",flat=True))|\
            Q(object_id__in=rels.values_list("target_ref",flat=True)),
        )
    prop = {}
    noprop = {"name":"N/A", "y":[]}
    if tgt:
        for t in tgt:
            category = None
            if cnt_by == "sector":
                category = t.sectors.all()
            elif cnt_by in ["label", "lalias"]:
                category = t.labels.all()
            if category:
                for c in category:
                    value = c.value
                    if cnt_by == "lalias" and c.alias:
                        value = c.alias
                    if not value in prop:
                        prop[value] = [t]
                    else:
                        prop[value].append(t)
            else:
                noprop["y"].append(t)
    for k,v in prop.items():
        item = {"name":k,"y":len(v)}
        if drilldown:
            item["drilldown"] = {"data": []}
            dd = cnt_actor_from_tgt(v, rels, sights, drilldown=False)
            item["drilldown"] = {
                "name": "Threat actor targets " + k,
                "data": dd,
            }
        if not item in dataset:
            dataset.append(item)
    dataset = sorted(
            dataset,
            key=lambda kv: kv["y"],
            reverse=True
    )
    if len(noprop["y"]) > 0:
        if drilldown:
            dd = cnt_actor_from_tgt(noprop["y"], rels, sights, drilldown=False)
            noprop["drilldown"] = {
                "name": "Threat actor targets " + noprop["name"],
                "data": dd,
            }
        noprop["y"] = len(noprop["y"])
        dataset.append(noprop)
    return dataset

def kill_chain_view(request):
    tas = []
    type = STIXObjectType.objects.filter(
        name__in=[
            "attack-pattern",
            "indicator",
            "malware",
            "tool",
        ]
    )
    zoom = 3
    form = None
    if request.method == "POST":
        if "refresh" in request.POST:
            form = MatrixForm(request.POST)
            if form.is_valid():
                tas = form.cleaned_data["threat_actor"]
                type = form.cleaned_data["type"]
                zoom = form.cleaned_data["zoom"]
    if not form:
            form = MatrixForm()
            form.fields["type"].initial = type.values_list("id",flat=True)
    objs = STIXObject.objects.filter(
        object_type__in=type
    )
    killchain = KillChainPhase.objects.all()
    data =[] 
    for obj in objs:
        o = get_obj_from_id(obj.object_id)
        if o.kill_chain_phases:
            #print(o)
            for kcp in o.kill_chain_phases.all():
                k = {
                    "id": str(kcp.id),
                    "name": kcp.phase_name,
                    "sortIndex": kcp.id,
                }
                #print(k)
                if not k in data:
                    data.append(k)
                p = {
                    "id":o.object_id.object_id,
                    "name": o.name,
                    "parent": str(kcp.id),
                    #"value": 1
                }
                #print(p)
                if not p in data:
                    data.append(p)
                #print(rels)
                for ta in tas:
                    rels = Relationship.objects.filter(
                        #source_ref__object_id__startswith="threat-actor",
                        source_ref=ta.object_id,
                        target_ref__object_id=o.object_id.object_id
                    )
                    #ta = get_obj_from_id(s)
                    a = {
                        "id": ta.object_id.object_id,
                        "name": ta.name,
                        "parent": str(o.object_id.object_id),
                        "value": 1,
                        "sortIndex": ta.id,
                    }
                    if rels:
                        a["color"] = "#" + str(hashlib.md5(ta.object_id.object_id.encode("utf8")).hexdigest()[0:6])
                    else:
                        a["color"] = "darkgray"
                        a["name"] = " "
                    if not a in data:
                        data.append(a)
    c = {
        "form":form,
        "zoom":int(zoom),
        "data":data,
    }
    return render(request, 'matrix_viz.html', c)

def ttp_view(request, id=None):
    mode = "threat-actor"
    actor = []
    campaign = []
    sot = [
        "attack-pattern",
        #"indicator",
        "malware",
        "tool",
    ]
    type = STIXObjectType.objects.filter(name__in=sot)
    form = MatrixForm()
    if request.method == "POST":
        form = MatrixForm(request.POST)
        if form.is_valid():
            actor = form.cleaned_data["threat_actor"]
            if actor:
                actor = actor.values_list("object_id",flat=True)
            type = form.cleaned_data["type"]
            campaign = form.cleaned_data["campaign"]
            if campaign:
                campaign = campaign.values_list("object_id",flat=True)
                mode = "campaign"
    obj = None
    if id:
        if id.split("--")[0] == "threat-actor":
            mode = "campaign"
            actor = STIXObjectID.objects.filter(object_id=id)
        elif id.split("--")[0] == "campaign":
            mode = "campaign"
            campaign = STIXObjectID.objects.filter(object_id=id)
    objs = STIXObject.objects.filter(object_type__in=type)
    killchain = KillChainPhase.objects.all()
    data = {}
    cdata = {}
    color = {}
    for k in killchain:
        data[k.phase_name] = {}
        cdata[k.phase_name] = {}
        color[k.phase_name] = hashlib.md5(k.phase_name.encode("utf8")).hexdigest()[0:6]
    clist = []
    for obj in objs:
        o = get_obj_from_id(obj.object_id)
        if o.kill_chain_phases:
            for kcp in o.kill_chain_phases.all():
                rel = Relationship.objects.filter(
                    source_ref__object_id__startswith="campaign",
                    relationship_type__name="uses",
                    target_ref=o.object_id,
                )
                if campaign:
                    rel = rel.filter(source_ref__in=campaign)
                c = rel.values_list("source_ref", flat=True).order_by().distinct()
                rel = Relationship.objects.filter(
                    source_ref__in=c,
                    relationship_type__name="attributed-to",
                    target_ref__object_id__startswith="threat-actor",
                    #target_ref__in=actor,
                )
                if actor:
                    rel = rel.filter(target_ref__in=actor)
                a = rel.values_list("target_ref", flat=True).order_by().distinct()
                if a:
                    #data[kcp.phase_name][o] = rel
                    data[kcp.phase_name][o] = a
                c = rel.values_list("source_ref", flat=True).order_by().distinct()
                if c:
                    cdata[kcp.phase_name][o] = c
                    clist += list(c)

    if mode == "campaign":
        actor = Campaign.objects.filter(object_id__in=clist)
        data = cdata
    else:
        actor = ThreatActor.objects.filter(object_id__in=actor)
    content = {
        "killchain": killchain,
        "actor":actor,
        "data":data,
        "color":color,
        "form":form,
    }
    return render(request, 'ttp_view.html', content)
