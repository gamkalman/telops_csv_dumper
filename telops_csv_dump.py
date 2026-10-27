#!/usr/bin/python3
import os
import copy
import sys
import argparse
import csv
import logging
import glob
import numpy as np
from collections import OrderedDict

# constants
# ---------
DEBUG = os.environ.get('DEBUG', '0') != '0'
this_script = sys.argv[0]
usage_message = f'python3 {this_script} -d <input_directory|str> -o <outdir|str>'
VERSION = '1.0.0'

# set up logging
# --------------
logging.basicConfig(stream = sys.stderr,
  level = logging.DEBUG if DEBUG else logging.INFO,
  format  =
    '[%(asctime)s.%(msecs)03d %(levelname)s] %(filename)s:%(lineno)d:\n%(message)s'
      if DEBUG else '[%(asctime)s.%(msecs)03d %(levelname)s] %(message)s',
  datefmt = '%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

class telops_csv_file(object):

  # define class hash for QA data
  # -----------------------------
  qa_hash = OrderedDict([
    ('Source_CSV', ''),
    ('Measurement_Time_UTC', ''),
    ('Width_Pixels', ''),
    ('Height_Pixels', ''),
    ('OffsetX', ''),
    ('OffsetY', ''),
    ('Latitude_Ground_Degrees', ''),
    ('Longitude_Ground_Degrees', ''),
    ('Brightness_Temp_K_Percentile_25', ''),
    ('Brightness_Temp_K_Percentile_50', ''),
    ('Brightness_Temp_K_Percentile_75', ''),
    ('Display_Sensitivity%', ''),
    ('Opacity_Min%', ''),
    ('Opacity_Max%', ''),
    ('Clean_Background_Fraction', ''),
    ('Background_PCA_Energy_Fraction', ''),
    ('Dual_Test_PFA', ''),
    ('Dual_Test_Correlation_Percentile', ''),
    ('Plume_Expansion_PFA', ''),
    ('Plume_Expansion_PFA_Percentile', ''),
    ('Identification_Criteria_Type', ''),
    ('Identification_Threshold', ''),
    ('Sensitivity', ''),
    ('Specificity', ''),
    ('Plume_Expansion', ''),
    ('Bad_Pixels', ''),
    ('Saturated_Pixels', ''),
    ('Saturated_Pixels_in_Counts', ''),
    ('Saturated_Pixels_in_Current', '')
  ])

  def __init__(self, csv_filename: str, outdir: str = '') -> None:
    '''Constructor method'''
    self.filename = csv_filename
    self.outdir = outdir

  def __del__(self):
    '''Destructor method'''
    pass

  @staticmethod
  def write_all_ge_display_csv(csv_filenames: list, outDir: str) -> None:

    # get header line ; we can just use any file (first one)
    # to get it
    # ------------------------------------------------------
    with open(csv_filenames[0], mode = 'r', newline = '', encoding = 'utf-8') as f:
      reader = csv.reader(f)
      header_line = next(reader)
   
    # gather all CSV data from all files (GE display)
    # -----------------------------------------------
    all_ge_display_lines = []

    for csv_filename in csv_filenames:
      with open(csv_filename, mode = 'r', newline = '', encoding = 'utf-8') as f:
        reader = csv.reader(f)
        next(reader)

        for row in reader:
          all_ge_display_lines.append(row)

    # finally write out CSV with ALL GE dispaly data
    # ----------------------------------------------
    outname_csv_all_ge_display_data = os.path.join(outDir, 'all_ge_display_data.csv')
    if os.path.isfile(outname_csv_all_ge_display_data):
      os.remove(outname_csv_all_ge_display_data)

    with open(outname_csv_all_ge_display_data, 'w', newline = '', encoding = 'utf-8') as f:
      writer = csv.writer(f)
      writer.writerow(header_line)

      for ge_display_line in all_ge_display_lines:
        writer.writerow(ge_display_line)

  @staticmethod
  def write_all_qa_data_csv(outname_csv: str, qa_headers: list, outDir: str) -> None:
    
    # remove csv if already exists
    # ----------------------------
    if os.path.isfile(outname_csv):
      os.remove(outname_csv)
    
    # get header line
    # ---------------
    csv_header_line = [s.replace('_', ' ') for s in list(qa_headers[0].keys())]

    with open(outname_csv, mode = 'w', newline = '', encoding = 'utf-8') as f:
      
      csv_writer = csv.writer(f)
      csv_writer.writerow(csv_header_line)

      for qa_header in qa_headers:
        qa_csv_line = [str(s) for s in list(qa_header.values())]
        csv_writer.writerow(qa_csv_line) 

  def write_ge_display_data_csv(self):
    '''
    Instance method to write out the GE display CSV.
    '''
    # get QA header information + display data lines
    # ----------------------------------------------
    qa_header = self.get_qa_data()
    chemical_display_data = self.get_ge_display_data()

    # read attributes required for outputting display data CSV
    #   e.g. longitude, latitude, etc.
    # --------------------------------------------------------
    source_csv = qa_header['Source_CSV']
    measurement_time_csv = qa_header['Measurement_Time_UTC']
    longitude = qa_header['Longitude_Ground_Degrees']
    latitude = qa_header['Latitude_Ground_Degrees']

    full_csv_header = ['Source CSV', 'Measurement Time [UTC]', 'Latitude[°]', 'Longitude[°]'] + \
            chemical_display_data[0]
    
    # establish name of output CSV data with GE display data
    # ------------------------------------------------------
    outname_csv = self.filename.replace('.csv', '_ge_display_data.csv')
    if os.path.isfile(outname_csv):
      os.remove(outname_csv)
 
    if self.outdir:
      outname_csv = os.path.join(self.outdir, os.path.basename(outname_csv))

    chemical_display_data.pop(0)
    line_counter = 0

    with open(outname_csv, mode = 'w', newline = '', encoding = 'utf-8') as f:
      csv_writer = csv.writer(f)
      for csv_line in [full_csv_header] + chemical_display_data:
        # prepend CSV, UTC time, lat/lon if not header (actual data)
        # ----------------------------------------------------------
        if line_counter > 0:
          csv_line = [source_csv, measurement_time_csv, longitude, latitude] + csv_line
        csv_writer.writerow(csv_line)
        line_counter += 1

    # return output filename of csv created
    # -------------------------------------
    return outname_csv

  def get_ge_display_data(self):
    '''
    Method to return the lower part of the CSV file (GE display with
    chemical data).

    Returns:
      list: List of chemical data and attributes + header.
    '''
    in_section = False
    header_labels = None
    chemical_lines = []

    with open(self.filename, mode = 'r', newline = '', encoding = 'latin1') as f:
      csv_reader = csv.reader(f)

      for row in csv_reader:
        # skip empty row
        # --------------
        if len(row) < 1: 
          continue

        # skip any QA info
        # ----------------
        if 'saturated' in row[0].lower():
          continue
        if 'bad pixels' in row[0].lower():
          continue

        # when we hit the line with Name, Formula, ... we are
        # in the appropriate section
        # ---------------------------------------------------
        row = list(filter(None, row))
        
        if row[0].strip().startswith('Name;Formula;Visible;Color;'):
          header_labels = row[0].split(';')
          in_section = True

        if in_section and 'formula' not in row[0].lower():
          row = row[0].split(';')
          chemical_lines.append(row)

    # remove empty entries from header
    # --------------------------------
    header_labels = list(filter(None, header_labels))

    # fill in blank entries for each chemical line
    # --------------------------------------------
    n_columns = len(header_labels)

    for chemical_line in chemical_lines:
      chemical_line.extend([''] * max(0, n_columns - len(chemical_line)))
    return [header_labels] + chemical_lines

  def get_qa_data(self) -> dict:
    '''
    Method to read the top part of the CSV file (first sheet) - QA info.
    
    Returns:
      dict: Hash with QA values.
    '''
    with open(self.filename, mode = 'r', newline = '', encoding = 'latin1') as f:
      csv_reader = csv.reader(f)

      for row in csv_reader:
        if len(row) < 1:
          continue # skip empty rows

        # remove empty entries
        # --------------------
        row = list(filter(None, row))
        first_entry = row[0].strip()
        self.qa_hash['Source_CSV'] = os.path.basename(self.filename)

        # now parse for each QA factor
        # ----------------------------
        if first_entry.startswith('Measurement time'):
          self.qa_hash['Measurement_Time_UTC'] = row[0].split(';')[1]
        if first_entry.startswith('Width'):
          self.qa_hash['Width_Pixels'] = float(row[0].split(';')[1])
        if first_entry.startswith('Height'):
          self.qa_hash['Height_Pixels'] = float(row[0].split(';')[1])
        if first_entry.startswith('OffsetX'):
          self.qa_hash['OffsetX'] = float(row[0].split(';')[1])
        if first_entry.startswith('OffsetY'):
          self.qa_hash['OffsetY'] = float(row[0].split(';')[1])
        if first_entry.lower().startswith('latitude ground'):
          self.qa_hash['Latitude_Ground_Degrees'] = float(row[0].split(';')[1])
        if first_entry.lower().startswith('longitude ground'):
          self.qa_hash['Longitude_Ground_Degrees'] = float(row[0].split(';')[1])
        if first_entry.startswith('Brightness temp percentile 25'):
          self.qa_hash['Brightness_Temp_K_Percentile_25'] = float(row[0].split(';')[1])
        if first_entry.startswith('Brightness temp percentile 50'):
          self.qa_hash['Brightness_Temp_K_Percentile_50'] = float(row[0].split(';')[1])
        if first_entry.startswith('Brightness temp percentile 75'):
          self.qa_hash['Brightness_Temp_K_Percentile_75'] = float(row[0].split(';')[1])
        if first_entry.startswith('Display Sensitivity'):
          self.qa_hash['Display_Sensitivity%'] = float(row[0].split(';')[1])
        if first_entry.startswith('Opacity min'):
          self.qa_hash['Opacity_Min%'] = float(row[0].split(';')[1])
        if first_entry.startswith('Opacity max'):
          self.qa_hash['Opacity_Max%'] = float(row[0].split(';')[1])
        if first_entry.startswith('Clean Background Fraction'):
          self.qa_hash['Clean_Background_Fraction'] = float(row[0].split(';')[1])
        if first_entry.lower().startswith('background pca energy fraction'):
          self.qa_hash['Background_PCA_Energy_Fraction'] = float(row[0].split(';')[1])
        if first_entry.startswith('Dual Test PFA'):
          self.qa_hash['Dual_Test_PFA'] = float(row[0].split(';')[1]) 
        if first_entry.startswith('Dual Test Correlation Percentile'):
          self.qa_hash['Dual_Test_Correlation_Percentile'] = float(row[0].split(';')[1])
        if first_entry.startswith('Plume Expansion PFA') and 'percentile' not in first_entry.lower():
          self.qa_hash['Plume_Expansion_PFA'] = float(row[0].split(';')[1])
        if first_entry.startswith('Plume Expansion PFA Percentile'):
          self.qa_hash['Plume_Expansion_PFA_Percentile'] = float(row[0].split(';')[1])
        if first_entry.startswith('Identification Criteria Type'):
          self.qa_hash['Identification_Criteria_Type'] = float(row[0].split(';')[1])
        if first_entry.startswith('Identification Threshold'):
          self.qa_hash['Identification_Threshold'] = float(row[0].split(';')[1])
        if first_entry.startswith('Sensitivity'):
          self.qa_hash['Sensitivity'] = float(row[0].split(';')[1])
        if first_entry.startswith('Specificity'):
          self.qa_hash['Specificity'] = float(row[0].split(';')[1])
        if first_entry.startswith('Plume Expansion') and 'pfa' not in first_entry.lower():
          self.qa_hash['Plume_Expansion'] = float(row[0].split(';')[1])
        if first_entry.lower().startswith('bad pixels'):
          self.qa_hash['Bad_Pixels'] = float(list(filter(None, row[0].split(';')))[-1])
        if first_entry.lower().startswith('saturated pixels') and 'current' not in first_entry.lower() \
                and 'counts' not in first_entry.lower():
          self.qa_hash['Saturated_Pixels'] = float(list(filter(None, row[0].split(';')))[-1])
        if first_entry.lower().startswith('saturated pixels in counts'):
          self.qa_hash['Saturated_Pixels_in_Counts'] = float(list(filter(None, row[0].split(';')))[-1])
        if first_entry.lower().startswith('saturated pixels in current'):
          self.qa_hash['Saturated_Pixels_in_Current'] = float(list(filter(None, row[0].split(';')))[-1])
    
    # return the hash with the QA values
    # ----------------------------------
    return copy.copy(self.qa_hash)

def show_version() -> None:
  '''
  Show version.
  '''
  print(f'Version: {VERSION}')
  sys.exit(0)

def show_usage(error_message: str = '') -> None:
  '''
  Show help message.

  Args:
    error_message (str): error message.

  Returns:
    None.
  '''
  print(error_message)
  print(usage_message)
  sys.exit()

def main():

  # set up command-line arguments
  # -----------------------------
  parser = argparse.ArgumentParser(description = 'telops. CSV dumper tool.')

  parser.add_argument('-d', '--directory', required = False, 
          dest = 'directory', help = 'input directory')
  parser.add_argument('-o', '--outdir', required = False, 
          dest = 'outdir', help = 'output directory')
  parser.add_argument('-v', '--version', required = False, 
          dest = 'version', action = 'store_true', help = 'show version.')
  parser.add_argument('-u', '--usage', required = False, 
          dest = 'usage', action = 'store_true', help = 'show usage message.')

  # gather actual comand-line arguments
  # -----------------------------------
  args = parser.parse_args()

  input_directory = args.directory
  outDir = args.outdir
  inDir = args.directory

  # show version of this script, or usage message, if requested
  # -----------------------------------------------------------
  version = args.version
  usage = args.usage

  if version:
    show_version()
  elif usage:
    show_usage()

  # check the input directory
  # -------------------------
  if not inDir:
    inDir = os.getcwd()
    logger.warn(f'WARNING: no input directory passed-in via --directory (-d) flag. \
            Looking for .csv files in current working directory (CWD) ...')
    
  # at this point, input directory will be either what user passed-in
  # OR the current working directory
  # -----------------------------------------------------------------
  inDir = str(inDir) 
  if not os.path.isdir(inDir):
    show_usage(f'ERROR: not an existing directory. Exiting ...')

  # if the user did not supply an output directory,
  # then set the outDir to the input directory
  # -----------------------------------------------
  if outDir and not os.path.isdir(outDir):
    loggger.warn(f'not a directory: {outDir}. Setting output directory to input dir.')

  if not outDir:
    outDir = inDir
  
  # now look for .CSV files in the input directory (or CWD)
  # -------------------------------------------------------
  csv_filenames = glob.glob(inDir + '/*.report.csv') 
  sorted(csv_filenames)

  # exit if no such .CSV files found
  # ---------------------------------
  if len(csv_filenames) < 1:
    logger.error(f'No *.report.csv files found in: {inDir}. Exiting ...')
    sys.exit(1)

  # now iterate through and process the CSV files
  # ---------------------------------------------
  qa_headers_all_csv = []
  all_ge_display_csvs = []

  for csv_filename in csv_filenames:

    csv_ob = telops_csv_file(csv_filename, outDir)
    csv_ge_display = csv_ob.write_ge_display_data_csv()
    all_ge_display_csvs.append(csv_ge_display)
    quality_info_header = csv_ob.get_qa_data()
    qa_headers_all_csv.append(quality_info_header)

  outname_csv_all_qa_headers = os.path.join(outDir, 'all_qa_headers.csv')
  if os.path.isfile(outname_csv_all_qa_headers):
    os.remove(outname_csv_all_qa_headers)
  telops_csv_file.write_all_qa_data_csv(outname_csv_all_qa_headers, qa_headers_all_csv, outDir)
  telops_csv_file.write_all_ge_display_csv(all_ge_display_csvs, outDir)

if __name__ == '__main__':
  main()
