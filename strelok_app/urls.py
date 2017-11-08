from django.conf.urls import url, include
from django.contrib import admin, auth

from .views.sdo import sdo_list,sdo_view, sdo_view_recursive
from .views.observables import obs_view
from .views.drs import viz_drs, data_drs
from .views.stix import stix_view ,stix2_json, stix2type_json, stix2_json_masked
from .views.taxii import taxii_discovery, taxii_collection, taxii_get_objects
from .views.timeline import timeline_view
from .views.chart import kill_chain_view, ttp_view, target_chart, actor_chart, chart_view
from .tables import *

from two_factor.admin import AdminSiteOTPRequired

urlpatterns = [
    url(r'', include('two_factor.urls', 'two_factor')),
    url(r'^account/', include('django.contrib.auth.urls')),
    url(r'^admin/', admin.site.urls),
    url(r'^data/attack-pattern/', AttackPatternData.as_view()),
    url(r'^data/campaign/', CampaignData.as_view()),
    url(r'^data/course-of-action/', CourseOfActionData.as_view()),
    url(r'^data/identity/', IdentityData.as_view()),
    url(r'^data/intrusion-set/', IntrusionSetData.as_view()),
    url(r'^data/malware/', MalwareData.as_view()),
    url(r'^data/observed-data/', ObservedDataData.as_view()),
    url(r'^data/report/', ReportData.as_view()),
    url(r'^data/threat-actor/', ThreatActorData.as_view()),
    url(r'^data/tool/', ToolData.as_view()),
    url(r'^data/vulnerability/', VulnerabilityData.as_view()),
    url(r'^data/relationship/', RelationshipData.as_view()),
    url(r'^data/sighting/', SightingData.as_view()),
    url(r'^data/indicator/', IndicatorData.as_view()),
    url(r'^data/observable/', ObservableObjectData.as_view()),
    url(r'^data/pattern/', IndicatorPatternData.as_view()),
    url(r'^data/drs/$', data_drs),
    url(r'^chart/target/(?P<cnt_by>[a-z]+)$', target_chart),
    url(r'^chart/threat-actor/(?P<cnt_by>[a-z]+)$', actor_chart),
    url(r'^chart/(?P<id>[a-z\-]+--[0-9a-f\-]+)/(?P<cnt_by>[a-z]+)$', chart_view),
    url(r'^stix/$', stix_view),
    url(r'^stix/drs/$', viz_drs),
    url(r'^stix/matrix/$', ttp_view),
    url(r'^stix/matrix/(?P<id>[a-z\-]+--[0-9a-f\-]+)$', ttp_view),
    url(r'^stix/(?P<id>[a-z\-]+--[0-9a-f\-]+)\.json$', stix2_json),
    url(r'^stix/(?P<id>[a-z\-]+--[0-9a-f\-]+)$', sdo_view),
    url(r'^stix/(?P<id>[a-z\-]+--[0-9a-f\-]+)/recursive$', sdo_view_recursive),
    url(r'^stix/all.json$', stix2_json),
    url(r'^stix/masked-all.json$', stix2_json_masked),
    url(r'^stix/(?P<type>[^/]+)\.json$', stix2type_json),
    url(r'^stix/(?P<type>[^/]+)', sdo_list),
    url(r'^timeline/(?P<id>[a-z\-]+--[0-9a-f\-]+)$', timeline_view),
    url(r'^timeline/$', timeline_view),
    url(r'^observable/(?P<id>[^/]+)', obs_view),
    url(r'^taxii/api/collections/(?P<id>[^/]+)/id/(?P<object_id>[^/]+)/$', taxii_collection),
    url(r'^taxii/api/collections/(?P<id>[^/]+)/objects/$', taxii_get_objects),
    url(r'^taxii/api/collections/(?P<id>[^/]+)/$', taxii_collection),
    url(r'^taxii/api/collections/$', taxii_collection),
    url(r'^taxii/$', taxii_discovery),
    url(r'^$', viz_drs, name='document_root'),
]
