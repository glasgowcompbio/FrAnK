__author__ = "Scott Greig"

from django.conf import settings
from frank.models import Peak, SampleFile, CandidateAnnotation, Compound, AnnotationTool, \
    CompoundAnnotationTool, FragmentationSet, Experiment, AnnotationQuery
from djcelery import celery
from celery import chain
from celery.utils.log import get_task_logger
from decimal import *
from frank.peakFactories import MSNPeakBuilder
from suds.client import WebFault
import os
import sys
import logging
from frank.models import *
from frank.fragfile_extraction import *
import frank.network_sampler as ns
import jsonpickle
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned, ValidationError
from frank.annotationTools import MassBankQueryTool, NISTQueryTool, MAGMAQueryTool
from urllib2 import URLError
import datetime
from decimal import *
import pandas as pd
import numpy as np

import requests,json
import pandas as pd

from lxml import etree
import lxml.sax
from xml.sax.handler import ContentHandler

celery_logger = get_task_logger(__name__)
logger = logging.getLogger(__name__)

class MyContentHandler(ContentHandler):
    def __init__(self):
        self.scan_amount = 0
        self.polarity = None
        self.polarity_found = False

    def startElementNS(self, name, qname, attributes):
        uri, localname = name
        if localname == 'scan':
            self.scan_amount += 1
            if self.scan_amount == 1 :
                attrs = {}
                try:
                    iter_attributes = attributes.iteritems()
                except AttributeError:
                    iter_attributes = attributes.items()
                for name_tuple, value in iter_attributes:
                    if name_tuple[1] == 'polarity':
                      self.polarity = value
        elif localname == 'spectrum':
            self.scan_amount += 1
        elif localname == 'cvParam':
            if not self.polarity_found:
                attrs = {}
                try:
                    iter_attributes = attributes.iteritems()
                except AttributeError:
                    iter_attributes = attributes.items()
                for name_tuple, value in iter_attributes:
                    if (name_tuple[1] == 'value' and str(value) == 'Positive') or \
                            (name_tuple[1] == 'name' and str(value) == 'positive scan'):
                        self.polarity = "+"
                        self.polarity_found = True
                    elif (name_tuple[1] == 'value' and str(value) == 'Negative') or \
                            (name_tuple[1] == 'name' and str(value) == 'negative scan'):
                        self.polarity = "-"
                        self.polarity_found = True

def findpolarity(file):
    tree = etree.parse(file)
    handler = MyContentHandler()
    lxml.sax.saxify(tree, handler)
    return handler.polarity


# Return the correct annotation Tool given it's id.
def get_annotation_tool(name):
    annotation_tool = AnnotationTool.objects.get(name=name)
    return annotation_tool


# Create and return annotation query given the correct parameters
def get_annotation_query(fragSet, name, tool_name, params):
    annotation_query, created = AnnotationQuery.objects.get_or_create(
        name=fragSet.name + name,
        fragmentation_set=fragSet,
        annotation_tool=get_annotation_tool(tool_name),
        annotation_tool_params=jsonpickle.encode(params))

    return annotation_query


# Method to run a set of default annotations and set the preferred annotations to the highest
# confidence level (clean methods) - currently used for PiMP/FrAnK intergration
@celery.task
def run_default_annotations(fragSet, user):

    logger.info("In default annotations")
    # Parameters for nist annotation tool
    default_params_nist = {"search_type": "G",
                           "library": ["mona_export_msms", "massbank_msms"],
                           "max_hits": 10}
    # Create nist_query
    nist_query = get_annotation_query(fragSet, "-MSPepSearchQ", "MSPepSearch", default_params_nist)

    # Run the nist search for annotations
    logger.info("running Nist from default")
    nist_batch_search(nist_query.id)

    # Create a precursor mass query using the annotations from the NIST search
    pre_default_params = {"parents": [str(nist_query.id)],
                          "positive_transforms": ["M+H"],
                          "negative_transforms": ["M-H"],
                          "mass_tol": 5}
    precursor_query = get_annotation_query(fragSet, "-preFQ", "Precursor Mass Filter", pre_default_params)

    # Run the precursor mass filter to remove any results that differ from the m/z by a certain threshold
    logger.info("running precursor mass query from default")
    precursor_mass_filter(precursor_query.id)

    # Create a relationship between the parent and child annotations
    AnnotationQueryHierarchy.objects.create(
        parent_annotation_query=nist_query,
        subquery_annotation_query=precursor_query)

    # Create a run to remove duplicate annotations for a peak, setting the preferred annotation automatically
    clean_default_params = {}
    clean_default_params['parents'] = [str(precursor_query.id)]
    clean_default_params['preferred_threshold'] = Decimal(50)
    clean_default_params['delete_original'] = False
    clean_default_params['do_preferred'] = True
    clean_default_params['collapse_multiple'] = True

    clean_query = get_annotation_query(fragSet, "-cleanQ", "Clean Annotations", clean_default_params)
    clean_filter(clean_query.id, user)

    #Create a relationship between the parent and child annotations
    AnnotationQueryHierarchy.objects.get_or_create(
        parent_annotation_query=precursor_query,
        subquery_annotation_query=clean_query)

    logger.info("At the end of the default annotations run")


@celery.task
def runNetworkSampler(annotation_query_id):
    # def runNetworkSampler(fragmentation_set_id, sample_file_name, annotation_query_id):
    """
    Method to run the Network Sampler developed by Simon Rogers
    :author Simon Rogers
    :param fragmentation_set_id: A string containing the unique id for the fragmentation set
    :param sample_file_name: A string for the sample file name
    :param annotation_query_id: A string containing the unique id for the annotation query
    :return: edge_dict:
    """
    new_annotation_query = AnnotationQuery.objects.get(id=annotation_query_id)
    parameters = jsonpickle.decode(new_annotation_query.annotation_tool_params)
    fragmentation_set = new_annotation_query.fragmentation_set
    # fragmentation set is the fragmentation set we want to run the analysis on (id)
    # annotation_query is the new annotation query id
    # fragmentation_set = FragmentationSet.objects.get(id=fragmentation_set_id)
    parent_annotation_query = AnnotationQuery.objects.filter(id__in=parameters['parents'])[0]
    # parent_annotation_query = new_annotation_query.parent_annotation_query
    # sample_file = SampleFile.objects.filter(name=sample_file_name)
    # check if the new annotation query already has annotations attached and delete them if it does
    # might want to remove this at some point, but it's useful for debugging
    old_annotations = CandidateAnnotation.objects.filter(annotation_query=new_annotation_query)
    if old_annotations:
        logger.info("Deleting old annotations...")
        for annotation in old_annotations:
            annotation.delete()

    new_annotation_query.status = 'Submitted'
    new_annotation_query.save()
    # Extract the peaks
    # peaks = Peak.objects.filter(fragmentation_set=fragmentation_set, msn_level=1, source_file=sample_file)
    peaks = Peak.objects.filter(fragmentation_set=fragmentation_set, msn_level=1)
    logger.info("Found " + str(len(peaks)) + " peaks")

    peakset = ns.FragSet()
    peakset.compounds = []

    logger.info("Extracting peaks")
    # for i in range(100):
    for p in peaks:
        # p = peaks[i]
        newmeasurement = ns.Measurement(p.id)
        peakset.measurements.append(newmeasurement)
        # Loop over all candidate annotations for this peak
        all_annotations = CandidateAnnotation.objects.filter(peak=p, annotation_query=parent_annotation_query)
        for annotation in all_annotations:
            # split the name up - THIS WILL BE REMOVED
            split_name = annotation.compound.name.split(';')
            short_name = split_name[0]
            # find this one in the previous ones
            previous_compound = [n for n in peakset.compounds if n.name == short_name]
            if len(previous_compound) == 0:
                peakset.compounds.append(ns.Compound(annotation.compound.id, annotation.compound.formula, short_name))
                newmeasurement.annotations[ns.Annotation(peakset.compounds[-1], annotation.id)] = float(
                    annotation.confidence)
            else:
                this_compound = previous_compound[0]
                # Have we seen this compound in this measurement at all?
                previous_annotation_local = [n for n in newmeasurement.annotations if n.compound == this_compound]
                if len(previous_annotation_local) > 0:
                    this_annotation = previous_annotation_local[0]
                    this_annotation.parentid = annotation.id
                    newmeasurement.annotations[this_annotation] = float(annotation.confidence)
                else:
                    newmeasurement.annotations[ns.Annotation(this_compound, annotation.id)] = float(
                        annotation.confidence)


                    # previous_annotations = [n for n in newmeasurement.annotations if n.name==short_name]
                    # if len(previous_annotations) == 0:
                    #     # ADD A COMPOUND ID
                    #     peakset.annotations.append(ns.Annotation(annotation.compound.formula,short_name,annotation.compound.id,annotation.id))
                    #     newmeasurement.annotations[peakset.annotations[-1]] = float(annotation.confidence)
                    # else:
                    #     # check if this measurement has had this compound in its annotation before
                    #     # (to remove duplicates with different collision energies - highest confidence is used)
                    #     this_annotation = previous_annotations[0]
                    #     current_confidence = newmeasurement.annotations[this_annotation]
                    #     if float(annotation.confidence) > current_confidence:
                    #         newmeasurement.annotations[this_annotation] = float(annotation.confidence)
                    #         this_annotation.parentid = annotation.id

    logger.info("Stored " + str(len(peakset.measurements)) + " peaks and " + str(len(peakset.compounds)) + " unique compounds")

    print "Sampling..."
    sampler = ns.NetworkSampler(peakset)
    sampler.set_parameters(parameters)
    sampler.sample()

    new_annotation_query.status = 'Processing'
    new_annotation_query.save()
    print "Storing new annotations..."
    # Store new annotations in the database
    for m in peakset.measurements:
        peak = Peak.objects.get(id=m.id)
        for annotation in m.annotations:
            compound = Compound.objects.get(id=annotation.compound.id)
            parent_annotation = CandidateAnnotation.objects.get(id=annotation.parentid)
            add_info_string = "Prior: {:5.4f}, Edges: {:5.2f}".format(peakset.prior_probability[m][annotation],
                                                                      peakset.posterior_edges[m][annotation])
            an = CandidateAnnotation.objects.create(compound=compound, peak=peak,
                                                    confidence=peakset.posterior_probability[m][annotation],
                                                    annotation_query=new_annotation_query,
                                                    difference_from_peak_mass=parent_annotation.difference_from_peak_mass,
                                                    mass_match=parent_annotation.mass_match,
                                                    additional_information=add_info_string)

    edge_dict = sampler.global_edge_count()
    new_annotation_query.status = 'Completed Successfully'
    new_annotation_query.save()
    return edge_dict


@celery.task
def msn_generate_peak_list(experiment_id, fragmentation_set_id, ms1_df):
    """
    Method to extract peak data from a collection of sample files
    :param experiment_id: Integer id of the experiment from which the files orginate
    :param fragmentation_set_id:    Integer id of the fragmentation set to be populated
    :return: True   Boolean value denoting the completion of the task
    Passing the MS1 peaks from Pimp when they are run together.
    """
    logger.info('In MSN generate peak list')
    # Determine the directory of the experiment
    experiment_object = Experiment.objects.get(pk=experiment_id)
    experimental_condition = ExperimentalCondition.objects.filter(experiment=experiment_object)[0]
    sample = Sample.objects.filter(experimental_condition=experimental_condition)[0]

    # Filepath takes us to the directory above the polarity dirs (Positive and Negative)
    # in which the files are stored.
    filepath = os.path.join(
        settings.MEDIA_ROOT,
        'frank',
        experiment_object.created_by.username,
        str(experiment_object.id),
        str(experimental_condition.id),
        str(sample.id)
    )
    logger.info("The fragment filepath is %s ", filepath)
    # Get the fragmentation set object from the database
    fragmentation_set_object = FragmentationSet.objects.get(id=fragmentation_set_id)

    # Update the status of the task for the user
    fragmentation_set_object.status = 'Processing'
    fragmentation_set_object.save()

    polarity_dirs = os.listdir(filepath)

    if ms1_df is None:
        logger.info("Running stand-alone FrAnK, no PiMP MS1 peaks")
        for d in polarity_dirs: #For each polarity directory
            process_and_populate(filepath, d, ms1_df, fragmentation_set_object, experiment_id)

    else: #We have passed MS1 peaks from PIMP
        logger.info("Running FrAnK from PiMP using PiMP MS1 peaks")

        df_polarity = ms1_df.polarity.unique() #The unique polarity passed from the integrated system
        if df_polarity == 'negative':
            d = 'Negative'
        elif df_polarity == 'positive':
            d = 'Positive'
        else:
            logger.error("A horrible polarity problem has arisen")

        # If matching fragments have been loaded process the fragments
        if d in polarity_dirs:
            process_and_populate(filepath, d, ms1_df, fragmentation_set_object, experiment_id)

    # Upon completion the status of the fragmentation set is updated, to inform the user of completion
    fragmentation_set_object.status = 'Completed Successfully'
    fragmentation_set_object.save()

def process_and_populate(filepath, dir, ms1_df, frag_set_object, experiment_id):

    filepath_pol = os.path.join(filepath, dir)
    files = os.listdir(filepath_pol)

    logger.info('The current filepath is %s and the files are %s', filepath_pol, files)

    #For stand-alone FrAnK we may have several of each files in the polarity folders.
    for f in files:
        input_file = os.path.join(filepath_pol, f)
        logger.info("The input file is %s", input_file)

        if ms1_df is None:
            mzML_loader = LoadMZML()
        else:
            del ms1_df['polarity']  # Delete the polarity column to pass to ffile_extraction
            ms1_peaks = ms1_df.values.tolist() #Prepare the peaklist
            #We are not filtering out duplicates and have set the max_ms1_rt to 4000 when the peaks are passed from PiMP
            mzML_loader = LoadMZML(peaklist=ms1_peaks, min_ms1_intensity=-10, max_ms1_rt = 4000, duplicate_filter=True)

        output = mzML_loader.load_spectra(input_file)

        try:
            # Pass the experiment id in order to grab the experiment.
            peak_generator = MSNPeakBuilder(output, frag_set_object.id, experiment_id)
            # peak_generator = MSNPeakBuilder(output, fragmentation_set_object.id)
            # Each of sub class of the 'Abstract' PeakBuilder class will have the populate_database_peaks() method
            peak_generator.populate_database_peaks()

        # Should the addition of the peaks to the database fail, the exceptions are passed back up
        # and the status is updated.
        except Exception as e:
            logger.error("An error has occurred populating the DB: %s", e.message)
            frag_set_object.status = 'Completed with Errors'
            raise

@celery.task
def massbank_batch_search(annotation_query_id):
    """
    Method to query the MassBank spectral reference library
    :param annotation_query_id: Integer id of the annotation query to be performed
    :return: True   Boolean denoting the completion of the query
    """

    # Get the annotation query object and update the status to update the user
    annotation_query = AnnotationQuery.objects.get(id=annotation_query_id)
    annotation_query.status = 'Processing'
    annotation_query.save()
    # Derive the associated fragmentation set from the annotation query
    fragmentation_set = annotation_query.fragmentation_set
    try:
        # The MassBank query tool performs the formatting, sending of the query and population of the database
        mass_bank_query_tool = MassBankQueryTool(annotation_query_id, fragmentation_set.id)
        mass_bank_query_tool.get_mass_bank_annotations()
        annotation_query.status = 'Completed Successfully'
    # In order to inform the user of any errors, exceptions are raised and the status is reflected
    # to reflect the end of the process
    except:
        annotation_query.status = 'Completed with Errors'
        raise
    finally:
        annotation_query.save()
    return True


@celery.task
def nist_batch_search(annotation_query_id):
    """
    Method to retrieve candidate annotations from the NIST spectral reference library
    :param annotation_query_id: Integer id of the annotation query to be performed
    :return: True:  Boolean indicating the completion of the task
    """

    # Get the annotation object to be performed and update the process status for the user
    logger.info("In the Nist batch search")
    annotation_query = AnnotationQuery.objects.get(id=annotation_query_id)
    annotation_query.status = 'Processing'
    annotation_query.save()
    try:
        # A NIST query tool, is used to write the query files to a temporary file, which
        # NIST uses to generate candidate annotations which are written to a temporary file
        # The NIST query tool updates the database from the NIST output file.
        nist_annotation_tool = NISTQueryTool(annotation_query_id)
        nist_annotation_tool.get_nist_annotations()
        annotation_query.status = 'Completed Successfully'
        # As before, to prevent to maintain the celery workers, any errors which cannot be resolved
        # by the NISTQueryTool are raised and the status of the task is updated.
    except:
        annotation_query.status = 'Completed with Errors'
        raise
    finally:
        annotation_query.save()
    logger.info("Completed the NIST batch search")


# """
# SIRIUS details added by Karen
# """
#
#
# @celery.task
# def sirius_batch_search(annotation_query_id):
#     print 'In batch search'
#
#     """
#     Method to retrieve candidate annotations from the NIST spectral reference library
#     :param annotation_query_id: Integer id of the annotation query to be performed
#     :return: True:  Boolean indicating the completion of the task
#     """
#
#     # Get the annotation object to be performed and update the process status for the user
#     annotation_query = AnnotationQuery.objects.get(id=annotation_query_id)
#     annotation_query.status = 'Processing'
#     annotation_query.save()
#     # Derive the associated fragmentation set from the annotation query
#     fragmentation_set = annotation_query.fragmentation_set
#
#     try:
#         print ('Print anything in tasks')
#         # A SIRIUS query tool, is used to write the query files to a temporary file, which
#         # SIRIUS uses to generate candidate annotations which are written to a temporary file
#         # The SIRIUS query tool updates the database from the SIRIUS output file.
#         sirius_annotation_tool = SIRIUSQueryTool(annotation_query_id, fragmentation_set.id)
#         sirius_annotation_tool.get_sirius_annotations
#         annotation_query.status = 'Completed Successfully'
#         # As before, to prevent to maintain the celery workers, any errors which cannot be resolved
#         # by the SIRIUSQueryTool are raised and the status of the task is updated.
#     except:
#         annotation_query.status = 'Completed with Errors'
#         raise
#     finally:
#         annotation_query.save()
#     return True


@celery.task
def magma_batch_search(annotation_query_id):

    logger.info('In magma batch search')

    """
    Method to retrieve candidate annotations from the MAGMA spectral reference library
    :param annotation_query_id: Integer id of the annotation query to be performed
    :return: True:  Boolean indicating the completion of the task
    """

    # Get the annotation object to be performed and update the process status for the user
    annotation_query = AnnotationQuery.objects.get(id=annotation_query_id)
    annotation_query.status = 'Processing'
    annotation_query.save()
    # Derive the associated fragmentation set from the annotation query
    fragmentation_set = annotation_query.fragmentation_set

    try:
        logger.info('Passing to the MAGMA tool')
        #9June16:KMcL: At this stage we are assuming MAGMA will work similarly to SIRIUS
        #described below...comments taken from SIRIUS & might change...
        # A MAGMA query tool, is used to write the query files to a temporary file, which
        # MAGMA uses to generate candidate annotations which are written to a temporary file
        # The MAGMA query tool updates the database from the MAGMA output file.
        magma_annotation_tool = MAGMAQueryTool(annotation_query_id, fragmentation_set.id)
        magma_annotation_tool.get_magma_annotations()
        annotation_query.status = 'Completed Successfully'
        # As before, to prevent to maintain the celery workers, any errors which cannot be resolved
        # by the MAGMAQueryTool are raised and the status of the task is updated.
    except:
        annotation_query.status = 'Completed with Errors'
        raise
    finally:
        annotation_query.save()
    return True



"""
The following are additions by Simon Rogers
"""
# This really should not be here! - Simon's Addition
# In both of the following, the first number is subtracted from the observed mass
# and the second number is divided
# hence the first number is the total mass gain of the adduct (including any reduction in electrons), divided by the charge
# and the second number is the reciprocal of the charge
POSITIVE_TRANSFORMATIONS = {
    "M+2H": [1.00727645199076, 0.5, 0.0],
    "M+H+NH4": [9.52055100354076, 0.5, 0.0],
    "M+H+Na": [11.99824876604076, 0.5, 0.0],
    "M+H+K": [19.98521738604076, 0.5, 0.0],
    "M+ACN+2H": [21.520551003540763, 0.5, 0.0],
    "M+2Na": [22.98922108009076, 0.5, 0.0],
    "M+H": [1.00727645199076, 1.0, 0.0],
    "M+HC13": [1.00727645199076, 1.0, -1.00335],
    "M+H2C13": [1.00727645199076, 1.0, -2.00670],
    "M+NH4": [18.03382555509076, 1.0, 0.0],
    "M+Na": [22.98922108009076, 1.0, 0.0],
    "M+NaC13": [22.98922108009076, 1.0, -1.00335],
    "M+CH3OH+H": [33.033491201890754, 1.0, 0.0],
    "M+K": [38.963158320090756, 1.0, 0.0],
    "M+KC13": [38.963158320090756, 1.0, -1.00335],
    "M+ACN+H": [42.03382555509076, 1.0, 0.0],
    "M+2Na-H": [44.97116570819076, 1.0, 0.0],
    "M+IsoProp+H": [61.06479132949075, 1.0, 0.0],
    "M+ACN+Na": [64.01577018319077, 1.0, 0.0],
    "M+2K-H": [76.91904018819076, 1.0, 0.0],
    "M+DMSO+H": [79.02121199569076, 1.0, 0.0],
    "M+2ACN+H": [83.06037465819077, 1.0, 0.0],
}
# TODO: add some more of these
NEGATIVE_TRANSFORMATIONS = {
    "M-H": [-1.00727645199076, 1.0, 0.0],
    "M-2H": [-1.00727645199076, 0.5, 0.0],
}


@celery.task
def precursor_mass_filter(annotation_query_id):
    # Runs a filter on the annotations
    import math
    logger.info('In the precursor mass-filter tool')
    annotation_query = AnnotationQuery.objects.get(id=annotation_query_id)
    annotation_query.status = 'Processing'
    annotation_query.save()

    parameters = jsonpickle.decode(annotation_query.annotation_tool_params)
    parent_annotation_queries = AnnotationQuery.objects.filter(id__in=parameters['parents'])
    positive_transforms_to_use = parameters['positive_transforms']
    negative_transforms_to_use = parameters['negative_transforms']
    mass_tol = parameters['mass_tol']

    fragmentation_set = annotation_query.fragmentation_set
    peaks = Peak.objects.filter(fragmentation_set=fragmentation_set,
                                msn_level=1, source_file__polarity='Positive')
    for peak in peaks:
        peak_annotations = CandidateAnnotation.objects.filter(peak=peak, annotation_query__in=parent_annotation_queries)
        for a in peak_annotations:
            for t in positive_transforms_to_use:
                transformed_mass = (float(peak.mass) - POSITIVE_TRANSFORMATIONS[t][0]) / POSITIVE_TRANSFORMATIONS[t][
                    1] + POSITIVE_TRANSFORMATIONS[t][2]
                mass_error = 1e6 * math.fabs(transformed_mass - float(a.compound.exact_mass)) / transformed_mass
                if mass_error < mass_tol:
                    new_annotation = CandidateAnnotation(peak=peak,
                                                         annotation_query=annotation_query, compound=a.compound,
                                                         mass_match=True, confidence=a.confidence,
                                                         difference_from_peak_mass=peak.mass - a.compound.exact_mass,
                                                         adduct=t,
                                                         instrument_type=a.instrument_type,
                                                         collision_energy=a.collision_energy,
                                                         additional_information=a.additional_information)
                    new_annotation.save()

    peaks = Peak.objects.filter(fragmentation_set=fragmentation_set,
                                msn_level=1, source_file__polarity='Negative')
    for peak in peaks:
        peak_annotations = CandidateAnnotation.objects.filter(peak=peak, annotation_query__in=parent_annotation_queries)
        for a in peak_annotations:
            for t in negative_transforms_to_use:
                transformed_mass = (float(peak.mass) - NEGATIVE_TRANSFORMATIONS[t][0]) / NEGATIVE_TRANSFORMATIONS[t][
                    1] + NEGATIVE_TRANSFORMATIONS[t][2]
                mass_error = 1e6 * math.fabs(transformed_mass - float(a.compound.exact_mass)) / transformed_mass
                if mass_error < mass_tol:
                    new_annotation = CandidateAnnotation(peak=peak,
                                                         annotation_query=annotation_query, compound=a.compound,
                                                         mass_match=True, confidence=a.confidence,
                                                         difference_from_peak_mass=peak.mass - a.compound.exact_mass,
                                                         adduct=t,
                                                         instrument_type=a.instrument_type,
                                                         collision_energy=a.collision_energy,
                                                         additional_information=a.additional_information)
                    new_annotation.save()

    annotation_query.status = "Completed Successfully"
    annotation_query.save()
    logger.info("At the end of the Precursor tool, saved,")


"""
End of additions by Simon Rogers
"""


@celery.task
def clean_filter(annotation_query_id, user):
    # This cleans a set of annotations by only keeping one annotation for each compound for each peak
    # and only keeping annotations above a threshold
    # the highest confidence annotation (abover the threshold) is set as the preferred annotation)
    logger.info("In the clean filter tool")
    annotation_query = AnnotationQuery.objects.get(id=annotation_query_id)
    annotation_query.status = 'Processing'
    annotation_query.save()
    parameters = jsonpickle.decode(annotation_query.annotation_tool_params)
    parent_annotation_queries = AnnotationQuery.objects.filter(id__in=parameters['parents'])
    preferred_threshold = parameters['preferred_threshold']

    # # Following does nothing yet
    # delete_original = parameters['delete_original']

    # Following is true if the user wants the preferred annotations set
    do_preferred = parameters['do_preferred']

    # Following is true if we should collapse multiple instances of the same compound
    collapse_multiple = parameters['collapse_multiple']

    fragmentation_set = annotation_query.fragmentation_set
    peaks = Peak.objects.filter(fragmentation_set=fragmentation_set,
                                msn_level=1)

    for peak in peaks:
        peak_annotations = CandidateAnnotation.objects.filter(peak=peak, annotation_query__in=parent_annotation_queries)
        found_compounds = {}
        best_annotation = None
        for annotation in peak_annotations:
            if annotation.compound in found_compounds:
                this_annotation = found_compounds[annotation.compound]
                if annotation.confidence > this_annotation.confidence:
                    this_annotation.confidence = annotation.confidence
                    this_annotation.instrument_type = annotation.instrument_type
                    this_annotation.collision_energy = annotation.collision_energy
                    this_annotation.save()
                    logger.info("Saving preferred annotation")
                    if this_annotation.confidence > best_annotation.confidence:
                        best_annotation = this_annotation

            else:
                if annotation.confidence > preferred_threshold:
                    new_annotation = CandidateAnnotation(peak=peak,
                                                         annotation_query=annotation_query,
                                                         compound=annotation.compound,
                                                         mass_match=annotation.mass_match,
                                                         confidence=annotation.confidence,
                                                         difference_from_peak_mass=peak.mass - annotation.compound.exact_mass,
                                                         adduct=annotation.adduct,
                                                         instrument_type=annotation.instrument_type,
                                                         collision_energy=annotation.collision_energy)
                    new_annotation.save()
                    if collapse_multiple:
                        found_compounds[annotation.compound] = new_annotation
                    if best_annotation == None:
                        best_annotation = new_annotation
                    else:
                        if new_annotation.confidence > best_annotation.confidence:
                            best_annotation = new_annotation
        if do_preferred:
            peak.preferred_candidate_annotation = best_annotation
            peak.preferred_candidate_description = "Added automatically with annotation query {} with threshold of {}".format(
                annotation_query.name, preferred_threshold)
            peak.preferred_candidate_user_selector = user
            peak.preferred_candidate_updated_date = datetime.datetime.now()
            peak.save()

    annotation_query.status = 'Completed Successfully'
    annotation_query.save()
    logger.info("At the end of the clean filter tool")