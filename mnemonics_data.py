"""
GEMA-MED — Mnemonics high-yield USMLE curados.
Fuente: First Aid, Sketchy Medical, UWorld, UpToDate.
"""

MNEMONICS: dict[str, list[dict]] = {

    "cardiology": [
        {
            "title": "Heart Failure Signs — FACES",
            "mnemonic": "**F**atigue · **A**ctivity limitation · **C**ongestion · **E**dema · **S**hortness of breath",
            "detail": "Classic symptoms of congestive heart failure. Congestion → JVP elevation, orthopnea, PND.",
        },
        {
            "title": "Acute MI Management — MONA",
            "mnemonic": "**M**orphine · **O**xygen · **N**itrates · **A**spirin",
            "detail": "MONA greets patients with ACS. Morphine for pain, O₂ if saturation <94%, nitrates for vasodilation, aspirin 325mg immediately.",
        },
        {
            "title": "QT-Prolonging Drugs — MALE",
            "mnemonic": "**M**acrolides · **A**ntipsychotics (haloperidol, quetiapine) · **L**evofloxacin · **E**lectrolyte imbalances",
            "detail": "Also amiodarone, methadone, TCAs. Risk of Torsades de Pointes. Check K⁺, Mg²⁺, Ca²⁺.",
        },
        {
            "title": "Aortic Stenosis Triad — SAD",
            "mnemonic": "**S**yncope · **A**ngina · **D**yspnea (Dyspnea on exertion)",
            "detail": "Survival: 5yr after syncope, 3yr after angina, 2yr after dyspnea. Crescendo-decrescendo murmur at RUSB radiating to carotids.",
        },
        {
            "title": "Atrial Fibrillation Rate Control vs. Rhythm",
            "mnemonic": "**ABCD** rate control drugs: **A**midarone (rhythm only) · **B**eta-blockers · **C**alcium channel blockers (non-DHP) · **D**igoxin",
            "detail": "Beta-blockers or CCBs first-line for rate control. Cardioversion requires anticoagulation ≥3 weeks or TEE to rule out thrombus.",
        },
    ],

    "pharmacology": [
        {
            "title": "Sulfonamide Side Effects — SULFA",
            "mnemonic": "**S**tevens-Johnson syndrome · **U**rinary crystals · **L**upus-like syndrome · **F**olate antagonism · **A**plastic anemia",
            "detail": "Also kernicterus in neonates (displaces bilirubin from albumin). Drink plenty of water to prevent crystalluria.",
        },
        {
            "title": "ACE Inhibitor Side Effects — CAPTOPRIL",
            "mnemonic": "**C**ough · **A**ngioedema · **P**otassium increase · **T**eratogen · **O**nco-nephroprotective · **P**roteinuria reduction · **R**enovascular hypertension (worsens) · **I**ntolerance in bilateral renal artery stenosis · **L**ower GFR",
            "detail": "Cough is #1 side effect (bradykinin). Switch to ARB if intolerable. Contraindicated in pregnancy (category D/X).",
        },
        {
            "title": "Beta-Blocker Selectivity — β₁ selective (heart)",
            "mnemonic": "**A**tenolol · **M**etoprolol · **E**smolol — '**AME**' (B₁ selective, use in asthma/COPD)",
            "detail": "Non-selective (β₁+β₂): propranolol, carvedilol, labetalol. Carvedilol also blocks α₁. High dose selective blockers lose β₁ selectivity.",
        },
        {
            "title": "Statins Side Effects — STATINS",
            "mnemonic": "**S**keletal myopathy (rhabdomyolysis) · **T**eratogen · **A**LT elevation · **T**hink CK if muscle pain · **I**nhibit CYP3A4 metabolism · **N**ot with fibrates · **S**top if pregnant",
            "detail": "Monitor LFTs and CK. Risk increased with gemfibrozil (but not fenofibrate). Main mechanism: HMG-CoA reductase inhibition.",
        },
        {
            "title": "Warfarin Interactions — The P450 Inducers Lower It",
            "mnemonic": "**P**henytoin · **R**ifampin · **C**arbamazepine · **B**arbiturates — all INDUCE CYP → ↓warfarin effect",
            "detail": "Inhibitors (↑warfarin): amiodarone, fluconazole, metronidazole, cimetidine. Vitamin K reverses; FFP for urgent reversal.",
        },
    ],

    "microbiology": [
        {
            "title": "Encapsulated Bacteria — SHiNE SKiS",
            "mnemonic": "**S**trep pneumoniae · **H**aemophilus influenzae · **N**eisseria meningitidis · **E**. coli K1 · **S**almonella typhi · **K**lebsiella · **i**dle (group B Strep)",
            "detail": "Asplenic patients are at highest risk. Vaccines: meningococcal, pneumococcal, Hib. Opsonization is the key defense.",
        },
        {
            "title": "Urease-Positive Organisms — PUNCH KHN",
            "mnemonic": "**P**roteus · **U**reaplasma · **N**ocardia · **C**ryptococcus · **H**. pylori · **K**lebsiella · **H**. pylori · **N**...",
            "detail": "Classic: PUNCH = Proteus (struvite stones), Ureaplasma, Nocardia, Cryptococcus, H. pylori. Urease splits urea → NH₃ + CO₂.",
        },
        {
            "title": "Gram+ Cocci vs Gram- Rods in Meningitis by Age",
            "mnemonic": "**N**eonates (<1mo): Group B Strep + E. coli + Listeria\n**B**abies (1-3mo): above + S. pneumoniae\n**C**hildren/Adults: S. pneumoniae + N. meningitidis\n**E**lderly/Immune: + Listeria",
            "detail": "Empiric: neonates → ampicillin+gentamicin; adults → ceftriaxone+vancomycin±ampicillin. Add dexamethasone to reduce inflammation.",
        },
        {
            "title": "Intracellular Organisms —'Stay Inside' — TROLL CRABS",
            "mnemonic": "**T**oxoplasma · **R**ickettsia · **O**rthopoxvirus · **L**egionella · **L**isteria · **C**hlamydia · **R**ickettsia · **A**naplasma · **B**rucella · **S**almonella",
            "detail": "Obligate intracellular: Rickettsia, Chlamydia. Facultative: Salmonella, Listeria, Legionella, Brucella, Toxoplasma. These evade antibodies.",
        },
        {
            "title": "Bugs With No Cell Wall (No β-lactam activity)",
            "mnemonic": "**My**coplasma · **U**reaplasma · **C**hlamydia → **MUC**",
            "detail": "Use macrolides, tetracyclines, or fluoroquinolones. Mycoplasma causes 'walking pneumonia' — atypical presentation, cold agglutinins.",
        },
    ],

    "neurology": [
        {
            "title": "Stroke Syndromes — FAST (public) + MCA signs",
            "mnemonic": "**F**ace drooping · **A**rm weakness · **S**peech slurred · **T**ime to call 911\nMCA: Contralateral face+arm > leg weakness + aphasia (dominant hemisphere)",
            "detail": "PCA: vision loss (homonymous hemianopsia). PICA: Wallenberg syndrome (ipsilateral face, contralateral body). ACA: leg > arm weakness.",
        },
        {
            "title": "Wernicke's Encephalopathy Triad — CAT",
            "mnemonic": "**C**onfusion · **A**taxia · **ophthalmoplegia** (nystagmus/gaze palsy) = **CAT**",
            "detail": "Caused by thiamine (B1) deficiency — alcoholics, hyperemesis gravidarum, malnutrition. Give IV thiamine BEFORE glucose. Korsakoff = confabulation.",
        },
        {
            "title": "Parkinson's Motor Triad — TRAP",
            "mnemonic": "**T**remor (resting, pill-rolling) · **R**igidity (cogwheel) · **A**kinesia/bradykinesia · **P**ostural instability",
            "detail": "Loss of dopaminergic neurons in substantia nigra. Treat: levodopa+carbidopa. Carbidopa prevents peripheral metabolism of levodopa.",
        },
        {
            "title": "Epidural vs Subdural Hematoma",
            "mnemonic": "**E**pidural = **E**arteRy (middle meningeal) = biconvex, lucid interval then rapid deterioration\n**S**ubdural = **S**ubdural veins = crescent, gradual, elderly/alcoholic",
            "detail": "Epidural: lens-shaped on CT, does NOT cross suture lines. Subdural: crescent-shaped, crosses suture lines. Subarachnoid: thunderclap headache, blood in cisterns.",
        },
        {
            "title": "Spinal Cord Syndromes — Brown-Séquard",
            "mnemonic": "Hemisection: ipsilateral UMN + proprioception loss; contralateral pain/temp loss",
            "detail": "Remember: spinothalamic (pain/temp) crosses immediately; dorsal columns (proprioception) cross in medulla. Anterior cord: bilateral motor + pain/temp loss, proprioception preserved.",
        },
    ],

    "gastroenterology": [
        {
            "title": "Liver Failure Signs — ABCDEFG",
            "mnemonic": "**A**scites · **B**leeding (coagulopathy) · **C**erebral edema · **D**ilation (portal HTN) · **E**ncephalopathy · **F**etor hepaticus · **G**ynecomastia",
            "detail": "Ascites: low albumin (↓oncotic pressure) + portal HTN. Caput medusae = dilated periumbilical veins. Spider angiomas on trunk.",
        },
        {
            "title": "Causes of Acute Pancreatitis — GET SMASHED",
            "mnemonic": "**G**allstones · **E**thanol · **T**rauma · **S**teroids · **M**umps · **A**utoimmune · **S**corpion sting · **H**ypercalcemia/Hypertriglyceridemia · **E**RCP · **D**rugs",
            "detail": "Gallstones #1 overall, alcohol #2. High amylase (faster rise) + lipase (more specific, stays elevated longer). Cullen's = periumbilical bruising; Grey Turner's = flank bruising.",
        },
        {
            "title": "Crohn's vs Ulcerative Colitis",
            "mnemonic": "**C**rohn = **C**omplete GI tract, skip lesions, full thickness, granulomas, fistulas, string sign on barium\n**U**C = **U**niform from rectum, superficial, pseudopolyps, lead-pipe colon",
            "detail": "Both ↑colon cancer risk (UC > Crohn's). Crohn → B12 malabsorption (terminal ileum). Toxic megacolon more common in UC.",
        },
        {
            "title": "Hepatitis Serology Quick Review",
            "mnemonic": "**HBsAg** = active infection · **Anti-HBs** = immunity (vaccine or recovery) · **Anti-HBc IgM** = acute · **Anti-HBc IgG** = past · **Window** = only anti-HBc positive",
            "detail": "HBeAg = high infectivity. HBV: DNA virus. HDV needs HBV. HCV = 'seductive' — highest rate of chronicity (~75%). HAV/HEV = fecal-oral.",
        },
    ],

    "endocrinology": [
        {
            "title": "DKA vs HHS Key Differences",
            "mnemonic": "**DKA**: Type 1, glucose >250, pH <7.3, ketones +++, bicarbonate <15 — treat insulin+fluids+K\n**HHS**: Type 2, glucose >600, minimal ketosis, serum osm >320, mortality higher",
            "detail": "DKA: anion gap metabolic acidosis. Give K⁺ before insulin if <3.5 mEq/L. HHS: massive fluid deficit (up to 9L). Both need Q1h glucose monitoring.",
        },
        {
            "title": "Cushing Syndrome Features — HUMP DAD",
            "mnemonic": "**H**ypertension · **U**rinary cortisol ↑ · **M**oon face/central obesity · **P**urple striae · **D**iabetes · **A**trophied muscles · **D**epression/psychosis",
            "detail": "MCC: exogenous steroids. Pituitary adenoma = Cushing DISEASE (high ACTH). Adrenal adenoma = ACTH low. Ectopic ACTH (small cell lung) = very high ACTH.",
        },
        {
            "title": "Hypothyroidism vs Hyperthyroidism",
            "mnemonic": "**HYPO**: Slow COLD — Cold intolerance, Bradycardia, wt gain, constipation, dry skin, hair loss, myxedema\n**HYPER**: Fast HOT — Heat intolerance, palpitations, wt loss, diarrhea, tremor, exophthalmos (Graves)",
            "detail": "TSH is the most sensitive test. In hypothyroidism: TSH↑, T4↓. In hyperthyroidism: TSH↓, T4↑. Graves = anti-TSH receptor antibodies (stimulating).",
        },
        {
            "title": "MEN Syndromes",
            "mnemonic": "**MEN1** = 3 P's: **P**arathyroid + **P**ituitary + **P**ancreas (Zollinger-Ellison/insulinoma)\n**MEN2A** = 2C's+1P: **C**arcinoma (medullary thyroid) + **C**heochromocytoma + **P**arathyroid\n**MEN2B** = MEN2A - parathyroid + **M**arfanoid + **M**ucosal neuromas",
            "detail": "MEN1: menin gene mutation. MEN2: RET proto-oncogene. Pheochromocytoma: alpha-block (phenoxybenzamine) BEFORE beta-block to prevent hypertensive crisis.",
        },
    ],

    "hematology": [
        {
            "title": "Anemia Classification by MCV",
            "mnemonic": "**Micro** (<80): Iron deficiency, Thalassemia, Lead poisoning, Sideroblastic\n**Normo** (80-100): Anemia of chronic disease, Hemolysis, Aplastic\n**Macro** (>100): B12/Folate deficiency, Liver disease, Hypothyroid, Medications (hydroxyurea)",
            "detail": "Iron deficiency: low ferritin, high TIBC, low serum iron. B12 deficiency: neurological symptoms (subacute combined degeneration). Folate: no neuro.",
        },
        {
            "title": "Coagulation Cascade Basics — PT vs PTT",
            "mnemonic": "**PT** (Prothrombin Time) → **Extrinsic** (Factor VII) — warfarin affects this\n**PTT** (Partial Thromboplastin Time) → **Intrinsic** (VIII, IX, XI, XII) — heparin affects this\n**Both** ↑ = common pathway (I, II, V, X) or liver disease",
            "detail": "Hemophilia A: ↑PTT, normal PT (Factor VIII deficiency). vWF disease: ↑bleeding time + ↑PTT. DIC: both ↑ + ↓platelets + ↓fibrinogen + ↑D-dimer.",
        },
        {
            "title": "Sickle Cell Complications — SICKLE",
            "mnemonic": "**S**plenic sequestration/autosplenectomy · **I**nfarcts (bone, spleen, brain) · **C**hronic hemolytic anemia · **K**idney (papillary necrosis) · **L**ung (acute chest) · **E**xtremity pain crises",
            "detail": "Autosplenectomy → encapsulated organism susceptibility (vaccinate). Treat acute crises: hydration, O₂, analgesia, transfusion. HbS: Glu→Val substitution at β-chain position 6.",
        },
    ],

    "nephrology": [
        {
            "title": "Acid-Base Interpretation Steps",
            "mnemonic": "1. pH: acidosis (<7.35) or alkalosis (>7.45)\n2. pCO₂: respiratory? (↑CO₂=respiratory acidosis)\n3. HCO₃: metabolic? (↓HCO₃=metabolic acidosis)\n4. Compensation? (compensating, not correcting)\n5. Anion gap: Na - (Cl + HCO₃) — normal 8-12",
            "detail": "MUDPILES (high anion gap): Methanol, Uremia, DKA, Propylene glycol, Isoniazid, Lactic acidosis, Ethylene glycol, Salicylates. HARDUP (normal AG metabolic acidosis): Hyperalimentation, Acetazolamide, RTA, Diarrhea, Ureteral diversion, Pancreatic fistula.",
        },
        {
            "title": "Nephrotic vs Nephritic Syndrome",
            "mnemonic": "**NephROTic** = ROT = lots of pROTein → protein loss, edema, hypoalbuminemia, hyperlipidemia (MCNS, FSGS, membranous)\n**NephRITic** = GRIT = gRITty urine → hematuria, RBC casts, HTN, oliguria, mild proteinuria (IgA, PSGN, crescentic)",
            "detail": "MCNS: most common in children, responds to steroids, 'foot process effacement' on EM. PSGN: 2-3 weeks post strep, low complement. IgA nephropathy: synpharyngitic hematuria.",
        },
        {
            "title": "Renal Tubular Acidosis Types",
            "mnemonic": "**Type 1** (Distal): can't acidify urine, pH >5.5, ↓K, kidney stones (autoimmune, sickle cell)\n**Type 2** (Proximal): bicarb wasting, Fanconi syndrome, ↓K\n**Type 4** (Hyperkalemic): aldosterone deficiency/resistance, DM nephropathy, ACEi",
            "detail": "There is no Type 3 clinically. Type 4 most common overall (diabetic nephropathy). Urine anion gap differentiates RTAs from GI losses.",
        },
    ],

    "pulmonology": [
        {
            "title": "COPD vs Asthma Key Differences",
            "mnemonic": "**COPD**: >40yo smoker, irreversible obstruction, FEV1/FVC <70%, emphysema+chronic bronchitis\n**Asthma**: young+allergic, reversible obstruction, peak at night/exercise, eosinophils",
            "detail": "COPD: FEV1 determines severity (GOLD staging). GOLD 1-2: LABA/LAMA; GOLD 3-4: + ICS. Pulmonary rehab improves quality of life but not FEV1.",
        },
        {
            "title": "PE Wells Score Risk Factors",
            "mnemonic": "**DVT signs** +3 · **PE most likely diagnosis** +3 · **HR >100** +1.5 · **Immobilization >3 days/surgery <4wk** +1.5 · **Prior DVT/PE** +1.5 · **Hemoptysis** +1 · **Malignancy** +1",
            "detail": ">4 = PE likely → CT-PA. ≤4 = PE unlikely → D-dimer first. Treat: anticoagulation (LMWH/DOACs). Massive PE + instability → thrombolytics.",
        },
        {
            "title": "Types of Lung Pathology by Distribution",
            "mnemonic": "**Upper lobe**: TB, silicosis, sarcoidosis, coal worker's (S=top)\n**Lower lobe**: IPF, asbestosis, UIP pattern (FAIL=bottom)\n**Bilateral hilar adenopathy**: Sarcoidosis, Lymphoma, TB",
            "detail": "Asbestos: causes mesothelioma + bronchogenic carcinoma. Ferruginous bodies on BAL. Silicosis: eggshell calcification of hilar nodes. Both → ↑TB risk.",
        },
    ],

    "ob_gyn": [
        {
            "title": "Preeclampsia Diagnosis Criteria",
            "mnemonic": "**BP** ≥140/90 after 20 weeks + **P**roteinuria ≥300mg/24h OR\n**Severe features**: BP ≥160/110, headache, visual changes, RUQ pain, thrombocytopenia, ↑creatinine",
            "detail": "Delivery is the only cure. <34 wks: steroids + expectant management if stable. >37 wks: deliver. Severe/HELLP: deliver regardless of GA. MgSO₄ for seizure prophylaxis.",
        },
        {
            "title": "HELLP Syndrome",
            "mnemonic": "**H**emolysis · **E**levated **L**iver enzymes · **L**ow **P**latelets",
            "detail": "Variant of severe preeclampsia. Treat with MgSO₄ + antihypertensives + delivery. Steroids may improve platelet count temporarily.",
        },
        {
            "title": "Contraceptive Methods and Failure Rates",
            "mnemonic": "**Most effective**: Implant < IUD < Sterilization\n**LARC**: IUD (copper/hormonal) and implant — 'set and forget'\n**OCPs**: 0.3% perfect use, 9% typical\n**Condom**: 2% perfect, 18% typical",
            "detail": "Copper IUD = emergency contraception up to 5 days. OCPs: lower risk endometrial/ovarian cancer, ectopic pregnancy. Contraindications: DVT/PE history, smoking >35yo, migraines with aura.",
        },
    ],

    "pediatrics": [
        {
            "title": "Developmental Milestones — Rule of 4s",
            "mnemonic": "**4 months**: head control, social smile (2mo), roll front-to-back\n**6 months**: sits with support, transfers objects, babbles\n**12 months**: walks with support, 1-2 words, pincer grasp\n**18 months**: 10+ words, runs, stacks 4 cubes\n**24 months**: 50+ words, 2-word sentences, jump in place",
            "detail": "Red flags: no smile at 3mo, no babbling at 12mo, no words at 16mo, any regression. Denver II = standard developmental screening tool.",
        },
        {
            "title": "Congenital Heart Defects — Cyanotic vs Acyanotic",
            "mnemonic": "**Cyanotic (5 T's)**: Tetralogy of Fallot, Transposition, Truncus arteriosus, Tricuspid atresia, TAPVR\n**Acyanotic**: VSD (#1), ASD, PDA, Coarctation, AS, PS",
            "detail": "VSD = MCC of CHD. PDA: keeps open with PGE1 (ductal-dependent), close with indomethacin. Tetralogy: boot-shaped heart, tet spells → knee-chest position.",
        },
        {
            "title": "Vaccines Schedule Key Points",
            "mnemonic": "**Birth**: HepB\n**2,4,6 months**: DTaP, IPV, Hib, PCV13, RV\n**12-15 months**: MMR, Varicella, HepA, PCV13\n**11-12 years**: Tdap, MCV4, HPV",
            "detail": "Live vaccines: MMR, Varicella, LAIV, Yellow fever, Rotavirus. Contraindicated in immunocompromised patients. 28-day interval between live vaccines if not given same day.",
        },
    ],

    "psychiatry": [
        {
            "title": "Antidepressant Classes — Key Side Effects",
            "mnemonic": "**SSRIs**: Sexual dysfunction, Serotonin syndrome risk, SIADH\n**SNRIs**: Same + ↑BP (venlafaxine)\n**TCAs**: Anticholinergic (DUCTS), QT prolongation, lethal in overdose\n**MAOIs**: Tyramine crisis (cheese), hypertensive crisis",
            "detail": "DUCTS (TCA anticholinergic): Dry mouth, Urinary retention, Constipation, Tachycardia, Sedation. First-line depression: SSRIs. Bupropion: no sexual dysfunction, seizure risk.",
        },
        {
            "title": "Antipsychotic Side Effects — Typical vs Atypical",
            "mnemonic": "**Typicals** (haloperidol): EPS (dystonia, akathisia, parkinsonism, TD) + hyperprolactinemia\n**Atypicals** (clozapine, olanzapine): Metabolic syndrome + weight gain\n**Clozapine specifically**: Agranulocytosis → monitor CBC weekly",
            "detail": "EPS treatment: benztropine (anticholinergic). Tardive dyskinesia: stop offending drug, try valbenazine. Neuroleptic malignant syndrome: STOP drug, dantrolene + bromocriptine.",
        },
        {
            "title": "DSM-5 Major Depression Criteria — SIG E CAPS",
            "mnemonic": "**S**leep (↑or↓) · **I**nterest loss (anhedonia) · **G**uilt/worthlessness · **E**nergy ↓ · **C**oncentration ↓ · **A**ppetite (↑or↓) · **P**sychomotor changes · **S**uicidal ideation",
            "detail": "≥5 symptoms (must include depressed mood OR anhedonia) for ≥2 weeks = MDD. 1-2 symptoms = adjustment disorder. Bereavement: grief vs MDD distinction.",
        },
    ],

    "biostatistics": [
        {
            "title": "2x2 Table — Sensitivity vs Specificity",
            "mnemonic": "**Sensitivity** = TP/(TP+FN) → 'SnNOut': high **Sn**, when Negative → rules OUT\n**Specificity** = TN/(TN+FP) → 'SpPIn': high **Sp**, when Positive → rules IN\n**PPV** = TP/(TP+FP) — depends on prevalence\n**NPV** = TN/(TN+FN) — depends on prevalence",
            "detail": "Sensitivity used for screening (don't miss disease). Specificity used for confirmation (confirm disease). LR+ = Sens/(1-Spec). LR- = (1-Sens)/Spec.",
        },
        {
            "title": "Bias Types",
            "mnemonic": "**Selection**: Berkson (hospital-based), Healthy worker\n**Information**: Recall bias (cases remember exposure more), Observer bias, Hawthorne effect\n**Confounding**: Third variable affects both exposure and outcome\n**Lead-time**: Screening finds disease earlier but doesn't improve survival",
            "detail": "Randomization controls confounding. Double-blinding controls observer/recall bias. Restriction, matching, and stratification also control confounders.",
        },
        {
            "title": "Study Design Hierarchy",
            "mnemonic": "**Meta-analysis/SR** > **RCT** > **Cohort** (prospective) > **Case-control** (retrospective) > **Cross-sectional** > **Case series** > Expert opinion",
            "detail": "RCT: gold standard for causation. Cohort: calculates RR. Case-control: calculates OR. Cross-sectional: prevalence. Number needed to treat (NNT) = 1/ARR.",
        },
        {
            "title": "Statistical Tests Quick Guide",
            "mnemonic": "**2 groups, continuous**: t-test (parametric) or Mann-Whitney (non-parametric)\n**3+ groups**: ANOVA (parametric)\n**Categorical**: Chi-square\n**Survival data**: Kaplan-Meier, log-rank\n**Correlation**: Pearson (continuous) or Spearman (ordinal)",
            "detail": "p-value <0.05 = statistically significant (5% chance of Type I error). Power = 1 - β. Increase sample size to increase power.",
        },
    ],

    "pathology": [
        {
            "title": "Types of Necrosis — When to Use Each",
            "mnemonic": "**Coagulative**: MI, renal infarct — architecture preserved\n**Liquefactive**: Brain infarct, bacterial abscess — liquefied pus\n**Caseous**: TB, fungi — 'cottage cheese'\n**Fat**: Pancreatitis, trauma — calcium soap\n**Fibrinoid**: Immune complexes, hypertension — vessel walls\n**Gangrenous**: Limb ischemia",
            "detail": "TB: Ghon complex (primary), ghon focus + hilar LN. Caseating granulomas = TB, histoplasma. Non-caseating = sarcoidosis.",
        },
        {
            "title": "Tumor Suppressor vs Oncogenes",
            "mnemonic": "**Tumor suppressors** (both alleles lost — 'two-hit hypothesis'): **RB** (retinoblastoma), **p53** (Li-Fraumeni, 50% all cancers), **APC** (FAP, colon), **BRCA1/2** (breast/ovarian), **VHL** (RCC)\n**Oncogenes** (dominant, 1 hit): **RAS** (many cancers), **MYC** (Burkitt), **HER2** (breast), **BCR-ABL** (CML)",
            "detail": "p53: guardian of the genome → G1/S checkpoint, apoptosis. Loss → cells bypass checkpoint. BCR-ABL: Philadelphia chromosome t(9;22) → treat with imatinib.",
        },
    ],

    "anatomy": [
        {
            "title": "Brachial Plexus — Roots Trunks Divisions Cords Branches",
            "mnemonic": "**Real Texans Drink Cold Beer** = Roots Trunks Divisions Cords Branches\n**C5-T1** roots → upper/middle/lower trunks → cords (lateral/posterior/medial) → branches",
            "detail": "Erb's palsy (C5-C6): 'waiter's tip' — arm extension, pronation, wrist flexion. Klumpke's (C8-T1): hand intrinsics, claw hand, Horner's syndrome. Axillary nerve (C5-C6): shoulder dislocation → deltoid weakness.",
        },
        {
            "title": "Femoral Triangle Contents — NAVEL",
            "mnemonic": "Lateral→Medial: **N**erve · **A**rtery · **V**ein · **E**mpty (femoral canal) · **L**ymphatics",
            "detail": "Femoral nerve is lateral, vein is most medial (mnemonic: NAVY = Nerve Artery Vein, Y=lymphatics). Femoral hernia passes through femoral canal (medial). More common in women.",
        },
    ],

    "physiology": [
        {
            "title": "Cardiac Output Equation — Fick's Principle",
            "mnemonic": "**CO = HR × SV**\nSV depends on: **P**reload (EDV, Starling), **A**fterload (SVR), **C**ontractility = **PAC**",
            "detail": "Normal CO: 5 L/min. CI = CO/BSA (normal 2.5-4). Increased preload → increased SV (Starling curve). Increased afterload → decreased SV. Positive inotropes ↑ contractility.",
        },
        {
            "title": "Starling Forces (Capillary Fluid Exchange)",
            "mnemonic": "**OUT of capillary** (filtration): hydrostatic pressure inside + oncotic pressure outside\n**INTO capillary** (reabsorption): hydrostatic pressure outside + oncotic pressure inside\nNet filtration = Kf × [(Pc - Pi) - σ(πc - πi)]",
            "detail": "Edema causes: ↑capillary HP (heart failure, portal HTN), ↓plasma oncotic (hypoalbuminemia), ↑capillary permeability (inflammation), lymphatic obstruction.",
        },
    ],

    "biochemistry": [
        {
            "title": "Vitamins — Fat-Soluble ADEK",
            "mnemonic": "**A**: Night blindness, xerophthalmia; retinoids → teratogen in excess\n**D**: Rickets (children), osteomalacia (adults); ↑Ca absorption; toxicity = hypercalcemia\n**E**: Antioxidant, hemolytic anemia in premature infants\n**K**: Clotting factors II, VII, IX, X + protein C/S; deficiency = hemorrhagic disease of newborn",
            "detail": "All fat-soluble vitamins can accumulate (toxicity risk). D3 synthesized in skin via UV. K antagonized by warfarin. Coumarin inhibits vitamin K epoxide reductase.",
        },
        {
            "title": "Glycolysis Key Irreversible Steps — 'Pathway Frozen by Kids'",
            "mnemonic": "**P**hosphofructokinase-1 (PFK-1) → step 3 [regulated by AMP, ATP, citrate]\n**F**ructose-1,6-bisphosphatase bypass in gluconeogenesis\n**K**inases: hexokinase (step 1) and pyruvate kinase (step 10) — irreversible",
            "detail": "Gluconeogenesis uses 3 unique enzymes: PEPCK, fructose-1,6-bisphosphatase, glucose-6-phosphatase (liver only). Cori cycle: lactate → liver → glucose (costs 6 ATP net).",
        },
        {
            "title": "Lysosomal Storage Diseases",
            "mnemonic": "**Gaucher** (glucocerebrosidase ↓): Erlenmeyer flask bones, 'crinkled tissue paper' cells\n**Niemann-Pick** (sphingomyelinase ↓): cherry-red spot, foam cells\n**Tay-Sachs** (hexosaminidase A ↓): cherry-red spot, NO hepatosplenomegaly\n**Fabry** (α-galactosidase ↓): angiokeratomas, X-linked, renal/cardiac",
            "detail": "GM2 gangliosidoses: Tay-Sachs (hexA absent) and Sandhoff (hexA+B absent). Both: cherry-red spot. Only Tay-Sachs: no hepatosplenomegaly. Gaucher: most common lysosomal storage disease.",
        },
    ],
}

def get_mnemonics(topic: str) -> list[dict]:
    """Returns mnemonics for a given topic. Falls back to empty list."""
    return MNEMONICS.get(topic.lower(), [])


def get_all_topics() -> list[str]:
    return sorted(k for k, v in MNEMONICS.items() if v)
