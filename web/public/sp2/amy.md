# Personalized Evidence Pack — amy_runner

- Compiled at: 2026-05-27T10:16:28.190742+00:00
- Library version: 0.1.0

---

## Client context

- **Profile:** F, 32y, 58.0 kg, 168 cm, training status: recreational
- **Goals:** endurance, performance
- **Constraints:**
  - *injury*: left knee mild patellar tendinopathy

## Nutrition

### Pattern: RP-NUT-endurance-fueling-performance (sim=0.85)

**Applies because:** Carbohydrate availability is the primary limiter of high-intensity endurance performance; periodic training in a low-carbohydrate state upregulates fat oxidation enzymes and mitochondrial biogenesis signals, improving metabolic flexibility; iron is the rate-limiting micronutrient for oxygen-carrying capacity in endurance athletes, and its deficiency — even subclinical — demonstrably impairs endurance and behavioral markers in women.
**For this client (F, 32y, recreational):** Recreational endurance athletes (5-10 h/week training): train-high on interval and threshold sessions (>=6 g/kg/day carbohydrate on key days); train-low on 1-2 easy aerobic sessions per week (carbohydrate <2 g/kg the day before or low-glycogen morning sessions); do not exceed 2 train-low sessions per week to avoid overreaching; total carbohydrate average 5-7 g/kg/day.
<details><summary>All populations covered by this pattern</summary>

Sedentary adults beginning endurance training (0-6 months, <5 h/week): carbohydrate periodization is premature at this stage; consume 4-5 g/kg/day total carbohydrate; prioritize consistent fueling over train-low strategies; iron status screening is warranted (especially females) as even mild iron deficiency impairs aerobic endurance in this group. Recreational endurance athletes (5-10 h/week training): train-high on interval and threshold sessions (>=6 g/kg/day carbohydrate on key days); train-low on 1-2 easy aerobic sessions per week (carbohydrate <2 g/kg the day before or low-glycogen morning sessions); do not exceed 2 train-low sessions per week to avoid overreaching; total carbohydrate average 5-7 g/kg/day. Trained endurance athletes (>10 h/week): systematic train-low periodization aligned with training blocks; carbohydrate 6-10 g/kg/day during high-load phases; race fueling 60-90 g/h from a glucose:fructose 2:1 ratio blend for sessions >60-75 min; gut training required to tolerate high intra-race carbohydrate rates. Older endurance athletes (>=60 y): glycogen synthesis rate and storage capacity decline with age; prioritize carbohydrate intake within 60 min post-session for replenishment; train-low protocols should be less aggressive due to higher muscle protein catabolism risk at low fuel availability; co-ingest protein (20-25 g) with post-session carbohydrate. Female endurance athletes: iron deficiency is a high-prevalence performance limiter; monitor serum ferritin proactively (target >30 ng/mL); early-follicular phase iron status is at nadir and may impair response to high-intensity sessions; carbohydrate periodization targets are comparable to males when weight-adjusted.

</details>
**Safety bounds:** Train-low sessions must not be used on high-intensity interval days or competition simulation days — impaired glycolytic fuel availability during high-intensity work increases injury risk and training quality is severely compromised; do not exceed 90 g/h intra-race carbohydrate without prior gut adaptation training; iron supplementation above 45 mg/day requires physician oversight.

**Backing evidence (top 3 by population match):**

### Pattern: RP-NUT-meal-timing-protein-distribution (sim=0.74)

**Applies because:** Skeletal muscle protein synthesis is acutely stimulated by a leucine threshold-dependent mechanism per meal; distributing protein across multiple feedings captures repeated MPS pulses throughout the day rather than relying on a single large bolus, which saturates the response and leaves the muscle in a relative fasting state between feedings.
**For this client (F, 32y, recreational):** Trained females (18-49 y): same per-meal dose structure as resistance-trained adults; body weight-adjusted targets land at 25-35 g/meal for most women; no evidence of sex-specific meal frequency interaction on MPS rate.
<details><summary>All populations covered by this pattern</summary>

Sedentary or untrained healthy adults: 3-4 meals daily, ~25-30 g protein per meal from high-leucine sources (dairy, eggs, lean meat), total daily intake 0.8-1.2 g/kg; leucine threshold easily met with whole-food protein sources at these doses. Resistance-trained adults (18-49 y): 4-5 meals daily, 0.4 g/kg/meal (typically 30-45 g per meal for a 75 kg adult), total 1.6-2.2 g/kg/day; spacing meals 3-5 h apart to allow MPS refractory period recovery. Older adults (>=60 y): 4-5 meals with >=25-30 g protein per meal using leucine-enriched or isolated protein sources (whey preferred); whole-food leucine trigger is less reliable in this population so isolated protein supplements are more applicable; total 1.2-1.6 g/kg/day minimum. Trained females (18-49 y): same per-meal dose structure as resistance-trained adults; body weight-adjusted targets land at 25-35 g/meal for most women; no evidence of sex-specific meal frequency interaction on MPS rate. Older adults post-resistance training: whey protein >=20 g within 2 h post-session as one of the distributed feedings; leucine co-ingestion may augment response when whole-food protein is the primary source.

</details>
**Safety bounds:** No upper safety limit on meal frequency at physiological protein doses; protein per meal above 0.6 g/kg has not been shown to produce further MPS benefit and represents unnecessary intake cost; do not exceed total daily intake upper bounds (3.1 g/kg) without renal screening.

**Backing evidence (top 3 by population match):**

### Pattern: RP-NUT-protein-band (sim=0.73)

**Applies because:** Resistance-trained adults in an energy deficit.
**Parameterization:** 2.3-3.1 g/kg/day for resistance-trained adults in a hypocaloric period; pick upper end in steeper deficits or higher training volume.
**Safety bounds:** Flag renal history before recommending; daily intakes above ~3.1 g/kg/d are not supported by the cited evidence for additional FFM benefit.

**Backing evidence (top 3 by population match):**
- Protein intakes of 2.3-3.1 g/kg/day may be needed to maximize retention of lean body mass in resistance-trained subjects during hypocaloric periods. ([10.1186/s12970-017-0177-8])

- **EA-NUT-5322** (sim 0.71, pop-match 1.00): Calorie restriction combined with exercise is the most effective strategy for reducing weight and fat percentage while maintaining lean body mass in healthy adults. ([10.3390/nu16173007])
- **EA-NUT-0926** (sim 0.66, pop-match 1.00): In community-dwelling adults aged 50 or older, a serum amino acid factor reflecting insulin resistance-related branched-chain and aromatic amino acids is positively associated with nondynapenic obesity in both sexes, while sex-specific nitrogen metabolism patterns are differentially linked to dynapenia and adiposity. ([10.1007/s40200-025-01746-x])
- **EA-NUT-4389** (sim 0.66, pop-match 1.00): Meta-analysis quantifies the accuracy of blood glucose prediction models across various horizons and the performance of meal and physical activity detection models. ([10.1088/2516-1091/ae39b9])
- **EA-NUT-5593** (sim 0.60, pop-match 1.00): Interventions leveraging gamification, social interaction, and goal-setting have shown greater efficacy in improving body-nutrition profile. ([10.3390/nu17223542])
- **EA-NUT-3698** (sim 0.59, pop-match 1.00): Combining exercise with very low energy diets (VLEDs) results in higher retention of fat free mass (FFM) compared to VLED alone during rapid weight loss. ([10.1016/j.orcp.2025.10.001])

## Training

**For this client — constraint-aware notes:**
- Patellar tendinopathy: emphasize slow eccentric tempo (3-5s down) on lower-body work; avoid plyometric volume escalation until pain-free; consider isometric loading for rehab phases.
- Knee constraint: reduce impact volume; emphasize controlled eccentric tempo; avoid jumping volume escalation in tendinopathy contexts.

### Pattern: RP-TRA-endurance-concurrent-trained (sim=0.83)

**Applies because:** Concurrent endurance and resistance training trigger conflicting intracellular signaling cascades (AMPK vs mTOR) that can attenuate hypertrophic adaptations from resistance training when scheduled too closely; this interference effect is dose-dependent and modifiable by session separation, intensity selection, and exercise specificity, allowing trained adults to develop both strength and endurance capacities concurrently with appropriate programming.
**Parameterization:** Endurance-trained adults adding resistance training (e.g., distance runners, cyclists, triathletes): 2 strength sessions per week, 30-45 min each, focused on compound movements (squat, deadlift, lunge, single-leg work) at 4-8 reps and 75-85% 1RM; cap weekly resistance volume at 8-12 hard sets per major lower-body muscle group during peak endurance training phases. Concurrent training schedule: separate endurance and strength sessions by at least 6 hours, ideally morning endurance / evening strength or alternate days; if same-day required, strength should precede endurance for maximal-strength outcomes or follow for endurance-priority outcomes. Athletes in offseason / build phase: temporarily increase strength volume to 15-18 weekly sets per muscle and reduce endurance volume by 30-50% to drive strength adaptations before returning to specificity. Performance-oriented hybrid trained adults (combining strength + conditioning for sport carryover): pair 2.5x strength + 2.5x conditioning weekly with one full rest day; use heart rate variability and session RPE to autoregulate weekly load.
**Safety bounds:** Cap weekly concurrent training hours at 10-12 without dedicated recovery protocols; require sleep monitoring at >= 7 h/night sustained or reduce overall training volume; halt strength volume escalation if endurance performance regresses by more than 5% over 3 weeks; do not add high-impact running or jumping volume in trainees with prior tendinopathy without progressive return-to-impact program.

**Backing evidence (top 3 by population match):**
- Resistance training significantly improves muscle strength, hypertrophy, power, and physical function in healthy adults, with specific adaptations enhanced by manipulating load, volume, and velocity. ([10.1249/MSS.0000000000003897])
- Aerobic and resistance training significantly improve quality of life, fatigue, body composition, and functional capacity in patients across various cancer types. ([10.1007/s00520-026-10363-0])
- Concurrent training significantly improves countermovement jump performance compared to resistance training alone in children and adolescents. ([10.1111/sms.14764])

### Pattern: RP-TRA-hypertrophy-frequency-volume-trained (sim=0.76)

**Applies because:** In resistance-trained adults, hypertrophy follows a graded dose-response to weekly volume (~0.023 effect-size increment per added weekly set per muscle), with training frequency of 2-3x/week per muscle producing greater hypertrophy than 1x/week at matched volume due to distributed mechanical tension and higher per-session quality enabled by inter-session recovery.
**For this client (F, 32y, recreational):** Recreational lifters (less than 1 yr): start at the lower end (6-10 weekly sets per muscle) and add 1-2 sets weekly until reaching 10-12 sets before plateauing volume.
<details><summary>All populations covered by this pattern</summary>

Trained adults (1+ year consistent resistance training): 10-20 weekly hard sets per muscle group distributed across 2-3 sessions per week, 6-15 reps at RIR 1-3, with primary compound lifts driving 50-70% of weekly set volume. Advanced trainees (3+ years, hypertrophy plateau): consider 16-22 weekly sets with frequency 2-3x/week per muscle and 25-30% of volume at 5-8 reps for stimulus diversity. Older trained adults (50+ y): same weekly volume framework but extend recovery to 48-72 h between same-muscle sessions; prioritize machine-supported variants for axial-loading-sensitive joints. Body recomposition during caloric deficit: cap weekly volume at 12-15 sets per muscle to preserve recovery quality; emphasize the higher-load end of the rep range (6-10 reps) to maintain strength under reduced calories. Hypertrophy-focused phase during caloric surplus: progress toward upper bound (15-20 sets) over 4-6 week mesocycles with weekly volume increase of 10-15% from baseline. Recreational lifters (less than 1 yr): start at the lower end (6-10 weekly sets per muscle) and add 1-2 sets weekly until reaching 10-12 sets before plateauing volume.

</details>
**Safety bounds:** Cap weekly sets per muscle group at 25 without experienced coach supervision; reduce volume by 20-30% during planned deload weeks every 4-8 weeks; halt volume progression and reassess if joint pain, sleep deterioration, or chronically elevated session RPE (>9 across multiple sessions) emerge; do not escalate volume across multiple muscles simultaneously when recovery markers are trending unfavorably.

**Backing evidence (top 3 by population match):**
- Resistance training significantly improves muscle strength, hypertrophy, power, and physical function in healthy adults, with specific adaptations enhanced by manipulating load, volume, and velocity. ([10.1249/MSS.0000000000003897])
- Increases in weekly training set volume are associated with increases in both muscle hypertrophy and strength, though both exhibit diminishing returns. ([10.1007/s40279-025-02344-w])

### Pattern: RP-TRA-maximal-strength-low-rep-trained (sim=0.75)

**Applies because:** Maximal strength adaptation is mediated by neural drive and motor unit recruitment, which are preferentially stimulated by high-load (>= 85% 1RM) low-rep contractions; resistance-trained adults have the connective tissue and motor control to safely tolerate near-maximal loads and require this intensity stimulus to drive further strength gains beyond the moderate-load hypertrophy zone.
**For this client (F, 32y, recreational):** Trained females: same percent-1RM prescriptions; absolute strength progression rate may be slower but relative gains comparable to males in the literature.
<details><summary>All populations covered by this pattern</summary>

Resistance-trained adults pursuing strength (1+ year consistent training): 1-5 reps at 85-100% 1RM, 3-6 sets per primary compound lift, 2-4 sessions per week, 3-5 min rest between heavy sets. Powerlifting-style athletes: squat / bench / deadlift centric, 1-3 reps at 90-100% on top sets, accessory work 5-10 reps at 70-85% 1RM. Strength + hypertrophy concurrent (powerbuilding-style): pair heavy compound 3-5 reps with hypertrophy accessory work 8-12 reps, total weekly hard sets 12-18 per major muscle. Older trained adults (50+ y): cap top-set intensity at 80-85% 1RM unless under direct supervision; extend warm-up sequence to 3-4 ramp-up sets; recovery 72 h between primary lift exposures. Trained females: same percent-1RM prescriptions; absolute strength progression rate may be slower but relative gains comparable to males in the literature. Strength athletes preparing for competition: peak with 1-3 weeks of higher intensity (90-100% 1RM) at reduced volume, then taper 4-7 days pre-meet.

</details>
**Safety bounds:** Require medical clearance before initiating 1-3 rep maximal loads in adults with hypertension, cardiac history, or prior musculoskeletal injury; mandatory spotter or safety pins for back squat / bench press above 85% 1RM; halt session and reassess if technique breakdown occurs on top sets; avoid concurrent maximal strength testing across multiple compound lifts in the same week.

**Backing evidence (top 3 by population match):**
- Resistance training significantly improves muscle strength, hypertrophy, power, and physical function in healthy adults, with specific adaptations enhanced by manipulating load, volume, and velocity. ([10.1249/MSS.0000000000003897])
- Increases in weekly training set volume are associated with increases in both muscle hypertrophy and strength, though both exhibit diminishing returns. ([10.1007/s40279-025-02344-w])

- **EA-TRA-1931** (sim 0.72, pop-match 1.00): Resistance training under hypoxic conditions (RTH) results in trivial benefits for muscle strength gains compared to normoxic conditions (RTN), with specific programming variables like non-full-body routines and higher weekly volumes potentially enhancing this effect. ([10.1080/02640414.2024.2425536])
- **EA-TRA-9632** (sim 0.70, pop-match 1.00): Linear and undulating periodization resistance training have comparable effects on enhancing athletic capacity, improving body composition, and regulating blood glucose and insulin resistance. ([10.3389/fpubh.2026.1707627])
- **EA-TRA-9824** (sim 0.69, pop-match 1.00): Endurance exercise training improves cardiorespiratory function and health-related quality of life related to physical function in patients with sickle cell disease. ([10.1016/j.bcmd.2026.102989])

## Conditioning

### Pattern: RP-CON-hiit-vo2max-broad-population (sim=0.68)

**Applies because:** HIIT drives superior mitochondrial biogenesis, stroke volume augmentation, and peripheral oxygen extraction versus lower-intensity modalities by repeatedly stressing the oxygen transport chain near its ceiling, as corroborated by consistent effect-size advantages (SMD/g 0.37–3.6 for VO2-related outcomes) across diverse meta-analyses spanning clinical, youth, and performance populations.
**Parameterization:** Healthy endurance athletes: standard normoxic HIIT; add hypoxic stimulus (live-high-train-low or hypoxic intervals) for an incremental VO2max gain of ~SMD 0.26 over normoxic HIIT alone. Racket-sport and team-sport athletes: HIIT or small-sided games (SSG) are interchangeable for VO2max; HIIT favored when sprint and power outcomes are co-primary. Youth athletes: apply age-appropriate volume scaling; effect sizes are large (g ≈ 0.97) so moderate session counts (2–3×/week) suffice. Post-stroke patients: begin at 50–60% HRR and progress to ≥80% HRR under supervised conditions; target VO2-VT improvements first (MD +2.20 mL/kg/min vs. MICT). HFpEF patients: combine HIIT with inspiratory muscle training (IMT) for additive VO2 peak benefit (IMT SMD 3.6, HIIT SMD 3.5 mL/kg·min); reduce session duration and increase rest intervals relative to healthy cohorts.
**Safety bounds:** Clinical populations require physician clearance before initiating HIIT; absolute contraindications include unstable angina, decompensated heart failure (NYHA IV), acute arrhythmia, or recent (≤3 months) cardiovascular event. Maximum session intensity should not exceed 90% HRmax without on-site medical supervision for cardiac patients. Hypoxic protocols are contraindicated in individuals with sickle-cell trait, severe anemia (Hb < 8 g/dL), or symptomatic pulmonary hypertension. Youth athletes: cap work intervals at ≤95% HRmax; mandatory warm-up ≥10 min.

**Backing evidence (top 3 by population match):**
- In patients with heart failure with preserved ejection fraction (HFpEF), inspiratory muscle training, high-intensity interval training, and combined aerobic and resistance exercise are the most effective interventions for improving aerobic capacity (VO2 peak). ([10.1097/CRD.0000000000000447])
- High-intensity interval training (HIIT) performed under hypoxic conditions results in greater improvements in VO2 max compared to normoxic conditions in distance runners. ([10.14814/phy2.70349])
- High-Intensity Interval Training (HIIT) improves VO2 max, running and repetitive sprint performance, jumping performance, and hitting speed in racket sports athletes. ([10.1371/journal.pone.0295362])

- **EA-CON-9235** (sim 0.58, pop-match 1.00): Greater age is associated with longer phosphocreatine (PCr) recovery times in upper leg muscles, and more acidic end-of-exercise pH correlates with longer PCr recovery times across muscle groups in healthy individuals. ([10.1002/nbm.70023])

## Supplements

### Pattern: RP-SUP-creatine-resistance-body-composition (sim=0.65)

**Applies because:** Creatine supplementation saturates intramuscular phosphocreatine stores, accelerating ATP resynthesis during repeated high-intensity bouts and enabling higher training volumes, thereby amplifying the anabolic stimulus of resistance training and producing consistent meta-analytic gains in fat-free mass (+0.82–1.39 kg) and strength across diverse populations.
**Parameterization:** Postmenopausal women: ≥5 g/day required to elicit lean mass gains (+0.37 kg) and lower-body strength (+7.5 kg leg-press 1RM); untrained individuals: expect larger absolute strength gains than trained athletes, who show greater absolute FFM gains (1.82 kg vs 1.23 kg); active females: performance responses are inconsistent and clients should set conservative expectations; combat sport and swimming athletes: use for sport-specific power and ergogenic outcomes; co-supplementation with β-alanine (divided 4–6.4 g/day) may further enhance repeated high-intensity bout performance without adding to maximal strength beyond creatine alone.
**Safety bounds:** Loading phase ceiling: 20 g/day for ≤7 days in 4 divided doses; maintenance ceiling: 5 g/day for healthy adults; expect a transient, clinically non-significant serum creatinine rise (~0.07 µmol/L) with no meaningful GFR change in healthy kidneys; clinical supervision and eGFR monitoring required if baseline eGFR < 60 mL/min/1.73 m²; do not use loading phase without medical clearance in individuals with hypertension or fluid-sensitive conditions.

**Backing evidence (top 3 by population match):**
- Pre-exercise caffeinated chewing gum supplementation is effective in improving endurance, repetitive sprinting, lower limb strength, and sport-specific performance, as well as lowering rating of perceived exertion (RPE) or fatigue index even with lower dosages of caffeine. ([10.3390/nu16213611])
- Creatine supplementation significantly improves muscle strength in the general population, with untrained individuals showing greater improvements than trained ones, and low-to-moderate doses combined with high-intensity exercise yielding better effects. ([10.7717/peerj.20380])
- Nutritional supplementation combined with exercise does not significantly improve muscle mass or bone health outcomes in women across reproductive stages, though it may improve upper-body strength. ([10.7150/ijms.130435])

## Recovery

### Pattern: RP-REC-exercise-sleep-quality (sim=0.65)

**Applies because:** Multiple systematic reviews and meta-analyses consistently report significant SMD improvements in subjective sleep quality (range ~0.47–1.56 across modalities), likely mediated by thermoregulatory normalization, hypothalamic-pituitary-adrenal axis down-regulation, and circadian rhythm entrainment via timed physical stimulation.
**Parameterization:** Adults ≥50 yr: combined aerobic + resistance training preferred (SMD −1.56); perinatal women: relaxation exercises 30–60 min/session, 1–2×/week, ≤4 weeks (SMD −2.54 to −3.13); cancer patients on chemotherapy: activity pacing plus progressive muscle relaxation first-line (ranked 98.6%), aerobic exercise or walking as alternatives; older adults with sleep disturbance or mild cognitive impairment: Tai Chi, Baduanjin-style Qigong (PSQI reduction −2.47), or rTMS+Tai Chi combination; perimenopausal women with insomnia: acupuncture or community-based traditional Chinese exercises as adjuncts; general adults: any aerobic, resistance, or mind-body modality scaled to baseline sleep impairment severity and intervention duration.
**Safety bounds:** Avoid vigorous exercise within 2–3 hours of intended sleep onset; obtain medical clearance before initiating resistance or aerobic programs in cancer patients, frail older adults, or individuals with cardiopulmonary comorbidities; rTMS must be administered by a licensed clinician and is contraindicated in individuals with implanted metallic devices, cochlear implants, or a personal or family history of seizures.

**Backing evidence (top 3 by population match):**
- Exercise improves subjective sleep quality in adults, with the magnitude of benefit influenced by baseline sleep quality and intervention duration. ([10.1016/j.smrv.2026.102239])
- Relaxation exercises performed for 30-60 minutes per session, 1-2 times per week, for a duration of 4 weeks or less, are the most effective regimen for improving sleep quality in perinatal women. ([10.1186/s12884-026-08673-6])
- Dance interventions produce a statistically significant overall improvement in sleep quality with a small-to-approaching-moderate effect. ([10.3389/fpubh.2026.1776902])

- **EA-REC-4676** (sim 0.66, pop-match 1.00): Physical post-exercise recovery techniques produce a small to moderate positive effect on vagally-mediated heart rate variability (RMSSD), with cold water immersion showing a moderate to large effect and techniques following resistance exercise demonstrating a larger positive effect than those following cardiovascular exercise. ([10.1111/cpf.12855])
- **EA-REC-1657** (sim 0.63, pop-match 1.00): Sleep and circadian interventions in athletes have a more substantial impact on positive affect compared to negative affect. ([10.1007/s40279-025-02387-z])
- **EA-REC-8562** (sim 0.56, pop-match 1.00): Cold-water immersion is significantly more effective than body cryotherapy for alleviating delayed onset muscle soreness within 24 hours post-exercise. ([10.1097/MD.0000000000046781])

## Behavioral

### Pattern: RP-BEH-multicomponent-exercise-adherence (sim=0.73)

**Applies because:** COM-B model and TDF analyses establish that exercise adherence is co-determined by capability, opportunity, and motivational factors simultaneously, meaning isolated single-domain strategies produce insufficient and non-durable behavior change, while multi-component approaches address the full causal architecture of adherence.
**Parameterization:** Scale social support modality by setting and age: older adults benefit from AI-assisted or robotic social prompting to extend training duration and engagement; T2D populations require integration of glycemic self-monitoring feedback (HbA1c, fasting glucose, waist circumference targets) as motivational anchors; chronic pain populations should pair adherence strategies with high-value physiotherapy protocols and technology-based delivery where in-person access is limited; autonomy support and emotional experience management should be weighted more heavily when extrinsic motivation is low.
**Safety bounds:** Exercise intensity must remain within individually medically cleared ranges; patients with uncontrolled HbA1c >10%, unstable cardiovascular disease, acute musculoskeletal injury, or severe unmanaged chronic pain flares require direct clinical supervision before program enrollment; AI/robotic-assisted interventions must include human clinical oversight protocols.

**Backing evidence (top 3 by population match):**
- Therapeutic patient education interventions in the Eastern Mediterranean Region produce significant improvements in diabetes self-management outcomes, specifically waist circumference, HbA1c, and fasting blood glucose. ([10.1186/s12889-025-24721-w])
- Flexible and personalized physical activity programs, multidimensional social support, participant education, enhancing self-efficacy and motivation, monitoring and feedback, and managing emotional experiences are key implementation strategies to improve adherence in individuals with type 2 diabetes. ([10.1007/s12529-025-10400-y])
- Technology-based interventions can improve exercise adherence in patients with chronic pain undergoing high-value physiotherapy. ([10.1093/pm/pnad134])

### Pattern: RP-BEH-multicomponent-bct-physical-activity (sim=0.66)

**Applies because:** BCTs target the psychological, social, and environmental determinants of behavior simultaneously; multicomponent designs reduce barriers across all three levels at once, producing additive or synergistic effects on motivation, habit formation, and sustained behavior change that single-component approaches cannot match.
**Parameterization:** Adolescents (12–18 y): emphasize Social reward, Behavioral contract, and Prompts/cues alongside Social support for greatest effect on physical activity adherence; digital delivery of social support is a viable substitute when in-person access is limited. University students (18–25 y): structured physical activity programs alone yield large mental-health gains; pairing with self-monitoring apps amplifies wellbeing and depression/anxiety reductions. Middle-aged adults (40–60 y): add goal-setting and meditation BCTs to the core stack to generate co-benefits in sleep quality and cognitive function. Environmental or policy components (e.g., activity-friendly spaces, cue redesign) can be layered into any age cohort to further reduce sedentary behavior.
**Safety bounds:** BCT-based behavioral programs carry no known pharmacological risk; however, prescribed exercise intensity should remain within age-appropriate aerobic guidelines (moderate–vigorous, ≤60 min/day for youth per WHO) and must not substitute for clinical care in participants with diagnosed psychiatric or sleep disorders requiring pharmacological or psychotherapeutic treatment.

**Backing evidence (top 3 by population match):**
- Behavioral change techniques such as Social support, Self-monitoring, Feedback, Social reward, Prompts/cues, and Behavioral contract are more frequently applied in effective physical activity interventions for adolescents. ([10.1186/s12889-025-25618-4])

- **EA-BEH-0513** (sim 0.53, pop-match 1.00): Exercise may be moderately more effective than a control intervention for reducing symptoms of depression. ([10.1002/14651858.CD004366.pub7])
- **EA-BEH-8816** (sim 0.50, pop-match 1.00): Interactive conversational agents can improve specific dietary behaviors, including fruit and vegetable intake and adherence to the Mediterranean diet, while also enhancing nutritional knowledge. ([10.2196/78220])

## Metadata

- top_k_per_domain: 30
- applicability_threshold: 0.5
- total queries issued: 22
- total contraindication hits: 0
