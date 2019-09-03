import json
import logging
import os
import re

from .utils.brat import generate_brat_conf_files
from .utils.misc import find_ngrams
from .utils.path import ensure_dir, get_other_extension


def generate_brat_files(input_dir: str, output_dir: str, mapping_file_path: str) -> None:
    """
    Generate brat version of the corpus

    Args:
        input_dir: working directory where ZIP files have been decompressed and sorted
        output_dir: path where brat files will be created
        mapping_file_path: mapping file with character mapping
    """

    # Loading character mapping
    with open(mapping_file_path, "r", encoding="UTF-8") as input_file:
        char_mapping = json.load(input_file)

    input_path_i2b2 = os.path.join(os.path.abspath(input_dir), "gold-standard-sorted")

    # Setting up task1c output directories
    input_path_task1c_train = os.path.join(input_path_i2b2, "task1c", "train")
    output_path_task1c_train = os.path.join(output_dir, "task1c", "train")

    input_path_task1c_test = os.path.join(input_path_i2b2, "task1c", "test")
    output_path_task1c_test = os.path.join(output_dir, "task1c", "test")

    # Converting i2b2 formatted files to brat
    i2b2_to_brat(input_path_task1c_train, output_path_task1c_train, char_mapping)
    i2b2_to_brat(input_path_task1c_test, output_path_task1c_test, char_mapping)

    # Generating configuration files for brat visualization
    generate_brat_conf_files(os.path.join(output_dir, "task1c"))


def get_splits(doc_filepath: str) -> dict:
    """
    Fetch i2b2 -> char mapping for a given document.

    Args:
        doc_filepath (str): document filepath

    Returns:
        dict: mapping
    """

    all_rets = dict()

    old_global_start = 0
    global_start = 0

    with open(doc_filepath, "r", encoding="UTF-8") as input_file:
        for i, line in enumerate(input_file, start=1):
            chunks = re.split(r"[\s]", line.rstrip("\n"))
            current_ret = list()

            for j, chunk in enumerate(chunks):
                if len(chunk) == 0:
                    if j == 0:
                        current_ret.append((
                            chunk, global_start, global_start + len(chunk)
                        ))
                        global_start += len(chunk) + 1

                    elif j != 0:
                        global_start += 1
                        continue
                else:
                    current_ret.append((
                        chunk, global_start, global_start + len(chunk)
                    ))
                    global_start += len(chunk) + 1

            all_rets[i] = current_ret
            old_global_start += len(line)
            global_start = old_global_start

    return all_rets


def i2b2_to_brat(input_dir: str, output_dir: str, char_mapping: dict) -> None:
    """
    Convert an i2b2 corpus part to brat

    Args:
        input_dir (str): input i2b2 corpus
        output_dir (str): output directory where brat file will be created
        char_mapping (dict): char mapping used during text file copying process
    """

    # Matching regex for concept
    regex_concept = re.compile(r'^c="(.*)" (\d+):(\d+) (\d+):(\d+)\|\|t="(.*)"$')

    for dirname in os.listdir(input_dir):
        # Computing current output_dir for current processed dir
        current_output_dir = os.path.join(output_dir, dirname)
        ensure_dir(current_output_dir)

        # Computing source directory paths
        doc_dir = os.path.join(input_dir, dirname, "docs")
        concepts_dir = os.path.join(input_dir, dirname, "concepts")
        chains_dir = os.path.join(input_dir, dirname, "chains")

        for filename in os.listdir(doc_dir):
            concept_annotations = dict()

            concept_file_path = os.path.join(concepts_dir, get_other_extension(filename, "con"))
            chain_file_path = os.path.join(chains_dir, get_other_extension(filename, "chains"))

            if not os.path.isfile(chain_file_path):
                chain_file_path = os.path.join(chains_dir, get_other_extension(filename, "txt.chains"))

            with open(concept_file_path, "r", encoding="UTF-8") as con_file:
                for line in con_file:
                    match = regex_concept.match(line)  # Match a concept

                    if match:
                        concept_str = match.group(1)
                        concept_line_start = int(match.group(2))
                        concept_start = int(match.group(3))
                        concept_line_end = int(match.group(4))
                        concept_end = int(match.group(5))
                        concept_type = match.group(6)

                        if concept_line_start not in concept_annotations:
                            concept_annotations[concept_line_start] = list()

                        payload = (concept_line_start, concept_start, concept_line_end, concept_end, concept_str,
                                   concept_type)

                        if payload in concept_annotations[concept_line_start]:
                            logging.info("Skipping one mention in {} (already exists): {}".format(
                                os.path.join(dirname, filename),
                                line.rstrip("\n")
                            ))

                        # Appending the concept to the line
                        concept_annotations[concept_line_start].append((
                            concept_line_start, concept_start, concept_line_end, concept_end, concept_str, concept_type
                        ))

                pairs = list()

                # Fetching coreference pairs
                with open(chain_file_path, "r", encoding="UTF-8") as ch_file:
                    for line in ch_file:
                        concepts = line.split("||")

                        # Extracting chain type
                        type_chain_str = concepts[-1]
                        type_chain = re.match(r"t=\"coref\s(.*)\"", type_chain_str).group(1)

                        regex_mention = re.compile(r"c=\"(.*)\" (\d+):(\d+) (\d+):(\d+)")

                        # Creating mention pairs by going over concept ngrams
                        for mention_1_str, mention_2_str in find_ngrams(concepts[:-1], 2):
                            match_1 = regex_mention.match(mention_1_str)
                            match_2 = regex_mention.match(mention_2_str)

                            match_1_str = match_1.group(1).lower()
                            match_2_str = match_2.group(1).lower()

                            item_1 = "{}#{}:{}#{}:{}".format(
                                match_1_str,
                                match_1.group(2),
                                match_1.group(3),
                                match_1.group(4),
                                match_1.group(5)
                            )

                            item_2 = "{}#{}:{}#{}:{}".format(
                                match_2_str,
                                match_2.group(2),
                                match_2.group(3),
                                match_2.group(4),
                                match_2.group(5)
                            )

                            pairs.append((item_1, item_2, "coref_{}".format(type_chain)))

            # Setting up target filenames
            target_txt_filename = os.path.join(current_output_dir, filename)
            target_ann_filename = os.path.join(current_output_dir, get_other_extension(filename, "ann"))

            # Reading text file content (UTF-8)
            with open(os.path.join(doc_dir, filename), "r", encoding="UTF-8") as input_file:
                content = input_file.read()

            # Replacing characters when necessary
            if filename in char_mapping:
                for idx, (source, target) in char_mapping[filename].items():
                    content = content[:int(idx)] + target + content[int(idx) + 1:]
                    assert len(target) == len(source)

            # Dumping content to target files
            with open(target_txt_filename, "w", encoding="UTF-8") as output_file:
                output_file.write(content)

            # Re-reading file from disk
            with open(target_txt_filename, "r", encoding="UTF-8") as input_file:
                content = input_file.read()

            brat_entities = dict()

            with open(os.path.join(doc_dir, filename), "r", encoding="UTF-8") as txt_file:
                with open(target_ann_filename, "w", encoding="UTF-8") as output_file:

                    all_rets = get_splits(os.path.join(doc_dir, filename))

                    line_counter = 1
                    id_entity_counter = 1
                    id_relation_counter = 1

                    for _ in txt_file:
                        if line_counter in concept_annotations:
                            for concept_line_start, concept_token_start, concept_line_end, concept_token_end, \
                                concept_str, concept_type in concept_annotations[line_counter]:

                                current_concept_start = concept_token_start
                                current_concept_end = concept_token_end

                                try:
                                    entity_start = all_rets[concept_line_start][current_concept_start][1]
                                    entity_end = all_rets[concept_line_end][current_concept_end][2]
                                    entity_str = content[entity_start:entity_end]
                                    entity_type = concept_type
                                except:
                                    print(all_rets[concept_line_start])
                                    print(concept_line_start, current_concept_start, current_concept_end)
                                    raise

                                if entity_start >= entity_end:
                                    print(filename)
                                    print(all_rets[concept_line_start])
                                    print(concept_line_start, current_concept_start, current_concept_end)

                                # Computing entity hash for brat-entity-id mapping
                                entity_hash = "{}#{}:{}#{}:{}".format(
                                    concept_str.lower(),
                                    concept_line_start,
                                    concept_token_start,
                                    concept_line_end,
                                    concept_token_end
                                )

                                entity_str_tmp = entity_str.lstrip()
                                diff = len(entity_str) - len(entity_str_tmp)
                                if diff > 0:
                                    entity_start += diff
                                    entity_str = entity_str[diff:]

                                entity_str_tmp = entity_str.lstrip()
                                diff = len(entity_str) - len(entity_str_tmp)
                                if diff > 0:
                                    entity_end -= diff

                                brat_entities[entity_hash] = id_entity_counter

                                output_file.write("T{}\t{} {}\t{}\n".format(
                                    id_entity_counter,
                                    entity_type,
                                    "{} {}".format(entity_start, entity_end),
                                    entity_str
                                ))

                                id_entity_counter += 1

                        line_counter += 1

                    for item_1, item_2, rel_type in pairs:
                        output_file.write("R{}\t{} Arg1:T{} Arg2:T{}\n".format(
                            id_relation_counter,
                            rel_type,
                            brat_entities[item_2],
                            brat_entities[item_1]
                        ))

                        id_relation_counter += 1
