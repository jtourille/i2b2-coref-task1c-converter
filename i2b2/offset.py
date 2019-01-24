import json
import os


def create_offset_mapping(source_dir: str, modified_dir: str, target_json_filepath: str) -> None:
    """
    Create an offset mapping between two set of document

    Args:
        source_dir (str): directory containing source documents
        modified_dir (str): directory containing modified documents
        target_json_filepath (str): mapping filepath
    """
    mapping = dict()

    for filename in os.listdir(os.path.abspath(source_dir)):
        mapping[filename] = dict()
        source_filepath = os.path.join(os.path.abspath(source_dir), filename)
        modified_filepath = os.path.join(os.path.abspath(modified_dir), filename)

        source_content = open(source_filepath, "r", encoding="UTF-8").read()
        modified_content = open(modified_filepath, "r", encoding="UTF-8").read()

        for idx, source_char in enumerate(source_content):
            if source_char != modified_content[idx:idx + 1]:
                mapping[filename][idx] = (source_char, modified_content[idx:idx + 1])

    with open(target_json_filepath, "w", encoding="UTF-8") as output_file:
        json.dump(mapping, output_file)
