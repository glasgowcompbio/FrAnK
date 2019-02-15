import logging

import jsonpickle
from django.core.management.base import BaseCommand

from frank.models import AnnotationTool, ExperimentalProtocol, AnnotationToolProtocol

logger = logging.getLogger('frank.management.commands.populate_parameters')


def populate(apps, schema_editor):
    NIST_annotation_tool = add_annotation_tool(
        name='MSPepSearch',
        default_params={
            'source': 'C:\\2013_06_04_MSPepSearch_x32\\MSPepSearch.exe',
            'library_path': 'C:\\NIST14\\MSSEARCH',
        }
    )

    MS2LDA_annotation_tool = add_annotation_tool(
        name='MS2LDA',
        default_params={},
    )

    MAGMA_annotation_tool = add_annotation_tool(
        name='MAGMa',
        default_params={},
    )

    # this needs to be filled in properly
    precursor_mass_filter_annotation_tool = add_annotation_tool(
        name='Precursor Mass Filter',
        default_params={},
    )

    clean_annotation_tool = add_annotation_tool(
        name='Clean Annotations',
        default_params={},
    )

    lcms_dda_experimental_protocol = add_experimental_protocol(
        name='Liquid-Chromatography Mass-Spectroscopy'
    )

    # gcms_dia_experimental_protocol = add_experimental_protocol(
    #     name='Gas-Chromatography Mass-Spectroscopy Electron Impact Ionisation'
    # )

    # lcms_dia_experimental_protocol = add_experimental_protocol(
    #     name = 'Liquid-Chromatography Data-Independent Acquisition'
    # )

    add_annotation_tool_protocols(
        [lcms_dda_experimental_protocol],
        NIST_annotation_tool
    )

    add_annotation_tool_protocols(
        [lcms_dda_experimental_protocol],
        MS2LDA_annotation_tool
    )

    add_annotation_tool_protocols(
        [lcms_dda_experimental_protocol],
        MAGMA_annotation_tool
    )

    # this needs to be filled in properly
    add_annotation_tool_protocols(
        [lcms_dda_experimental_protocol], precursor_mass_filter_annotation_tool
    )

    add_annotation_tool_protocols(
        [lcms_dda_experimental_protocol],
        clean_annotation_tool
    )


def add_annotation_tool(name, default_params):
    default_params = jsonpickle.encode(default_params)
    annotation_tool = AnnotationTool.objects.get_or_create(
        name=name,
        default_params=default_params,
    )[0]
    # print 'Creating default annotation tool - '+name+'...'
    annotation_tool.save()
    return annotation_tool


def add_experimental_protocol(name):
    experimental_protocol = ExperimentalProtocol.objects.get_or_create(
        name=name,
    )[0]
    # print 'Creating experimental protocol - '+name+'...'
    experimental_protocol.save()
    return experimental_protocol


def add_annotation_tool_protocols(protocols_list, annotation_tool):
    for protocol in protocols_list:
        # print 'Adding '+protocol.name+' to Annotation Tool '+annotation_tool.name
        annotation_tool_protocol = AnnotationToolProtocol.objects.get_or_create(
            annotation_tool=annotation_tool,
            experimental_protocol=protocol
        )


class Command(BaseCommand):
    help = 'Initialises Database with Parameters'

    def handle(self, *args, **options):
        logger.info('Starting initial database parameter population')
        populate(None, None)
        logger.info('Initial database parameter population done')
