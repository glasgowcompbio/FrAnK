import magma
import argparse
import pickle
from magma.models import Base, Molecule, Scan, Run
from magma.models import Peak as MagmaPeak
from magma.models import Fragment as MagmaFragment
import magma.script
import pkg_resources
import os
import sys

def main():
    os.chmod('.', 0o777)

    # Arguments to be passed in from the user form/from PiMP
    parser = argparse.ArgumentParser()

    parser.add_argument('-m', '--ms_data', help='file with MS/MS data')
    parser.add_argument('-db', '--db', help='DB name to hold the results')
    parser.add_argument('-sdb', '--structure_database', help='Retrieve molecules from structure database')

    parser.add_argument('-rel_ppm', '--mz_precision', help='Maximum relative m/z error (ppm)')
    parser.add_argument('-abs', '--mz_precision_abs', help='Maximum absolute m/z error (Da)')

    parser.add_argument('-nd', '--max_broken_bonds', help='Maximum number of bond breaks to generate substructures')
    parser.add_argument('-asl', '--max_water_losses',
                        help='Maximum number of additional water (OH) and/or ammonia (NH2) losses')
    parser.add_argument('-i', '--ionisation_mode', help='Ionisation mode')

    args = parser.parse_args()
    args.description = 'No current description'
    args.max_ms_level = 2 #not default but all we are currently interested in
    args.db_options = ''
    args.precursor_mz_precision = 0.005 #default
    args.max_charge = 1 #default
    args.ncpus = 1 #default
    args.time_limit = None #default

    # need to check for what
    args.fast = True
    args.log = 'debug'
    args.call_back_url = None
    args.ms_data_format = 'mass_tree' #type of file that is passed
    args.abs_peak_cutoff = 1000 #default
    args.read_molecules = ''
    args.skip_fragmentation = False
    args.ms_intensity_cutoff = 0 #default
    args.msms_intensity_cutoff = 0 #default
    args.use_all_peaks = True
    args.adducts = None #default
    args.molids = None
    args.scans = 'all'

    try:

        # Read the ms data with the above args
        mc = magma.script.MagmaCommand()
        mc.read_ms_data(args)
        mc.annotate(args)

        ms = magma.MagmaSession(args.db)
        ms.db_session.query(Run).one()

        moleculedata = ms.db_session.query(Molecule).all()
        fragmentdata = ms.db_session.query(MagmaFragment).all()
        peakdata = ms.db_session.query(MagmaPeak).all()

        # Create a dictionary for all of the fragments and molecules to pass back to PiMP:

        fragment_dict = {}
        for f in fragmentdata:
            frag_attributes = {'f_mz': f.mz, 'f_formula': f.formula, 'f_score': f.score,
                               'f_parentfragid': f.parentfragid, 'f_mass': f.mass, 'f_molid': f.molid}

            fragment_dict[f.fragid] = frag_attributes

        molecule_dict = {}
        for m in moleculedata:
            mol_attributes = {'m_molid': m.molid, 'm_inchikey14': m.inchikey14, 'm_reference': m.reference,
                              'm_name': m.name, 'm_formula': m.formula}
            molecule_dict[m.molid] = mol_attributes

        print molecule_dict

        peak_dict = {}
        for p in peakdata:
            peak_dict[p.mz] = p.intensity

        results_dict = {}
        results_dict['molecule_dict'] = molecule_dict
        results_dict['fragment_dict'] = fragment_dict
        results_dict['peak_dict'] = peak_dict

        pickle.dump(results_dict, open(str(args.db) + "_dict.p", "wb"))

        os.remove(str(args.db))
        os.chmod(str(args.db) + "_dict.p", 0o777)

    except Exception:
        print 'Exception'
        sys.exit(1)

if __name__ == '__main__':
    main()
