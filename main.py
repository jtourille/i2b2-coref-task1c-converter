import argparse
import json
import logging
import os
import re
import shutil
import sys
import time
from datetime import timedelta

from i2b2.brat import generate_brat_files, i2b2_to_brat, generate_brat_conf_files
from i2b2.conll import conll_to_i2b2, conll_files_task1c
from i2b2.conll import create_conll_files
from i2b2.offset import create_offset_mapping
from i2b2.prepare import prepare_data_task1c
from i2b2.utils.misc import replace_semantic_types
from i2b2.utils.path import ensure_dir

if __name__ == "__main__":

    start = time.time()

    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(title="Sub-commands", description="Valid sub-commands",
                                       help="Valid sub-commands", dest="subparser_name")

    parser_conll_to_i2b2 = subparsers.add_parser('CONLL-TO-I2B2', help="Convert CoNLL files to i2b2 format")
    parser_conll_to_i2b2.add_argument("--input-dir", help="", dest="input_dir", type=str, required=True)
    parser_conll_to_i2b2.add_argument("--output-dir", help="", dest="output_dir", type=str, required=True)
    parser_conll_to_i2b2.add_argument("--overwrite", help="Overwrite existing documents", dest="overwrite",
                                      action="store_true")

    parser_brat = subparsers.add_parser("CREATE-BRAT", help="Create brat version of the corpus")
    parser_brat.add_argument("--input-dir", help="Directory where data is stored (step 1)", dest="input_dir",
                             type=str, required=True)
    parser_brat.add_argument("--mapping-file", help="Character mapping filepath", dest="mapping_file",
                             type=str, required=True)
    parser_brat.add_argument("--overwrite", help="Overwrite existing documents", dest="overwrite",
                             action="store_true")

    parser_conll_files = subparsers.add_parser('CREATE-CONLL', help="Create CoNLL version of the corpus")
    parser_conll_files.add_argument("--input-dir", help="Directory where data is stored (step 2)",
                                    dest="input_dir", type=str, required=True)
    parser_conll_files.add_argument("--overwrite", help="Overwrite existing documents", dest="overwrite",
                                    action="store_true")

    parser_file_mapping = subparsers.add_parser('CREATE-MAPPING', help="Create character mapping file")
    parser_file_mapping.add_argument("--source-dir", help="Directory where untouched txt files are stored",
                                     dest="source_dir", type=str, required=True)
    parser_file_mapping.add_argument("--modified-dir", help="Directory where altered text files are stored",
                                     dest="modified_dir", type=str, required=True)
    parser_file_mapping.add_argument("--target-file", help="Output mapping filepath", dest="target_file", type=str)
    parser_file_mapping.add_argument("--overwrite", help="Overwrite existing documents", dest="overwrite",
                                     action="store_true")

    parser_prepare_data = subparsers.add_parser("PREPARE-DATA", help="Process source data (decompress, sort, "
                                                                     "rename, correct)")
    parser_prepare_data.add_argument("--zip-dir", help="Path where source zip files are stored", dest="zip_dir",
                                     type=str, required=True)
    parser_prepare_data.add_argument("--output-dir", help="Path where output files will be created",
                                     dest="output_dir", type=str, required=True)
    parser_prepare_data.add_argument("--correction-file", help="Path to annotation correction json file",
                                     dest="correction_file", type=str, required=True)
    parser_prepare_data.add_argument("--overwrite", help="Overwrite existing documents", dest="overwrite",
                                     action="store_true")

    parser_regroup = subparsers.add_parser("REGROUP-FILES", help="Regroup files for mapping creation")
    parser_regroup.add_argument("--input-dir", help="Directory where data is stored", dest="input_dir",
                                type=str, required=True)
    parser_regroup.add_argument("--overwrite", help="Overwrite existing documents", dest="overwrite",
                                action="store_true")

    parser_remove = subparsers.add_parser('REMOVE-TYPES', help="Change all semantic types to procedure")
    parser_remove.add_argument("--input-dir", help="Path where prepared data is stored", dest="input_dir",
                               type=str, required=True)
    parser_remove.add_argument("--overwrite", help="Overwrite existing documents", dest="overwrite",
                               action="store_true")

    parser_run_to_conll = subparsers.add_parser('RUN-TO-CONLL', help="Convert one run to CoNLL")
    parser_run_to_conll.add_argument("--input-dir", help="Path where the run is stored", dest="input_dir",
                                     type=str, required=True)
    parser_run_to_conll.add_argument("--output-dir", help="Path where the CoNLL version will be stored",
                                     dest="output_dir", type=str, required=True)
    parser_run_to_conll.add_argument("--gs-conll-dir", help="Path where the gs CoNLL files are stored",
                                     dest="gs_conll_dir", type=str, required=True)
    parser_run_to_conll.add_argument("--mapping-file", help="Character mapping filepath", dest="mapping_file",
                                     type=str, required=True)
    parser_run_to_conll.add_argument("--overwrite", help="Overwrite existing documents", dest="overwrite",
                                     action="store_true")

    args = parser.parse_args()

    log = logging.getLogger('')
    log_format = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

    log.setLevel(logging.INFO)

    # Adding a stdout handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(log_format)
    log.addHandler(ch)

    if args.subparser_name == "CONLL-TO-I2B2":

        if not os.path.isdir(args.input_dir):
            raise NotADirectoryError("The input path does not exist: {}".format(
                os.path.abspath(args.input_dir)
            ))

        if not args.overwrite:
            if os.path.isdir(args.output_dir):
                logging.info("The output path already exists, use the appropriate launcher flag to overwrite")
                raise IsADirectoryError("The output directory already exists: {}".format(
                    args.output_dir
                ))

        if os.path.isdir(os.path.abspath(args.output_dir)):
            shutil.rmtree(os.path.abspath(args.output_dir))

        ensure_dir(args.output_dir)

        conll_to_i2b2(
            os.path.abspath(args.input_dir),
            os.path.abspath(args.output_dir)
        )

    elif args.subparser_name == "CREATE-BRAT":

        if not os.path.isfile(os.path.abspath(args.mapping_file)):
            raise NotADirectoryError("The mapping file does not exist: {}".format(
                os.path.abspath(args.mapping_file)
            ))

        output_dir = os.path.join(os.path.abspath(args.input_dir), "brat-raw")
        if not args.overwrite:
            if os.path.isdir(output_dir):
                logging.info("The output directory already exists, use the appropriate flag to overwrite")
                raise IsADirectoryError("The output directory already exists: {}".format(
                    output_dir
                ))

        if os.path.isdir(os.path.abspath(output_dir)):
            shutil.rmtree(os.path.abspath(output_dir))

        ensure_dir(output_dir)

        generate_brat_files(
            input_dir=os.path.abspath(args.input_dir),
            output_dir=os.path.abspath(output_dir),
            mapping_file_path=os.path.abspath(args.mapping_file)
        )

    elif args.subparser_name == "CREATE-CONLL":

        brat_dir = os.path.join(os.path.abspath(args.input_dir), "brat-raw")
        if not os.path.isdir(brat_dir):
            raise NotADirectoryError("The brat directory does not exist: {}".format(
                os.path.abspath(brat_dir)
            ))

        gs_dir = os.path.join(os.path.abspath(args.input_dir), "gold-standard-sorted")
        if not os.path.isdir(gs_dir):
            raise NotADirectoryError("The gs directory does not exist: {}".format(
                os.path.abspath(gs_dir)
            ))

        output_dir = os.path.join(os.path.abspath(args.input_dir), "conll")
        if not args.overwrite:
            if os.path.isdir(output_dir):
                logging.info("The output directory already exists, use the appropriate launcher flag to overwrite")
                raise IsADirectoryError("The output directory already exists: {}".format(
                    output_dir
                ))

        if os.path.isdir(os.path.abspath(output_dir)):
            shutil.rmtree(os.path.abspath(output_dir))

        ensure_dir(output_dir)

        create_conll_files(
            brat_dir=brat_dir,
            gs_dir=gs_dir,
            output_dir=output_dir,
        )

    elif args.subparser_name == "CREATE-MAPPING":

        if not os.path.isdir(os.path.abspath(args.source_dir)):
            raise NotADirectoryError("The input directory does not exist: {}".format(
                os.path.abspath(args.source_dir)
            ))

        if not os.path.isdir(os.path.abspath(args.modified_dir)):
            raise NotADirectoryError("The input directory does not exist: {}".format(
                os.path.abspath(args.modified_dir)
            ))

        if not args.overwrite:
            if os.path.isfile(os.path.abspath(args.target_file)):
                raise FileExistsError("The output file already exists: {}".format(
                    os.path.abspath(args.target_file)
                ))

        if os.path.isfile(os.path.abspath(args.target_file)):
            os.remove(os.path.abspath(args.target_file))

        create_offset_mapping(
            os.path.abspath(args.source_dir),
            os.path.abspath(args.modified_dir),
            os.path.abspath(args.target_file)
        )

    elif args.subparser_name == "PREPARE-DATA":

        if not os.path.isdir(os.path.abspath(args.zip_dir)):
            raise NotADirectoryError("The source directory does not exist: {}".format(
                os.path.abspath(args.zip_dir)
            ))

        if not os.path.isfile(os.path.abspath(args.correction_file)):
            raise FileNotFoundError("The correction file does not exist: {}".format(
                os.path.abspath(args.correction_file)
            ))

        if not args.overwrite:
            if os.path.isdir(os.path.abspath(args.output_dir)):
                logging.info("The output directory already exists, use the appropriate flag to overwrite")
                raise IsADirectoryError("The output directory already exists: {}".format(
                    os.path.abspath(args.output_dir)
                ))

        if os.path.isdir(os.path.abspath(args.output_dir)):
            shutil.rmtree(os.path.abspath(args.output_dir))

        ensure_dir(args.output_dir)

        prepare_data_task1c(
            input_dir=os.path.abspath(args.zip_dir),
            output_dir=os.path.abspath(args.output_dir),
            correction_file=os.path.abspath(args.correction_file)
        )

    elif args.subparser_name == "REGROUP-FILES":

        input_dir = os.path.join(os.path.abspath(args.input_dir), "gold-standard-flatten")
        if not os.path.isdir(input_dir):
            raise NotADirectoryError("The input directory does not exists: {}".format(
                input_dir
            ))

        output_dir = os.path.join(os.path.abspath(args.input_dir), "mapping")
        if not args.overwrite:
            if os.path.isdir(output_dir):
                logging.info("The output directory already exists, use the appropriate flag to overwrite")
                raise IsADirectoryError("The output directory already exists: {}".format(
                    output_dir
                ))

        if os.path.isdir(os.path.abspath(output_dir)):
            shutil.rmtree(os.path.abspath(output_dir))

        ensure_dir(output_dir)

        target_modified_dir = os.path.join(output_dir, "modified")
        target_untouched_dir = os.path.join(output_dir, "untouched")

        ensure_dir(target_modified_dir)
        ensure_dir(target_untouched_dir)

        for root, dirs, files in os.walk(input_dir):
            for filename in files:
                if re.match("^.*\.txt$", filename):
                    source_txt_filepath = os.path.join(root, filename)
                    target_modified_filepath = os.path.join(target_modified_dir, filename)
                    target_untouched_filepath = os.path.join(target_untouched_dir, filename)

                    shutil.copy(source_txt_filepath, target_modified_dir)
                    shutil.copy(source_txt_filepath, target_untouched_dir)

    elif args.subparser_name == "REMOVE-TYPES":

        input_dir = os.path.join(os.path.abspath(args.input_dir), "gold-standard-flatten")
        if not os.path.isdir(input_dir):
            raise NotADirectoryError("The input directory does not exists: {}".format(
                input_dir
            ))

        output_dir = os.path.join(os.path.abspath(args.input_dir), "gold-standard-flatten-replace")
        if not args.overwrite:
            if os.path.isdir(output_dir):
                logging.info("The output directory already exists, use the appropriate launcher flag to overwrite")
                raise IsADirectoryError("The output directory already exists: {}".format(
                    output_dir
                ))

        if os.path.isdir(os.path.abspath(output_dir)):
            shutil.rmtree(os.path.abspath(output_dir))

        ensure_dir(output_dir)

        replace_semantic_types(input_dir, output_dir)

    elif args.subparser_name == "RUN-TO-CONLL":

        if not os.path.isfile(os.path.abspath(args.mapping_file)):
            raise NotADirectoryError("The mapping file does not exist: {}".format(
                os.path.abspath(args.mapping_file)
            ))

        if not os.path.isdir(os.path.abspath(args.input_dir)):
            raise IsADirectoryError("The input directory does not exist: {}".format(
                os.path.abspath(args.input_dir)
            ))

        if not os.path.isdir(os.path.abspath(args.gs_conll_dir)):
            raise IsADirectoryError("The GS CoNLL directory does not exist: {}".format(
                os.path.abspath(args.gs_conll_dir)
            ))

        if not args.overwrite:
            if os.path.isdir(os.path.abspath(args.output_dir)):
                logging.info("The output directory already exists, use the appropriate launcher flag to overwrite")
                raise IsADirectoryError("The output directory already exists: {}".format(
                    os.path.abspath(args.output_dir)
                ))

        if os.path.isdir(os.path.abspath(os.path.abspath(args.output_dir))):
            shutil.rmtree(os.path.abspath(os.path.abspath(args.output_dir)))

        ensure_dir(os.path.abspath(args.output_dir))

        brat_dir = os.path.join(os.path.abspath(args.output_dir), "brat")
        conll_dir = os.path.join(os.path.abspath(args.output_dir), "conll")

        ensure_dir(brat_dir)
        ensure_dir(conll_dir)

        # Loading character mapping
        with open(os.path.abspath(args.mapping_file), "r", encoding="UTF-8") as input_file:
            char_mapping = json.load(input_file)

        i2b2_to_brat(os.path.abspath(args.input_dir),
                     brat_dir,
                     char_mapping)

        generate_brat_conf_files(brat_dir)

        conll_files_task1c(brat_dir=brat_dir,
                           gs_dir=os.path.abspath(args.gs_conll_dir),
                           output_dir=conll_dir)

        target_conll_file = os.path.join(os.path.abspath(args.output_dir), "all.conll")

        with open(target_conll_file, "w", encoding="UTF-8") as output_file:
            for dirname in os.listdir(conll_dir):
                for root, dirs, files in os.walk(os.path.join(conll_dir, dirname)):
                    for filename in files:
                        if re.match("^.*\.conll$", filename):
                            with open(os.path.join(root, filename), "r", encoding="UTF-8") as input_file:
                                for line in input_file:
                                    output_file.write(line)

    end = time.time()

    logging.info("Done ! (Time elapsed: {})".format(timedelta(seconds=round(end - start))))
