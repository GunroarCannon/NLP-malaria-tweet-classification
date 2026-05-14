To ensure the **BERTweet** model achieves high accuracy and consistency for your thesis, you are following a **functional, priority-based schema**. Since the Nigerian Twitter space is "noisy" (filled with slang, politics, and metaphors), the guideline must focus on the **primary intent** of the tweet.

Here are the definitive guidelines for labelling the corpus:

---

## **1. Symptoms & Burden [1]**

* **Definition:** The tweet describes the biological, physical, or socio-economic impact of the disease on a person.
* **Biological Signals:** Fever, headache, shivering ("cold"), "body pepper," "Ako iba" (Yoruba for strong fever), "bitter taste."
* **Burden Signals:** "I can't work," "Malaria has finished my money," "I'm suffering."
* **The Rule:** If the tweet only describes **feeling sick** or the **consequences of being sick**, it is Label 1.

## **2. Treatment & Health System [2]**

* **Definition:** The tweet involves an action taken to cure or manage the disease.
* **Medical Anchors:** ACTs, Coartem, Lonart, "Chemists," "Injection," "Drip," "Doctor," "Hospital."
* **Traditional Anchors:** Agbo, "Dogonyaro," "Herbal."
* **Behavioral Anchors:** "I didn't finish my dose," "I just treated malaria," "Which drug should I take?"
* **The Rule:** **Action overrides Symptom.** If a user says "I have a fever [1] and I took a drug [2]," the label is **[2]**.

## **3. Prevention & Awareness [3]**

* **Definition:** Proactive measures to avoid infection or the spread of health information.
* **Prevention Anchors:** Mosquito nets (ITNs), insecticide (Sniper/Raid), vaccines, "Clear the gutters."
* **Awareness Anchors:** Clinical research titles, sharing statistics, "Malaria is deadly, stay safe."
* **The Rule:** If the intent is to **stop the disease before it starts**, it is Label 3.

## **4. Misinformation & False Claims [4]**

* **Definition:** The spread of scientifically unverified, dangerous, or conspiratorial content.
* **Anchors:** "Malaria is a scam," "Drink [dangerous substance] to cure it," "Government created it to kill us."
* **The Rule:** This is strictly for **factual falsehoods** that pose a public health risk.

## **5. Irrelevant [5]**

* **Definition:** Mentions "malaria" but has zero public health utility.
* **Metaphor/Slang:** "This government is malaria," "This song is malaria (sick/good)."
* **Politics:** "Politicians go to UK to treat malaria" (This is a vote-seeking/political critique, not a health event).
* **The Rule:** If a health official can't use the data to track a real medical case or a trend, it’s Noise.

---

### **The Annotation Decision Tree**

### **Why this works for the BERTweet Model:**

1. **Mutual Exclusivity:** It prevents the model from getting confused between someone *being* sick and someone *treating* the sickness.
2. **Entity Weighting:** By prioritizing Label 2 (Treatment) when drugs are mentioned, you teach the model to give higher "weights" to pharmaceutical entities.
3. **Pidgin Handling:** These rules allow you to map Pidgin phrases like *"I don treat"* directly to Label 2, ensuring the model understands the cultural context of health-seeking behavior in Nigeria.