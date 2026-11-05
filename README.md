# Hazard-Prioritisation Module for Vision-Language Walking Assistance

This project was completed for the unit FOSE7902 - Advanced STEM Research Placement at Macquarie University.

The project is about helping vision-language walking assistants decide which hazard matters most. It introduces a training-free module that ranks hazards in walking scenes by severity and likelihood (closeness, position relative to the walking path, motion and context), decides an action (stop, move, slow, caution or clear), and passes the result to a vision-language model as a short hint.

The module is evaluated on the Walking Awareness Dataset (WAD) against two references: WAD's own reminders and the labels of two independent human judges, who saw only the video frames. Its effect on Qwen2-VL-2B is tested by comparing the model's reminders with no hint, with an unranked list of the detected objects, and with the module's ranked hint.

## Data
The Walking Awareness Dataset (WAD) is available from its authors at
https://walkvlm2024.github.io (Yuan et al., *WalkVLM: Aid Visually Impaired People Walking by Vision Language Model*, ICCV 2025).

WAD frames, reminders and other annotation text are **not** included in this repository. `data/subsets/` contains only the clip identifiers of every subset used, with WAD's short scene tags (danger level, area type, weather and so on), so that the subsets can be rebuilt from the original dataset.

| Subset | Clips | Source | Used for |
|---|---|---|---|
| `dev_00` | 500 | WAD train | all tuning of the module; prompt selection |
| `check_01`–`check_04` | 4 × 500 | WAD train | stability only, never used for tuning |
| `test` | 1,007 | WAD `test_alter` | final evaluation, run once |

The training-split subsets are video-disjoint from each other and stratified by danger level and response type (seed 42).

## Repository layout

```
hazard-prioritisation-wad/
├── data/
│   └── subsets/                                # Clip identifiers of every subset (CSV)
├── notebooks/
│   ├── 1_wad_inspection_subsets_creation.ipynb # Inspect WAD and create the subsets (local)
│   ├── 2_build_reference_labels.ipynb          # Parse WAD's reminders into labels (local)
│   ├── 3_hazard_prioritisation_module.ipynb    # The module, from perception to hints (Kaggle, GPU)
│   ├── 4_qwen_reminders.ipynb                  # Qwen2-VL-2B under the three conditions (Kaggle, GPU)
│   ├── 5_human_check.ipynb                     # Labelling by the two judges (local)
│   ├── 6_evaluation.ipynb                      # All result tables and figures (local)
│   └── 7_report_figures.ipynb                  # Method figures for one example clip (local)
└── results/
│   ├── tables/                                 # Every result table in the report (CSV)
│   ├── figures/                                # Result figures in the report
│   └── outputs/                                # Module, Qwen and judge outputs (not committed)
├── scripts/
│   └── wad_parser.py                           # Rule-based parser for WAD's reminders and Qwen's replies
├── README.md                                   # This file
├── requirements.txt                            # Python packages for the local notebooks
├── .gitignore                                  # Keeps WAD data and large outputs out of the repository
```

## How to run
1. Get WAD from the link above and set `DATA_DIR` / `FRAMES_DIR` in each notebook.
   
2. Subsets: run `wad_inspection_subsets_creation.ipynb`. It recreates the files in `data/subsets/` exactly.
   
3. Reference labels: run `build_reference_labels.ipynb`, which writes `data/references/wad_references.csv` (not committed).
   
4. Module (Kaggle, GPU): run `hazard_prioritisation_module.ipynb` once per subset, changing only `SUBSET` and `DATA_DIR`. Download `<subset>_outputs.zip` and extract it to `results/outputs/<subset>/`.
   
5. VLM (Kaggle, GPU): run `qwen_reminders.ipynb` with `SUBSET = "test"` and `MODE = "full"`, and put `qwen_full_v13.jsonl` in `results/outputs/qwen/`.
   
6. Human labels: run `human_check.ipynb` with `JUDGE = 1` or `2`. Labels are saved to `results/outputs/human/`.
   
7. Evaluation: run `evaluation.ipynb` (Restart & Run All). It writes every table to `results/tables/` and every result figure to `results/figures/`.
   
8. Method figures: run `report_figures.ipynb`. These figures show WAD frames and are therefore not committed.

**Note:** On a single Kaggle GPU T4, perception takes about 5 s per clip (detection 1.3 s, segmentation 1.5 s, depth 2.5 s), and Qwen2-VL-2B takes about 4.6 s per clip for the three conditions.

## Requirements

```
pip install -r requirements.txt
```

The local notebooks need `pandas`, `numpy`, `matplotlib`, `scikit-learn`, `scipy`, `rouge-score` and `sentence-transformers`.
The Kaggle notebooks install `ultralytics` and `transformers` themselves.