import json
import os
import re
import shutil
import tarfile
import zipfile

from .utils.path import ensure_dir

TASK1C_COMPRESSED_FILES = [
    "i2b2_Beth_Train_Release.tar.gz",
    "i2b2_Partners_Train_Release.tar.gz",
    "Task_1C.zip",
    "Test-ground-truth-Beth-Partners_111004.tar.gz"
]

TASK1C_DESTINATION_PATHS = [
    "PARTNERS/chains",
    "PARTNERS/concepts",
    "PARTNERS/docs",
    "PARTNERS/pairs",

    "BETH/chains",
    "BETH/concepts",
    "BETH/docs",
    "BETH/pairs",
]

TASK1C_DOC_PATHS = {
    "task1c/train/BETH/docs": "i2b2_Beth_Train_Release/Beth_Train/docs",
    "task1c/test/BETH/docs": "Task_1C/i2b2_Test/i2b2_Beth_Test/docs",

    "task1c/train/PARTNERS/docs": "i2b2_Partners_Train_Release/Partners_Train/docs",
    "task1c/test/PARTNERS/docs": "Task_1C/i2b2_Test/i2b2_Partners_Test/docs",
}

TASK1C_CONCEPT_PATHS = {
    "task1c/train/BETH/concepts": "i2b2_Beth_Train_Release/Beth_Train/concepts",
    "task1c/test/BETH/concepts": "Task_1C/i2b2_Test/i2b2_Beth_Test/concepts",

    "task1c/train/PARTNERS/concepts": "i2b2_Partners_Train_Release/Partners_Train/concepts",
    "task1c/test/PARTNERS/concepts": "Task_1C/i2b2_Test/i2b2_Partners_Test/concepts",
}

TASK1C_CHAIN_PATHS = {
    "task1c/train/BETH/chains": "i2b2_Beth_Train_Release/Beth_Train/chains",
    "task1c/test/BETH/chains": "Test-ground-truth-Beth-Partners_111004/Test-ground-truth-Beth-Partners/"
                               "Task_1C/i2b2_Test/i2b2_Beth_Test/chains",
    "task1c/train/PARTNERS/chains": "i2b2_Partners_Train_Release/Partners_Train/chains",
    "task1c/test/PARTNERS/chains": "Test-ground-truth-Beth-Partners_111004/Test-ground-truth-Beth-Partners/"
                                   "Task_1C/i2b2_Test/i2b2_Partners_Test/chains",
}

TASK1C_PAIR_PATHS = {
    "task1c/train/BETH/pairs": "i2b2_Beth_Train_Release/Beth_Train/pairs",
    "task1c/train/PARTNERS/pairs": "i2b2_Partners_Train_Release/Partners_Train/pairs",
}


def copy_chain_files(input_dir: str, output_dir: str, ann_corrections: dict) -> None:
    """
    Copy chain files.
    Perform renaming when necessary.
    Correct annotation according to the corrections provided.

    Args:
        input_dir (str): input directory where chains files are stored
        output_dir (str): target directory where chain files will be copied
        ann_corrections (dict): annotation corrections
    """

    for filename in os.listdir(input_dir):
        source_filepath = os.path.join(input_dir, filename)

        if re.match("^.*\.txt\.chains$", filename):
            doc_id = filename.split(".")[0]
            target_filepath = "{}.chains".format(os.path.join(output_dir, doc_id))

        elif re.match("^.*\.chains$", filename):
            doc_id = filename.split(".")[0]
            target_filepath = "{}.chains".format(os.path.join(output_dir, doc_id))

        else:
            doc_id = filename
            target_filepath = "{}.txt".format(os.path.join(output_dir, doc_id))

        with open(source_filepath, "r", encoding="UTF-8") as input_file:
            with open(target_filepath, "w", encoding="UTF-8") as output_file:
                for i, line in enumerate(input_file):
                    if doc_id in ann_corrections:
                        if "chains" in ann_corrections[doc_id]:
                            if str(i) in ann_corrections[doc_id]["chains"]:
                                output_file.write(ann_corrections[doc_id]["chains"][str(i)])
                                continue

                    output_file.write(line)


def copy_con_files(input_dir: str, output_dir: str, ann_corrections: dict) -> None:
    """
    Copy concept files.
    Perform renaming when necessary.
    Correct annotation according to the corrections provided.

    Args:
        input_dir (str):
        output_dir (str):
        ann_corrections (dict):
    """

    for filename in os.listdir(input_dir):
        source_filepath = os.path.join(input_dir, filename)

        if re.match("^.*\.txt\.concept$", filename):
            doc_id = filename.split(".")[0]
            target_filepath = "{}.con".format(os.path.join(output_dir, doc_id))

        elif re.match("^.*\.concept$", filename):
            doc_id = filename.split(".")[0]
            target_filepath = "{}.con".format(os.path.join(output_dir, doc_id))

        elif re.match("^.*\.txt\.con$", filename):
            doc_id = filename.split(".")[0]
            target_filepath = "{}.con".format(os.path.join(output_dir, doc_id))

        elif re.match("^.*\.con$", filename):
            doc_id = filename.split(".")[0]
            target_filepath = "{}.con".format(os.path.join(output_dir, doc_id))

        else:
            doc_id = filename
            target_filepath = "{}.txt".format(os.path.join(output_dir, doc_id))

        with open(source_filepath, "r", encoding="UTF-8") as input_file:
            with open(target_filepath, "w", encoding="UTF-8") as output_file:
                for i, line in enumerate(input_file):
                    if doc_id in ann_corrections:
                        if "concepts" in ann_corrections[doc_id]:
                            if str(i) in ann_corrections[doc_id]["concepts"]:
                                output_file.write(ann_corrections[doc_id]["concepts"][str(i)])
                                continue

                    output_file.write(line)


def copy_doc_files(input_dir: str, output_dir: str) -> None:
    """
    Copy text files.
    Perform renaming when necessary.

    Args:
        input_dir (str): input directory where text files are stored
        output_dir (str): target directory where text files will be copied
    """

    for filename in os.listdir(input_dir):
        source_filepath = os.path.join(input_dir, filename)

        if re.match("^.*\.txt$", filename):
            target_filepath = os.path.join(output_dir, filename)
        else:
            target_filepath = "{}.txt".format(os.path.join(output_dir, filename))

        shutil.copy(source_filepath, target_filepath)


def copy_pair_files(input_dir: str, output_dir: str) -> None:
    """
    Copy pair files.
    Perform renaming when necessary.

    Args:
        input_dir (str): input directory where pair files are stored
        output_dir (str): target directory where pair files will be copied
    """

    for filename in os.listdir(input_dir):
        source_filepath = os.path.join(input_dir, filename)

        if re.match("^.*\.txt\.pairs$", filename):
            doc_id = filename.split(".")
            target_filepath = "{}.pairs".format(os.path.join(output_dir, doc_id[0]))

        else:
            target_filepath = "{}.pairs".format(os.path.join(output_dir, filename))

        shutil.copy(source_filepath, target_filepath)


def flatten(input_dir: str, output_dir: str) -> None:
    """
    Flatten an i2b2 directory structure

    Args:
        input_dir (str): input i2b2 directory
        output_dir (str): output directory where chains, concepts and docs files will be created
    """

    # Creating subdirectories
    chain_dir = os.path.join(os.path.abspath(output_dir), "chains")
    concept_dir = os.path.join(os.path.abspath(output_dir), "concepts")
    doc_dir = os.path.join(os.path.abspath(output_dir), "docs")

    ensure_dir(chain_dir)
    ensure_dir(concept_dir)
    ensure_dir(doc_dir)

    for root, dirs, files in os.walk(os.path.abspath(input_dir)):
        for filename in files:
            if re.match("^.*\.chains$", filename):
                shutil.copy(os.path.join(root, filename), chain_dir)

            elif re.match("^.*\.con", filename):
                shutil.copy(os.path.join(root, filename), concept_dir)

            elif re.match("^.*\.txt", filename):
                shutil.copy(os.path.join(root, filename), doc_dir)


def prepare_data_task1c(input_dir: str, output_dir: str, correction_file: str) -> None:
    """
    Prepare task1c documents (decompress, rename, correct and sort).
    The function creates two subdirectories within output_dir:
    * decompressed: zip files are decompressed into this directory
    * gold-standard-sorted/task1c: chain, text and concept files are sorted, renamed, corrected and put in
    this directory according to the corpus part they belong to
    * gold-standard-flatten/task1c: all chain, text and concept files are regrouped together to facilitate evaluation

    Args:
        input_dir: directory where zip files are stored
        output_dir: working directory where files will decompressed and sorted
        correction_file: annotation correction JSON file path
    """

    # Directory where zip will be decompressed
    target_uncompressed_path = os.path.join(os.path.abspath(output_dir), "decompressed")
    ensure_dir(target_uncompressed_path)

    # Verifying that compressed files exist
    for filename in TASK1C_COMPRESSED_FILES:
        if not os.path.isfile(os.path.join(input_dir, filename)):
            raise FileNotFoundError("One file is missing: {}".format(filename))

    # Decompressing compressed files
    for filename in TASK1C_COMPRESSED_FILES:
        if filename.endswith(".zip"):
            source_file_path = os.path.join(input_dir, filename)
            target_path = os.path.join(target_uncompressed_path, filename[:-4])

            zip_file = zipfile.ZipFile(source_file_path, 'r')
            zip_file.extractall(target_path)
            zip_file.close()

        elif filename.endswith(".tar.gz"):
            source_file_path = os.path.join(input_dir, filename)
            target_path = os.path.join(target_uncompressed_path, filename[:-7])

            tar_file = tarfile.open(source_file_path, "r:gz")
            tar_file.extractall(target_path)
            tar_file.close()

    # Preparing directory structure in the target directory
    destination_directory = os.path.join(output_dir, "gold-standard-sorted")
    prepare_destination_directory_task1c(destination_directory)

    # Loading annotation corrections
    with open(os.path.abspath(correction_file), "r", encoding="UTF-8") as input_file:
        ann_corrections = json.load(input_file)

    # Copying text files
    for sub_path, doc_path in TASK1C_DOC_PATHS.items():
        source_path = os.path.join(target_uncompressed_path, doc_path)
        target_path = os.path.join(destination_directory, sub_path)

        copy_doc_files(source_path, target_path)

    # Copying concept files
    for sub_path, doc_path in TASK1C_CONCEPT_PATHS.items():
        source_path = os.path.join(target_uncompressed_path, doc_path)
        target_path = os.path.join(destination_directory, sub_path)

        copy_con_files(source_path, target_path, ann_corrections)

    # Copying chain files
    for sub_path, doc_path in TASK1C_CHAIN_PATHS.items():
        source_path = os.path.join(target_uncompressed_path, doc_path)
        target_path = os.path.join(destination_directory, sub_path)

        copy_chain_files(source_path, target_path, ann_corrections)

    # Copying pair files
    for sub_path, doc_path in TASK1C_PAIR_PATHS.items():
        source_path = os.path.join(target_uncompressed_path, doc_path)
        target_path = os.path.join(destination_directory, sub_path)

        copy_pair_files(source_path, target_path)

    # Flattening structures
    input_train_dir = os.path.join(destination_directory, "task1c", "train")
    output_flatten_train_dir = os.path.join(output_dir, "gold-standard-flatten", "task1c", "train")

    input_test_dir = os.path.join(destination_directory, "task1c", "test")
    output_flatten_test_dir = os.path.join(output_dir, "gold-standard-flatten", "task1c", "test")

    flatten(input_train_dir, output_flatten_train_dir)
    flatten(input_test_dir, output_flatten_test_dir)


def prepare_destination_directory_task1c(destination_directory: os.path) -> None:
    """
    Prepare directory structure for task1c files

    Args:
        destination_directory: destination directory where the structure must be created
    """

    for subdirectory in TASK1C_DESTINATION_PATHS:
        task1a_train_target_path = os.path.join(destination_directory, "task1c", "train", subdirectory)
        task1a_test_target_path = os.path.join(destination_directory, "task1c", "test", subdirectory)

        ensure_dir(task1a_train_target_path)
        ensure_dir(task1a_test_target_path)
