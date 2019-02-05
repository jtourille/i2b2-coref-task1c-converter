import os
import re

import networkx as nx

from .utils.brat import parse_ann_file
from .utils.path import ensure_dir, remove_abs, get_other_extension
from .utils.span import overlap


def create_conll_files(brat_dir: str, gs_dir: str, output_dir: str) -> None:
    """
    Create CoNLL-formatted files

    Args:
        brat_dir (str): directory where brat files are stored
        gs_dir (str): directory where gold-standard files are stored
        output_dir (str): directory where CoNLL files will be stored

    Returns:
        None
    """

    # Setting up paths
    task1c_input_brat_dir = os.path.join(os.path.abspath(brat_dir), "task1c")
    task1c_input_gs_dir = os.path.join(os.path.abspath(gs_dir), "task1c")
    task1c_output_dir = os.path.join(os.path.abspath(output_dir), "task1c")

    ensure_dir(task1c_output_dir)

    # CoNLL file creation for task1c
    conll_files_task1c(
        brat_dir=task1c_input_brat_dir,
        gs_dir=task1c_input_gs_dir,
        output_dir=task1c_output_dir
    )

    for dirname in os.listdir(task1c_output_dir):
        target_conll_file = os.path.join(task1c_output_dir, "{}.conll".format(dirname))

        with open(target_conll_file, "w", encoding="UTF-8") as output_file:
            for root, dirs, files in os.walk(os.path.join(task1c_output_dir, dirname)):
                for filename in files:
                    if re.match("^.*\.conll$", filename):
                        with open(os.path.join(root, filename), "r", encoding="UTF-8") as input_file:
                            for line in input_file:
                                output_file.write(line)


def conll_files_task1c(brat_dir: str, gs_dir: str, output_dir: str) -> None:
    """
    Create CoNLL-formatted files for task 1C

    Args:
        brat_dir (str): directory where brat files are stored
        gs_dir (str): directory where gold-standard files are stored
        output_dir (str): directory where CoNLL files will be stored

    Returns:
        None
    """
    for root, dirs, files in os.walk(os.path.abspath(brat_dir)):
        for filename in files:
            if re.match("^.*\.ann$", filename):
                subdir = remove_abs(re.sub(re.escape(os.path.abspath(brat_dir)), "", root))

                # Setting up source paths
                source_ann_filepath = os.path.join(root, filename)
                source_txt_filepath = os.path.join(root, get_other_extension(filename, "txt"))

                # Fetching sentence and token offsets following the i2b2 format
                splits = get_splits(source_txt_filepath)

                target_conll_dir = os.path.join(os.path.abspath(output_dir), subdir)
                ensure_dir(target_conll_dir)

                # Target CoNLL file path
                target_conll_file = os.path.join(target_conll_dir, get_other_extension(filename, "conll"))

                # Extracting sentences
                modified_splits = get_splits(source_txt_filepath)

                sentences = list()
                for line_counter, ret in modified_splits.items():
                    if len(ret) == 0:
                        continue

                    new_sentence = {
                        "tokens": list()
                    }
                    all_spans = list()

                    for t_counter, (t_str, t_begin, t_end) in enumerate(ret):
                        if len(t_str) == 0:
                            continue

                        new_token = {
                            "begin": t_begin,
                            "end": t_end,
                            "text": t_str,
                            "conll_begin": list(),
                            "conll_end": list(),
                            "conll_unique": list(),
                            "gs_tokens": get_i2b2_mapping(t_begin, t_end, splits)
                        }

                        if len(new_token["gs_tokens"]) == 0:
                            raise Exception("One token does not have a gs mapping")

                        all_spans.append(t_begin)
                        all_spans.append(t_end)

                        new_sentence["tokens"].append(new_token)

                        new_sentence["begin"] = min(all_spans)
                        new_sentence["end"] = max(all_spans)

                    sentences.append(new_sentence)

                # Extracting entities, relations
                entities, relations = parse_ann_file(source_ann_filepath)
                extracted_chains = extract_chains_with_networkx(relations)

                # Setting up tokens labels
                chain_id = 0
                for chain in extracted_chains:

                    for e_id in chain:
                        current_entity = list()

                        e_begin = entities[e_id]["spans"][0][0]
                        e_end = entities[e_id]["spans"][0][1]

                        for s, sentence in enumerate(sentences):
                            for t, token in enumerate(sentence["tokens"]):
                                if e_begin <= token["begin"] < token["end"] <= e_end:
                                    current_entity.append((s, t))

                        if len(current_entity) == 1:
                            sentences[current_entity[0][0]]["tokens"][
                                current_entity[0][1]]["conll_unique"].append(chain_id)

                        elif len(current_entity) > 1:
                            sentences[current_entity[0][0]]["tokens"][
                                current_entity[0][1]]["conll_begin"].append(chain_id)
                            sentences[current_entity[-1][0]]["tokens"][
                                current_entity[-1][1]]["conll_end"].append(chain_id)
                        else:
                            raise Exception("Span problem")

                    chain_id += 1

                # Writing conll file to disk
                with open(target_conll_file, "w", encoding="UTF-8") as output_file:
                    output_file.write("#begin document ({});\n".format(".".join(filename.split(".")[:-1])))

                    for i, sentence in enumerate(sentences, start=1):
                        for token in sentence["tokens"]:

                            start_str = "|".join(["({}".format(item) for item in token["conll_begin"]])
                            uniq_str = "".join(["({})".format(item) for item in token["conll_unique"]])
                            end_str = "|".join(["{})".format(item) for item in token["conll_end"]])

                            if len(start_str) > 0 and len(uniq_str) > 0 and len(end_str) > 0:
                                final_str = "{}|{}|{}".format(start_str, uniq_str, end_str)

                            elif len(start_str) > 0 and len(uniq_str) > 0 and len(end_str) == 0:
                                final_str = "{}|{}".format(start_str, uniq_str)

                            elif len(start_str) > 0 and len(uniq_str) == 0 and len(end_str) > 0:
                                final_str = "{}|{}".format(start_str, end_str)

                            elif len(start_str) == 0 and len(uniq_str) > 0 and len(end_str) > 0:
                                final_str = "{}|{}".format(uniq_str, end_str)

                            elif len(start_str) > 0 and len(uniq_str) == 0 and len(end_str) == 0:
                                final_str = "{}".format(start_str)

                            elif len(start_str) == 0 and len(uniq_str) == 0 and len(end_str) > 0:
                                final_str = "{}".format(end_str)

                            elif len(start_str) == 0 and len(uniq_str) > 0 and len(end_str) == 0:
                                final_str = "{}".format(uniq_str)

                            else:
                                final_str = "-"

                            output_file.write("{}\t{}\t{}\t{}\t{}\t{}\n".format(
                                i,
                                token["text"],
                                token["begin"],
                                token["end"],
                                "|".join(["{}:{}".format(l, i) for l, i in token["gs_tokens"]]),
                                final_str
                            ))

                        if i != len(sentences):
                            output_file.write("\n")

                    output_file.write("#end document\n")


def get_splits(doc_filepath: str) -> dict:
    """
    Extract character-offset--i2b2-offset mapping for a given document

    Args:
        doc_filepath: document filepath

    Returns:
        dict: mapping

    """
    all_rets = dict()

    old_global_start = 0
    global_start = 0

    with open(doc_filepath, "r", encoding="UTF-8") as input_file:
        for i, line in enumerate(input_file, start=1):
            chunks = re.split("[\s]", line.rstrip("\n"))
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


def get_i2b2_mapping(begin, end, splits):
    """
    Given a character-offset, return its i2b2 offset

    Args:
        begin (int): character begin offset
        end (int): character end offset
        splits (mapping): character-offset--i2b2-offset mapping

    Returns:
        list: i2b2 offset
    """
    mapping = list()

    for line_counter, ret in splits.items():
        for i, (t_str, t_begin, t_end) in enumerate(ret):
            if overlap(begin, end, t_begin, t_end):
                mapping.append((line_counter, i))

    return mapping


def extract_chains_with_networkx(relations: dict) -> set:
    """
    Given a set of relations extracted from a brat document, return the coreference chains

    Args:
        relations (dict): relations extracted from a brat document

    Returns:
        set: set of coreference chains
    """

    graph = nx.Graph()
    done = set()

    for rel_id, rel_pl in relations.items():
        graph.add_edge(rel_pl["arg1"], rel_pl["arg2"])
        done.add(rel_pl["arg1"])
        done.add(rel_pl["arg2"])

    connected_components = nx.connected_components(graph)

    return connected_components
