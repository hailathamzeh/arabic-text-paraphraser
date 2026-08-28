# Arabic Text Paraphrasing with AraT5

This repository contains the final project completed for the master's course **CIS733**.

The project was developed by:

- Samah Abazid
- Rahaf Alhazaymeh
- Hamzeh Hailat

## Project background

Arabic paraphrase generation aims to rewrite a sentence while preserving its main meaning. It is useful in text simplification, writing assistance, question generation, information retrieval, data augmentation, and other Arabic natural language processing tasks.

In this project, we fine-tuned an Arabic text-to-text Transformer to generate a paraphrase from a Modern Standard Arabic sentence. Two configurations were compared, one with a maximum tokenized sequence length of 128 and another with a maximum length of 256.

## Problem statement

Given a source sentence in Arabic, the model should generate a different Arabic sentence that retains the source meaning. The work focuses on three questions:

1. Can a pretrained Arabic sequence-to-sequence model learn this task from parallel sentence pairs?
2. How does increasing the maximum sequence length from 128 to 256 affect training behavior?
3. What do the generated examples and corpus-level BLEU calculation show about the two experiments?

## Dataset

The project is based on the Arabic paraphrasing corpus introduced by Fatima Al-Raisi, Abdelwahab Bourai, and Weijian Lin in [Neural Symbolic Arabic Paraphrasing with Automatic Evaluation](https://csitcp.org/abstract/8/86csit01). The source material describes a parallel monolingual Arabic corpus containing 100,000 pairs of original sentences and reference paraphrases, with sentence lengths ranging from 1 to 164 words.

The CSV used for the course project is available in this [Google Drive folder](https://drive.google.com/drive/folders/17eFOOjisQsSKEpWeIFt8rqQUsUIRIREJ?usp=sharing). This folder is a course copy, not the original dataset distribution page. The recorded notebook output shows a 10,000-row test set after a 20% split, which indicates that this CSV contains 50,000 sentence pairs.

The dataset is not stored in this repository.

### Download and arrange the dataset

1. Open the Google Drive folder.
2. Download the CSV file.
3. Rename it to `paraphrase_data.csv` if it has a different name.
4. Place it in the following location:

   ```text
   data/
   ├── README.md
   └── paraphrase_data.csv
   ```

5. Confirm that the CSV contains the columns `source` and `destination`.
6. Validate the file:

   ```bash
   python tools/validate_repository.py --check-dataset
   ```

If the CSV is stored elsewhere, set `ARABIC_PARAPHRASE_DATA` to its location. The notebooks resolve this value with `pathlib.Path`.

Linux or macOS:

```bash
export ARABIC_PARAPHRASE_DATA="/path/to/paraphrase_data.csv"
```

Windows PowerShell:

```powershell
$env:ARABIC_PARAPHRASE_DATA="C:\path\to\paraphrase_data.csv"
```

## Data preparation

The notebook workflow performs the following steps:

1. Load the parallel sentence pairs with pandas.
2. Convert the `source` and `destination` columns to strings.
3. Reserve 20% of the data for testing using `random_state=42`.
4. Reserve 10% of the remaining 80% for evaluation.
5. Tokenize the source and target sentences with the AraT5 tokenizer.
6. Wrap the tokenized tensors in a custom `ParaphraseDataset` for the Hugging Face Trainer.

The effective split is 72% training, 8% evaluation, and 20% testing. For the 50,000-pair course CSV, this corresponds to 36,000 training pairs, 4,000 evaluation pairs, and 10,000 test pairs.

## Model and training method

The experiments use [UBC-NLP/AraT5-msa-small](https://huggingface.co/UBC-NLP/AraT5-msa-small), an Arabic encoder-decoder model based on the T5 text-to-text architecture. The same pretrained checkpoint is used for both experiments.

| Setting | Model 1 | Model 2 |
|---|---:|---:|
| Maximum tokenized sequence length | 128 | 256 |
| Requested epochs | 30 | 30 |
| Batch size | Automatically selected | Automatically selected |
| Evaluation frequency | Every epoch | Every epoch |
| Random seed | 42 | 42 |
| Generation maximum length | 256 | 256 |
| Top-p sampling | 0.95 | 0.95 |
| Top-k sampling | 120 | 120 |

The original experiments were run on the following computer:

| Component | Hardware |
|---|---|
| CPU | AMD Ryzen 5 3600 |
| GPU | NVIDIA RTX 2060 with 6 GB VRAM |
| RAM | 24 GB DDR4 |

## Recorded results

### Model 1, maximum sequence length 128

| Epoch | Training loss | Validation loss |
|---:|---:|---:|
| 1 | No log | 1.173911 |
| 4 | 1.764000 | 0.758341 |
| 6 | 1.764000 | 0.696381 |
| 7 | 0.841000 | 0.678992 |
| 10 | 0.743400 | 0.645978 |
| 22 | 0.643200 | 0.598049 |
| 30 | 0.613800 | 0.593992 |

The notebook completed 30 epochs and recorded a Trainer runtime of 36,832.74 seconds, approximately 10 hours and 14 minutes. The course notes reported approximately 15 hours including the wider training and testing workflow.

### Model 2, maximum sequence length 256

| Epoch | Training loss | Validation loss |
|---:|---:|---:|
| 1 | 1.464700 | 0.857430 |
| 2 | 0.443800 | 0.700867 |
| 3 | 0.388300 | 0.645725 |
| 6 | 0.319800 | 0.594994 |
| 8 | 0.313200 | 0.590462 |
| 10 | 0.310500 | 0.590462 |
| 13 | 0.310700 | 0.590462 |

The validation loss reached 0.590462 by epoch 8 and remained at that displayed value through epoch 13. The recorded notebook progress reached epoch 13.87 after approximately 13 hours and 51 minutes. The original course notes estimated approximately 30 hours for the full 30-epoch configuration.

The tabulated values are also available in [`outputs/recorded_training_metrics.csv`](outputs/recorded_training_metrics.csv).

### Recorded BLEU calculation

| Model | Recorded BLEU |
|---|---:|
| Model 1, length 128 | 0.21093420727002457 |
| Model 2, length 256 | 0.16555913669653252 |

These values reproduce the calculation used in the course notebooks, where generated paraphrases were compared with the source sentences. This does not use the `destination` paraphrases as references, so the values should be treated as legacy experiment results rather than a standard reference-based paraphrase evaluation. Both notebooks include a second BLEU cell that compares generated text with the destination sentences for future runs.

### Example generations

The notebooks preserve several Arabic examples. One shared source sentence produced the following outputs:

| Version | Text |
|---|---|
| Source | ومع ذلك، أرى أن العكس قد يكون صحيحا في الواقع. |
| Model 1, length 128 | ومع ذلك، أعتقد أنه يمكن أن تكون صحيحة. |
| Model 2, length 256 | ونحن نعتقد أن العكس لن يكون صحيحا في الواقع. |

The examples show that both models produce fluent fragments in some cases, but meaning preservation and grammatical quality are inconsistent. This is why the quantitative results should be accompanied by human evaluation and semantic similarity measures.

## Repository structure

```text
arabic-text-paraphraser/
├── .github/
│   └── workflows/
│       └── validate.yml
├── data/
│   └── README.md
├── models/
│   └── README.md
├── notebooks/
│   ├── 01_arat5_128.ipynb
│   └── 02_arat5_256.ipynb
├── outputs/
│   ├── recorded_evaluation.csv
│   └── recorded_training_metrics.csv
├── tools/
│   └── validate_repository.py
├── .gitignore
├── README.md
└── requirements.txt
```

## Installation

Python 3.10 or 3.11 is recommended. A CUDA-capable GPU is strongly recommended for training.

```bash
python -m venv .venv
```

Activate the environment.

Linux or macOS:

```bash
source .venv/bin/activate
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install the dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The course experiments used Transformers 4.28.0. The repository requirements use maintained package ranges, so minor differences in warnings, training speed, and generated text are expected.

## Run the notebooks

Start Jupyter from the repository root:

```bash
jupyter lab
```

Open one notebook at a time:

1. `notebooks/01_arat5_128.ipynb`
2. `notebooks/02_arat5_256.ipynb`

Each notebook can train from the pretrained AraT5 checkpoint. Training is computationally expensive and writes checkpoints under `models/`, which is ignored by Git.

To run the generation cells from an existing fine-tuned checkpoint, set `ARABIC_PARAPHRASE_MODEL_DIR` before starting Jupyter:

```bash
export ARABIC_PARAPHRASE_MODEL_DIR="/path/to/checkpoint"
```

The base model can also be changed with `ARAT5_MODEL_NAME`, although doing so will no longer reproduce the original experiment design.

## Reproducibility notes

- The train, evaluation, and test splits use a fixed seed of 42.
- The notebooks use repository-relative paths and optional environment-variable overrides.
- Selected training tables, BLEU values, and example generations from the course runs remain visible in the notebooks.
- Generation uses sampling, so generated wording can differ across runs even when the data split is fixed.
- Exact results depend on the CSV version, hardware, CUDA and cuDNN versions, PyTorch, Transformers, batch size selected by `auto_find_batch_size`, and checkpoint used for evaluation.
- Model 2's displayed training record ends during epoch 13, even though the configuration requests 30 epochs.

Run the repository checks before committing changes:

```bash
python tools/validate_repository.py
```

## Limitations

- The course CSV appears to contain 50,000 pairs, while the source corpus is described as 100,000 pairs.
- The recorded BLEU values use the source sentences as references and are not a complete measure of paraphrase quality.
- BLEU alone does not adequately measure semantic equivalence, factual consistency, grammatical quality, or diversity.
- The project does not include human evaluation or modern semantic metrics such as BERTScore.
- Some recorded examples alter or weaken the source meaning.
- Padding token IDs were retained in the original training labels rather than being masked from the loss.
- Training both configurations is time-consuming on a consumer GPU.
- Performance may vary across Arabic domains, dialects, sentence lengths, and writing styles not represented in the course CSV.

## Citation and usage terms

Dataset source:

> Fatima Al-Raisi, Abdelwahab Bourai, and Weijian Lin. Neural Symbolic Arabic Paraphrasing with Automatic Evaluation. 2018.

The source publication page does not provide a verified direct dataset download or a clear dataset license. The Google Drive folder is a course copy. Confirm permission and attribution requirements with the dataset authors before redistribution or use outside the intended academic context.

AraT5 reference:

> El Moatez Billah Nagoudi, AbdelRahim Elmadany, and Muhammad Abdul-Mageed. [AraT5: Text-to-Text Transformers for Arabic Language Generation](https://aclanthology.org/2022.acl-long.47/). Proceedings of ACL, 2022.

The [AraT5 model card](https://huggingface.co/UBC-NLP/AraT5-msa-small) states that the released checkpoints are intended for research use and asks users to contact the authors for commercial use. Review the current model card before using or distributing model artifacts.
