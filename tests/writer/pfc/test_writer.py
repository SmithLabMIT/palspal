from pathlib import Path
from palspal.writer import PFCFile
import difflib
import sys


def show_file_differences(file1_path, file2_path):
    # Read files into lists of lines
    with open(file1_path, 'r', encoding='utf-8') as f1, open(file2_path, 'r', encoding='utf-8') as f2:
        file1_lines = f1.readlines()
        file2_lines = f2.readlines()

    # Generate a human-readable difference report
    diff = difflib.ndiff(file1_lines, file2_lines)
    
    # Filter and print only the lines that are NOT identical
    has_differences = False
    for line in diff:
        if line.startswith('- ') or line.startswith('+ ') or line.startswith('? '):
            sys.stdout.write(line)
            has_differences = True
            
    if not has_differences:
        print("Files are completely identical!")


def test_blank_write():
    PFCFile().write("blank.pfc")


def test_default_read():
    data_dir = Path(__file__).resolve().parent.parent.parent / "data_files"
    pfc = PFCFile().read(data_dir / "default.pfc")
    pfc.write("default_out.pfc")
    show_file_differences(data_dir / "default.pfc", "default_out.pfc")


def test_change_non_default_params():
    data_dir = Path(__file__).resolve().parent.parent.parent / "data_files"
    pfc = PFCFile().read(data_dir / "default.pfc")

    pfc.num_channels =
    pfc.format =
    pfc.spectrum_path =
    pfc.spectrum_label =
 
    pfc.area =
    pfc.fit =
    pfc.timescale =
    pfc.timezero_constraint =
    pfc.timezero =

    pfc.res_components =
    pfc.res_fwhm =
    pfc.res_intensity =
    pfc.res_shift =

    pfc.lt_components = 
    pfc.lt_constraint =
    pfc.lt =
    pfc.ln_constraint = 
    pfc.ln_broadening =

def change_default_params():

    pfc.echo =
    pfc.iteration =
    pfc.resid_plot =
    pfc.corr_matrix = 

    pfc.log_normal_fineness =

    pfc.inspec =

    pfc.int_constraint =
    pfc.int_constraint_info =
    pfc.lt_components_2 =
    pfc.lt_constraint_2 =
    pfc.lt_2 =
    pfc.ln_constraint_2 =
    pfc.ln_broadening_2 =
    pfc.int_constraint_2 =
    pfc.int_constraint_info_2 =

    pfc.bg_constraint =
    pfc.bg_channels =
    pfc.bg_fixed =

    pfc.area_constraint =
    pfc.area_channels =
    pfc.area_fixed =

    pfc.source_components =
    pfc.source_lt =
    pfc.source_broadening =
    pfc.source_int =
    pfc.source_total =
    pfc.new_cycle_input =
    pfc.source_components_2 =
    pfc.source_lt_2 =
    pfc.source_broadening_2 =
    pfc.source_int_2 =
    pfc.source_total_2 =
    pfc.timezero_constraint_2 =
    pfc.timezero_2 =



#def test_default_write():

#def test_area_constraint


#RFCFile().write("default.rfc")

test_default_read()