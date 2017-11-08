from django.db import models
from django.apps import apps
from django.core.exceptions import ValidationError

class STIXObjectType(models.Model):
    name = models.CharField(max_length=250, unique=True)
    model_name = models.CharField(max_length=250, blank=True, null=True)
    def __str__(self):
        return self.name
    class Meta:
        ordering = ["name"]

class STIXObjectID(models.Model):
    object_id = models.CharField(max_length=250, unique=True)
    #def __str__(self):
    #    return self.object_id
    class Meta:
        ordering = ["object_id"]
    def __str__(self):
        o = get_obj_from_id(self)
        if o:
            if hasattr(o, "name"):
                return ":".join([o.object_type.name, o.name])
            elif o.object_type.name == "relationship":
                s = get_obj_from_id(o.source_ref)
                t = get_obj_from_id(o.target_ref)
                if s and t:
                    r = " ".join([s.name, o.relationship_type.name, t.name])
                    return ":".join([o.object_type.name, r])
            elif o.object_type.name == "sighting":
                wsrs = []
                for wsr in o.where_sighted_refs.all():
                    w = get_obj_from_id(wsr.object_id)
                    wsrs.append(w.name)
                s = get_obj_from_id(o.sighting_of_ref)
                if wsrs and s:
                    sighted = ",".join(wsrs) +" sighted "+ s.name
                    return o.object_type.name +":"+ sighted
            else:
                return self.object_id
        return self.object_id

class RelationshipType(models.Model):
    name = models.CharField(max_length=250, unique=True)
    def __str__(self):
        return self.name
    class Meta:
        ordering = ["name"]

class DefinedRelationship(models.Model):
    type = models.ForeignKey(RelationshipType)
    source = models.ForeignKey(STIXObjectType, related_name='source')
    target = models.ForeignKey(STIXObjectType, related_name='target')
    def __str__(self):
        drs = self.source.name + " " + self.type.name + " " + self.target.name
        return drs
    class Meta:
        unique_together = (("source", "type", "target"),)
        ordering = ["source", "type", "target"]

def get_obj_from_id(oid):
    so = STIXObject.objects.filter(object_id=oid)
    if so.count() == 1:
        so = so[0]
        if so.object_type.model_name:
            m = apps.get_model(so._meta.app_label, so.object_type.model_name)
            o = m.objects.get(id=so.id)
            return o
    return None

def _simple_name(obj):
    simple_name = obj.object_id.object_id
    if obj.object_type.model_name:
        m = apps.get_model(
            obj._meta.app_label, 
            obj.object_type.model_name
        )
        o = m.objects.get(id=obj.id)
        if hasattr(o, "name"):
            simple_name = ":".join([o.object_type.name, o.name])
        elif o.object_type.name == "relationship":
            s = get_obj_from_id(o.source_ref)
            t = get_obj_from_id(o.target_ref)
            if s and t:
                r = " ".join([s.name, o.relationship_type.name, t.name])
                simple_name = ":".join([o.object_type.name, r])
            elif o.object_type.name == "sighting":
                wsrs = []
                for wsr in o.where_sighted_refs.all():
                    w = get_obj_from_id(wsr)
                    wsrs.append(w.name)
                s = get_obj_from_id(o.sighting_of_ref)
                if wsrs and s:
                    sighted = ",".join(wsrs) +" sighted "+ s.name
                    simple_name = o.object_type.name +":"+ sighted
    obj.simple_name = simple_name
    return obj


class STIXObject(models.Model):
    object_type = models.ForeignKey(STIXObjectType, blank=True, null=True)
    object_id = models.OneToOneField(STIXObjectID, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    created_by_ref = models.ForeignKey(STIXObjectID, related_name="created_by_ref", blank=True, null=True)
    confidence = models.PositiveSmallIntegerField(blank=True, null=True)
    #object_marking_refs = models.ManyToManyField(STIXObjectID, blank=True)
    #simple_name = models.CharField(max_length=250, blank=True, null=True)
    class Meta:
        unique_together = (("object_type", "object_id"),)
        ordering = ["object_type", "object_id"]
    def delete(self):
        if self.object_id:
            self.object_id.delete()
        super(STIXObject, self).delete()
    #def save(self, *args, **kwargs):
        #self = _simple_name(self)
        #super(STIXObject, self).save(*args, **kwargs)
    def __str__(self):
        #return self.simple_name
        if self.object_type.model_name:
            m = apps.get_model(self._meta.app_label, self.object_type.model_name)
            o = m.objects.get(id=self.id)
            if hasattr(o, "name"):
                return ":".join([o.object_type.name, o.name])
            elif o.object_type.name == "relationship":
                s = get_obj_from_id(o.source_ref)
                t = get_obj_from_id(o.target_ref)
                if s and t:
                    r = " ".join([s.name, o.relationship_type.name, t.name])
                    return ":".join([o.object_type.name, r])
            elif o.object_type.name == "sighting":
                wsrs = []
                for wsr in o.where_sighted_refs.all():
                    w = get_obj_from_id(wsr.object_id)
                    wsrs.append(w.name)
                s = get_obj_from_id(o.sighting_of_ref)
                if wsrs and s:
                    sighted = ",".join(wsrs) +" sighted "+ s.name
                    return o.object_type.name +":"+ sighted
            else:
                return self.object_id.object_id
        return self.object_id.object_id

class MarkingDefinition(STIXObject):
    DEFINITION_TYPE_CHOICES = {
        ('statement','statement'),
        ('tlp','tlp'),
    }
    #object_marking_refs = models.ManyToManyField(STIXObjectID)
    definition_type = models.CharField(max_length=250, choices=DEFINITION_TYPE_CHOICES)
    definition =  models.CharField(max_length=250)
    class Meta:
        unique_together = (("definition_type", "definition"),)
        ordering = ["definition_type", "definition"]
    def __str__(self):
        return ":".join([definition_type,definition])

def _set_id(obj, name):
    from uuid import uuid4
    if not obj.object_type:
        s = STIXObjectType.objects.filter(name=name)
        if s.count() == 1:
            obj.object_type = STIXObjectType.objects.get(name=name)
    if obj.object_type and not obj.object_id:
        soi = STIXObjectID.objects.create(
            object_id = obj.object_type.name + "--" + str(uuid4())
        )
        obj.object_id = soi
    return obj

class KillChainPhase(models.Model):
    kill_chain_name = models.CharField(max_length=250)
    phase_name = models.CharField(max_length=250)
    seq = models.SmallIntegerField(default=1)
    def __str__(self):
        return self.phase_name
    class Meta:
        unique_together = (("kill_chain_name", "phase_name"),)
        ordering = ["seq"]

# SDO

class AttackPattern(STIXObject):
    name = models.CharField(max_length=250, unique=True)
    description = models.TextField(blank=True, null=True)
    #external_references = models.ManyToManyField(ExternalReference, blank=True)
    kill_chain_phases = models.ManyToManyField(KillChainPhase, blank=True)
    def save(self, *args, **kwargs):
        self = _set_id(self, 'attack-pattern')
        super(AttackPattern, self).save(*args, **kwargs)
    def __str__(self):
        return self.name
    class Meta:
        ordering = ["name"]

class CampaignAlias(models.Model):
    name = models.CharField(max_length=250, unique=True, blank=False)
    def __str__(self):
        return self.name
    class Meta:
        ordering = ["name"]

class Campaign(STIXObject):
    name = models.CharField(max_length=250, unique=True)
    description = models.TextField(blank=True, null=True)
    aliases = models.ManyToManyField(CampaignAlias, blank=True)
    first_seen = models.DateTimeField(blank=True, null=True)
    last_seen = models.DateTimeField(blank=True, null=True)
    def save(self, *args, **kwargs):
        self = _set_id(self, 'campaign')
        super(Campaign, self).save(*args, **kwargs)
    def __str__(self):
        return self.name
    class Meta:
        ordering = ["name"]

class CourseOfAction(STIXObject):
    name = models.CharField(max_length=250, unique=True)
    description = models.TextField(blank=True, null=True)
    def save(self, *args, **kwargs):
        self = _set_id(self, 'course-of-action')
        super(CourseOfAction, self).save(*args, **kwargs)
    def __str__(self):
        return self.name
    class Meta:
        ordering = ["name"]

class IdentityLabel(models.Model):
    value = models.CharField(max_length=250, unique=True)
    alias = models.CharField(max_length=250, blank=True, null=True)
    def __str__(self):
        return self.value
    class Meta:
        ordering = ["value"]

class IndustrySector(models.Model):
    value = models.CharField(max_length=250, unique=True)
    description = models.TextField(blank=True, null=True)
    def __str__(self):
        return self.value
    class Meta:
        ordering = ["value"]

class Identity(STIXObject):
    IDENTITY_CLASS_CHOICES = {
        ('individual','individual'),
        ('group','group'),
        ('organization','organization'),
        ('class','class'),
        ('unknown','unknown'),
    }
    name = models.CharField(max_length=250,unique=True)
    identity_class = models.CharField(max_length=250, choices=IDENTITY_CLASS_CHOICES)
    #identity_class = models.ForeignKey(IdentityClass, blank=True)
    description = models.TextField(blank=True, null=True)
    sectors = models.ManyToManyField(IndustrySector, blank=True)
    labels = models.ManyToManyField(IdentityLabel, blank=True)
    def save(self, *args, **kwargs):
        self = _set_id(self, 'identity')
        super(Identity, self).save(*args, **kwargs)
    def __str__(self):
        return self.name
    class Meta:
        ordering = ["name"]

class IntrusionSetAlias(models.Model):
    name = models.CharField(max_length=250, unique=True, blank=False)
    def __str__(self):
        return self.name
    class Meta:
        ordering = ["name"]

class IntrusionSet(STIXObject):
    name = models.CharField(max_length=250, unique=True)
    description = models.TextField(blank=True, null=True)
    aliases = models.ManyToManyField(IntrusionSetAlias, blank=True)
    first_seen = models.DateTimeField(blank=True, null=True)
    last_seen = models.DateTimeField(blank=True, null=True)
    def save(self, *args, **kwargs):
        self = _set_id(self, 'intrusion-set')
        super(IntrusionSet, self).save(*args, **kwargs)
    def __str__(self):
        return self.name
    class Meta:
        ordering = ["name"]

class MalwareLabel(models.Model):
    value = models.CharField(max_length=250, unique=True)
    def __str__(self):
        return self.value
    class Meta:
        ordering = ["value"]

class Malware(STIXObject):
    name = models.CharField(max_length=250, unique=True)
    description = models.TextField(blank=True, null=True)
    labels = models.ManyToManyField(MalwareLabel)
    kill_chain_phases = models.ManyToManyField(KillChainPhase, blank=True)
    def save(self, *args, **kwargs):
        self = _set_id(self, 'malware')
        super(Malware, self).save(*args, **kwargs)
    def __str__(self):
        return self.name
    class Meta:
        ordering = ["name"]

class ReportLabel(models.Model):
    value = models.CharField(max_length=250, unique=True)
    def __str__(self):
        return self.value
    class Meta:
        ordering = ["value"]

class Report(STIXObject):
    name = models.CharField(max_length=250, unique=True)
    labels = models.ManyToManyField(ReportLabel)
    description = models.TextField(blank=True, null=True)
    published = models.DateTimeField(blank=True, null=True)
    object_refs = models.ManyToManyField(STIXObjectID, blank=True)
    def save(self, *args, **kwargs):
        self = _set_id(self, 'report')
        super(Report, self).save(*args, **kwargs)
    def __str__(self):
        return self.name
    class Meta:
        ordering = ["name"]

class ThreatActorLabel(models.Model):
    value = models.CharField(max_length=250, unique=True)
    def __str__(self):
        return self.value
    class Meta:
        ordering = ["value"]

class ThreatActorAlias(models.Model):
    name = models.CharField(max_length=250, unique=True, blank=False)
    description = models.TextField(blank=True, null=True)
    def __str__(self):
        return self.name
    class Meta:
        ordering = ["name"]

class ThreatActor(STIXObject):
    name = models.CharField(max_length=250, unique=True, blank=False)
    description = models.TextField(blank=True, null=True)
    labels = models.ManyToManyField(ThreatActorLabel, blank=True)
    aliases = models.ManyToManyField(ThreatActorAlias, blank=True)
    def save(self, *args, **kwargs):
        self = _set_id(self, 'threat-actor')
        super(ThreatActor, self).save(*args, **kwargs)
    def __str__(self):
        return self.name
    class Meta:
        ordering = ["name"]

class ToolLabel(models.Model):
    value = models.CharField(max_length=250, unique=True)
    def __str__(self):
        return self.value
    class Meta:
        ordering = ["value"]

class Tool(STIXObject):
    name = models.CharField(max_length=250, unique=True)
    description = models.TextField(blank=True, null=True)
    labels = models.ManyToManyField(ToolLabel, blank=True)
    kill_chain_phases = models.ManyToManyField(KillChainPhase, blank=True)
    def save(self, *args, **kwargs):
        self = _set_id(self, 'tool')
        super(Tool, self).save(*args, **kwargs)
    def __str__(self):
        return self.name
    class Meta:
        ordering = ["name"]

class Vulnerability(STIXObject):
    name = models.CharField(max_length=250, unique=True)
    description = models.TextField(blank=True, null=True)
    def save(self, *args, **kwargs):
        self = _set_id(self, 'vulnerability')
        super(Vulnerability, self).save(*args, **kwargs)
    def __str__(self):
        return self.name
    class Meta:
        ordering = ["name"]


class IndicatorLabel(models.Model):
    value = models.CharField(max_length=250, unique=True)
    def __str__(self):
        return self.value
    class Meta:
        ordering = ["value"]

class ObservableObjectType(models.Model):
    name = models.CharField(max_length=250, unique=True)
    model_name = models.CharField(max_length=250, unique=True, null=True, blank=True)
    def __str__(self):
        return self.name
    class Meta:
        ordering = ["name"]

class ObservableObject(models.Model):
    object_id = models.CharField(max_length=250, unique=True, blank=True, null=True)
    type = models.ForeignKey(ObservableObjectType)
    description = models.TextField(blank=True, null=True)
    def __str__(self):
        if self.type.model_name:
            m = apps.get_model(self._meta.app_label, self.type.model_name)
            o = m.objects.get(id=self.id)
            if hasattr(o, "name"):
                return o.type.name + ":" + o.name
            elif hasattr(o, "value"):
                return o.type.name + ":" + o.value
        return str(self.id)
    class Meta:
        ordering = ["type"]

class DomainNameObject(ObservableObject):
    value = models.CharField(max_length=25000, unique=True)
    #resolve_to_refs = models.ManyToManyField(ObservableObject, related_name="resolve_to_refs", blank=True)
    resolves_to_refs = models.ManyToManyField(ObservableObject, related_name="resolves_to_refs", blank=True)
    def __str__(self):
        return self.value
    class Meta:
        ordering = ["value"]

class IPv4AddressObject(ObservableObject):
    value = models.CharField(max_length=15, unique=True)
    #resolves_to_refs = models.ManyToManyField(ObservableObject)
    def __str__(self):
        return self.value
    class Meta:
        ordering = ["value"]

class URLObject(ObservableObject):
    value = models.CharField(max_length=25000, unique=True)
    def __str__(self):
        return self.value
    class Meta:
        ordering = ["value"]

class FileObject(ObservableObject):
    name = models.CharField(max_length=25000, unique=True)
    hashes_md5 = models.CharField(max_length=250, null=True, blank=True)
    hashes_sha1 = models.CharField(max_length=250, null=True, blank=True)
    hashes_sha256 = models.CharField(max_length=250, null=True, blank=True)
    contains_refs = models.ManyToManyField(ObservableObject, related_name="contains_refs", blank=True)
    def __str__(self):
        return self.name
    class Meta:
        ordering = ["name"]

class ObservedData(STIXObject):
    first_observed = models.DateTimeField()
    last_observed = models.DateTimeField()
    number_observed = models.PositiveSmallIntegerField(default=1)
    observable_objects = models.ManyToManyField(ObservableObject)
    def save(self, *args, **kwargs):
        self = _set_id(self, 'observed-data')
        super(ObservedData, self).save(*args, **kwargs)


class IndicatorPattern(models.Model):
    pattern = models.TextField()
    observable = models.ManyToManyField(ObservableObject)
    def __str__(self):
        return self.pattern

class Indicator(STIXObject):
    name = models.CharField(max_length=250, unique=True)
    description = models.TextField(blank=True, null=True)
    labels = models.ManyToManyField(IndicatorLabel)
    valid_from = models.DateTimeField(blank=True, null=True)
    valid_until = models.DateTimeField(blank=True, null=True)
    pattern = models.OneToOneField(IndicatorPattern, blank=True, null=True)
    kill_chain_phases = models.ManyToManyField(KillChainPhase, blank=True)
    def save(self, *args, **kwargs):
        self = _set_id(self, 'indicator')
        super(Indicator, self).save(*args, **kwargs)

# SRO
class Relationship(STIXObject):
    source_ref= models.ForeignKey(STIXObjectID, related_name='source_ref')
    target_ref = models.ForeignKey(STIXObjectID, related_name='target_ref')
    relationship_type = models.ForeignKey(RelationshipType)
    description = models.TextField(blank=True, null=True)
    def __str__(self):
        #src = self.source_ref.object_id
        #tgt = self.target_ref.object_id
        #rel = self.relationship_type.name
        #return " ".join([src, rel, tgt])
        return self.object_id.object_id
    def save(self, *args, **kwargs):
        v = DefinedRelationship.objects.filter(
            type=self.relationship_type,
            source__name=str(self.source_ref.object_id).split("--")[0],
            target__name=str(self.target_ref.object_id).split("--")[0],
        )
        if not v:
            raise ValidationError("Invalid Relationship")
        else:
            self = _set_id(self, 'relationship')
            super(Relationship, self).save(*args, **kwargs)

class Sighting(STIXObject):
    sighting_of_ref= models.ForeignKey(STIXObjectID, related_name='sighting_of_ref')
    #where_sighted_refs = models.ManyToManyField(STIXObjectID, related_name='where_sighted_ref')
    where_sighted_refs = models.ManyToManyField(Identity, related_name='where_sighted_ref')
    first_seen = models.DateTimeField()
    last_seen = models.DateTimeField(blank=True, null=True)
    observed_data_refs = models.ManyToManyField(ObservedData, related_name='observed_data_refs')
    def save(self, *args, **kwargs):
        self = _set_id(self, 'sighting')
        super(Sighting, self).save(*args, **kwargs)
    def __str__(self):
        return self.object_id.object_id

class TaxiiCollection(models.Model):
    collection_id = models.CharField(max_length=250, unique=True, blank=True, null=True)
    title = models.CharField(max_length=250, unique=True, blank=False, null=False)
    description = models.TextField(blank=True, null=True)
    can_read = models.BooleanField(default=True)
    can_write = models.BooleanField(default=False)
    stix_objects = models.ManyToManyField(STIXObject)
    def save(self, *args, **kwargs):
        if not self.collection_id:
            from uuid import uuid4
            self.collection_id = str(uuid4()) 
        super(TaxiiCollection, self).save(*args, **kwargs)
