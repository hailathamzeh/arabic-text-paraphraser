# Dataset setup

The dataset is stored outside this repository. A course copy is available in this [Google Drive folder](https://drive.google.com/drive/folders/17eFOOjisQsSKEpWeIFt8rqQUsUIRIREJ?usp=sharing).

## Required file

Download the CSV from the folder, rename it to `paraphrase_data.csv` if necessary, and place it here:

```text
data/
├── README.md
└── paraphrase_data.csv
```

The CSV must contain these columns:

| Column | Meaning |
|---|---|
| `source` | Original Arabic sentence |
| `destination` | Reference Arabic paraphrase |

The notebook output indicates that the course CSV contained 50,000 sentence pairs. The source publication describes a larger corpus of 100,000 pairs, so confirm the row count of the downloaded copy before comparing a new run with the recorded results.

To use a CSV stored elsewhere, set `ARABIC_PARAPHRASE_DATA` to its path before starting Jupyter.

Linux or macOS:

```bash
export ARABIC_PARAPHRASE_DATA="/path/to/paraphrase_data.csv"
```

Windows PowerShell:

```powershell
$env:ARABIC_PARAPHRASE_DATA="C:\path\to\paraphrase_data.csv"
```

Validate the file and its required headers from the repository root:

```bash
python tools/validate_repository.py --check-dataset
```

The Google Drive folder is a course copy, not an official distribution page. The dataset is attributed to Fatima Al-Raisi, Abdelwahab Bourai, and Weijian Lin in the project README. Confirm the original terms with the dataset authors before redistribution or use outside the course context.
