from django_datatables_view.base_datatable_view import BaseDatatableView
from django.utils.html import escape
from django.apps import apps
from .models import *
from .forms import *


def _get_row_from_column(column, row):
    if column == 'id':
        return '<a class="btn btn-default btn-xs">{0}</button>'.format(row.id)
    elif column == 'name':
        n = escape(row.name)
        return '<a href="/stix/{0}">{1}</a>'.format(row.object_id.object_id,n)
    elif column == 'aliases':
        a = []
        for alias in row.aliases.all():
            n = escape(alias.name)
            if not n in a:
                a.append(n)
        return " / ".join(a)
    elif column == 'kill_chain_phases':
        k = []
        for kcp in row.kill_chain_phases.all():
            n = escape(kcp.phase_name)
            if not n in k:
                k.append(n)
        return " / ".join(k)
    elif column == 'labels':
        l = []
        for label in row.labels.all():
            v = escape(label.value)
            if not v in l:
                l.append(v)
        return " / ".join(l)
    elif column == 'publisher':
        p = Identity.objects.filter(object_id=row.created_by_ref)
        if p.count() == 1:
            return escape(p[0].name)
        else:
            return None
    elif column == 'object_refs':
        return row.object_refs.count()
    elif column == 'created_by_ref':
        name = ""
        if row.created_by_ref:
            c = get_obj_from_id(row.created_by_ref)
            name = c.name
        return escape(name)
    return False

class AttackPatternData(BaseDatatableView):
    model = AttackPattern
    columns = ['created', 'name', 'kill_chain_phases']
    order_columns = columns
    max_display_length = 100
    def render_column(self, row, column):
        result = _get_row_from_column(column, row)
        if result == False:
            return super(AttackPatternData, self).render_column(row, column)
        else:
            return result
    def filter_queryset(self, qs):
        search = self.request.GET.get(u'search[value]', None)
        if search:
            qs = qs.filter(kill_chain_phases__phase_name__iregex=search) \
                | qs.filter(name__iregex=search)
        return qs.distinct()

class CampaignData(BaseDatatableView):
    model = Campaign
    columns = ['created', 'name', 'aliases', 'first_seen']
    order_columns = columns
    max_display_length = 100
    def render_column(self, row, column):
        result = _get_row_from_column(column, row)
        if result == False:
            return super(CampaignData, self).render_column(row, column)
        else:
            return result
    def filter_queryset(self, qs):
        search = self.request.GET.get(u'search[value]', None)
        if search:
            qs = qs.filter(aliases__name__iregex=search) \
                | qs.filter(name__iregex=search)
        return qs.distinct()


class CourseOfActionData(BaseDatatableView):
    model = CourseOfAction
    columns = ['created', 'name', 'description']
    order_columns = ['created', 'name', 'description']
    max_display_length = 100
    def render_column(self, row, column):
        result = _get_row_from_column(column, row)
        if result == False:
            return super(CourseOfActionData, self).render_column(row, column)
        else:
            return result
    def filter_queryset(self, qs):
        search = self.request.GET.get(u'search[value]', None)
        if search:
            qs = qs.filter(description__iregex=search) \
                | qs.filter(name__iregex=search)
        return qs.distinct()

class IdentityData(BaseDatatableView):
    model = Identity
    columns = ['modified', 'name', 'sectors', 'labels']
    order_columns = columns
    max_display_length = 100
    def render_column(self, row, column):
        if column == 'name':
            n = escape(row.name)
            if self.request.user.is_authenticated():
                return '<a href="/stix/{0}">{1}</a>'.format(row.object_id.object_id,n)
            else:
                return '<a href="/stix/{0}">{0}</a>'.format(row.object_id.object_id)
        elif column == 'labels':
            l = ""
            for label in row.labels.all():
                v = escape(label.value)
                l += v+"<br>"
            return l
        elif column == 'sectors':
            s = ""
            for sector in row.sectors.all():
                v = escape(sector.value)
                s += v+"<br>"
            return s
        else:
            return super(IdentityData, self).render_column(row, column)
    def filter_queryset(self, qs):
        search = self.request.GET.get(u'search[value]', None)
        if search:
            qs = qs.filter(sectors__value__iregex=search) \
                | qs.filter(name__iregex=search)
        return qs.distinct()

class IntrusionSetData(BaseDatatableView):
    model = IntrusionSet
    columns = ['created', 'name', 'aliases', 'first_seen']
    order_columns = columns
    max_display_length = 100
    def render_column(self, row, column):
        result = _get_row_from_column(column, row)
        if result == False:
            return super(IntrusionSetData, self).render_column(row, column)
        else:
            return result
    def filter_queryset(self, qs):
        search = self.request.GET.get(u'search[value]', None)
        if search:
            qs = qs.filter(aliases__name__iregex=search) \
                | qs.filter(name__iregex=search)
        return qs.distinct()

class MalwareData(BaseDatatableView):
    model = Malware
    columns = ['created', 'name', 'labels', 'kill_chain_phases']
    order_columns = columns
    max_display_length = 100
    def render_column(self, row, column):
        result = _get_row_from_column(column, row)
        if result == False:
            return super(MalwareData, self).render_column(row, column)
        else:
            return result
    def filter_queryset(self, qs):
        search = self.request.GET.get(u'search[value]', None)
        if search:
            qs = qs.filter(labels__value__iregex=search) \
                | qs.filter(name__iregex=search)
        return qs.distinct()

class ObservedDataData(BaseDatatableView):
    model = ObservedData
    columns = ['created', 'object_id', 'observable_objects']
    order_columns = columns
    max_display_length = 100
    def render_column(self, row, column):
        if column == 'object_id':
            return "<a href=/stix/{0}>{0}</href>".format(row.object_id.object_id)
        elif column == 'observable_objects':
            results = ""
            for obs in row.observable_objects.all():
                o = escape(str(obs))
                results += "<a href=/observable/{0}>{1}</href><br>".format(obs.id,o)
            return results
        else:
            return super(ObservedDataData, self).render_column(row, column)
    def filter_queryset(self, qs):
        search = self.request.GET.get(u'search[value]', None)
        ids = []
        if search:
            for q in qs.all():
                for o in q.observable_objects.all():
                    if search in str(o):
                        ids.append(q.id)
            qs = qs.filter(id__in=ids) \
                | qs.filter(object_id__object_id__iregex=search)
        return qs.distinct()

class ReportData(BaseDatatableView):
    model = Report
    columns = ['created', 'name', 'created_by_ref', 'published']
    order_columns = columns
    max_display_length = 100

    def get_initial_queryset(self):
        qs = Report.objects.all()
        return qs
    def render_column(self, row, column):
        result = _get_row_from_column(column, row)
        if result == False:
            return super(ReportData, self).render_column(row, column)
        else:
            return result
    def filter_queryset(self, qs):
        search = self.request.GET.get(u'search[value]', None)
        if search:
            qs = qs.filter(published__iregex=search) \
                | qs.filter(name__iregex=search)
        return qs.distinct()

class ThreatActorData(BaseDatatableView):
    model = ThreatActor
    columns = ['created', 'name', 'aliases']
    order_columns = columns
    max_display_length = 100
    def render_column(self, row, column):
        result = _get_row_from_column(column, row)
        if result == False:
            return super(ThreatActorData, self).render_column(row, column)
        else:
            return result
    def filter_queryset(self, qs):
        search = self.request.GET.get(u'search[value]', None)
        if search:
            qs = qs.filter(aliases__name__iregex=search) \
                | qs.filter(name__iregex=search)
        return qs.distinct()

class ToolData(BaseDatatableView):
    model = Tool
    columns = ['created', 'name', 'labels', 'kill_chain_phases']
    order_columns = columns
    max_display_length = 100
    def render_column(self, row, column):
        result = _get_row_from_column(column, row)
        if result == False:
            return super(ToolData, self).render_column(row, column)
        else:
            return result
    def filter_queryset(self, qs):
        search = self.request.GET.get(u'search[value]', None)
        if search:
            qs = qs.filter(labels__value__iregex=search) \
                | qs.filter(name__iregex=search)
        return qs.distinct()

class VulnerabilityData(BaseDatatableView):
    model = Vulnerability
    columns = ['created', 'name', 'description']
    order_columns = columns
    max_display_length = 100
    def render_column(self, row, column):
        result = _get_row_from_column(column, row)
        if result == False:
            return super(VulnerabilityData, self).render_column(row, column)
        else:
            return result
    def filter_queryset(self, qs):
        search = self.request.GET.get(u'search[value]', None)
        if search:
            qs = qs.filter(description__iregex=search) \
                | qs.filter(name__iregex=search)
        return qs.distinct()

# SRO
class RelationshipData(BaseDatatableView):
    model = Relationship
    columns = ['created', 'object_id', 'source_ref', 'relationship_type', 'target_ref']
    order_columns = columns
    max_display_length = 100
    def render_column(self, row, column):
        if column == 'source_ref':
            o = get_obj_from_id(row.source_ref)
            if o:
                o = escape(str(o))
            return "<a href=/stix/{0}>{1}</href>".format(row.object_id.object_id, o)
        elif column == 'target_ref':
            o = get_obj_from_id(row.target_ref)
            if o:
                o = escape(str(o))
            return "<a href=/stix/{0}>{1}</href>".format(row.object_id.object_id, o)
        elif column == 'relationship_type':
            return escape(row.relationship_type.name)
        elif column == 'object_id':
            return "<a href=/stix/{0}>{1}</href>".format(row.object_id.object_id, row.object_id.object_id)
        else:
            return super(RelationshipData, self).render_column(row, column)
    def filter_queryset(self, qs):
        search = self.request.GET.get(u'search[value]', None)
        ids = []
        if search:
            for q in qs.all():
                obj = get_related_obj(q)
                for o in obj:
                    if search in str(o):
                        ids.append(q.id)
            qs = qs.filter(id__in=ids) \
                | qs.filter(relationship_type__name__iregex=search)
        return qs.distinct()

class SightingData(BaseDatatableView):
    model = Sighting
    columns = ['created', 'object_id', 'where_sighted_refs', 'sighting_of_ref']
    order_columns = columns
    max_display_length = 100
    def render_column(self, row, column):
        if column == 'sighting_of_ref':
            o = get_obj_from_id(row.sighting_of_ref)
            if o:
                o = escape(str(o))
            return "<a href=/stix/{0}>{1}</href>".format(row.object_id.object_id, o)
        elif column == 'where_sighted_refs':
            wsr = ""
            for r in row.where_sighted_refs.all():
                o = get_obj_from_id(r.object_id)
                if o:
                    o = escape(str(o))
                wsr += "<a href=/stix/{0}>{1}</href><br>".format(r.object_id.object_id, o)
            return wsr
        elif column == 'object_id':
            return "<a href=/stix/{0}>{1}</href>".format(row.object_id.object_id, row.object_id.object_id)
        else:
            return super(SightingData, self).render_column(row, column)
    def filter_queryset(self, qs):
        search = self.request.GET.get(u'search[value]', None)
        ids = []
        if search:
            for q in qs.all():
                obj = get_related_obj(q)
                for o in obj:
                    if search in str(o):
                        ids.append(q.id)
            qs = qs.filter(id__in=ids)
        return qs.distinct()

class ObservableObjectData(BaseDatatableView):
    model = ObservableObject
    columns = ['id', 'type']
    order_columns = ['id', 'type']
    max_display_length = 100
    def render_column(self, row, column):
        if column == 'id':
            return "<a href=/observable/{0}>{0}</href>".format(row.id)
        elif column == 'type':
            t = row.type.name
            if row.type.model_name:
                m = apps.get_model(row._meta.app_label, row.type.model_name)
                o = m.objects.get(id=row.id)
                if hasattr(o, "name"):
                    return t + ":" + o.name
                elif hasattr(o, "value"):
                    return t + ":" + o.value
            return row.type.name
        else:
            return super(ObservableObjectData, self).render_column(row, column)

class IndicatorPatternData(BaseDatatableView):
    model = IndicatorPattern
    columns = ['pattern']
    order_columns = ['pattern']
    max_display_length = 100
    def render_column(self, row, column):
        if column == 'property':
            p = row.property.type.name + ":" + row.property.name
            return p
        else:
            return super(IndicatorPatternData, self).render_column(row, column)

class IndicatorData(BaseDatatableView):
    model = Indicator
    columns = ['created', 'name', 'pattern']
    order_columns = ['created', 'name', 'pattern']
    max_display_length = 100
    def render_column(self, row, column):
        if column == 'pattern':
            pattern = ""
            if row.pattern:
                pattern = row.pattern.pattern
            #pattern = " OR ".join(sorted(row.pattern.all().values_list("pattern", flat=True)))
            return escape(pattern)
        elif column == 'name':
            n = escape(row.name)
            return '<a href="/stix/{0}">{1}</a>'.format(row.object_id.object_id,n)
        else:
            return super(IndicatorData, self).render_column(row, column)
    def filter_queryset(self, qs):
        search = self.request.GET.get(u'search[value]', None)
        if search:
            qs = qs.filter(pattern__pattern__iregex=search) \
                | qs.filter(name__iregex=search)
        return qs.distinct()

