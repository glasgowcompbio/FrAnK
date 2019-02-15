__author__ = 'Scott Greig'

from frank.models import *
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned, ValidationError
from decimal import *
from suds.client import Client, WebFault
import time
import jsonpickle
import re
from django.conf import settings
from subprocess import call, CalledProcessError
import os
import logging
from django.db.models import Max
from django.db import transaction
import math
from urllib2 import URLError


#Sirius specific imports
import tempfile
import platform
import subprocess
import shutil
import json
import pprint

#MAGMa specific imports
import pickle
import zlib
#import sqlite3
#import unittest
import argparse
import pkg_resources
from StringIO import StringIO

#from rdkit import Chem

from chemspipy import ChemSpider
from celery.utils.log import get_task_logger
logger = logging.getLogger(__name__)

MASS_OF_A_PROTON = 1.00727645199076
NEGATIVE = "-1"
POSITIVE = "1" #Constants for the inonisation modes used the tools
MASS_TOL = 5 #5 ppm.

#A constant to represent a peak intensity that has been set to -0.25 previousy
#Add 0.000001 onto the value when used to stop duplicate entries.
PSEUDO_PARENT_INTENSITY = 123456.123456
#For Old versions of FrAnK need to deal with - 0.25
SET_TO_NEG_2_5 = -0.25

import errno

def make_sure_path_exists(path):
    print "Make sure path exists: ", path
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise
# Returns True or False depending on wether or not the annotation mass matches the peak.
def get_mass_match(peak, annot_mass):

    positive_m_h = [1.00727645199076, 1.0, 0.0]
    negative_m_h = [-1.00727645199076, 1.0, 0.0]

    if peak.source_file.polarity =="Positive":
        transformed_mass = (float(peak.mass) - positive_m_h[0]) / positive_m_h[
            1] + positive_m_h[2]
    if peak.source_file.polarity == "Negative":
        transformed_mass = (float(peak.mass) - negative_m_h[0]) / negative_m_h[
            1] + negative_m_h[2]

    mass_error = 1e6 * math.fabs(transformed_mass - float(annot_mass)) / transformed_mass

    return mass_error < MASS_TOL

class MassBankQueryTool:

    """
    Class to query the external API for MassBank - can also be used when MassBank installed on internal server
    """

    def __init__(self, annotation_query_id, fragmentation_set_id):
        """
        Constructor for the MassBankQuery Tool
        :param annotation_query_id: Integer id of a AnnotationQuery model instance
        :param fragmentation_set_id: Integer id of a FragmentationSet model instance
        """

        # Check to ensure these id'd correspond to existing model instances
        self.annotation_query = AnnotationQuery.objects.get(id=annotation_query_id)
        self.fragmentation_set = FragmentationSet.objects.get(id=fragmentation_set_id)
        self.annotation_tool = self.annotation_query.annotation_tool

    def get_mass_bank_annotations(self):

        """
        Method to form a query to massbank for retrieval of candidate annotations
        :return: True:  Boolean indicating the completion of the query
        """

        print 'Forming MassBank Query Spectra'
        # The query spectra comprise grouping of parent ions and there associated fragments
        query_spectra = self._generate_query_spectra()
        # While MassBank allows for 'pooled' query spectra to be sent, it was determined that it would
        # be better to send the positive and negative spectra separately to improve candidate annotations.
        positive_spectra = None
        negative_spectra = None
        if query_spectra:
            positive_spectra = query_spectra['positive_spectra']
            negative_spectra = query_spectra['negative_spectra']
        else:
            raise ValidationError('No spectra to be queried')
        print 'Querying MassBank...'
        # Queries are only sent to MassBank if there are spectra to be sent
        if len(positive_spectra) > 0:
            print 'Sending Positive Spectra...'
            # The positive spectra query is then sent to MassBank
            positive_annotations = self._query_mass_bank(positive_spectra, 'Positive')
            if positive_annotations:
                print 'Populating Positive Annotations...'
                # Candidate annotations are populated into the database
                self._populate_annotations_table(positive_annotations)
                print 'Positive Annotations Populated...'
        if len(negative_spectra) > 0:
            print 'Sending Negative Spectra...'
            # The negative spectra query is then sent to MassBank
            negative_annotations = self._query_mass_bank(negative_spectra, 'Negative')
            if negative_annotations:
                print 'Populating Negative Annotations...'
                # The candidate annotations are populated into the database
                self._populate_annotations_table(negative_annotations)
                print 'Negative Annotations Populated...'
        print 'MassBank Query Completed Successfully'
        return True

    def _generate_query_spectra(self):

        """
        Method to format the query to be sent to MassBank
        :return: query_spectra: A dictionary containing both the 'positive_spectra' and 'negative_spectra'
                                of the fragmentation set.
        """

        # Retrieve all peak associated with this fragmentation set
        sample_peak_qset = Peak.objects.filter(fragmentation_set=self.fragmentation_set)
        total_number_of_peaks = len(sample_peak_qset)
        # If there are no peaks then there is no query_spectra
        if total_number_of_peaks == 0:
            return None
        number_of_msn_levels = sample_peak_qset.aggregate(Max('msn_level'))
        number_of_msn_levels = number_of_msn_levels['msn_level__max']
        positive_samples_query = []
        negative_samples_query = []
        # Each msn level is considered in turn
        for level in range(1, number_of_msn_levels):
            # Get all the peaks in the level
            peaks_in_msn_level = sample_peak_qset.filter(msn_level=level)
            # For each peak in the msn level
            for peak in peaks_in_msn_level:
                # Retrieve the polarity and id
                # As the id is unique, it is used to associate a query spectra back to the parent ion
                polarity = peak.source_file.polarity
                peak_identifier = peak.id
                # Retrieve the fragments associated with the precursor peak
                fragmented_peaks = sample_peak_qset.filter(parent_peak=peak)
                # Only if there are fragments is the spectra added to the query
                if len(fragmented_peaks) > 0:
                    spectrum_query_string = list('Name:'+str(peak_identifier)+';')
                    for fragment in fragmented_peaks:
                        # The fragmentation spectra consists of mass and intensity pairs
                        spectrum_query_string.append(''+str(fragment.mass)+','+str(fragment.intensity)+';')
                    if polarity == 'Positive':
                        positive_samples_query.append(''.join(spectrum_query_string))
                    elif polarity == 'Negative':
                        negative_samples_query.append(''.join(spectrum_query_string))
        query_spectra = {
            'positive_spectra': positive_samples_query,
            'negative_spectra': negative_samples_query,
        }
        return query_spectra

    def _query_mass_bank(self, query_spectra, polarity):

        """
        Method to send the query to mass bank and retrieve the candidate annotation as a results set
        :return: mass_bank_results: The result set returned by mass_bank
        """

        # Check to ensure there are spectra to send to mass bank
        if len(query_spectra) == 0:
            return None
        # The search parameters specified by the user are in the annotation query
        mass_bank_parameters = jsonpickle.decode(self.annotation_query.annotation_tool_params)
        # MassBank provides a service to email the recipiant upon completion of query
        mail_address = mass_bank_parameters['mail_address']
        # Spectra can be queried against pre-specified instrument types
        instruments = mass_bank_parameters['instrument_types']
        # The polarity of the spectra is included - although can be 'both'
        # However, positive and negative were separated to ensure candidate annotations match the polarity of
        # the query spectra
        ion = polarity
        # The default parameters for the tool itself are retrieved from the AnnotationTool
        # These can be modified in the population script (populate_pimp.py)
        search_parameters = jsonpickle.decode(self.annotation_tool.default_params)
        # Note - MassBank batch search of spectra is type '1'
        search_type = search_parameters['type']
        # The address required for the client is the MassBank server, again see population script, can be changed
        # there for change over to local install
        client_address = search_parameters['client']

        client_address = "http://massbank.ufz.de:80/api/services/MassBankAPI?wsdl"

        client = Client(client_address)
            # Submit the batch search to MassBank, a job ID is returned
        submission_response = client.service.execBatchJob(
            search_type,
            mail_address,
            query_spectra,
            instruments,
            ion,
        )

        job_id = submission_response
        job_list = [job_id]
        job_status = None
        for repetition in range(0, 200):
            # At present, the celery worker will sleep for 5 minutes between job status queries to MassBank,
            # for a total of 200 attempts, however, queries could occur at a higher frequency when a local install
            # is available. The 200 repetitions is due to the frequency with which the external service can be
            # busy at present. Therefore, jobs do not process immediately upon submission.
            time.sleep(300)
            # Query MassBank for the status of the job
            job_status = client.service.getJobStatus(job_list)
            print job_status

            if job_status['status'] == 'Completed':
                break
        # If, at the end of the repetitions, MassBank has failed to complete the job in the alloted time
        if job_status['status'] != 'Completed':
            raise ValidationError('MassBank Service Unavailable or Busy, No Results Returned.')
        else:  # MassBank completed the query
                # If the job has been completed, then retrieve the results from MassBank
            response3 = client.service.getJobResult(job_list)
            mass_bank_results = response3
        return mass_bank_results

    def _populate_annotations_table(self, annotation_results):

        """
        Method to populate the database tables of the application using the results generated from massbank
        :param annotation_results:  The results set returned by MassBank (in python this is a dictionary)
        :return: True   Indicates that the results of the query have been successfully added to the database
        """

        for result_set_dict in annotation_results:
            # A result_set corresponds to the candidate annotations for one peak's fragmentation spectra
            peak_identifier_id = result_set_dict['queryName']
            print 'Processing...'+peak_identifier_id
            annotations = result_set_dict['results']
            # The candidate annotations are stored in a list
            # Get the peak the candidate annotations are associated with
            peak_object = Peak.objects.get(pk=peak_identifier_id)
            for each_annotation in annotations:
                # The elements of the annotation title are separated by a '; '
                elements_of_title = re.split('; ', each_annotation['title'])
                try:
                    with transaction.atomic():
                        # Create a compound in the database if one does not already exist
                        compound_object = Compound.objects.get_or_create(
                            formula=each_annotation['formula'],
                            exact_mass=each_annotation['exactMass'],
                            name=elements_of_title[0],
                            # The first element of the title is always the compound name
                        )[0]
                        # And add the compound to the CompoundAnnotationTool table
                        compound_annotation_tool = CompoundAnnotationTool.objects.get_or_create(
                            compound=compound_object,
                            annotation_tool=self.annotation_tool,
                            annotation_tool_identifier=each_annotation['id'],
                        )[0]
                        annotation_mass = Decimal(each_annotation['exactMass'])
                        difference_in_mass = peak_object.mass-annotation_mass
                        mass_match = False
                        # By default the mass of the annotation does not match that of the peak
                        # However, if the difference in mass is within the mass of an electron, it may
                        # be considered a match in mass
                        if abs(difference_in_mass) <= MASS_OF_A_PROTON:
                            mass_match = True
                        # Try and obtain the adduct and collision energy from the description
                        adduct_label = None
                        collision_energy = None
                        """
                        Important to note that due to the open source nature of MassBank, there is a significant
                        variation in the format the candidate annotations are returned in. The adduct is typically
                        The last element of the title, however, this is not the case in all annotations. In addition,
                        the collision energy, may or may not be included, and the units of measurement may be either
                        eV or a percentage depending on the instrument manufacturer.

                        While eV is an exact measure of the collision energy, the % is a normalised collision energy
                        used by Thermo devices. Therefore, collision energy will be stored as a string including value and
                        units.

                        Therefore, the application will try and obtain the adduct and collision energy, where possible
                        to do so.
                        """
                        for element in elements_of_title:
                            if element.startswith('[M'):
                                adduct_label = element
                            if element.startswith('CE'):
                                try:
                                    collision_energy = re.split('CE:', element)[1].strip()
                                except IndexError:
                                    pass
                        # Finally create the candidate annotation in the database
                        CandidateAnnotation.objects.create(
                            compound=compound_object,
                            peak=peak_object,
                            confidence=each_annotation['score'],
                            annotation_query=self.annotation_query,
                            difference_from_peak_mass=difference_in_mass,
                            mass_match=mass_match,
                            adduct=adduct_label,
                            instrument_type=elements_of_title[1],
                            collision_energy=collision_energy,
                            additional_information=each_annotation['title']
                        )
                except ValidationError:
                    # If the annotation cannot be formatted to a model instance, it may be ignored
                    print 'Invalid Annotation - Annotation Ignored'
                    pass
                except MultipleObjectsReturned:
                    raise
                except InvalidOperation:
                    # If the annotation cannot be formatted to a model instance, it may be ignored
                    print 'Invalid Annotation - Annotation Ignored'
                    pass
        return True

"""
 Class to query MAGMA for annotations
 """
class MAGMAQueryTool:

    def __init__(self, annotation_query_id, fragmentation_set_id):

        logger.info('In MAGMA QUERYTOOL constructor')
        # Check to ensure the annotation query, associated fragmentation set and annotation tool exist
        self.annotation_query = AnnotationQuery.objects.get(id=annotation_query_id)
        self.fragmentation_set = FragmentationSet.objects.get(id=fragmentation_set_id)
        self.annotation_tool = self.annotation_query.annotation_tool

        # Determine suitable names for both the query file and magma output files
        self.query_tree = os.path.join(
            settings.INTERNAL_MAGMA_QUERY_DIR,
            str(self.annotation_query.id)+'.tree'
        )
        self.magma_output_file = os.path.join(
            settings.INTERNAL_MAGMA_QUERY_DIR,
            str(self.annotation_query.id)+'_magma_result_dict.p'
        )

        self.result_db_name = str(self.annotation_query.id) + '_magma_result'
        self.all_peaks = Peak.objects.filter(fragmentation_set=self.fragmentation_set)
        self.all_parents = self.all_peaks.filter(msn_level=1)
        self.found_duplicates = [] #Stores duplicate parent id with frament info for duplicated, useful for debugging

    """
    Method to retrieve candidate annotations from MAGMa
    :return True:   Boolean denoting the successful completion of the MAGMa query for annotations
    """
    def get_magma_annotations(self):

        logger.info("Getting MAGMA annotations")

        magma_parameters = jsonpickle.decode(self.annotation_query.annotation_tool_params)

        #Parents have msn level of 1.
        total_number_of_parents = len(self.all_parents)

        #Annotation parameters that are passed to MAGMa
        db = magma_parameters['db_type']
        no_dissociations = magma_parameters['no_bond_diss']
        rel_ppm = magma_parameters['rel_ppm']
        abs_Da = magma_parameters['abs_Da']
        add_small_loss = magma_parameters['add_sm_ls']

        logger.info('total number of parents in this fragmentation set is %s', total_number_of_parents)

        # For all of the parents, send the parent and associated children to MAGMa
        for parent in self.all_parents:

            polarity = parent.source_file.polarity

            if polarity == 'Negative':
                ionisation_mode = NEGATIVE
            if polarity =='Positive':
                ionisation_mode = POSITIVE

            fragmented_peaks = self.all_peaks.filter(parent_peak=parent)
            result_name = self.result_db_name
            # get the name of the tree file for use in MAGMa and the peak_dict {mass, intensity} = peak_id
            tree, peak_dict = self._write_magma_tree_file(parent, fragmented_peaks)
            # Call MAGMa on the temporary tree file.
            f_data, mol_data, p_data = self._query_magma(tree, rel_ppm, abs_Da, no_dissociations, add_small_loss, db, result_name, ionisation_mode)

            #If we have annotation data then populate the FrAnK annotation list
            if bool(f_data):
                self._populate_magma_annotation_list(f_data, mol_data, p_data, peak_dict)
            else:
                logging.info("No annotations returned from MAGMa for this peak")

            #Finally remove the files written (probably unecessary)
            os.remove(self.query_tree)
            os.remove(self.magma_output_file)

        logger.info("Returning from getting the MAGMa annotations")

        return True

    """ Method to write the fragmentation spectra to a tree file format for querying of MAGMa
        :param: all-parents - all MS1 peaks in the fragmentation set
        :param: all_peaks - all of the peaks in the fragmentation set
        :Return: String (tree-styled for all MS1 peaks and their associated unique fragments)
        :return: peak_dict {(peak_mass, peak_intensity):peak_id}
    """

    def _write_magma_tree_file(self, parent, fragmented_peaks):

        # String to contain tree for all MS1 peaks and their MS2 children
        tree =""
        # A dictionary to keep track of the peak ids
        peak_dict = {}

        parent_intensity = round(parent.intensity, 6)  # Use variable to change intensity value for -0.25 entries
        parent_mass = round(parent.mass, 6)


        #KMcL: Work around for old data sets that have MS1 with -0.25 intensity, means the score will be wrong.
        if parent_intensity == SET_TO_NEG_2_5:
            parent_intensity = PSEUDO_PARENT_INTENSITY

        logger.info('Parent id %s parent intensity %s parent mass %s parent rt %s', str(parent.id), str(parent_intensity), str(parent_mass), str(parent.retention_time))


        peak_dict[str(parent_mass), str(parent_intensity)] = parent.id

        # Number of fragments associated with the parent peak.
        frag_count = len(fragmented_peaks)
        fragment_set = set()
        mass_set = set() #Set to ensure fragments masses are unique

        #If there are fragments associated with the parent peak.
        if frag_count > 0:
            for fragment in fragmented_peaks:

                frag_mass = round(fragment.mass, 6)
                frag_intensity = round(fragment.intensity, 6)
                frag_id = fragment.id
                frag_tup = (frag_mass, frag_intensity, frag_id)
                peak_dict[str(frag_mass), str(frag_intensity)] = frag_id

                if (frag_mass) not in mass_set:
                    mass_set.add((frag_mass))
                    fragment_set.add(frag_tup)

                #Store these fragments as duplicate peaks
                else:
                    logger.info("Duplicate peaks found and adding to list")
                    frag_list = list(frag_tup)
                    frag_list = [parent.id]+frag_list
                    self.found_duplicates.append(frag_list)

            tree += "" + str(parent_mass) + ": " + str(parent_intensity)

            #For each unique set of mz/intensity pairs run MagMa - dulipcates will be added back later
            tree +="("
            for f_list in fragment_set:
                f_mass = f_list[0]
                f_intensity = f_list[1]
                if frag_count > 1:
                    tree += "\n"
                    tree += str(f_mass) + ":" + str(f_intensity) + ","
                    frag_count=frag_count-1
                elif frag_count == 1:
                    tree += "\n"
                    tree += str(f_mass) + ":" + str(f_intensity)
            tree += ")" + "\n"


        with open(self.query_tree, "w") as tree_file:
            tree_file.write(tree)
        _, filename = os.path.split(tree_file.name)


        return filename, peak_dict

    """
        Method to send the query call to MAGMa
    """
    def _query_magma(self, tree, rel_ppm, abs_Da, no_dissociations, add_small_loss, db, result_name, ionisation_mode):

        query_file = os.path.join(
            settings.BASE_DIR+'/frank/docker_magma_query.py')

        f = open(query_file, "rb")
        query = f.read()

        magma_query_call = ["docker","run","--rm","-v",
                            settings.EXTERNAL_MAGMA_QUERY_DIR+":"+"/data",
                            "--entrypoint", "/opt/conda/bin/python", "nlesc/magma",
                            "-c", query, "-m", tree,
                            "-db", result_name, "-sdb", db,
                            "-rel_ppm", str(rel_ppm), "-abs", str(abs_Da),
                            "-nd", str(no_dissociations), "-asl", str(add_small_loss), "-i", ionisation_mode]
        try:
            return_code = call(magma_query_call)
        except CalledProcessError:
            raise
        except OSError as e:
            print(e)

        assert return_code == 0, "MAGMa failed for a horrible (or other) reason"
        assert os.path.isfile(self.magma_output_file),"MAGMa failed to write the output file!"

        results_dict = pickle.load(open(self.magma_output_file, "rb"))
        fragmentdata = results_dict['fragment_dict']
        moleculedata = results_dict['molecule_dict']
        peakdata = results_dict['peak_dict']

        return fragmentdata, moleculedata, peakdata

    """A method to populate the annotation table. Passing in one parent.
    Magma gives annotations for the parent peaks and the fragments
    Param: f_data, mol_data, p_data - dictionary files returned from MAGMa with information about the annotation
    #peak_dict maps the mass, int pairs to the peak ids
    Returns True: Boolean denoting the successful completion of the annotation population.
    """
    def _populate_magma_annotation_list(self, f_data, mol_data, p_data, peak_dict):

        logger.info("Populating the annotation list")

        #loop over all annotations and find matching entry
        for frag, fdata in f_data.iteritems():

            formula_adduct = fdata['f_formula']

            #Spilt the reference into formul and adduct.
            isfound = re.search('(.+?)<br>', formula_adduct)
            if isfound:
                formula_annot = isfound.group(1)

            isfound = re.search('<br>(.*)', formula_adduct)
            if isfound:
                adduct = isfound.group(1)

            annot_mass = Decimal(fdata['f_mass'])
            peak_mz = Decimal(fdata['f_mz'])
            score = fdata['f_score']

            peak_id = self.get_peak_id(peak_mz, p_data, peak_dict)
            correct_peak = self.all_peaks.get(id=peak_id)

            for mol, mdata in mol_data.iteritems():
                if fdata['f_molid'] == mdata['m_molid']:
                    inchi_key=mdata['m_inchikey14']
                    hmdb_ref=mdata['m_reference']
                    name = mdata['m_name']

                    #Get the hmdb id from the reference to it.
                    #Extra_data is not required as the URL is calculated later on.
                    isfound = re.search('metabolites/(.+?)" target', hmdb_ref)
                    if isfound:
                        hmdb_id = isfound.group(1)
                    # extra_data = {
                    #     'HMBD_ID': hmdb_id,
                    #     'HMBD_Reference': hmdb_ref
                    #     }
            #If a fragment has no parents then it's a parent.
            if fdata['f_parentfragid']==0: #if the fragment has no parents
                compound_object, created = Compound.objects.get_or_create(formula=formula_annot, inchikey=inchi_key)
                compound_object.name = name
                compound_object.hmdb_id = hmdb_id
                compound_object.exact_mass = annot_mass
                compound_object.save()

            #Child has no associated inchi and so has no common name or ID at this stage.
            elif fdata['f_parentfragid']>0:
                compound_object, created = Compound.objects.get_or_create(formula=formula_annot, name=formula_annot)
                compound_object.exact_mass = annot_mass
                compound_object.save()
            else:
                logger.error("Peak is not parent or child")


            # And add the compound to the CompoundAnnotationTool table
            CompoundAnnotationTool.objects.get_or_create(
                compound=compound_object,
                annotation_tool=self.annotation_tool,
                annotation_tool_identifier='id',
                    )

            # Finally add the candidate annotation to the database
            # Determine the difference in mass between the candidate annotation and the measured mass

            mass_match = get_mass_match(correct_peak, annot_mass)

            new_candidate_annotation = CandidateAnnotation.objects.create(
                compound=compound_object,
                peak=correct_peak,
                confidence=score,
                #additional_information = extra_data,
                annotation_query=self.annotation_query,
                difference_from_peak_mass=correct_peak.mass-annot_mass,
                adduct=adduct,
                mass_match=mass_match
                    )

            #Set the preferred annotation for the child peak as the one with the greatest confidence.
            if fdata['f_parentfragid']>0:
                #If a preferred candidate annotation is set
                if correct_peak.preferred_candidate_annotation:
                    #Check if the confidence of this peak is greater.
                    if new_candidate_annotation.confidence > correct_peak.preferred_candidate_annotation.confidence:
                                correct_peak.preferred_candidate_annotation=new_candidate_annotation
                                correct_peak.save()
                #Else not set, set the preferred annotation
                else:
                    correct_peak.preferred_candidate_annotation=new_candidate_annotation
                    correct_peak.save()
        return True

    """
    A method to return the peak_id given the m/z of the fragment
    """
    def get_peak_id(self, f_mz, p_data, peak_dict):

        assert f_mz in p_data, "mz value " + str(f_mz) + " not found in peak data"

        intensity = p_data[f_mz]
        f_mz = round(f_mz, 6)
        intensity = round(intensity, 6)
        mz_int = (str(f_mz), str(intensity))

        assert mz_int in peak_dict, "Peak ID can't be found for mz, intensity pair " + str(mz_int)
        peak_id = peak_dict[mz_int]

        return peak_id
"""
Class to get ChemSpider data
"""

class ChemSpiderQueryTool:

    # CAn search with inchikey but also with the CAS-codes when they are availiable.
    def __init__(self):

        self.cs = ChemSpider('8f40d3ca-3119-4b9c-be8f-c9d18ef6131c')

    #Identifier can be search term ,inchikey and in most cases from NIST - compound_cas
    def populate_compound_csid(self, compound_id):

        compound_object = Compound.objects.get(id=compound_id)
        csid = compound_object.csid

        #If there is not a csid associated with this compound
        if csid is None:

            cas_code = compound_object.cas_code
            inchikey = compound_object.inchikey

            #Choose inchikey to search ChemSpider if avaliable, else choose cas-code, if available.
            identifier = None

            if inchikey is not None:
                identifier = inchikey

            elif cas_code is not None:
                identifier = cas_code

            if identifier is not None:
                csresults = self.cs.search("'" + identifier + "'")  # search DB using the cas-code

                # If there is a result from chemSpider
                if csresults:
                    csresult = csresults[0]  # Take the first compound as the result, should be unique.
                else:
                    csresult = None

                if csresult is not None:
                    try:
                        csid = csresult.csid
                        compound_name = csresult.common_name
                        compound_object.csid = csid
                        #compound_object.name = compound_name
                        compound_object.save()

                        logger.info("the identified CSID is and the Chemspider compound name is %s %s", csid, compound_name)
                        #seen_before[identifier] = csid
                    except:
                        logger.info("Compound name error for ChemSpider, ignoring")
                        pass
            else:
                logger.info("There is no cas_code or inchikey that allows the searching of ChemSpider")
        else:
            logger.info("A CSID was already availiable for this compound and is %s", compound_object.csid)


    def search(self, identifier):

        logger.info("the identifier is %s" + identifier)

        csresults = self.cs.search("'" + identifier + "'")  # search DB using the cas-code
        # If there is a result from chemSpider
        if csresults:
            csresult = csresults[0]  # Take the first compound as the result, should be unique.
        else:
            csresult = None

        return csresult

    def get_cs_name(self):

         return self.c.common_name

    def get_cs_image_url(self):

         return self.c.image_url

    def get_cs_image(self):

         return self.c.image


class NISTQueryTool:

    """
    Class representing the NIST spectral reference library
    """

    def __init__(self, annotation_query_id):
        """
        Constructor for the NIST query tool
        """

            # Check to ensure the annotation query, associated fragmentation set and annotation tool exist
        self.annotation_query = AnnotationQuery.objects.get(id=annotation_query_id)
        self.fragmentation_set = self.annotation_query.fragmentation_set
        self.annotation_tool = self.annotation_query.annotation_tool

        # Determine suitable names for both the query file and nist output files

        #Docker directory name

        self.query_docker_dir = os.path.join(
            'data'
            )

        self.query_file_name = os.path.join(
            settings.INTERNAL_NIST_QUERY_DIR,
            str(self.annotation_query.id)+'.msp'
            )

        self.nist_output_file_name = os.path.join(
            settings.INTERNAL_NIST_QUERY_DIR,
            str(self.annotation_query.id)+'_nist_out.txt'
            )

        # Docker input file name
        self.docker_input_file = os.path.join(
            self.query_docker_dir,
            str(self.annotation_query.id)+'.msp'
            )

        # Docker file name
        self.docker_output_file_name = os.path.join(
            self.query_docker_dir,
            str(self.annotation_query.id)+'_nist_out.txt'
            )


    def get_nist_annotations(self):

        """
        Method to retrieve candidate annotations from the NIST spectral reference library
        :return True:   Boolean denoting the successfull completion of a query for annotations
        """

        logger.info('Writing MSP File...')
        # Write the query spectrum to a temporary file
        self._write_nist_msp_file()
        # Generate the subprocess call, ensuring that the user-specified parameters are included
        logger.info('Generating NIST subprocess call...')
        nist_query_call = self._generate_nist_call()
        logger.info('Querying NIST...')
        # Query the NIST reference database, generating an output file
        self._query_nist(nist_query_call)
        logger.info('Populating Annotations Table...')
        # Read in the NIST output file and populate the database
        self._populate_annotation_list()
        logger.info('Annotations Completed')
        # Finally upon completion, delete both the temporary files for NIST
        # os.remove(self.nist_output_file_name)
        # os.remove(self.query_file_name)

        return True

    def _generate_nist_call(self):

        """
        Method to construct the appropriate call to the NIST subprocess
        :return: nist_query_call:   A String call to NIST containing the user specified search parameters

        """

        # From the annotation query - get the user selected parameters
        nist_parameters = jsonpickle.decode(self.annotation_query.annotation_tool_params)
        tool_parameters = jsonpickle.decode(self.annotation_tool.default_params)
        

        library_list = nist_parameters['library']

        # Check that the user has specified at least one library for the query
        if len(library_list) == 0:
            raise ValueError('No MSPepSearch Libraries were selected by the user')
        max_number_of_hits = nist_parameters['max_hits']
        # The maximum number of hits NIST will return must be between 1 and 100
        if max_number_of_hits < 1 or max_number_of_hits > 100:
            raise ValueError('The maximum number of hits exceeds specified bounds (between 1 and 100)')
        search_type = nist_parameters['search_type']
        # The call to NIST is performed via Wine


        nist_query_call = ["docker","run","--rm","-v",
                           settings.EXTERNAL_NIST_QUERY_DIR+":"+"/home/nist/data",
                           settings.MSPEPSEARCH_IMAGE,
                           "wine",
                           "C:\\2013_06_04_MSPepSearch_x32\\MSPepSearch.exe",
                           #tool_parameters['source'],
                           search_type,
                           "/HITS",
                           str(max_number_of_hits),
                           '/PATH',
                           tool_parameters['library_path']
                           ]
        # Add the libraries which are to be included in the search to NIST: old massbank and newer MoNA
        for library in library_list:
            if library == 'mona_export_msms':
                nist_query_call.extend(['/LIB', 'mona_export_msms'])
            elif library == 'massbank_msms':
                nist_query_call.extend(['/LIB', 'massbank_msms'])
        additional_parameters = ['/INP', self.docker_input_file,
                                 '/OUT', self.docker_output_file_name]
        nist_query_call.extend(additional_parameters)

        return nist_query_call

    def _query_nist(self, nist_query_call):

        """
        Method to perform a subprocess call to NIST
        :param nist_query_call: A string containing the call to NIST
        :return: True:  A Boolean to denote the completion of the call to NIST
        """

        try:
            # Make the call to NIST to write the candidate annotations to the output file
            logger.info("Calling the nist_query_call %s" % nist_query_call)
            call(nist_query_call)
            logger.info("Finished the nist_query_call")
        except CalledProcessError:
            raise
        except OSError as e:
            print(e)
        # Finally check to see if the call was successfull and the output file exists, AssertionError thrown if not.
        assert os.path.isfile(self.nist_output_file_name),"NIST failed to write the output file!"

        return True

    def _write_nist_msp_file(self):

        """
        Method to write the fragmentation spectra to a MSP file format for querying of NIST
        :return: True:  A boolean to confirm the output file was written successfully
        """

        """
        MSP file format for NIST queries is as follows
        #   NAME: name_of_query
        #   DB#: name_of_query
        #   Precursormz: mass_of_parent_ion (required for 'G', but not 'M' type search)
        #   Comments: nothing
        #   Num Peaks: number_of_peaks_in_spectra
        #   mass    intensity   ### For each of the peaks in the spectra
        """

        experiment_protocol = self.fragmentation_set.experiment.detection_method
        include_precursor_mz = False
        if experiment_protocol.name == 'Liquid-Chromatography Mass-Spectroscopy':
            include_precursor_mz = True
        # Due to the use of a pseudo ms1 peak in the gcms datasets, the stored precursor is not a genuine precursor
        # Therefore, its mass should not be submitted to NIST which takes this into account.
        # Conversely, massbank's search API does not
        output_file = None
        # Open new MSP file for writing
        logger.info('query_file_name: %s', self.query_file_name)
        make_sure_path_exists(os.path.dirname(self.query_file_name))
        with open(self.query_file_name, "w") as output_file:
            # Retrieve all the peaks in the fragmentation set
            peaks_in_fragmentation_set = Peak.objects.filter(fragmentation_set=self.fragmentation_set)
            # Determine if there are peaks to be written to the MSP file
            if len(peaks_in_fragmentation_set) < 1:
                raise ValueError('No peaks found in fragmentation set')
            # Determine the number of msn levels
            number_of_msn_levels = peaks_in_fragmentation_set.aggregate(Max('msn_level'))
            number_of_msn_levels = number_of_msn_levels['msn_level__max']
            for level in range(1, number_of_msn_levels):
                # Get all peaks in the current msn level
                peaks_in_msn_level = peaks_in_fragmentation_set.filter(msn_level=level)
                # For each peak in the level
                for peak in peaks_in_msn_level:
                    fragmentation_spectra = peaks_in_fragmentation_set.filter(parent_peak=peak)
                    # Only write the spectra to the file if it has fragmentation spectra
                    if len(fragmentation_spectra) > 0:
                        if include_precursor_mz:
                            output_file.write('NAME: '+str(peak.id)+'\nDB#: ' + str(peak.id) +
                                              '\nComments: None\nPrecursormz:' + str(peak.mass) +
                                              '\nNum Peaks: ' + str(len(fragmentation_spectra)) + '\n')
                        else:
                            output_file.write('NAME: ' + str(peak.id) + '\nDB#: ' + str(peak.id) +
                                              '\nComments: None\nNum Peaks: ' +
                                              str(len(fragmentation_spectra)) + '\n')
                        for fragment in fragmentation_spectra:
                            output_file.write(str(fragment.mass)+' ' + str(fragment.intensity) + '\n')
                        output_file.write('\n')
        return True

    def _populate_annotation_list(self):

        """
        Method to populate the candidate annotations into the database from NIST
        :return: True:  A boolean denoting the successfull populatation of the candidate annotations
        """

        # Get the peaks for the fragmentation set from the database
        peaks_in_fragmentation_set = Peak.objects.filter(fragmentation_set=self.fragmentation_set)
        input_file = None
        try:
            with open(self.nist_output_file_name, "r") as input_file:
                # Open the NIST output file
                current_parent_peak = None

                for line in (line for line in input_file if not line.startswith('>')):
                    try:
                        # Due to use of wine,'NIST' uses a distinct encoding which alters the greek letters
                        line = line.decode('cp437').encode('utf-8', errors='strict')
                    except UnicodeError as ue:
                        print ue.message
                        # This type of error results from NIST output files using cp437 characters
                        # which seems to only impact on greek letters...therefore, exception is passed
                        pass
                    if line.startswith('Unknown:'):
                        # These lines indicate the title of the query spectra - i.e. the peak id identifier
                        line_tokens = [token.split() for token in line.splitlines()]
                        # Retrieves the id of the parent peak
                        parent_ion_id = line_tokens[0][1]
                        if parent_ion_id.startswith('<<') and parent_ion_id.endswith('>>'):
                            # The parent_ion_id is encased in <<peak_id>>, so create substring
                            parent_ion_id = parent_ion_id[2:-2]
                        try:
                            current_parent_peak = peaks_in_fragmentation_set.get(pk=parent_ion_id)
                            #print 'Populating Annotations For: '+current_parent_peak.id
                            #print current_parent_peak.mass
                        except MultipleObjectsReturned:
                            raise
                        except ObjectDoesNotExist:
                            raise
                    elif line.startswith('Hit'):
                        # Get the description of the annotation
                        annotation_description = line.splitlines()[0]
                        string_annotation_attributes = re.findall('<<(.*?)>>', annotation_description, re.DOTALL)
                        # The compound name is the first attribute encased in << >>
                        compound_name = string_annotation_attributes[0]
                        # The compound formula is the second
                        compound_formula = string_annotation_attributes[1]
                        # Retrieve the confidence value
                        annotation_confidence = Decimal(re.findall(
                            'Prob: (.*?);', annotation_description, re.DOTALL)[0])
                        # Try to retrieve the CAS code, a unique compound identifier
                        compound_cas = re.findall('CAS:(.*?);', annotation_description, re.DOTALL)[0]
                        if compound_cas == '0-00-0':
                            # For some compounds in the NIST database, the cas code is unknown
                            compound_cas = None
                        # Get the mass of the compound
                        compound_mass = Decimal(re.findall('Mw: (.*?);', annotation_description, re.DOTALL)[0])
                        # And the unique identifier NIST uses to identify the compound
                        compound_annotation_tool_identifier = re.findall('Id: (\d+).', annotation_description)[0]

                        try:
                            # Try to add the compound to the database (all of these are true to create compound)
                            with transaction.atomic():
                                compound_object = Compound.objects.get_or_create(
                                    formula=compound_formula,
                                    exact_mass=compound_mass,
                                    name=compound_name,
                                    cas_code=compound_cas
                                )[0]

                                # And form the association with the NIST Annotation Tool
                                compound_annotation_tool = CompoundAnnotationTool.objects.get_or_create(
                                    compound=compound_object,
                                    annotation_tool=self.annotation_tool,
                                    annotation_tool_identifier=compound_annotation_tool_identifier,
                                )[0]
                                # Determine the difference in mass between the candidate annotation and the measured mass
                                difference_in_mass = current_parent_peak.mass-compound_mass

                                logger.finer("the difference in mass is %s", difference_in_mass)
                                logger.finer("the polarity is %s", current_parent_peak.source_file.polarity)

                                mass_match = get_mass_match(current_parent_peak, compound_mass)

                                logger.finer("the mass_match is %s", mass_match)

                                # Add the candidate annotation to the database
                                CandidateAnnotation.objects.create(
                                    compound=compound_object,
                                    peak=current_parent_peak,
                                    confidence=annotation_confidence,
                                    annotation_query=self.annotation_query,
                                    difference_from_peak_mass=difference_in_mass,
                                    mass_match=mass_match,
                                    additional_information=annotation_description
                                )
                        except ValidationError as ve:
                            print ve.message
                            # In the event of a validation error, simply ignore this candidate annotation
                            # and resume trying to add the remaining annotations
                            pass
                        except MultipleObjectsReturned:
                            raise
        except IOError:
            raise
        finally:
            # Using 'with' should close the file but make sure
            if input_file.closed is False:
                input_file.close()
        return True


class ChemSpiderQueryTool:

    # CAn search with inchikey but also with the CAS-codes when they are availiable.
    def __init__(self):

        self.cs = ChemSpider('8f40d3ca-3119-4b9c-be8f-c9d18ef6131c')

    #Identifier can be search term ,inchikey and in most cases from NIST - compound_cas
    def populate_compound_csid(self, compound_id):

        compound_object = Compound.objects.get(id=compound_id)
        csid = compound_object.csid

        #If there is not a csid associated with this compound
        if csid is None:

            cas_code = compound_object.cas_code
            inchikey = compound_object.inchikey

            #Choose inchikey to search ChemSpider if avaliable, else choose cas-code, if available.
            identifier = None

            if inchikey is not None:
                identifier = inchikey

            elif cas_code is not None:
                identifier = str(cas_code)

            print "THE IDENTIFIER IS ", identifier

            if identifier is not None:
                csresults = self.cs.search(identifier)  # search DB using the cas-code

                # If there is a result from chemSpider
                if csresults:
                    csresult = csresults[0]  # Take the first compound as the result, should be unique.
                else:
                    csresult = None

                if csresult is not None:
                    try:
                        csid = csresult.csid
                        compound_name = csresult.common_name

                        compound_object.csid = csid
                        #compound_object.name = compound_name
                        compound_object.save()

                        logger.info("the identified CSID is and compound name is %s %s", csid, compound_name)
                    except:
                        logger.info("Compound name error for ChemSpider, ignoring")
                        pass

            else:
                logger.info("There is no cas_code or inchikey that allows the searching of ChemSpider")

        else:

            logger.info("A CSID was already availiable for this compound and is %s", compound_object.csid)


    def search(self, identifier):

        logger.info("the identifier is %s" + identifier)

        csresults = self.cs.search("'" + identifier + "'")  # search DB using the cas-code
        # If there is a result from chemSpider
        if csresults:
            csresult = csresults[0]  # Take the first compound as the result, should be unique.
        else:
            csresult = None

        return csresult

    def get_cs_name(self):

         return self.c.common_name

    def get_cs_image_url(self):

         return self.c.image_url

    def get_cs_image(self):

         return self.c.image

