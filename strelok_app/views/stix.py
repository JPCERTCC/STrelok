from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib import messages

from ..models import *
from ..forms import *
from .timeline import stix2timeline

import re, json, requests
import stix2

def stix2_json_masked(request):
    res = stix2_json(request, mask=True)
    return res

def stix2_json(request, id=None, mask=None):
    if not mask and request.user.is_authenticated():
        mask = False
    else:
        mask = True
    objs = []
    if not id:
        for i in STIXObjectID.objects.all():
            o = get_obj_from_id(i)
            if o:
                objs.append(get_obj_from_id(i))
    else:
        obj = STIXObject.objects.get(object_id__object_id=id)
        objs = get_related_obj(obj)
    bundle = stix_bundle(objs, mask=mask)
    j = json.dumps(json.loads(str(bundle)), indent=2)
    return HttpResponse(j,  content_type="application/json")

def stix2type_json(request, type):
    mask = None
    if not mask and request.user.is_authenticated():
        mask = False
    else:
        mask = True
    m = get_model_from_type(type)
    a = m.objects.all()
    bundle = stix_bundle(a, mask=mask)
    j = json.dumps(json.loads(str(bundle)), indent=2)
    return HttpResponse(j,  content_type="application/json")

def rel2db(rel, objs):
    src_id = rel["source_ref"]
    src = None
    if src_id in objs:
        src = objs[src_id]
    tgt_id = rel["target_ref"]
    tgt = None
    if tgt_id in objs:
        tgt = objs[tgt_id]
    type = None
    if "relationship_type" in rel:
        type = RelationshipType.objects.get(
            name=rel["relationship_type"]
        )
    dscr = None
    if "description" in rel:
        dscr = rel["description"]
    if src and tgt and type:
        r, cre = Relationship.objects.get_or_create(
            relationship_type=type,
            source_ref=src.object_id,
            target_ref=tgt.object_id,
            description=dscr,
        )
        return r
    return None

def sight2db(sight, objs):
    wsrs = []
    if "where_sighted_refs" in sight:
        for w in sight["where_sighted_refs"]:
            sdo = objs[w]
            wsrs.append(sdo)
    ods = []
    if "observed_data_refs" in sight:
        for o in sight["observed_data_refs"]:
            sdo = objs[o]
            ods.append(sdo)
    sor = None
    if "sighting_of_ref" in sight:
        sid = sight["sighting_of_ref"]
        if sid in objs:
            sor = objs[sid]
    first_seen = None
    if "first_seen" in sight:
        first_seen = sight["first_seen"]
    last_seen = None
    if "last_seen" in sight:
        last_seen = sight["last_seen"]
    if wsrs and sor and first_seen:
        s = Sighting.objects.filter(
            first_seen=first_seen,
            last_seen=last_seen,
            sighting_of_ref=sor.object_id,
            where_sighted_refs__in=wsrs,
        )
        if not s:
            s = Sighting.objects.create(
                first_seen=first_seen,
                last_seen=last_seen,
                sighting_of_ref=sor.object_id,
            )
        elif s.count() == 1:
            s = s[0]
        for od in ods:
            if od:
                s.observed_data_refs.add(od)
        for wsr in wsrs:
            s.where_sighted_refs.add(wsr)
        s.save()
        return s
    return None

def rep2db(rep, objs):
    r = None
    if "name" in rep:
        if rep["name"]:
            r, cre = Report.objects.get_or_create(name=rep["name"])
    if r:
        if "published" in rep:
            r.published = rep['published']
        if "description" in rep:
            r.description = rep['description']
        if "labels" in rep:
            labels = rep["labels"]
            for label in labels: 
                l = ReportLabel.objects.filter(value=label)
                if l.count() == 1:
                    r.labels.add(l[0])
        refs = []
        if "object_refs" in rep:
            for ref in rep["object_refs"]:
                sdo = objs[ref]
                if sdo:
                    refs.append(sdo.object_id)
        if refs:
            r.object_refs.add(*refs)
        r.save()
    return r

def _stix2property(so, obj):            
    if "description" in obj:
        so.description = obj["description"]
    if "kill_chain_phases" in obj:
        for kcp in obj["kill_chain_phases"]:
            k, cre = KillChainPhase.objects.get_or_create(
                kill_chain_name=kcp["kill_chain_name"],
                phase_name=kcp["phase_name"],
            )
            so.kill_chain_phases.add(k)
    if "first_seen" in obj:
        so.first_seen = obj["first_seen"]
    if "last_seen" in obj:
        so.last_seen = obj["last_seen"]
    if "confidence" in obj:
        so.confidence = obj["confidence"]
    return so

def stix2_db(obj):
    if "type" in obj:
        type = obj["type"]
        model = get_model_from_type(type)
        if type == 'threat-actor':
            t, cre = model.objects.get_or_create(name=obj["name"])
            if "description" in obj:
                t.description = obj["description"]
            if "aliases" in obj:
                aliases = obj["aliases"]
                for alias in aliases: 
                    a, cre = ThreatActorAlias.objects.get_or_create(name=alias)
                    t.aliases.add(a)
            if "labels" in obj:
                labels = obj["labels"]
                for label in labels: 
                    l, cre = ThreatActorLabel.objects.get_or_create(value=label)
                    t.labels.add(l)
            t.save()
            return t
        elif type == 'attack-pattern':
            a, cre = model.objects.get_or_create(name=obj["name"])
            a = _stix2property(a, obj)
            a.save()
            return a
        elif type == 'campaign':
            c, cre = model.objects.get_or_create(name=obj["name"])
            c = _stix2property(c, obj)
            if "aliases" in obj:
                aliases = obj["aliases"]
                for alias in aliases: 
                    a, cre = CampaignAlias.objects.get_or_create(name=alias)
                    c.aliases.add(a)
            c.save()
            return c
        elif type == 'course-of-action':
            c, cre = model.objects.get_or_create(name=obj["name"])
            c = _stix2property(c, obj)
            c.save()
            return c
        elif type == 'identity':
            i, cre = model.objects.get_or_create(name=obj["name"])
            if "description" in obj:
                i.description = obj["description"]
            if "identity_class" in obj:
                i.identity_class = obj["identity_class"]
            if "sectors" in obj:
                sectors = obj["sectors"]
                for sector in sectors: 
                    s, cre = IndustrySector.objects.get_or_create(value=sector)
                    i.sectors.add(s)
            if "labels" in obj:
                labels = obj["labels"]
                for label in labels: 
                    l, cre = IdentityLabel.objects.get_or_create(value=label)
                    i.labels.add(l)
            i.save()
            return i
        elif type == 'intrusion-set':
            c, cre = model.objects.get_or_create(name=obj["name"])
            c = _stix2property(c, obj)
            if "aliases" in obj:
                aliases = obj["aliases"]
                for alias in aliases: 
                    a, cre = IntrusionSetAlias.objects.get_or_create(name=alias)
                    c.aliases.add(a)
            c.save()
            return c
        elif type == 'malware':
            m, cre = model.objects.get_or_create(name=obj["name"])
            m = _stix2property(m, obj)
            if "labels" in obj:
                labels = obj["labels"]
                for label in labels: 
                    l, cre = MalwareLabel.objects.get_or_create(value=label)
                    m.labels.add(l)
            m.save()
            return m
        elif type == 'observed-data':
            if not "objects" in obj:
                return None
            o = model.objects.create(
                first_observed=obj["first_observed"],
                last_observed=obj["last_observed"],
                number_observed=obj["number_observed"],
            )
            from .observables import create_obs
            for n in obj["objects"]:
                d= obj["objects"][n]
                obs = None
                if d["type"] == "file":
                    obs = create_obs(d["type"], d["name"])
                else:
                    obs = create_obs(d["type"], d["value"])
                if obs:
                    o.observable_objects.add(obs)
            o.save()
            return o
        elif type == 'tool':
            t, cre = model.objects.get_or_create(name=obj["name"])
            t = _stix2property(t, obj)
            if "labels" in obj:
                labels = obj["labels"]
                for label in labels: 
                    l, cre = ToolLabel.objects.get_or_create(value=label)
                    t.labels.add(l)
            t.save()
            return t
        elif type == 'vulnerability':
            v, cre = model.objects.get_or_create(name=obj["name"])
            if "description" in obj:
                v.description = obj["description"]
            v.save()
            return v
        elif type == 'indicator':
            i, cre = model.objects.get_or_create(name=obj["name"])
            if "description" in obj:
                i.description = obj["description"]
            if "labels" in obj:
                labels = obj["labels"]
                for label in labels: 
                    l, cre = IndicatorLabel.objects.get_or_create(value=label)
                    i.labels.add(l)
            if "pattern" in obj:
                p = IndicatorPattern.objects.create(pattern=obj["pattern"])
                i.pattern = p
            if "valid_from" in obj:
                i.valid_from = obj["valid_from"]
            if "valid_until" in obj:
                i.valid_until = obj["valid_until"]
            i.save()
            return i

def stix2killchain(obj):
    kcps = []
    for k in obj.kill_chain_phases.all():
        kcp = stix2.KillChainPhase(
            kill_chain_name=k.kill_chain_name,
            phase_name=k.phase_name,
        )
        if not kcp in kcps:
            kcps.append(kcp)
    return kcps

def stix_bundle(objs, mask=True):
    objects = ()
    for obj in objs:
        oid = obj.object_id.object_id
        dscr = ""
        if not mask and hasattr(obj, "description"):
            dscr = obj.description
        if obj.object_type.name == 'attack-pattern':
            a = stix2.AttackPattern(
                id=oid,
                name=obj.name,
                description=dscr,
                created=obj.created,
                modified=obj.modified,
                kill_chain_phases=stix2killchain(obj),
            )
            objects += (a,)
        elif obj.object_type.name == 'campaign':
            c = stix2.Campaign(
                id=oid,
                name=obj.name,
                description=dscr,
                aliases=[str(a.name) for a in obj.aliases.all()],
                created=obj.created,
                modified=obj.modified,
                first_seen=obj.first_seen,
                last_seen=obj.last_seen,
            )
            objects += (c,)
        elif obj.object_type.name == 'course-of-action':
            c = stix2.CourseOfAction(
                id=oid,
                name=obj.name,
                description=dscr,
                created=obj.created,
                modified=obj.modified,
            )
            objects += (c,)
        elif obj.object_type.name == 'identity':
            name = obj.name
            if mask:
                name = oid
                label = obj.labels.all()
                if label.count() >=1:
                    name = str(obj.id)
                    if label[0].alias:
                        name += '-' + label[0].alias
                    else:
                        name += '-' + label[0].value
            i = stix2.Identity(
                id=oid,
                name=name,
                identity_class=obj.identity_class,
                description=dscr,
                sectors=[str(s.value) for s in obj.sectors.all()],
                labels=[str(l.value) for l in obj.labels.all()],
                created=obj.created,
                modified=obj.modified,
            )
            objects += (i,)
        elif obj.object_type.name == 'indicator':
            pattern = "[]"
            if not mask and obj.pattern:
                pattern = obj.pattern.pattern
            i = stix2.Indicator(
                id=oid,
                name=obj.name,
                description=dscr,
                labels=[str(l.value) for l in obj.labels.all()],
                pattern= pattern,
                created=obj.created,
                modified=obj.modified,
                valid_from=obj.valid_from,
                valid_until=obj.valid_until,
            )
            objects += (i,)
        elif obj.object_type.name == 'intrusion-set':
            i = stix2.IntrusionSet(
                id=oid,
                name=obj.name,
                description=dscr,
                aliases=[str(a.name) for a in obj.aliases.all()],
                created=obj.created,
                modified=obj.modified,
                first_seen=obj.first_seen,
                #last_seen=obj.last_seen,
            )
            objects += (i,)
        elif obj.object_type.name == 'malware':
            m = stix2.Malware(
                id=oid,
                name=obj.name,
                description=dscr,
                labels=[str(l.value) for l in obj.labels.all()],
                created=obj.created,
                modified=obj.modified,
                kill_chain_phases=stix2killchain(obj),
            )
            objects += (m,)
        elif obj.object_type.name == 'observed-data':
            obs = {}
            for o in obj.observable_objects.all():
                ob = None
                if o.type.name == "file":
                    f = FileObject.objects.get(id=o.id)
                    ob = stix2.File(name=f.name)
                elif o.type.name == "ipv4-addr":
                    i = IPv4AddressObject.objects.get(id=o.id)
                    ob = stix2.IPv4Address(value=i.value)
                elif o.type.name == "url":
                    u = URLObject.objects.get(id=o.id)
                    ob = stix2.URL(value=u.value)
                elif o.type.name == "domain-name":
                    dn = DomainNameObject.objects.get(id=o.id)
                    ob = stix2.DomainName(value=dn.value)
                if ob and not mask:
                    obs[str(o.id)] = json.loads(str(ob))
            od = stix2.ObservedData(
                id=oid,
                created=obj.created,
                modified=obj.modified,
                first_observed=obj.first_observed,
                last_observed=obj.last_observed,
                number_observed=obj.number_observed,
                objects = obs,
            )
            objects += (od,)
        elif obj.object_type.name == 'report':
            created_by = None
            if obj.created_by_ref:
                created_by=obj.created_by_ref.object_id
            r = stix2.Report(
                id=oid,
                labels=[str(l.value) for l in obj.labels.all()],
                name=obj.name,
                description=dscr,
                published=obj.published,
                object_refs=[str(r.object_id) for r in obj.object_refs.all()],
                created_by_ref=created_by,
                created=obj.created,
                modified=obj.modified,
            )
            objects += (r,)
        elif obj.object_type.name == 'threat-actor':
            t = stix2.ThreatActor(
                id=oid,
                name=obj.name,
                description=dscr,
                labels=[str(l.value) for l in obj.labels.all()],
                aliases=[str(a.name) for a in obj.aliases.all()],
                created=obj.created,
                modified=obj.modified,
            )
            objects += (t,)
        elif obj.object_type.name == 'tool':
            t = stix2.Tool(
                id=oid,
                name=obj.name,
                description=dscr,
                labels=[str(l.value) for l in obj.labels.all()],
                created=obj.created,
                modified=obj.modified,
                kill_chain_phases=stix2killchain(obj),
            )
            objects += (t,)
        elif obj.object_type.name == 'vulnerability':
            v = stix2.Vulnerability(
                id=oid,
                name=obj.name,
                description=dscr,
                created=obj.created,
                modified=obj.modified,
            )
            objects += (v,)
        elif obj.object_type.name == 'relationship':
            r = stix2.Relationship(
                id=oid,
                relationship_type=obj.relationship_type.name,
                description=dscr,
                source_ref=obj.source_ref.object_id,
                target_ref=obj.target_ref.object_id,
                created=obj.created,
                modified=obj.modified,
            )
            objects += (r,)
        elif obj.object_type.name == 'sighting':
            s = stix2.Sighting(
                id=oid,
                sighting_of_ref=obj.sighting_of_ref.object_id,
                where_sighted_refs=[str(w.object_id.object_id) for w in obj.where_sighted_refs.all()],
                observed_data_refs=[str(od.object_id.object_id) for od in obj.observed_data_refs.all()],
                first_seen=obj.first_seen,
                last_seen=obj.last_seen,
                created=obj.created,
                modified=obj.modified,
            )
            objects += (s,)
    bundle = stix2.Bundle(*objects)
    return bundle

def stix_view(request):
    form = InputForm()
    tform = TypeSelectForm()
    if request.method == "POST":
        if 'import' in request.POST:
            form = InputForm(request.POST)
            if request.user.is_authenticated() and form.is_valid():
                stix = json.loads(form.cleaned_data["input"])
                if "objects" in stix:
                    sdos = {}
                    rels = {}
                    sights = {}
                    reps = {}
                    for o in stix["objects"]:
                        if o["type"] == "relationship":
                            rels[o["id"]] = o
                        elif o["type"] == "sighting":
                            sights[o["id"]] = o
                        elif o["type"] == "report":
                            reps[o["id"]] = o
                        else:
                            sdo = stix2_db(o)
                            sdos[o["id"]] = sdo
                    for i in rels:
                        res = rel2db(rels[i], sdos)
                        if res:
                            sdos[i] = res
                    for i in sights:
                        res = sight2db(sights[i], sdos)
                        if res:
                            sdos[i] = res
                    for i in reps:
                        res = rep2db(reps[i], sdos)
                        if res:
                            sdos[i] = res
                messages.add_message(
                    request,
                    messages.SUCCESS,
                    'Import Completed '
                )
            else:
                messages.add_message(
                    request,
                    messages.ERROR,
                    'Import Failed'
                )
        elif 'timeline' in request.POST:
            form = InputForm(request.POST)
            if form.is_valid():
                stix = form.cleaned_data["input"]
                data = stix2timeline(json.loads(stix))
                c = {
                    "items":data["items"],
                    "groups":data["groups"],
                    "subgroups":data["subgroups"],
                    "colors":data["colors"],
                    "form":TimelineForm(),
                }
                return render(request, 'timeline_viz.html', c)
        elif 'parse_stix2' in request.POST or 'parse_url' in request.POST:
            form = InputForm(request.POST)
            tform = TypeSelectForm(request.POST)
            types = []
            relation = []
            if tform.is_valid():
                types = tform.cleaned_data["types"]
                types = list(types.values_list("name", flat=True))
                relation = tform.cleaned_data["relation"]
                relation = list(relation.values_list("name", flat=True))
            if form.is_valid():
                b = {"objects":[]}
                if 'parse_url' in request.POST:
                    urls = form.cleaned_data["input"]
                    for url in urls.split("\n"):
                        if not re.match("^https?://.+", url):
                            messages.add_message(
                                request,
                                messages.ERROR,
                                'ERROR: Invalid Input -> '+url,
                            )
                        else:
                            res = requests.get(url.strip())
                            if res:
                                j = res.json()
                                b = stix_filter(j, b, types=types, relation=relation)
                                
                elif 'parse_stix2' in request.POST:
                    j = form.cleaned_data["input"]
                    b = stix_filter(json.loads(j), b, types=types, relation=relation)
                c = {
                    "stix":json.dumps(b, indent=2),
                    "bundle":b,
                }
                return render(request, 'stix_view.html', c)
    c = {
        "form":form,
        "tform":tform,
    }
    return render(request, 'parse_view.html', c)

def stix_filter(j, b, types=[], relation=[]):
    temp = {}
    if "objects" in j:
        for o in j["objects"]:
            temp[o["id"]] = o
            if o["type"] in types:
                if o["type"] == "relationship":
                    if o["relationship_type"] in relation:
                        if not o in b["objects"]:
                            b["objects"].append(o)
                else:
                    if not o in b["objects"]:
                        b["objects"].append(o)
    for o in b["objects"]:
        if o["type"] == "relationship":
            src = temp[o["source_ref"]]
            if src not in b["objects"]:
                b["objects"].append(src)
            tgt = temp[o["target_ref"]]
            if tgt not in b["objects"]:
                b["objects"].append(tgt)
        elif o["type"] == "sighting":
            for wsr in o["where_sighted_refs"]:
                w = temp[wsr]
                if w not in b["objects"]:
                    b["objects"].append(w)
            sor = temp[o["sighting_of_ref"]]
            if sor not in b["objects"]:
                b["objects"].append(sor)
    return b
