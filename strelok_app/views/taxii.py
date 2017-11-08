from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib import messages

import strelok_app.forms as myforms
from ..models import *
from ..forms import *
import json
import stix2

content_type = "application/vnd.oasis.stix+json; version=2.0"

def taxii_discovery(request):
    url = request.build_absolute_uri()
    default = url + "api/"
    d = {
        "title": "TAXII Server",
        #"description": "This TAXII Server contains a listing of...",
        #"contact": "string containing contact information",
        "default": default,
        "api_roots": [
            default,
        ]
    }
    j = json.dumps(d, indent=2)
    return HttpResponse(j,  content_type=content_type)

def taxii_get_objects(request, id):
    # /<api-root>/collections/<id>/objects/
    r = taxii_collection(request, id=id, get_objects=True)
    return r

def taxii_get_object(request, id, object_id):
    # /<api-root>/collections/<id>/objects/<object-id>/
    r = taxii_collection(request, id=id, object_id=object_id)
    return r

def col2dict(col):
    c = {
        "id":col.collection_id,
        "title":col.title,
        "description":col.description,
        "can_read":col.can_read,
        "can_write":col.can_write,
    }
    return c

def taxii_collection(
        request,
        id=None,
        get_objects=False,
        object_id=None,
    ):
    res = {}
    if not id:
        # /<api-root>/collections/
        res["collections"] = []
        for col in TaxiiCollection.objects.all():
            c = col2dict(col)
            if not c in res["collections"]:
                res["collections"].append(c)
        res = json.dumps(res, indent=2)
    elif id:
        col = TaxiiCollection.objects.get(collection_id=id)
        if not object_id:
            if not get_objects:
                # /<api-root>/collections/<id>/
                c = col2dict(col)
                res = json.dumps(c, indent=2)
            elif get_objects:
                # /<api-root>/collections/<id>/objects/
                objects = col.stix_objects.all()
                bundle = stix_bundle(objects.all())
                res = json.dumps(json.loads(str(bundle)), indent=2)
        elif object_id:
            # /<api-root>/collections/<id>/objects/<object-id>/
            obj = STIXObject.objects.get(
                object_id__object_id=object_id
            )
            bundle = stix_bundle([obj])
            res = json.dumps(json.loads(str(bundle)), indent=2)
    return HttpResponse(res,  content_type=content_type)

def taxii_error():
    error = {
        "title":"Error",
    }
    return error

def stix_bundle(objs, rel=True, sight=True):
    objects = ()
    ids = []
    for o in objs:
        if not o.object_id.id in ids: 
            ids.append(o.object_id.id)
        if o.object_type.name == "report":
            r = Report.objects.get(id=o.id)
            for i in r.object_refs.all().values_list("id",flat=True):
                if i in ids: 
                    ids.append(i)
        if rel:
            rels = Relationship.objects.filter(
                Q(source_ref=o.object_id)\
                |Q(target_ref=o.object_id)\
            )
            lists = list(rels.values_list("object_id", flat=True)) + \
                    list(rels.values_list("source_ref", flat=True)) + \
                    list(rels.values_list("target_ref", flat=True))
            for i in lists:
                if not i in ids:
                    ids.append(i)
        if sight:
            sights = Sighting.objects.filter(
                Q(where_sighted_refs=o.object_id)\
                |Q(sighting_of_ref=o.object_id)\
            )
            lists = list(sights.values_list("object_id", flat=True)) + \
                    list(sights.values_list("sighting_of_ref", flat=True))
            for i in lists:
                if not i in ids:
                    ids += i
    oids = STIXObjectID.objects.filter(
        id__in=ids
    )
    for oid in oids:
        obj = myforms.get_obj_from_id(oid)
        if obj.object_type.name == 'identity':
            i = stix2.Identity(
                id=obj.object_id.object_id,
                name=obj.name,
                identity_class=obj.identity_class,
                description=obj.description,
                #sectors=[str(s.value) for s in obj.sectors.all()],
                sectors=[str(l.value) for l in obj.labels.all()],
                created=obj.created,
                modified=obj.modified,
            )
            objects += (i,)
        elif obj.object_type.name == 'attack-pattern':
            a = stix2.AttackPattern(
                id=obj.object_id.object_id,
                name=obj.name,
                description=obj.description,
                created=obj.created,
                modified=obj.modified,
            )
            objects += (a,)
        elif obj.object_type.name == 'malware':
            m = stix2.Malware(
                id=obj.object_id.object_id,
                name=obj.name,
                description=obj.description,
                labels=[str(l.value) for l in obj.labels.all()],
                created=obj.created,
                modified=obj.modified,
            )
            objects += (m,)
        elif obj.object_type.name == 'indicator':
            i = stix2.Indicator(
                id=obj.object_id.object_id,
                name=obj.name,
                description=obj.description,
                labels=[str(l.value) for l in obj.labels.all()],
                pattern=[str(p.value) for p in obj.pattern.all()],
                created=obj.created,
                modified=obj.modified,
            )
            objects += (i,)
        elif obj.object_type.name == 'threat-actor':
            t = stix2.ThreatActor(
                id=obj.object_id.object_id,
                name=obj.name,
                description=obj.description,
                labels=[str(l.value) for l in obj.labels.all()],
                aliases=[str(a.name) for a in obj.aliases.all()],
                created=obj.created,
                modified=obj.modified,
            )
            objects += (t,)
        elif obj.object_type.name == 'relationship':
            r = stix2.Relationship(
                id=obj.object_id.object_id,
                relationship_type=obj.relationship_type.name,
                description=obj.description,
                source_ref=obj.source_ref.object_id,
                target_ref=obj.target_ref.object_id,
                created=obj.created,
                modified=obj.modified,
            )
            objects += (r,)
        elif obj.object_type.name == 'sighting':
            s = stix2.Sighting(
                id=obj.object_id.object_id,
                sighting_of_ref=obj.sighting_of_ref.object_id,
                where_sighted_refs=[str(w.object_id) for w in obj.where_sighted_refs.all()],
                first_seen=obj.first_seen,
                last_seen=obj.last_seen,
                created=obj.created,
                modified=obj.modified,
            )
            objects += (s,)
        elif obj.object_type.name == 'report':
            r = stix2.Report(
                id=obj.object_id.object_id,
                labels=[str(l.value) for l in obj.labels.all()],
                name=obj.name,
                description=obj.description,
                published=obj.published,
                object_refs=[str(r.object_id) for r in obj.object_refs.all()],
                created=obj.created,
                modified=obj.modified,
            )
            objects += (r,)
    bundle = stix2.Bundle(*objects)
    return bundle

