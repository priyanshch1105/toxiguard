# Dataset

This project uses the Jigsaw Toxic Comment Classification Challenge data.

Download:

```bash
python -m ml.download_dataset
```

Files:

- `raw/train.csv` — 159,571 labeled comments
- `raw/test.csv` — unlabeled test comments
- `raw/test_labels.csv` — official labels; rows with `-1` are unused
- `processed/split_summary.json` — created during training
