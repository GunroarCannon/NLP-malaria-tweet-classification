# Malaria Topic Classification on Nigerian Twitter

This repository contains the tools and pipeline for building a specialized NLP model to classify malaria-related tweets in the Nigerian context. The project forms part of a public health infoveillance study, focusing on understanding sentiment, treatment-seeking behavior, and the spread of misinformation.

## Project Overview

The core objective is to fine-tune a **BERTweet-base** model on a curated corpus of Nigerian malaria tweets. The model classifies tweets into five functional categories to support real-time bio-surveillance and public health response.

### The 5-Class Taxonomy
1.  **Symptoms & Burden**: Biological/socio-economic impact (fever, body pain, "Ako iba").
2.  **Treatment & Health System**: Actions taken to cure (ACTs, Agbo, hospital visits).
3.  **Prevention & Awareness**: Proactive measures (nets, vaccines, clearing gutters).
4.  **Misinformation**: Factual falsehoods and dangerous claims ("Malaria is a scam").
5.  **Irrelevant**: Noise, metaphors, or political commentary.

---

## Components

### 1. Data Annotation Tool (`labeller_new.py`)
A crash-safe, CLI-based annotation tool designed for rapid labelling.
- **Features**: Auto-save every 5 labels, session stats (ETA, speed), "Undo" functionality, and Inter-Annotator Agreement (IAA) computation.
- **Usage**:
  ```bash
  python labeller_new.py --start
  ```

### 2. Data Processing (`splitter.py`, `data.py`)
- **`splitter.py`**: Separates raw data into `_replies.jsonl` and `_non_replies.jsonl` for focused analysis.
- **`data.py`**: Utility script for loading and preparing data for training.

### 3. Model Training (`NLP_builder.ipynb`)
- Fine-tunes `vinai/bertweet-base` using the Hugging Face Transformers library.
- Implements class weighting to handle imbalance (e.g., the prevalence of "Symptoms & Burden").
- Evaluates using Macro F1-score as the primary metric.

### 4. Implementation Strategy (`plan.md`, `guidelines.md`)
- **`plan.md`**: Detailed 4-phase roadmap (Training, Dashboard, Real-time Surveillance, Deployment).
- **`guidelines.md`**: Definitive annotation rules ensuring consistency and handling Nigerian Pidgin nuances.

---

## Getting Started

### Prerequisites
- Python 3.8+
- Recommended: Virtual environment (`venv` or `conda`)

### Installation
```bash
pip install pandas transformers torch scikit-learn ntscraper streamlit plotly
```

### Typical Workflow
1.  **Prepare Data**: Run `splitter.py` to organize your raw JSON/JSONL files.
2.  **Annotate**: Use `labeller_new.py` to label the corpus based on the `guidelines.md`.
3.  **Train**: Open `NLP_builder.ipynb` in Google Colab or locally to fine-tune the BERTweet model.
4.  **Evaluate**: Check the classification report and confusion matrix to identify label confusion (e.g., Misinformation vs. Treatment).

---

## 🗺️ Roadmap
- [x] Data collection and cleaning
- [x] Robust annotation tool development
- [/] Model fine-tuning (In Progress)
- [ ] Streamlit Dashboard for batch/live inference
- [ ] Geospatial mapping of "Symptoms & Burden" clusters

## 📜 License
*Project created for academic research purposes.*
