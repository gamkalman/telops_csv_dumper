###### Telops. CSV Dumper 
    
    Python script/tool to dump contents of telops. CSV files
    to separate quality assurance (QA) and GE display data CSV files.
    Also outputted is a KML file (soon to come, as of this writing). 

###### GENERAL USAGE

    usage: telops_csv_dump.py [-h] [-d DIRECTORY] [-o OUTDIR] [-v] [-u]

    telops. CSV dumper tool.

    optional arguments:
      -h, --help            show this help message and exit
      -d DIRECTORY, --directory DIRECTORY
                        input directory
      -o OUTDIR, --outdir OUTDIR
                        output directory
      -v, --version         show version.
      -u, --usage           show usage message.
 

###### USAGE/HOW TO RUN (Windows)
 
    Place your *.report.csv files in a directory of your choice.
    Then run the script:
    $ python3 telops_csv_dump.py -d <input_directory>

    After running, the outputs should be in the output directory 
    (-o flag, optional) and look like: *.report_ge_display_data.csv
    and all_qa_headers.csv.

    Second example:
    $ python3 telops_csv_dump.py -d <input_directory> -o <output_directory>


###### VERSION
    
    Beta Version
    Last Updated: 25 October 2026

###### 3rd party Python libraries used

    The required 3rd-party Python libraries are required:
    numpy - for array manipulation and matrix computations 

###### PYTHON VERSION:
     
    Supports Python 3.8.10+
