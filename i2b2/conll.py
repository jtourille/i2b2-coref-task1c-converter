import os
import re
from collections import defaultdict
from typing import DefaultDict, List, Set, Tuple

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


def conll_to_i2b2(input_conll_dir, output_i2b2_dir):
    """
    Convert a set of CoNLL document into i2b2 format.
    This is largely inspired by the allennlp implementation.
    :param input_conll_dir: path where conll documents are stored
    :param output_i2b2_dir: path where i2b2 documents will be stored
    :return: None
    """

    all_files: List[CoNLLFile] = list()

    for root, dirs, files in os.walk(os.path.abspath(input_conll_dir)):
        for filename in files:
            if re.match("^.*\.conll$", filename):
                source_conll_file = os.path.join(root, filename)

                conll_file = CoNLLFile(conll_file_path=source_conll_file)
                all_files.append(conll_file)

    target_concept_dir = os.path.join(output_i2b2_dir, "concepts")
    target_chain_dir = os.path.join(output_i2b2_dir, "chains")

    ensure_dir(target_concept_dir)
    ensure_dir(target_chain_dir)

    for conll_file in all_files:
        for document_id, document in conll_file.all_documents.items():
            concepts = document.get_document_concepts_i2b2_format()
            chains = document.get_document_chains_i2b2_format()

            concept_file_path = os.path.join(target_concept_dir, "{}.con".format(document_id))
            chain_file_path = os.path.join(target_chain_dir, "{}.chains".format(document_id))

            with open(concept_file_path, "w", encoding="UTF-8") as output_file:
                for con_str, con_begin, con_end, con_type in concepts:
                    line_str = "c=\"{}\" {}:{} {}:{}||t=\"{}\"\n".format(
                        con_str,
                        con_begin[0],
                        con_begin[1],
                        con_end[0],
                        con_end[1],
                        con_type
                    )

                    output_file.write(line_str)

            with open(chain_file_path, "w", encoding="UTF-8") as output_file:
                for chain_id, concept_list in chains.items():
                    all_concept_str = list()
                    for con_str, con_begin, con_end, con_type in sorted(concept_list, key=lambda x: (x[1][0], x[1][1])):
                        final_str = "c=\"{}\" {}:{} {}:{}".format(
                            con_str,
                            con_begin[0],
                            con_begin[1],
                            con_end[0],
                            con_end[1],
                        )
                        all_concept_str.append(final_str)

                    output_file.write("{}||t=\"coref procedure\"\n".format(
                        "||".join(all_concept_str)
                    ))

    return all_files


class CoNLLFile:
    """
    A CoNLL file may contain several documents
    """

    def __init__(self, conll_file_path=None):

        self.conll_file_path = conll_file_path
        self.all_documents = self.process_file()

    def process_file(self):
        """
        Main method of the class. Process the file and return a dict of Document objects
        :return: dict of Document objects
        """

        all_documents = dict()

        with open(self.conll_file_path, "r", encoding="UTF-8") as input_file:
            conll_rows = list()
            document_id = str()
            document = None

            for line in input_file:
                line = line.strip()

                if line.startswith('#begin document'):
                    match = re.match('#begin document \((.*)\);', line)
                    document_id = match.group(1)
                    document = Document(document_id)

                elif line != '' and not line.startswith('#'):
                    # Non-empty line. Collect the annotation.
                    conll_rows.append(line)

                else:
                    if conll_rows:
                        document.sentences.append(self._conll_rows_to_sentence(conll_rows))
                        conll_rows = list()

                if line.startswith("#end document"):
                    # document.sentences.append(self._conll_rows_to_sentence(conll_rows))
                    all_documents[document_id] = document
                    document_id = str()
                    document = None

            if conll_rows:
                # Collect any stragglers or files which might not
                # have the '#end document' format for the end of the file.
                document.sentences.append(self._conll_rows_to_sentence(conll_rows))

        return all_documents

    def _conll_rows_to_sentence(self, conll_rows):
        """
        Convert a sentence extracted from the CoNLL file to a Sentence object
        :param conll_rows: rows extracted from the file
        :return: a Sentence object
        """

        # Cluster id -> List of (start_index, end_index) spans.
        clusters: DefaultDict[int, List[Tuple[int, int]]] = defaultdict(list)
        # Cluster id -> List of start_indices which are open for this id.
        coref_stacks: DefaultDict[int, List[int]] = defaultdict(list)

        sentences: List[int] = list()
        words: List[str] = list()
        begins: List[int] = list()
        ends: List[int] = list()
        i2b2_mappings: List[str] = list()

        for index, row in enumerate(conll_rows):
            conll_components = row.split()

            t_sent_id = conll_components[0]
            t_word = conll_components[1]
            t_begin = conll_components[2]
            t_end = conll_components[3]

            i2b2 = conll_components[4].split('|')
            t_i2b2_mapping = list()

            for chunk in i2b2:
                t_i2b2_mapping.append((
                    int(chunk.split(":")[0]),
                    int(chunk.split(":")[1])
                ))

            try:
                self._process_coref_span_annotations_for_word(conll_components[-1],
                                                              index,
                                                              clusters,
                                                              coref_stacks)
            except:
                for i in conll_rows:
                    print(i)
                raise

            sentences.append(int(t_sent_id))
            words.append(t_word)
            begins.append(int(t_begin))
            ends.append(int(t_end))
            i2b2_mappings.append(t_i2b2_mapping)

        coref_span_tuples: Set[TypedSpan] = {(cluster_id, span)
                                             for cluster_id, span_list in clusters.items()
                                             for span in span_list}

        return Sentence(sentences, words, begins, ends, i2b2_mappings, coref_span_tuples)

    @staticmethod
    def _process_coref_span_annotations_for_word(label: str,
                                                 word_index: int,
                                                 clusters: DefaultDict[int, List[Tuple[int, int]]],
                                                 coref_stacks: DefaultDict[int, List[int]]) -> None:
        """
        For a given coref label, add it to a currently open span(s), complete a span(s) or
        ignore it, if it is outside of all spans. This method mutates the clusters and coref_stacks
        dictionaries.

        Parameters
        ----------
        label : ``str``
            The coref label for this word.
        word_index : ``int``
            The word index into the sentence.
        clusters : ``DefaultDict[int, List[Tuple[int, int]]]``
            A dictionary mapping cluster ids to lists of inclusive spans into the
            sentence.
        coref_stacks: ``DefaultDict[int, List[int]]``
            Stacks for each cluster id to hold the start indices of active spans (spans
            which we are inside of when processing a given word). Spans with the same id
            can be nested, which is why we collect these opening spans on a stack, e.g:

            [Greg, the baker who referred to [himself]_ID1 as 'the bread man']_ID1
        """
        if label != "-":
            for segment in label.split("|"):
                # The conll representation of coref spans allows spans to
                # overlap. If spans end or begin at the same word, they are
                # separated by a "|".
                if segment[0] == "(":
                    # The span begins at this word.
                    if segment[-1] == ")":
                        # The span begins and ends at this word (single word span).
                        cluster_id = int(segment[1:-1])
                        clusters[cluster_id].append((word_index, word_index))
                    else:
                        # The span is starting, so we record the index of the word.
                        cluster_id = int(segment[1:])
                        coref_stacks[cluster_id].append(word_index)
                else:
                    # The span for this id is ending, but didn't start at this word.
                    # Retrieve the start index from the document state and
                    # add the span to the clusters for this id.
                    cluster_id = int(segment[:-1])
                    start = coref_stacks[cluster_id].pop()
                    clusters[cluster_id].append((start, word_index))


TypedSpan = Tuple[int, Tuple[int, int]]


class Document:
    """
    A coreference document
    """

    def __init__(self, document_id):

        self.document_id = document_id
        self.sentences = list()

    def get_document_concepts_i2b2_format(self):
        """
        Get i2b2 formatted concepts from the CoNLL format
        :return: list of i2b2 formatted concepts
        """

        all_concepts = list()

        for sentence in self.sentences:
            for chain_id, (begin, end) in sentence.coref_spans:
                concept_str = " ".join([sentence.words[idx] for idx in range(begin, end + 1)])
                concept_begin = sorted(sentence.i2b2_mapping[begin], key=lambda x: (x[0], x[1]))[0]
                concept_end = sorted(sentence.i2b2_mapping[end], key=lambda x: (x[0], x[1]), reverse=True)[0]
                concept_type = "procedure"

                all_concepts.append((
                    concept_str,
                    concept_begin,
                    concept_end,
                    concept_type
                ))

        return all_concepts

    # def get_document_concepts(self):
    #
    #     all_concepts = list()
    #
    #     for sentence in self.sentences:
    #         for chain_id, (begin, end) in sentence.coref_spans:
    #             all_concepts.append((begin, end))
    #
    #     return all_concepts

    def get_document_chains_i2b2_format(self):
        """
        Get i2b2 formatted chains from the CoNLL format
        :return: list of i2b2 formatted chains
        """

        all_chains = defaultdict(list)

        for sentence in self.sentences:
            for chain_id, (begin, end) in sentence.coref_spans:
                concept_str = " ".join([sentence.words[idx] for idx in range(begin, end + 1)])
                concept_begin = sorted(sentence.i2b2_mapping[begin], key=lambda x: (x[0], x[1]))[0]
                concept_end = sorted(sentence.i2b2_mapping[end], key=lambda x: (x[0], x[1]), reverse=True)[0]
                concept_type = "procedure"

                all_chains[chain_id].append((
                    concept_str,
                    concept_begin,
                    concept_end,
                    concept_type
                ))

        return all_chains


class Sentence:
    """
    CoNLL sentence
    """

    def __init__(self,
                 sent_ids: List[int],
                 words: List[str],
                 begin: List[int],
                 end: List[int],
                 i2b2_mapping: List[str],
                 coref_spans: Set[TypedSpan]):

        self.sent_ids = sent_ids
        self.words = words
        self.begin = begin
        self.end = end
        self.i2b2_mapping = i2b2_mapping
        self.coref_spans = coref_spans
