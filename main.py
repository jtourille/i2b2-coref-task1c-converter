import argparse
import logging
import os
import re
import shutil
import sys
import time
from datetime import timedelta

from i2b2.brat import generate_brat_files
from i2b2.conll import create_conll_files
from i2b2.offset import create_offset_mapping
from i2b2.prepare import prepare_data_task1c
from i2b2.utils.path import ensure_dir

if __name__ == "__main__":

    start = time.time()

    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(title="Sub-commands", description="Valid sub-commands",
                                       help="Valid sub-commands", dest="subparser_name")

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

    args = parser.parse_args()

    log = logging.getLogger('')
    log_format = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

    log.setLevel(logging.INFO)

    # Adding a stdout handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(log_format)
    log.addHandler(ch)

    if args.subparser_name == "CREATE-BRAT":

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

    end = time.time()

    logging.info("Done ! (Time elapsed: {})".format(timedelta(seconds=round(end - start))))
