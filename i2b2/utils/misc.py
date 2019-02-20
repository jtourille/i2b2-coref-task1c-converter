import os
import re

from .path import remove_abs, ensure_dir


def find_ngrams(input_list: list, n: int) -> list:
    """
    Return a list of n_grams from a list

    Args:
        input_list (list): list from which n_grams are extracted
        n (int): n gram length

    Returns:
        list: n-gram list

    """
    if n == 1:
        return input_list
    else:
        return list(zip(*[input_list[i:] for i in range(n)]))


def replace_semantic_types(input_dir: str, output_dir: str) -> None:
    """
    Replace semantic types for evaluation with the i2b2 script

    Args:
        input_dir (str): path where gold standard files are stored (flattened version)
        output_dir (str): path where new files will be created

    Returns:
        None
    """

    for root, dirs, files in os.walk(os.path.abspath(input_dir)):
        for filename in files:
            subdir = remove_abs(re.sub(re.escape(os.path.abspath(input_dir)), "", root))

            source_file = os.path.join(root, filename)

            target_subdir = os.path.join(os.path.abspath(output_dir), subdir)
            target_file = os.path.join(target_subdir, filename)

            ensure_dir(target_subdir)

            with open(source_file, "r", encoding="UTF-8") as input_file:
                content = input_file.read()

            with open(target_file, "w", encoding="UTF-8") as output_file:
                if re.match("^.*\.chains$", filename):
                    content = re.sub("coref\s[^\"]*", "coref procedure", content)

                elif re.match("^.*\.con$", filename):
                    content = re.sub("t=\"[^\"]*\"", "t=\"procedure\"", content)

                output_file.write(content)
