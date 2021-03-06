__author__ = 'Scott Greig'

from django import forms
from frank.models import Experiment, ExperimentalCondition, ExperimentalProtocol,\
    Sample, SampleFile, FragmentationSet, AnnotationQuery, Peak, AnnotationTool, \
    IONISATION_PROTOCOLS, FILE_TYPES
from django.utils.safestring import mark_safe

# MAGMa can choose HMDB, PubChem and Kegg as databases. For the initial installation
#only HMDB will be added, the others may be integrated later.

MAGMA_DB_TYPES = (
    ('hmdb','HMDB'),
    #('kegg', 'KEGG'),
    #('pubchem', 'PubChem'),
    #('metacyc', 'MetaCyc')
 )

# From SIRIUS documentation:
# Specify the used analysis profile. Choose either **qtof**,
# **orbitrap** or **fticr**. By default, **qtof** is selected.
#
SIRIUS_PROFILE_TYPES = (
    ('qtof', 'Quadrupole-time-of-flight'), #should be default choice
    ('orbitrap', 'Ion trap mass analyzer'),
    ('fticr', 'Fourier transform ion cyclotron resonance'),
)

# From SIRIUS documentation
# Specify the format of the output of the fragmentation trees. This
#    can be either json (machine readable) or dot (visualizable)
SIRIUS_OUTPUT_FORMAT = (
    ('json', 'Machine readable (json)'),
    ('dot', 'Visualizable (dot)')
)

# The following are the GCMS instrument types supported by Massbank
MASS_BANK_GCMS_INSTRUMENT_TYPES = (
    ('EI-B', 'Electron Ionisation-Magnetic Sector (EI-B)'),
    ('EI-EBEB', 'Electron Ionisation-Four Sector (EI-EBEB)'),
    ('GC-EI-QQ', 'Gas Chromatography-Electron Ionisation-Double Quadrupole (GC-EI-QQ)'),
    ('GC-EI-TOF', 'Gas Chromatography-Electron Ionisation-Time of Flight (GC-EI-TOF)'),
)

# The following are the LCMS instrument types supported by Massbank
MASS_BANK_LCMS_INSTRUMENT_TYPES = (
    ('ESI-ITFT', 'Electrospray Ionisation-Ion Trap-Fourier Transform (ESI-ITFT)'),
    ('ESI-ITTOF', 'Electrospray Ionisation-Ion Trap-Time of Flight (ESI-ITTOF)'),
    ('LC-ESI-IT', 'Liquid Chromatography-Electrospray Ionisation-Ion Trap (LC-ESI-IT)'),
    ('LC-ESI-ITFT', 'Liquid Chromatography-Electrospray Ionisation-Ion Trap-Fourier Transform (LC-ESI-ITFT)'),
    ('LC-ESI-ITTOF', 'Liquid Chromatography-Electrospray Ionisation-Ion Trap-Time of Flight (LC-ESI-ITTOF)'),
    ('LC-ESI-Q', 'Liquid Chromatography-Electrospray Ionisation-Quadrupole(LC-ESI-Q)'),
    ('LC-ESI-QFT', 'Liquid Chromatography-Electrospray Ionisation-Quadrupole-Fourier Transform(LC-ESI-QFT)'),
    ('LC-ESI-QIT', 'Liquid Chromatography-Electrospray Ionisation-Quadrupole-Ion Trap(LC-ESI-QIT)'),
    ('LC-ESI-QQ', 'Liquid Chromatography-Electrospray Ionisation-Double Quadrupole(LC-ESI-QQ)'),
    ('LC-ESI-QTOF', 'Liquid Chromatography-Electrospray Ionisation-Quadrupole-Time of Flight(LC-ESI-QTOF)'),
    ('LC-ESI-TOF', 'Liquid Chromatography-Electrospray Ionisation-Time of Flight(LC-ESI-TOF)'),
)

# The following are the GCMS libraries for query for GCMS spectra
# KmcL: Currently not using GCMS data and if we were we couldn't use these libraries as they have been removed from the
# docker/tool.
NIST_GCMS_LIBRARIES = (
    ('mainlib', 'Main EI MS Library'),
    ('replib', 'Replicate EI MS Library'),
)

# The following are the LCMS libraries suitable for LCMS spectra
NIST_LCMS_LIBRARIES = (
    ('mona_export_msms', 'MoNA LC-MS/MS Spectral Library'),
    ('massbank_msms','MassBank MSMS Library')
)

# The search types suitable for GCMS
NIST_GCMS_SEARCH_PARAMS = (
    ('M', 'MS/MS in EI Library'),
    ('I', 'Identity')
)

# The search types suitable for LCMS
NIST_LCMS_SEARCH_PARAMS = (
    ('G', 'Generic MS/MS Search in a MS/MS Library'),
    ('P', 'Peptide MS/MS Search in a MS/MS Library'),
    ('I', 'Identity')
)

# Simon's Transformation Types
POSITIVE_TRANSFORMATION_TYPES = (
    ("M+H", "M+H"),
    ("M+Na", "M+Na"),
    ("M+K", "M+K"),
    ('M+2H', 'M+2H'),
    ("M+H+NH4", "M+H+NH4"),
    ("M+H+Na", "M+H+Na"),
    ("M+H+K", "M+H+K"),
    ("M+ACN+2H", "M+ACN+2H"),
    ("M+2Na", "M+2Na"),
    ("M+HC13", "M+HC13"),
    ("M+H2C13", "M+H2C13"),
    ("M+NH4", "M+NH4"),
    ("M+NaC13", "M+NaC13"),
    ("M+CH3OH+H", "M+CH3OH+H"),
    ("M+KC13", "M+KC13"),
    ("M+ACN+H", "M+ACN+H"),
    ("M+2Na-H", "M+2Na-H"),
    ("M+IsoProp+H", "M+IsoProp+H"),
    ("M+ACN+Na", "M+ACN+Na"),
    ("M+2K-H", "M+2K-H"),
    ("M+DMSO+H", "M+DMSO+H"),
    ("M+2ACN+H", "M+2ACN+H"),
)

NEGATIVE_TRANSFORMATION_TYPES = (
    ("M-H","M-H"),
    ("M-2H","M-2H"),
)

MOTIF_SETS = (
    ("massbank_motifset","massbank_motifset"),
    ("gnps_motifset","gnps_motifset"),
)


class ExperimentForm(forms.ModelForm):
    """
    Form class for the creation of an experiment
    """

    title = forms.CharField(
        max_length=60,
        help_text="Enter the name of the experiment."
    )
    description = forms.CharField(
        widget=forms.Textarea,
        max_length=300,
        help_text="Enter a description of the experiment (optional).",
        required=False
    )
    # A user must select the ionisation source for the experiment
    # IONISATION_PROTOCOLS is declared in 'frank.models'
    ionisation_method = forms.ChoiceField(
        choices=IONISATION_PROTOCOLS,
        help_text="Select the ionisation source.",
    )
    # A user must select the experimental protocol used for the experiment
    detection_method = forms.ModelChoiceField(
        queryset=ExperimentalProtocol.objects.all(),
        empty_label=None,
        help_text="Select the experimental protocol.",
    )

    class Meta:
        model = Experiment
        fields = (
            'title',
            'description',
            'ionisation_method',
            'detection_method'
        )


class ExperimentalConditionForm(forms.ModelForm):
    """
    Form class for the definition of an experimental condition of an experiment
    """

    name = forms.CharField(
        max_length=60,
        help_text="Enter the name of the experiment condition."
    )
    description = forms.CharField(
        widget=forms.Textarea,
        max_length=300,
        help_text="Enter a description of the condition (optional).",
        required=False
    )

    class Meta:
        model = ExperimentalCondition
        fields = (
            'name', 'description',
        )


class SampleForm(forms.ModelForm):
    """
    Form class for the creation of a new sample within an experimental sample
    """

    name = forms.CharField(
        max_length=60,
        help_text="Enter the name of the sample."
    )
    description = forms.CharField(
        widget=forms.Textarea,
        max_length=300,
        help_text="Enter a description of the sample (optional).",
        required=False
    )
    # A field to state the organism of a sample is associated for clarity
    # to others who may view the experiment
    organism = forms.CharField(
        max_length=60,
        help_text="Enter the name of the organism (optional).",
        required=False
    )

    class Meta:
        model = Sample
        fields = (
            'name', 'description', 'organism'
        )
        exclude = ('experimentalCondition',)


class SampleFileForm(forms.ModelForm):
    """
    Form class to upload new data files to an experimental sample
    """

    # At present the user must specify the polarity of the file
    # However, in subsequent iterations this could be performed on upload
    # using Yoann's XML parser. This wasn't included as we may also want to
    # specify MS1 files for upload.
    polarity = forms.ChoiceField(
        choices=FILE_TYPES,
        help_text="Please select the polarity of the file for upload."
    )
    # A simple alternative to the drag and drop file upload, requested by
    # the client. However, this will be removed in subsequent iterations.
    address = forms.FileField(
        help_text="Please select the .mzML file for upload."
    )

    class Meta:
        model = SampleFile
        fields = (
            'polarity', 'address',
        )
        exclude = (
            'sample',
        )

    def clean(self):
        """
        An overridden method to ensure the file type of the uploaded file
        is that of mzXML. However, in the future the application may support
        the mzML format.
        """
        cleaned_data = super(SampleFileForm, self).clean()
        # get the absolute address of the uploaded file
        input_file = cleaned_data.get('address')
        # if an absolute address has been registered
        if input_file:
            # derive the name of the file
            filename = input_file.name
            # check the file extension is '.mzXML'
            if filename.endswith('.mzML') is False:
                self.add_error("address", "Incorrect file format. Please upload an mzML file")
                raise forms.ValidationError("Incorrect file format")
        else:
            # In the event no file is provided, notify the user
            self.add_error("address", "No file selected. Please upload an mzML file")
            raise forms.ValidationError("No file selected.")


class FragmentationSetForm(forms.ModelForm):
    """
    Form class for the creation of a Fragmentation Set
    """

    name = forms.CharField(
        max_length=60,
        help_text="Enter the name of the fragmentation set."
    )

    class Meta:
        model = FragmentationSet
        fields = (
            'name',
        )


class AnnotationToolSelectionForm(forms.Form):
    """
    Form class for the selection of an AnnotationTool for a query
    """

    # The default is for all annotation tools to be available
    tool_selection = forms.ModelChoiceField(
        queryset=AnnotationTool.objects.all(),
        empty_label=None,
        help_text='Select a tool to generate candidate annotations.'
    )

    def __init__(self, *args, **kwargs):
        """
        Overridden method for construction of the form
        :param args:    Argument
        :param kwargs:  Keyword Arguments - 'experiment_object' should be provided
        """
        self.experiment = None
        if 'experiment_object' in kwargs:
            self.experiment = kwargs.pop('experiment_object')
        super(AnnotationToolSelectionForm, self).__init__(*args, **kwargs)
        # The experiment is used here to populate the choice field
        # with the annotation tools suitable for the experimental protocol
        if self.experiment:
            self.fields['tool_selection'] = forms.ModelChoiceField(
                queryset=AnnotationTool.objects.filter(
                    suitable_experimental_protocols=self.experiment.detection_method
                ),
                empty_label=None,
                help_text='Select a tool to generate candidate annotations.',
            )


class AnnotationQueryForm(forms.ModelForm):
    """
    A form class for the creation of an Annotation Query
    """

    name = forms.CharField(
        max_length=60,
        help_text="Please enter the name of the query."
    )

    class Meta:
        model = AnnotationQuery
        fields = (
            'name',
        )

class CleanFilterForm(AnnotationQueryForm):

    possible_parents = ()
    def __init__(self,fragmentation_set_name_id,*args,**kwargs):
        super(CleanFilterForm,self).__init__(*args,**kwargs)
        fragmentation_set = FragmentationSet.objects.get(pk = fragmentation_set_name_id)
        parent_annotations = AnnotationQuery.objects.filter(fragmentation_set = fragmentation_set)
        possible_parents = ()
        for a in parent_annotations:
            possible_parents = possible_parents + ((a.id,a.name),)
        self.fields['parent_annotation_queries'] = forms.MultipleChoiceField(
            choices = possible_parents,
            required = True,
            help_text = "Please choose a parent Annotation Query to filter")

    parent_annotation_queries = forms.MultipleChoiceField(
        choices = possible_parents,
        help_text = "Please choose a parent Annotation Query to filter"
    )

    preferred_threshold = forms.DecimalField(
        min_value = 0.0,
        required = True,
        help_text = "Please choose threshold for preferred annotations"
    )

    do_preferred = forms.BooleanField(
        help_text = "Automatically assign highest confidence annotation (if above threshold) to preferred annotation?",
        required = False,
        initial = True,
    )

    collapse_multiple = forms.BooleanField(
        help_text = "Collapse multiple annotations of the same compound into one?",
        required = False,
        initial = True
    )

    # delete_original = forms.BooleanField(
    #     help_text = "Delete parent annotation query object and annotations?",
    #     required = False,
    # )

    def clean(self):
        cleaned_data = super(CleanFilterForm, self).clean()
        user_selections = cleaned_data.get('parent_annotation_queries')
        if user_selections == None:
            self.add_error("parents", "No parents were selected. Please select at least one parent query.")
            raise forms.ValidationError("No parents were selected. Please select at least one parent query.")

class NetworkSamplerForm(AnnotationQueryForm):
    __author__ = 'Simon Rogers'
    possible_parents = []
    def __init__(self,fragmentation_set_name_id,*args, **kwargs):
        super(NetworkSamplerForm,self).__init__(*args, **kwargs)
        fragmentation_set = FragmentationSet.objects.get(pk = fragmentation_set_name_id)
        parent_annotations = AnnotationQuery.objects.filter(fragmentation_set = fragmentation_set)
        possible_parents = ()
        for a in parent_annotations:
            possible_parents = possible_parents + ((a.id,a.name),)
        self.fields['parent_annotation_queries'] = forms.MultipleChoiceField(
            choices = possible_parents,
            required = True,
            help_text = "Please choose a parent Annotation Query to filter")

    parent_annotation_queries = forms.MultipleChoiceField(
        choices = possible_parents,
        help_text = "Please choose a parent Annotation Query to filter")

    n_samples = forms.IntegerField(
        min_value=1,
        required = False,
        help_text="Please enter number of posterior samples (leave blank for default 1000)")

    n_burn = forms.IntegerField(
        min_value=1,
        required = False,
        help_text="Please enter number of burn-in samples (leave blank for default 100)")

    delta = forms.DecimalField(
        required = False,
        help_text="Please enter regularisation parameter delta")

    def clean(self):
        cleaned_data = super(NetworkSamplerForm, self).clean()
        user_selections = cleaned_data.get('parent_annotation_queries')
        if user_selections == None:
            self.add_error("no parent", "No parent query was selected. Please select at least one parent.")
            raise forms.ValidationError("No parent query was selected. Please select at least one parent.")
        n_samples = cleaned_data.get('n_samples',1000)
        n_burn = cleaned_data.get('n_burn',100)
        if n_burn > n_samples:
            self.add_error("Number of posterior samples must be greater than the  burn-in period")
            raise forms.ValidationError("Number of posterior samples must be greater than the  burn-in period")



class PrecursorMassFilterForm(AnnotationQueryForm):
    """
    Class for the Precursor Mass Filter - Simon Rogers contribution
    """
    possible_parents = []
    def __init__(self,fragmentation_set_name_id,*args, **kwargs):
        super(PrecursorMassFilterForm,self).__init__(*args, **kwargs)
        fragmentation_set = FragmentationSet.objects.get(pk = fragmentation_set_name_id)
        parent_annotations = AnnotationQuery.objects.filter(fragmentation_set = fragmentation_set)
        possible_parents = ()
        for a in parent_annotations:
            possible_parents = possible_parents + ((a.id,a.name),)
        self.fields['parent_annotation_queries'] = forms.MultipleChoiceField(
            choices = possible_parents,
            required = True,
            help_text = "Please choose a parent Annotation Query to filter")

    parent_annotation_queries = forms.MultipleChoiceField(
        choices = possible_parents,
        help_text = "Please choose a parent Annotation Query to filter")

    positive_transforms = forms.MultipleChoiceField(
        choices = POSITIVE_TRANSFORMATION_TYPES,
        required = True,
        initial = ['M+H'],
        widget=forms.CheckboxSelectMultiple(),
        help_text = "Please choose which transformation types to include in the filter"
        )

    negative_transforms = forms.MultipleChoiceField(
        choices = NEGATIVE_TRANSFORMATION_TYPES,
        required = True,
        initial = ['M-H'],
        widget = forms.CheckboxSelectMultiple(),
        help_text = "Please choose which negative mode transformation types to include in the filter"
        )

    mass_tol = forms.IntegerField(
        min_value= 0,
        max_value = 100,
        initial = 5,
        required = True,
        help_text = "Please specify mass tolerance (in ppm)")

    def clean(self):
        cleaned_data = super(PrecursorMassFilterForm, self).clean()
        user_selections = cleaned_data.get('positive_transforms')
        if user_selections == None:
            self.add_error("np_transforms", "No transformations were selected. Please select at least one transformation to query.")
            raise forms.ValidationError("No transformations were selected. Please select at least one transformation to query.")


class NISTQueryForm(AnnotationQueryForm):
    """
    A form for the specification of the search parameters for NIST
    """

    maximum_number_of_hits = forms.IntegerField(
        max_value=20,
        min_value=1,
        required=True,
        help_text="Please specify the maximum number of hits returned for each spectrum"
    )
    search_type = forms.ChoiceField(
        choices=NIST_LCMS_SEARCH_PARAMS,
        help_text="Please select the required MSPepSearch type."
    )
    query_libraries = forms.MultipleChoiceField(
        choices=NIST_LCMS_LIBRARIES,
        widget=forms.CheckboxSelectMultiple(),
        help_text="Please specify which library you wish to query."
    )

    def clean(self):
        """
        Overridden method to ensure at least one reference library has been selected
        """

        cleaned_data = super(NISTQueryForm, self).clean()
        # get the user's choices of reference libraries
        user_selections = cleaned_data.get('query_libraries')
        # if no selections were made, add error to the form and raise exception
        if user_selections is None:
            self.add_error("query_libraries",
                           "No libraries were selected. Please select at least one reference library to query."
                           )
            raise forms.ValidationError("No search libraries selected.")

    def __init__(self, *args, **kwargs):
        """
        Override the constructor for the form to ensure the choices
        of libraries and search parameters are suitable for the user's
        experimental protocol.
        """

        self.experiment = None
        # derive the experiment object from the keyword arguments
        if 'experiment_object' in kwargs:
            self.experiment = kwargs.pop('experiment_object')
        super(NISTQueryForm, self).__init__(*args, **kwargs)
        # get the experimental protocol used
        protocol_used = self.experiment.detection_method
        # As the default of the form is LCMS, alterations are only made for GCMS
        if protocol_used.name == 'Gas-Chromatography Mass-Spectroscopy Electron Impact Ionisation':
            # The fields here are the same as the default, with the exception
            # that it is the GCMS search parameters and libraries included
            self.fields['search_type'] = forms.ChoiceField(
                choices=NIST_GCMS_SEARCH_PARAMS,
                help_text="Please select the required NIST search type.",
            )
            self.fields['query_libraries'] = forms.MultipleChoiceField(
                choices=NIST_GCMS_LIBRARIES,
                widget=forms.CheckboxSelectMultiple(),
                help_text="Please specify which library you wish to query.",
            )


class MAGMAQueryForm(AnnotationQueryForm):
    """
    Form class for the querying MAGMa
    """
    #KMcL: Would be good if form could be prettier/more informative.
    #Currently form is taken directly from web-server (but less pretty) including
    #all of the max/min values and defaults.

    db_type = forms.ChoiceField(
        choices=MAGMA_DB_TYPES,
        help_text="Please select the chemical DB."
    )

    bond_dissociations = forms.DecimalField(
        max_value =4,
        min_value =0,
        initial= 3,
        required = True,
        help_text="Substructure options:"
    )
    additional_small_losses = forms.DecimalField(
        max_value=4,
        min_value=0,
        initial=1,
        required=True,
    )

    relative_ppm = forms.IntegerField(
        max_value =1000,
        min_value =5,
        initial= 5,
        required = True,
        help_text="Accuracy:"
    )

    absolute_Da = forms.DecimalField(
        max_value=1,
        min_value=0,
        initial=0.001,
        required=True,
    )
    #
    def clean(self):
        #         """
        #         Overridden method to ensure at least one profile and output format has been selected
        #         """
        # #       #Don't think error checking is required as not tick box - but leave at moment.
        cleaned_data = super(MAGMAQueryForm, self).clean()

    #
    def __init__(self, *args, **kwargs):
        #         """
        #         Override the constructor for the form to ensure the choices
        #         of libraries and search parameters are suitable for the user's
        #         experimental protocol.
        #         """
        print "form _init_"
        self.experiment = None
        #         # derive the experiment object from the keyword arguments
        if 'experiment_object' in kwargs:
            self.experiment = kwargs.pop('experiment_object')
        super(MAGMAQueryForm, self).__init__(*args, **kwargs)


#Add Sirius query form - any queries that are not defined are commented out
class SIRIUSQueryForm(AnnotationQueryForm):
    """
    Form class for the querying to SIRIUS API
    """
    #Check the ppm requirements and fix this KMcL - should have default of 5 for OrbiTrap and 10 for Q-TOF
    profile_type = forms.ChoiceField(
        choices=SIRIUS_PROFILE_TYPES,
        help_text="Please select the required profile type."
    )

    max_ppm = forms.IntegerField(
        max_value =15,
        min_value =5,
        initial= 10,
        required = True,
        help_text="Please specify the allowed mass deviation of the fragment peaks in ppm"
    )
    maximum_number_of_hits = forms.IntegerField(
        max_value=20,
        min_value=1,
        initial=5,
        required=True,
        help_text="Please specify the maximum number of candidate annotations"
    )

    output_format = forms.ChoiceField(
        choices=SIRIUS_OUTPUT_FORMAT,
        help_text="Please select the required output format."
    )
    #
    def clean(self):
        #         """
        #         Overridden method to ensure at least one profile and output format has been selected
        #         """
        # #       #Don't think error checking is required as not tick box - but leave at moment.
        cleaned_data = super(SIRIUSQueryForm, self).clean()

    #
    def __init__(self, *args, **kwargs):
        #         """
        #         Override the constructor for the form to ensure the choices
        #         of libraries and search parameters are suitable for the user's
        #         experimental protocol.
        #         """
        print "form _init_"
        self.experiment = None
        #         # derive the experiment object from the keyword arguments
        if 'experiment_object' in kwargs:
            self.experiment = kwargs.pop('experiment_object')
        super(SIRIUSQueryForm, self).__init__(*args, **kwargs)


class MassBankQueryForm(AnnotationQueryForm):
    """
    Form class for the querying to MassBank API
    """

    massbank_instrument_types = forms.MultipleChoiceField(
        choices=MASS_BANK_LCMS_INSTRUMENT_TYPES,
        widget=forms.CheckboxSelectMultiple(),
        help_text="MassBank provides spectra for the following instruments."
                  "Please select those that reflect your own experimental protocol.",
    )

    def clean(self):
        """
        Override the clean method to ensure at least one instrument type is included
        in the user-specified search parameters
        """

        cleaned_data = super(MassBankQueryForm, self).clean()
        # get the user-specified instrument types
        user_selections = cleaned_data.get('massbank_instrument_types')
        # if no instruments have been selected then an error should be raised
        if user_selections is None:
            self.add_error(
                "massbank_instrument_types",
                "No instrument types were selected. Please select at least one instrument type."
            )
            raise forms.ValidationError("No instrument types were selected.")

    def __init__(self, *args, **kwargs):
        """
        Constructor for the form, this has been overridden so the choices of instrument
        are appropriate for the experimental protocol used e.g. GCMS versus LCMS
        :param args:    Arguments passed to the  method
        :param kwargs:  Keyword arguments passed to the method
        """

        self.experiment = None
        if 'experiment_object' in kwargs:
            self.experiment = kwargs.pop('experiment_object')
        super(MassBankQueryForm, self).__init__(*args, **kwargs)
        # Get the protocol of the experiment
        protocol_used = self.experiment.detection_method
        # As LCMS is the default, only change the user's options for GCMS
        if protocol_used.name == 'Gas-Chromatography Mass-Spectroscopy Electron Impact Ionisation':
            self.fields['massbank_instrument_types'] = forms.ChoiceField(
                choices=MASS_BANK_GCMS_INSTRUMENT_TYPES,
                widget=forms.CheckboxSelectMultiple(),
                help_text="Massbank supports the following instruments for GCMS. "
                          "Please select those that apply to the experiment.",
            )





class PreferredAnnotationForm(forms.ModelForm):
    """
    Form class for the user to provide a justification when selecting a preferred annotation for a peak.
    """

    preferred_candidate_description = forms.CharField(
        max_length=500,
        help_text="Please enter a justification for the preferred annotation.",
        widget=forms.Textarea,
    )

    class Meta:
        model = Peak
        fields = (
            'preferred_candidate_description',
        )

class SelectFragmentationSetForm(forms.Form):
    """
    Form class for the selection of an AnnotationTool for a query
    """

    # The default is for all annotation tools to be available
    fragmentation_sets = forms.ModelChoiceField(
        queryset=FragmentationSet.objects.all(),
        empty_label=None,
    )

    mass_tolerance = forms.DecimalField(
        required = True,
        min_value = 0,
        initial = 5,
        )

    rt_tolerance = forms.DecimalField(
        required = True,
        min_value = 0,
        initial = 10,
        )


    def __init__(self,*args,**kwargs):
        if 'current_user' in kwargs:
            self.user = kwargs.pop('current_user')
        super(SelectFragmentationSetForm, self).__init__(*args, **kwargs)
        if self.user:
            self.fields['fragmentation_sets'] = forms.ModelChoiceField(
                queryset=FragmentationSet.objects.filter(experiment__created_by = self.user),
                empty_label=None,
            )