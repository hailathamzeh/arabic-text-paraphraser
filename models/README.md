# Model checkpoints

Training writes checkpoints under this directory. Checkpoints are not stored in Git because the AraT5 weights and fine-tuned artifacts are large.

The notebooks use `UBC-NLP/AraT5-msa-small` as the starting model. To run inference from a local fine-tuned checkpoint, set `ARABIC_PARAPHRASE_MODEL_DIR` before starting Jupyter.

Linux or macOS:

```bash
export ARABIC_PARAPHRASE_MODEL_DIR="/path/to/checkpoint"
```

Windows PowerShell:

```powershell
$env:ARABIC_PARAPHRASE_MODEL_DIR="C:\path\to\checkpoint"
```

AraT5 is provided by the UBC Deep Learning and NLP Lab. Review the current model-card terms before using or distributing a checkpoint.
