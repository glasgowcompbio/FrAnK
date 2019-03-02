__author__ = 'Scott Greig'

from django.conf.urls import patterns, url
from frank import views

urlpatterns = patterns(
    '',
    url(r'^$', views.index, name='frank_index'),
    url(r'^my-experiments/$', views.my_experiments, name='my_experiments'),
    url(r'^my-experiments/add-experiment/$', views.add_experiment, name='add_experiment'),
    url(r'^my-experiments/(?P<experiment_id>[0-9]+)/$', views.experiment_summary, name='experiment_summary'),
    url(r'^my-experiments/(?P<experiment_id>[0-9]+)/add_experimental_condition/$',
        views.add_experimental_condition, name='add_experimental_condition'),
    url(r'^my-experiments/(?P<experiment_id>[0-9]+)/create_fragmentation_set/$',
        views.create_fragmentation_set, name='create_fragmentation_set'),
    url(r'^my-experiments/(?P<experiment_id>[0-9]+)/condition/(?P<condition_id>[0-9]+)/$',
        views.condition_summary, name='condition_summary'),
    url(r'^my-experiments/(?P<experiment_id>[0-9]+)/condition/(?P<condition_id>[0-9]+)/add_sample/$',
        views.add_sample, name='add_sample'),
    url(r'^my-experiments/(?P<experiment_id>[0-9]+)/condition/(?P<condition_id>[0-9]+)/sample/'
        r'/(?P<sample_id>[0-9]+)/add_sample_file/$', views.add_sample_file, name='add_sample_file'),
    url(r'^my-fragmentation-sets/$', views.fragmentation_set_summary, name='fragmentation_set_summary'),
    url(r'^my-fragmentation-sets/(?P<fragmentation_set_id>[0-9]+)/$',
        views.fragmentation_set, name='fragmentation_set'),
    url(r'^my-fragmentation-sets/(?P<fragmentation_set_id>[0-9]+)/annotation_tool/(?P<annotation_tool_id>[0-9]+)'
        r'/define_annotation_query_paramaters/$', views.define_annotation_query, name='define_annotation_query'),
    url(r'^my-fragmentation-sets/(?P<fragmentation_set_id>[0-9]+)/peak/(?P<peak_id>[0-9]+)/$',
        views.peak_summary, name='peak_summary'),
    url(r'^my-fragmentation-sets/(?P<fragmentation_set_id>[0-9]+)/peak/'
        r'/(?P<peak_id>[0-9]+)/msn-spectra-plot.png/$', views.make_frag_spectra_plot, name="make_spectra_plot"),
    url(r'^my-fragmentation-sets/download/peak-spectra/(?P<peak_id>[0-9]+)/$',
        views.get_fragments_as_text, name='get_fragments_as_text'),
    url(r'^my-fragmentation-sets/download/peak-spectra/(?P<peak_id>[0-9]+)/format/(?P<format_type>[\w\-]+)$',
        views.get_fragments_as_text, name='get_fragments_as_text'),
    url(r'^my-fragmentation-sets/(?P<fragmentation_set_id>[0-9]+)/peak/(?P<peak_id>[0-9]+)'
        r'/annotation/(?P<annotation_id>[0-9]+/my-fragmentation-sets/2/56449/)/specify_preferred_annotation/$',
        views.specify_preferred_annotation, name='specify_preferred_annotation'),
    url(r'^remove-preferred-annotations/(?P<fragmentation_set_id>[0-9]+)',
        views.remove_preferred_annotations, name='remove_preferred_annotations'),
    url(r'^delete-annotation-query/(?P<fragmentation_set_id>[0-9]+)/annotation-query/(?P<annotation_query_id>[0-9]+)/$',
        views.delete_annotation_query, name='delete_annotation_query'),

    #ChemSpider url
    url(r'^chemspider_info/compound/(?P<compound_id>[0-9]+)/$',
        views.get_chemspider_info, name='get_chemspider_info'),

    # Network sample URL added by Simon
    url(r'^network_sampler/$', views.run_network_sampler, name='network_sampler'),

)
