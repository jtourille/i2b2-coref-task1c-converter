# I2B2 2011 Task1c Converter

This repository contains the tools that can be used to convert the i2b2/VA corpus on coreference from i2b2 to CoNLL and 
brat format. The conversion concerns only the documents provided by *Beth Israel Deaconess Medical Center* (BETH) and 
*Partners Healthcare* (PARTNERS). Documents from *University of Pittsburgh Medical Center* (UPMC) are discarded.

The conversion process is divided in several steps described below.

## 1. Data Extraction

In this first preprocessing step, original data will be extracted, renamed, corrected (if necessary) and sorted. The 
corrections concern three documents: `clinical-32`, `clinical-52` and `clinical-627`.
 
1. Create a directory that contains source compressed files.

```text
source
├── i2b2_Beth_Train_Release.tar.gz
├── i2b2_Partners_Train_Release.tar.gz
├── Task_1C.zip
└── Test-ground-truth-Beth-Partners_111004.tar.gz
```

2. Launch the following command to extract, rename, correct and sort data. A directory structure will be created under 
`/path/to/data-preparation`.

```bash
$ python main.py PREPARE-DATA \
  --zip-dir /path/to/source \
  --output-dir /path/to/data-preparation \
  --correction-file ./annotation-corrections.json \
  [--overwrite] 
```

## 2. Brat files creation

The conversion process from i2b2 to CoNLL rely on the brat data structure as intermediary format. In this step, we 
generate a brat version of the corpus. As an added bonus, this allows for better data visualization as both i2b2 and 
CoNLL formats are not convenient in this aspect.

Hard sentence breaks that occurred within mentions will be replaced by empty spaces during this step. This allows to 
keep the offset integrity intact while facilitating both the conversion and the visualization.

```bash
$ python main.py CREATE-BRAT \
  --input-dir /path/to/data-preparation \
  --mapping-file ./char_mapping.json \
  [--overwrite]
```

## 3. CoNLL files creation

This is the final step of the process. We create a CoNLL version of the corpus. Offset mapping between i2b2 and CoNLL 
are stored within the documents.

```bash
$ python main.py CREATE-CONLL \
  --input-dir /path/to/data-preparation \
  [--overwrite]
``` 

## 4. Other

### Mapping File Creation

The mapping file provided within this repository allows to remove hard sentence breaks that occurs within a sentence
 while keeping offsets untouched.
If you want to reproduce the steps that output this file, follow these instructions:

* Generate the directories that will be used for the procedure. A directory `mapping` with two subdirectories 
`modified` and `untouched` will be created.

```bash
$ python main.py REGROUP-FILES \
  --input-dir /path/to/data-preparation \
  [--overwrite]
```

* Modify the documents in the `modified` subdirectory to your convenience (number of characters must match) and generate
the mapping file.

```bash
$ python main.py CREATE-MAPPING \
  --source-dir /path/to/data-preparation/mapping/untouched \
  --modified /path/to/data-preparation/mapping/modified \
  --target-file char_mapping.json\
  [--overwrite]
```

### Reverse Transformation

To check the integrity of the transformation i2b2 -> conll, we can perform the reverse transformation conll -> i2b2 and
measure the similarity by applying the official evaluation script provided during the i2b2 shared task.

* Convert the CoNLL files to i2b2 format. All entity will be marked as `procedure` and all chains will be marked as 
`coref_procedure`.

```bash
$ python main.py CONLL-TO-I2B2 \
  --input-dir /path/to/data-preparation/conll/task1c/train \
  --output-dir /path/to/data-preparation/reverse-test/task1c/train \
  [--overwrite]
  
$ python main.py CONLL-TO-I2B2 \
  --input-dir /path/to/data-preparation/conll/task1c/test \
  --output-dir /path/to/data-preparation/reverse-test/task1c/test \
  [--overwrite]
```

* Entity types have been lost during the conversion from i2b2 to CoNLL. The official evaluation script is sensitive to
the types, so we have to get rid of the entity types in the gold standard. The following command will replace all types
by the type `procedure`. The files will be created at the location 
`/path/to/data-preparation/gold-standard-flatten-replace`.

```bash
$ python main.py REMOVE-TYPES \
  --input-dir /path/to/data-preparation/ \
  [--overwrite] 
```

* Launch the official evaluation script with on the converted annotations. First clone or download the 
[script](https://github.com/jtourille/i2b2-coreference-evaluation).

```bash
$ git clone git@github.com:jtourille/i2b2-coreference-evaluation.git
```

Prepare a Python 2 environment and install the required packages.

```bash
$ conda create -n i2b2-eval python=2
$ conda activate i2b2-eval
$ pip install pp
$ pip install munkres
```

Move to the evaluation script directory and launch the evaluations. Log files are located in the `evaluation` directory
of this repository.

```bash
$ python endToEndCoreferenceEvaluation.py \
  /path/to/data-preparation/gold-standard-flatten-replace/task1c/train/chains \
  /path/to/data-preparation/reverse-test/task1c/train/chains \
  /path/to/data-preparation/gold-standard-flatten-replace/task1c/train/concepts \
  /path/to/data-preparation/reverse-test/task1c/train/concepts \
  .

$ python endToEndCoreferenceEvaluation.py \
  /path/to/data-preparation/gold-standard-flatten-replace/task1c/test/chains \
  /path/to/data-preparation/reverse-test/task1c/test/chains \
  /path/to/data-preparation/gold-standard-flatten-replace/task1c/test/concepts \
  /path/to/data-preparation/reverse-test/task1c/test/concepts \
  .
```

### Single run conversion

It is possible to convert one single run from i2b2 to CoNLL format.

```bash
$ python main.py RUN-TO-CONLL \
    --input-dir /path/to/run \
    --output-dir /path/to/output-dir \
    --gs-conll-dir /path/to/data-preparation/conll/task1c/test/ \
    --mapping-file ./char_mapping.json \
    [--overwrite]
```

Run directory must be composed of two directories `BETH` and `PARTNERS`. Within these directories, three subdirectories 
must be created: 

* `chains`: contains system output
* `concepts`: contains gold standard concept annotations
* `docs`: contains gold standard text files 