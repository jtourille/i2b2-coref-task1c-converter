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

## 3. Other

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