Got everything I need. Here's the updated implementation plan aligned to your report and your 5-class taxonomy:

---

## Phase 1: Model Fine-Tuning (The "Engine")

**Dataset Prep**
Load your JSON and map the integer keys to their string labels:
```python
label2id = {"Symptoms & Burden": 1, "Treatment & Health System": 2,
            "Prevention & Awareness": 3, "Misinformation": 4, "Irrelevant": 5}
id2label = {v: k for k, v in label2id.items()}
```
Convert to a Hugging Face `Dataset` object, then do a stratified 80/10/10 train/val/test split. Stratify on label to fight class imbalance — based on your report's warning, "Symptoms & Burden" will likely dominate.

**Preprocessing (BERTweet-specific)**
BERTweet expects its own normalisation conventions before tokenisation:
- Replace all `@mentions` → `@USER`
- Replace all URLs → `HTTPURL`
- Don't lowercase — BERTweet is case-sensitive and was trained on raw tweet casing

Use `VinAIResearch/bertweet-base`'s `AutoTokenizer` with `normalization=True` — it handles Naija abbreviations and emoji tokens better than vanilla BERT's tokeniser.

**Handling Class Imbalance**
Since your report flags this explicitly, use `class_weight='balanced'` for SVM/LR baselines and `compute_class_weight` from sklearn to generate weights to pass as `class_weights` in `nn.CrossEntropyLoss` for BERTweet. Don't rely on oversampling alone given your ~1,255 tweet dataset size.

**Fine-Tuning**
Fine-tune `vinai/bertweet-base` as a sequence classifier with `num_labels=5`. Recommended config:
- LR: `2e-5`, batch size: `16`, epochs: `4–6`, warmup ratio: `0.1`
- Use `WeightedRandomSampler` or loss weighting for the imbalance
- Save the best checkpoint by macro F1 on the val set (not accuracy — your report correctly identifies macro F1 as the primary metric)

**Baselines**
Train SVM and Logistic Regression on TF-IDF features (same preprocessed text) so you have the comparison your report's RQ3 requires. These are fast — run them first.

**Evaluation**
Generate a full classification report with per-class F1 for all 5 labels and a confusion matrix. Pay special attention to:
- "Misinformation" vs "Treatment & Health System" confusion (they share drug/remedy vocabulary)
- "Irrelevant" precision (a leaky irrelevant class will pollute your public health signal)

Save both the fine-tuned model weights and tokenizer via `model.save_pretrained()` and `tokenizer.save_pretrained()`.

---

## Phase 2: Streamlit Dashboard (The "Interface")

**Model Loading**
```python
@st.cache_resource
def load_model():
    tokenizer = AutoTokenizer.from_pretrained("./saved_bertweet")
    model = AutoModelForSequenceClassification.from_pretrained("./saved_bertweet")
    return pipeline("text-classification", model=model, tokenizer=tokenizer)
```

**Input Methods**
- Manual text box for single tweet classification — show the predicted label and a confidence bar for all 5 classes
- CSV upload for batch inference — output a downloadable CSV with a `predicted_label` column appended

**Visualisations**
- Pie or bar chart (Plotly) showing distribution across all 5 classes from batch results
- Highlight the "Misinformation" slice separately given its public health relevance — your report's significance section justifies this framing
- Show a confidence threshold slider so users can filter out low-confidence predictions

---

## Phase 3: Real-Time Geospatial Surveillance (The "Infoveillance")

This directly operationalises your Infodemiology framework from Section 2.2.3.

**Data Ingestion**
Use `ntscraper` or `snscrape` (no API key needed) to pull live tweets with seed terms from your scope section: `malaria`, `#EndMalaria`, `artemisinin`, `coartem`, `fever chills Nigeria`, etc. Filter by Nigerian location signals as defined in your Section 1.6 geographic scope criteria.

**Real-Time Inference**
Pipe fetched tweets through your loaded BERTweet pipeline. Flag and separate tweets predicted as "Misinformation" (label 4) for a dedicated alert panel.

**Mapping**
If tweets contain location metadata, use `st.map()` or Folium to show:
- Red pins for "Symptoms & Burden" (label 1) clusters — your primary surveillance signal
- Orange pins for "Misinformation" (label 4) — mis-info hotspots
- This directly supports the bio-surveillance angle your significance section describes

---

## Phase 4: Deployment

- **Hugging Face Spaces** is the cleanest option — you can host both the model weights and the Streamlit app in one repo, which is easier to cite in your thesis appendix
- **Streamlit Community Cloud** as fallback — free, just needs a GitHub repo
- Your `requirements.txt`: `torch`, `transformers`, `datasets`, `streamlit`, `plotly`, `pandas`, `scikit-learn`, `ntscraper`

---

**One alignment note for your Colab:** Your report's objective 2 still says "seven predefined topic categories" — worth doing a ctrl+F sweep to update that to "five" before submission, since your JSON and this entire training pipeline will run on 5.