# I2B2 2011 Task1c Converter

This repository contains the tools used to transform the i2b2 coreference corpus (task1c) from i2b2 to CoNLL format.

## 1. Data Extraction

In the first preprocessing step, original data will be extracted, renamed, corrected and sorted.
 
* Create a directory that contains source compressed files.

```text
source
├── i2b2_Beth_Train_Release.tar.gz
├── i2b2_Partners_Train_Release.tar.gz
├── Task_1C.zip
└── Test-ground-truth-Beth-Partners_111004.tar.gz
```

* Launch the following command to extract, rename, correct and sort data.

```bash
$ python main.py PREPARE-DATA \
  --zip-dir /path/to/source \
  --output-dir /path/to/data-preparation \
  --correction-file ./annotation-corrections.json \
  [--overwrite] 
```

## 2. Brat version creation

Creation of a brat version of the corpus.

```bash
$ python main.py CREATE-BRAT \
  --input-dir /path/to/data-preparation \
  --mapping-file ./char_mapping.json \
  [--overwrite]
```

## 3. CoNLL files creation

Creation of a CoNLL version of the corpus.

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

