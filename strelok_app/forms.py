from django import forms
from django.db.models import Q

from .models import *
import strelok_app.models as mymodels

from operator import itemgetter

import logging
logging.basicConfig(level=logging.DEBUG)

#SDO

class AttackPatternForm(forms.ModelForm):
    class Meta:
        model = AttackPattern
        fields = [
            "name",
            "kill_chain_phases",
            "description",
        ]

identity_oid = STIXObjectID.objects.filter(
    object_id__startswith="identity--",
).order_by()

class CampaignForm(forms.ModelForm):
    new_alias = forms.CharField()
    class Meta:
        model = Campaign
        fields = [
            "name",
            "created_by_ref",
            "aliases",
            "first_seen",
            "last_seen",
            "description",
            #"confidence",
        ]
    def __init__(self, *args, **kwargs):
        super(CampaignForm, self).__init__(*args, **kwargs)
        self.fields["new_alias"].required = False
        self.fields["created_by_ref"].queryset = identity_oid
    def clean(self):
        c = self.cleaned_data
        name = c["name"]
        new = c["new_alias"]
        aliases = list(c["aliases"].values_list("id", flat=True))
        for n in new, name:
            if n:
                ca, cre = CampaignAlias.objects.get_or_create(
                    name=n
                )
                aliases.append(ca.id)
        c["aliases"] = CampaignAlias.objects.filter(
            id__in=aliases
        )
        return c

class CourseOfActionForm(forms.ModelForm):
    class Meta:
        model = CourseOfAction
        fields = [
            "name",
            "description",
        ]

class IdentityForm(forms.ModelForm):
    new_label = forms.CharField()
    class Meta:
        model = Identity
        fields = [
            "name",
            "identity_class",
            "sectors",
            "labels",
            "description",
            "new_label",
        ]
    def __init__(self, *args, **kwargs):
        super(IdentityForm, self).__init__(*args, **kwargs)
        self.fields["identity_class"].initial = "organization"
        self.fields["new_label"].required = False
    def clean(self):
        c = self.cleaned_data
        new = c["new_label"]
        labels = list(c["labels"].values_list("id", flat=True))
        if new:
            il, cre = IdentityLabel.objects.get_or_create(
                value=new
            )
            labels.append(il.id)
        c["labels"] = IdentityLabel.objects.filter(
            id__in=labels
        )
        return c

class IndicatorForm(forms.ModelForm):
    observable = forms.CharField(
        widget=forms.Textarea()
    )
    class Meta:
        model = Indicator
        fields = [
            "name",
            "labels",
            "description",
            "valid_from",
            "valid_until",
            #"pattern",
        ]
    def __init__(self, *args, **kwargs):
        super(IndicatorForm, self).__init__(*args, **kwargs)
        self.fields["observable"].required = False

class IntrusionSetForm(forms.ModelForm):
    new_alias = forms.CharField()
    class Meta:
        model = IntrusionSet
        fields = [
            "name",
            "description",
            "aliases",
            "first_seen",
            "last_seen",
        ]
    def __init__(self, *args, **kwargs):
        super(IntrusionSetForm, self).__init__(*args, **kwargs)
        self.fields["new_alias"].required = False
    def clean(self):
        c = self.cleaned_data
        name = c["name"]
        new = c["new_alias"]
        aliases = list(c["aliases"].values_list("id", flat=True))
        for n in new, name:
            if n:
                ia, cre = IntrusionSetAlias.objects.get_or_create(
                    name=n
                )
                aliases.append(ia.id)
        c["aliases"] = IntrusionSetAlias.objects.filter(
            id__in=aliases
        )
        return c

class MalwareForm(forms.ModelForm):
    class Meta:
        model = Malware
        fields = [
            "name",
            "labels",
            "kill_chain_phases",
            "description",
        ]

def create_obs(type, value):
    t = ObservableObjectType.objects.filter(name=type)
    o = None
    if t.count() == 1:
        t = t[0]
        if t.model_name and value:
            m = apps.get_model(t._meta.app_label, t.model_name)
            if t.name == "file":
                o, cre = m.objects.get_or_create(
                    type = t,
                    name = value
                )
            else:
                o, cre = m.objects.get_or_create(
                    type = t,
                    value = value
                )
    return o

def create_obs_from_line(line):
    o = None
    pattern = None
    type = line.strip().split(":")[0]
    value = ":".join(line.strip().split(":")[1:]).strip()
    o  = create_obs(type, value)
    return o

class ObservedDataForm(forms.ModelForm):
    new_observable = forms.CharField(
        widget=forms.Textarea()
    )
    class Meta:
        model = ObservedData
        fields = [
            "first_observed",
            "last_observed",
            "number_observed",
            "observable_objects",
        ]
    def __init__(self, *args, **kwargs):
        super(ObservedDataForm, self).__init__(*args, **kwargs)
        self.fields["new_observable"].required = False
        self.fields["observable_objects"].required = False
        self.fields["number_observed"].initial = 1
    def clean(self):
        c = self.cleaned_data
        obs = list(c["observable_objects"].values_list("id", flat=True))
        new = c["new_observable"]
        for line in new.split("\n"):
            for l in line.split("|"):
                if l:
                    o = create_obs_from_line(l)
                    if o:
                        obs.append(o.id)
        c["observable_objects"] = ObservableObject.objects.filter(
            id__in=obs
        )
        return c

class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = [
            "name",
            "created_by_ref",
            "published",
            "labels",
            "description",
            #"object_refs",
        ]
        widgets = {
            #"labels":forms.CheckboxSelectMultiple(),
        }
    def __init__(self, *args, **kwargs):
        super(ReportForm, self).__init__(*args, **kwargs)
        self.fields["created_by_ref"].choices = object_choices(
            ids=identity_oid,
            dummy=True
        )

class ThreatActorForm(forms.ModelForm):
    new_alias = forms.CharField()
    class Meta:
        model = ThreatActor
        fields = [
            "name",
            "labels",
            "aliases",
            "description",
            "new_alias",
        ]
    def __init__(self, *args, **kwargs):
        super(ThreatActorForm, self).__init__(*args, **kwargs)
        self.fields["new_alias"].required = False
        self.fields["labels"].required = True
    def clean(self):
        c = self.cleaned_data
        name = c["name"]
        new = c["new_alias"]
        aliases = list(c["aliases"].values_list("id", flat=True))
        for n in new, name:
            if n:
                ia, cre = ThreatActorAlias.objects.get_or_create(
                    name=n
                )
                aliases.append(ia.id)
        c["aliases"] = ThreatActorAlias.objects.filter(
            id__in=aliases
        )
        return c

class ToolForm(forms.ModelForm):
    class Meta:
        model = Tool
        fields = [
            "name",
            "labels",
            "kill_chain_phases",
            "description",
        ]
    def __init__(self, *args, **kwargs):
        super(ToolForm, self).__init__(*args, **kwargs)
        self.fields["labels"].required = True

class VulnerabilityForm(forms.ModelForm):
    class Meta:
        model = Vulnerability
        fields = [
            "name",
            "description",
        ]

# SRO
class RelationshipForm(forms.ModelForm):
    class Meta:
        model = Relationship
        fields = [
            "source_ref",
            "relationship_type",
            "target_ref",
            "description",
        ]
    def __init__(self, *args, **kwargs):
        super(RelationshipForm, self).__init__(*args, **kwargs)
        exclude_rel = STIXObjectID.objects.exclude(
                Q(object_id__startswith="relationship--")|\
                Q(object_id__startswith="sighting--")|\
                Q(object_id__startswith="observed-data--")|\
                Q(object_id__startswith="report--")
        )
        self.fields["source_ref"].queryset = exclude_rel
        self.fields["target_ref"].queryset = exclude_rel 
    def clean(self):
        c = self.cleaned_data
        v = DefinedRelationship.objects.filter(
            type=c["relationship_type"],
            source__name=str(c["source_ref"].object_id).split("--")[0],
            target__name=str(c["target_ref"].object_id).split("--")[0],
        )
        if not v:
            raise ValidationError("Invalid Relationship")
        else:
            return self.cleaned_data

class VisForm(forms.Form):
    plot = forms.ChoiceField(choices=(
        ("point","point"),
        ("box","box"),
        ("","default")
    ),initial="point")
    stack_groups = forms.BooleanField(initial=True)
    stack_subgroups = forms.BooleanField(initial=True)
    report = forms.BooleanField(initial=False)
    #show_minor_labels = forms.BooleanField(initial=True)
    def __init__(self, *args, **kwargs):
        super(VisForm, self).__init__(*args, **kwargs)
        self.fields["stack_groups"].required = False
        self.fields["stack_subgroups"].required = False
        self.fields["report"].required = False

class TimelineForm(forms.Form):
    group = forms.ModelMultipleChoiceField(
        queryset=STIXObjectType.objects.filter(
            name__in=[
                "attack-pattern",
                "campaign",
                "malware",
                "threat-actor",
                #"report",
            ]
        ),initial=STIXObjectType.objects.filter(name="threat-actor"),
        widget=forms.CheckboxSelectMultiple()
    )
    recursive = forms.BooleanField(initial=False)
    def __init__(self, *args, **kwargs):
        super(TimelineForm, self).__init__(*args, **kwargs)
        self.fields["recursive"].required = False
        self.fields["group"].required = False

class SightingForm(forms.ModelForm):
    observable = forms.CharField(
        widget=forms.Textarea()
    )
    class Meta:
        model = Sighting
        fields = [
            "where_sighted_refs",
            "sighting_of_ref",
            "first_seen",
            "last_seen",
            "observed_data_refs",
        ]
    def __init__(self, *args, **kwargs):
        super(SightingForm, self).__init__(*args, **kwargs)
        schoices = object_choices(
            ids = STIXObjectID.objects.filter(
                Q(object_id__startswith="threat-actor--")\
                |Q(object_id__startswith="indicator--")\
                |Q(object_id__startswith="malware--")\
                |Q(object_id__startswith="tool--")\
                |Q(object_id__startswith="campaign--")\
                |Q(object_id__startswith="attack-pattern--")\
                |Q(object_id__startswith="intrusion-set--")\
            ),dummy=True
        )
        self.fields["sighting_of_ref"].choices = schoices
        self.fields["observable"].required = False
        self.fields["observed_data_refs"].required = False
        #self.fields["sighting_of"].choices = schoices
    def clean(self):
        c = self.cleaned_data
        first = c["first_seen"]
        last = c["last_seen"]
        if first and not last:
            last = first
        odrs = list(c["observed_data_refs"].values_list("id", flat=True))
        # create observable objects
        new = c["observable"]
        for line in new.split("\n"):
            oos = []
            for l in line.split("|"):
                if l:
                    o = create_obs_from_line(l)
                    if o:
                        oos.append(o.id)
            # create observed-data and set observable objects
            if oos:
                od = ObservedData.objects.create(
                    first_observed=first,
                    last_observed=last,
                    number_observed=1,
                )
                for oo in ObservableObject.objects.filter(id__in=oos):
                    od.observable_objects.add(oo)
                od.save()
                odrs.append(od.object_id.id)
        c["observed_data_refs"] = ObservedData.objects.filter(id__in=odrs)
        return c

class MalwareLabelForm(forms.ModelForm):
    class Meta:
        model = Malware
        fields = [
            "labels",
        ]

class ReportLabelForm(forms.Form):
    label = forms.ModelMultipleChoiceField(
        queryset=ReportLabel.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={"checked":""})
    )

class ThreatActorLabelForm(forms.ModelForm):
    class Meta:
        model = ThreatActor
        fields = [
            "labels",
        ]
    def __init__(self, *args, **kwargs):
        super(ThreatActorLabelForm, self).__init__(*args, **kwargs)
        self.fields["labels"].required = True

class ToolLabelForm(forms.ModelForm):
    class Meta:
        model = Tool
        fields = [
            "labels",
        ]

class IdentityClassForm(forms.ModelForm):
    #new_label = forms.CharField()
    class Meta:
        model = Identity
        fields = [
            "identity_class",
        ]

class ReportRefForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = [
            "object_refs",
        ]
        widgets = {
            "object_refs":forms.CheckboxSelectMultiple(),
        }

class DefinedRelationshipForm(forms.Form):
    relation = forms.ModelChoiceField(
        queryset=DefinedRelationship.objects.all()
    )

class SelectObjectForm(forms.Form):
    type = forms.ModelChoiceField(
        queryset=STIXObjectType.objects.filter()
    )
    def __init__(self, *args, **kwargs):
        super(SelectObjectForm, self).__init__(*args, **kwargs)
        self.fields["type"].required = False

class AddObjectForm(forms.Form):
    relation = forms.ModelChoiceField(
        queryset=DefinedRelationship.objects.all()
    )
    objects = forms.ModelMultipleChoiceField(
        queryset=STIXObjectID.objects.all()
    )
    def __init__(self, *args, **kwargs):
        super(AddObjectForm, self).__init__(*args, **kwargs)
        self.fields["objects"].choices = object_choices()
        self.fields["relation"].required = False

class TypeSelectForm(forms.Form):
    icon = forms.BooleanField(initial=True)
    types = forms.ModelMultipleChoiceField(
        queryset=STIXObjectType.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={"checked":""})
    )
    relation = forms.ModelMultipleChoiceField(
        queryset=RelationshipType.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={"checked":""})
    )
    def __init__(self, *args, **kwargs):
        super(TypeSelectForm, self).__init__(*args, **kwargs)
        self.fields["types"].required = False
        self.fields["relation"].required = False
        self.fields["icon"].required = False

class InputForm(forms.Form):
    input = forms.CharField(
        widget=forms.Textarea()
    )

has_killchain = [                          
    "attack-pattern",                            
    #"indicator",    
    "malware",      
    "tool",         
]
type_has_killchain = STIXObjectType.objects.filter(name__in=has_killchain)

class MatrixForm(forms.Form):
    type = forms.ModelMultipleChoiceField(
        queryset=type_has_killchain,
        initial=type_has_killchain,
        #widget=forms.CheckboxSelectMultiple()
    )
    campaign = forms.ModelMultipleChoiceField(
        queryset=Campaign.objects.all()
    )
    threat_actor = forms.ModelMultipleChoiceField(
        queryset=ThreatActor.objects.all()
    )
    def __init__(self, *args, **kwargs):
        super(MatrixForm, self).__init__(*args, **kwargs)
        self.fields["threat_actor"].required = False
        self.fields["campaign"].required = False
        self.fields["type"].required = False


def get_related_obj(so, recursive=False):
    objects = []
    ids = [so.object_id.id]

    rels = Relationship.objects.filter(
            Q(source_ref=so.object_id)|\
            Q(target_ref=so.object_id)
    )
    sights = Sighting.objects.filter(
            #Q(where_sighted_refs=so.object_id)|\
            #Q(observed_data_refs=so.object_id)|\
            Q(sighting_of_ref=so.object_id)
    )
    rep = Report.objects.filter(object_refs=so.object_id)

    if so.object_type.name == "identity":
        sights = Sighting.objects.filter(where_sighted_refs=so)
    elif so.object_type.name == "observed-data":
        sights = Sighting.objects.filter(observed_data_refs=so)
    elif so.object_type.name == "report":
        # no relation but refs contains SRO
        so = Report.objects.get(id=so.id)
        ids += so.object_refs.all().values_list("id",flat=True)
        rels = Relationship.objects.filter(id__in=so.object_refs.all())
        sights = Sighting.objects.filter(id__in=so.object_refs.all())
    elif so.object_type.name == "sighting":
        sights = Sighting.objects.filter(object_id__id__in=ids)
    elif so.object_type.name == "relationship":
        rels = Relationship.objects.filter(object_id_id__in=ids)

    if rels:
        ids += rels.values_list("object_id", flat=True)
        ids += rels.values_list("source_ref", flat=True)
        ids += rels.values_list("target_ref", flat=True)
    if sights:
        ids += sights.values_list("object_id", flat=True)
        ids += sights.values_list("sighting_of_ref", flat=True)
        ids += sights.values_list("where_sighted_refs", flat=True)
        ids += sights.values_list("observed_data_refs", flat=True)
    if rep:
        ids += rep.values_list("object_id", flat=True)
        ids += rep.values_list("object_refs", flat=True)
    ids = list(set(ids))
    #print(ids)
    additional = Relationship.objects.filter(
            source_ref__in=ids,target_ref__in=ids
    )
    #print(additional)
    if additional:
        ids += additional.values_list("object_id", flat=True)

    oids = STIXObjectID.objects.filter(id__in=ids)
    for oid in oids:
        obj = get_obj_from_id(oid)
        if obj:
            if not obj in objects:
                objects.append(obj)
    if recursive == True:
        rec = []
        #print(objects)
        for o in objects:
            rec += get_related_obj(o, recursive=False)
        objects += rec
    objects = list(set(objects))
    return objects

def object_choices(
        #ids=STIXObjectID.objects.all(),
        ids=[],
        dummy=False
    ):
    choices = []
    if dummy:
        choices = [("","----------")]
    for soi in ids:
        obj = get_obj_from_id(soi)
        name = ""
        if not obj:
            logging.error("Could not get object: "+soi.object_id)
            if soi.id:
                soi.delete()
        else:
            if obj.object_type.name == 'relationship':
                src = get_obj_from_id(obj.source_ref)
                tgt = get_obj_from_id(obj.target_ref)
                rel = obj.relationship_type.name
                if src and tgt and rel:
                    name = " ".join([src.name, rel, tgt.name])
            elif obj.object_type.name == 'sighting':
                sor = get_obj_from_id(obj.sighting_of_ref)
                tgt = []
                for wsr in obj.where_sighted_refs.all():
                    i = get_obj_from_id(wsr)
                    if i:
                        tgt.append(i.name)
                if sor and tgt:
                    name = ",".join(tgt) + " sighted " + sor.name
            else:
                if hasattr(obj, 'name'):
                    name = obj.name
            if name:
                choices.append((
                #choices += ((
                    obj.object_id.id,
                    obj.object_type.name + " : " + name,
                ))
    if choices:
        choices.sort(key=itemgetter(1))
    return choices

class IndicatorPatternForm(forms.ModelForm):
    generate_pattern = forms.BooleanField()
    new_observable = forms.CharField(
        widget=forms.Textarea(
            attrs={'style':'height:100px;'}
        )
    )
    class Meta:
        model = IndicatorPattern
        fields = [
            "observable",
            "pattern",
        ]
    def __init__(self, *args, **kwargs):
        super(IndicatorPatternForm, self).__init__(*args, **kwargs)
        self.fields["generate_pattern"].required = False
        self.fields["new_observable"].required = False
        self.fields["observable"].required = False
        self.fields["pattern"].required = False

class SelectObservableForm(forms.Form):
    label = forms.ModelChoiceField(
        queryset=IndicatorLabel.objects.all()
    )
    #property = forms.ModelChoiceField(
    #    queryset=ObservableObjectProperty.objects.all()
    #)
    indicates = forms.ModelChoiceField(
        queryset=Malware.objects.all()
    )
    def __init__(self, *args, **kwargs):
        super(SelectObservableForm, self).__init__(*args, **kwargs)
        self.fields["indicates"].required = False

def get_model_from_type(type):
    name = ""
    for i in type.split("-"):
        name += i.capitalize()
    m = getattr(mymodels, name)
    return m

class DomainNameForm(forms.ModelForm):
    new_refs = forms.CharField(
        widget=forms.Textarea(
            attrs={'style':'height:100px;'}
        )
    )
    class Meta:
        model = DomainNameObject
        fields = [
            "value",
            "resolves_to_refs",
        ]
    def __init__(self, *args, **kwargs):
        super(DomainNameForm, self).__init__(*args, **kwargs)
        self.fields["new_refs"].required = False

class KillChainForm(forms.Form):
    killchain = forms.ModelChoiceField(
        queryset=KillChainPhase.objects.all()
    )
