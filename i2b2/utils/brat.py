import copy
import os
import random
import re

colors_pastel = ["#efdccd", "#88aee1", "#d1f3c2", "#bfa0d0", "#b1d7b1", "#cdaede", "#72c8b8", "#e2c2f3", "#97be9b",
                 "#f2c8e8", "#dee7bc", "#88aee1", "#eddaac", "#88aee1", "#d5b898", "#88aee1", "#e9ad9f", "#79c9db",
                 "#ecb1c2", "#97e0eb", "#d8b0a7", "#88aee1", "#d3f1d6", "#95bbef", "#bfcbaa", "#aba7cf", "#b6eee2",
                 "#ddb3d2", "#8dc3b8", "#d5d0fa", "#a6b79f", "#c0bbe4", "#d4efe9", "#9db3d6", "#c7bfad", "#a7dcf9",
                 "#d2b9c0", "#95c4db", "#efd5dc", "#97b1ab", "#e6d6ee", "#a4beb8", "#b8cff2", "#b8d3cd", "#c3b3cb",
                 "#c2e9f5", "#a8b3c4", "#d9e3f5", "#add4e0", "#c4cee0"]

colors_fancy = ["#9bd1c6", "#e6ade5", "#d8f3af", "#74aff3", "#fae09f", "#c9b5f7", "#bcd794", "#adb5f0", "#a1bb7a",
                "#e2c2f3", "#8ac793", "#eda4c1", "#81e6d3", "#eea899", "#41c9dc", "#efb98d", "#67c6f2", "#f4f5b6",
                "#8eb4e8", "#dedfa2", "#a3c9fe", "#adaf74", "#bda7d4", "#a7eabe", "#e4bad9", "#d8fbc9", "#c7c2ec",
                "#c2c387", "#7cd3eb", "#dbc58e", "#8beaf7", "#e3aba7", "#84eced", "#ebb9c7", "#64c8c5", "#dfb89b",
                "#acd2f2", "#a7c99a", "#97b8d8", "#c3e5b5", "#8dd2d8", "#c0b18d", "#c3f4df", "#d5c5a1", "#80b6aa",
                "#eadab6", "#88c6a5", "#dee7bc", "#a5d1b3", "#bbc49a"]

colors_intense = ["#d040bb", "#52c539", "#bb46e0", "#8bba3c", "#5533c0", "#54be66", "#6c63da", "#b4b43b", "#742d90",
                  "#42822b", "#e14498", "#4ecc99", "#e1435b", "#399b71", "#e75a30", "#808ae6", "#daae40", "#3f2f6a",
                  "#e28b2f", "#4a62a8", "#b8351f", "#58c3b7", "#8c2425", "#59b6cf", "#b0385e", "#8fbf8f", "#d17bd7",
                  "#737d28", "#912f6f", "#729563", "#9769ab", "#a4802b", "#69a6e0", "#a55e27", "#446c90", "#dd986a",
                  "#368686", "#76341a", "#b79ed0", "#2f481b", "#d97fa1", "#37694a", "#6b263d", "#b8b274", "#724c6f",
                  "#6b5121", "#d2968e", "#5f3629", "#82764b", "#b7645a"]


def generate_brat_conf_files(input_dir: str) -> None:
    """
    Generate brat configuration files for a given directory

    Args:
        input_dir (str): directory with brat annotation files
    """

    regex_ann_filename = re.compile(r'.*\.ann')
    regex_entity = re.compile(r"T(\d+)\t([^\s]*)\s(\d+\s\d+;?)+\t([^\t]*)")
    regex_attribute = re.compile(r'^A(\d+)\t([^\s]+)\sT(\d+)\s(.*)')
    regex_relation = re.compile(r'^R(\d+)\t([^\s]+)\sArg1:T(\d+)\sArg2:T(\d+)')

    entities_list = set()
    attributes_list = dict()
    relations_list = set()

    for root, dirs, files in os.walk(os.path.abspath(input_dir)):
        for filename in files:
            if regex_ann_filename.match(filename):
                with open(os.path.join(root, filename), "r", encoding="UTF-8") as input_file:
                    for line in input_file:

                        entity_match = regex_entity.match(line)
                        if entity_match:
                            entities_list.add(entity_match.group(2))

                        attrib_match = regex_attribute.match(line)
                        if attrib_match:
                            if attrib_match.group(2) not in attributes_list:
                                attributes_list[attrib_match.group(2)] = set(attrib_match.group(4))
                            else:
                                attributes_list[attrib_match.group(2)].add(attrib_match.group(4))

                        relation_match = regex_relation.match(line)
                        if relation_match:
                            relations_list.add(relation_match.group(2))

    write_confs(entities_list, attributes_list, relations_list, input_dir)


def write_confs(entities_list: set, attributes_list: dict, relations_list: set, input_dir: str) -> None:
    """
    Writes brat configuration files

    Args:
        entities_list (set): corpus entities
        attributes_list (dict): corpus attributes
        relations_list (set): corpus relations
        input_dir (set): corpus path
    """

    with open(os.path.join(os.path.abspath(input_dir), "annotation.conf"), "w", encoding="UTF-8") as ann_conf:

        # Entities
        ann_conf.write("[entities]\n")
        for entity in entities_list:
            ann_conf.write("{0}\n".format(entity))

        # Relations
        ann_conf.write("[relations]\n")
        ann_conf.write("<OVERLAP> 	Arg1:<ANY>, Arg2:<ANY>, <OVL-TYPE>:<ANY>\n")
        for relation in relations_list:
            ann_conf.write("{0}\tArg1:<ANY>, Arg2:<ANY>\n".format(relation))

        # Events
        ann_conf.write("[events]\n")

        # Attributes
        ann_conf.write("[attributes]\n")
        for attribute in attributes_list:
            if attribute not in ["LEMMA", "FORM"]:
                ann_conf.write("{0}\tArg:<ANY>, Value:".format(attribute))
                for x, value in enumerate(attributes_list[attribute]):
                    if x < len(attributes_list[attribute])-1:
                        ann_conf.write(value+"|")
                    else:
                        ann_conf.write(value+"\n")

    with open(os.path.join(os.path.abspath(input_dir), "visual.conf"), "w", encoding="UTF-8") as visu_conf:
        visu_conf.write("[labels]\n")

        colors_entities = copy.deepcopy(colors_pastel)
        colors_relations = copy.deepcopy(colors_intense)

        random.shuffle(colors_entities)
        random.shuffle(colors_relations)

        for entity in entities_list:
            visu_conf.write("{0} | {1}\n".format(entity, entity))

        for relation in relations_list:
            visu_conf.write("{0} | {1}\n".format(relation, relation))

        visu_conf.write("[drawing]\n")
        for idx, entity in enumerate(entities_list):
            visu_conf.write("{0}\tfgColo:black, bgColor:{1}, borderColor:darken\n".format(
                entity,
                colors_entities.pop()
            ))

        for attribute in attributes_list:
            visu_conf.write("{0}\tposition:left, glyph:".format(attribute))
            for i in range(len(attributes_list[attribute])):
                if i < len(attributes_list[attribute])-1:
                    visu_conf.write("*|")
                else:
                    visu_conf.write("*\n")

        for relation in relations_list:
            visu_conf.write("{}\tcolor:{}, dashArray:3-3, arrowHead:triangle-5\n".format(
                relation,
                colors_relations.pop()
            ))


def get_last_ids(file_path: str) -> tuple:
    """
    Get last IDs of entities, relations, attributes and annaotions for a given brat document
    Args:
        file_path (str): brat annotation filepath

    Returns:
        (int, int, int, int): last entity ID, last attribute ID, last relation ID, last annotation ID
    """

    regex_entity = re.compile(r'^T(\d+)\t([^\s]+)\s(.*)\t(.*)')
    regex_relation = re.compile(r'^R(\d+)\t([^\s]+)\sArg1:T(\d+)\sArg2:T(\d+)')
    regex_attribute = re.compile(r'^A(\d+)\t([^\s]+)\sT(\d+)\s(.*)')
    regex_annotation = re.compile(r'#(\d+)\tAnnotatorNotes\s(T|R)(\d+)\t(.*)')

    last_entity_id = 0
    last_att_id = 0
    last_relation_id = 0
    last_ann_id = 0

    with open(file_path, "r", encoding="UTF-8") as input_file:

        for line in input_file:

            entity_match = regex_entity.match(line)
            if entity_match:
                if int(entity_match.group(1)) > last_entity_id:
                    last_entity_id = int(entity_match.group(1))

            relation_match = regex_relation.match(line)
            if relation_match:
                if int(relation_match.group(1)) > last_relation_id:
                    last_relation_id = int(relation_match.group(1))

            attribute_match = regex_attribute.match(line)
            if attribute_match:
                if int(attribute_match.group(1)) > last_att_id:
                    last_att_id = int(attribute_match.group(1))

            annotation_match = regex_annotation.match(line)
            if annotation_match:
                if int(annotation_match.group(1)) > last_ann_id:
                    last_ann_id = int(annotation_match.group(1))

    return last_entity_id, last_att_id, last_relation_id, last_ann_id


def parse_ann_file(ann_filename: str) -> tuple:
    """
    Parse a brat .ann file and return a dictionary of entities and a list of relations.

    Args:
        ann_filename (str): brat annotation filepath

    Returns:
        (dict, list): document entities and document relations
    """

    regex_entity = re.compile("^T(\d+)\t([^\s]+)\s([^\t]+)\t([^\t]*)$")
    regex_attribute = re.compile("^A(\d+)\t([^\s]+)\sT(\d+)\s(.*)$")
    regex_relation = re.compile("^R(\d+)\t([^\s]+)\sArg1:T(\d+)\sArg2:T(\d+)$")

    entities = dict()
    relations = dict()

    # Extraction entity annotations (without attributes)
    with open(ann_filename, "r", encoding="UTF-8") as input_file:
        for line in input_file:
            match_entity = regex_entity.match(line)
            if match_entity:

                brat_id = int(match_entity.group(1))

                current_entity = {
                    "id": brat_id,
                    "brat_id": brat_id,
                    "spans": list(),
                    "is_split": False,
                    "type": match_entity.group(2),
                    "text": match_entity.group(4).rstrip("\n"),
                    "attributes": dict()
                }

                spans = match_entity.group(3).split(";")
                for span in spans:
                    begin = int(span.split()[0])
                    end = int(span.split()[1])

                    current_entity["spans"].append((begin, end))

                if len(current_entity["spans"]) == 1:
                    current_entity["is_split"] = True

                entities[brat_id] = current_entity

    # Extracting entity attributes
    with open(ann_filename, "r", encoding="UTF-8") as input_file:
        for line in input_file:
            match_attribute = regex_attribute.match(line)
            if match_attribute:
                if int(match_attribute.group(3)) in entities:
                    entities[int(match_attribute.group(3))][
                        'attributes'][match_attribute.group(2)] = match_attribute.group(4)

    # Extracting relations
    with open(ann_filename, "r", encoding="UTF-8") as input_file:
        for line in input_file:
            match_relation = regex_relation.match(line)
            if match_relation:
                relations[int(match_relation.group(1))] = {
                    "type": match_relation.group(2),
                    "arg1": int(match_relation.group(3)),
                    "arg2": int(match_relation.group(4))
                }

    return entities, relations
