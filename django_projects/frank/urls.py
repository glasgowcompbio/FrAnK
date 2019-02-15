__author__ = 'Scott Greig'

from django.conf.urls import patterns, url
from frank import views

urlpatterns = patterns('',
    url(r'^$', views.index, name='frank_index'),
    url(r'^my_experiments/$', views.my_experiments, name='my_experiments'),
    url(r'^my_experiments/add_experiment/$', views.add_experiment, name='add_experiment'),
    url(r'^my_experiments/(?P<experiment_name_id>[\w\-]+)/$', views.experiment_summary, name='experiment_summary'),
    url(r'^my_experiments/(?P<experiment_name_id>[\w\-]+)/add_experimental_condition/$',
        views.add_experimental_condition, name='add_experimental_condition'),
    url(r'^my_experiments/(?P<experiment_name_id>[\w\-]+)/create_fragmentation_set/$',
        views.create_fragmentation_set, name='create_fragmentation_set'),
    url(r'^my_experiments/(?P<experiment_name_id>[\w\-]+)/(?P<condition_name_id>[\w\-]+)/$',
        views.condition_summary, name='condition_summary'),
    url(r'^my_experiments/(?P<experiment_name_id>[\w\-]+)/(?P<condition_name_id>[\w\-]+)/add_sample/$',
        views.add_sample, name='add_sample'),
    url(r'^my_experiments/(?P<experiment_name_id>[\w\-]+)/(?P<condition_name_id>[\w\-]+)'
        r'/(?P<sample_id>[\w\-]+)/add_sample_file/$', views.add_sample_file, name='add_sample_file'),
    url(r'^my_fragmentation_sets/$', views.fragmentation_set_summary, name='fragmentation_set_summary'),
    url(r'^my_fragmentation_sets/(?P<fragmentation_set_name_id>[\w\-]+)/$',
        views.fragmentation_set, name='fragmentation_set'),
    url(r'^my_fragmentation_sets/(?P<fragmentation_set_name_id>[\w\-]+)/(?P<annotation_tool_id>[\w\-]+)'
        r'/define_annotation_query_paramaters/$', views.define_annotation_query, name='define_annotation_query'),
    url(r'^my_fragmentation_sets/(?P<fragmentation_set_name_id>[\w\-]+)'
        r'/(?P<peak_name_id>[\w\-]+)/$', views.peak_summary, name='peak_summary'),
    url(r'^my_fragmentation_sets/(?P<fragmentation_set_name_id>[\w\-]+)'
        r'/(?P<peak_name_id>[\w\-]+)/msn_spectra_plot.png/$', views.make_frag_spectra_plot, name="make_spectra_plot"),
    url(r'^my_fragmentation_sets/(?P<fragmentation_set_name_id>[\w\-]+)/(?P<peak_name_id>[\w\-]+)'
        r'/(?P<annotation_id>[\w\-]+)/specify_preferred_annotation/$',
        views.specify_preferred_annotation, name='specify_preferred_annotation'),
    url(r'^remove_preferred_annotations/(?P<fragmentation_set_name_id>[\w\-]+)',
        views.remove_preferred_annotations, name='remove_preferred_annotations'),
    url(r'^delete_annotation_query/(?P<fragmentation_set_name_id>[\w\-]+)'
        r'/(?P<annotation_query_id>[\w\-]+)/$',views.delete_annotation_query, name='delete_annotation_query'),

    #ChemSpider url
    url(r'^chemspider_info/(?P<compound_id>[\w\-]+)/$',
        views.get_chemspider_info, name='get_chemspider_info'),

    # Network sample URL added by Simon
    url(r'^network_sampler/$',views.run_network_sampler, name='network_sampler'),

)
