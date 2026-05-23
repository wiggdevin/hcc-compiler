# Personalized Evidence Pack — test_v2_sebastian

- Compiled at: 2026-05-23T08:51:44.824430+00:00
- Library version: 0.1.0

---

## Nutrition

### Pattern: RP-NUT-protein-band (sim=0.76)

**Applies because:** Resistance-trained adults in an energy deficit.
**Parameterization:** 2.3-3.1 g/kg/day for resistance-trained adults in a hypocaloric period; pick upper end in steeper deficits or higher training volume.
**Safety bounds:** Flag renal history before recommending; daily intakes above ~3.1 g/kg/d are not supported by the cited evidence for additional FFM benefit.

**Backing evidence (top 3 by population match):**

### Pattern: RP-NUT-caloric-restriction-rt-protein-body-comp (sim=0.74)

**Applies because:** Caloric restriction alone induces negative nitrogen balance and upregulates muscle-protein catabolism, while resistance training activates mTOR-mediated myofibrillar synthesis and high protein intake saturates muscle fractional synthetic rate, together creating a net anabolic intramuscular environment that counteracts the catabolic energy deficit.
**Parameterization:** Sedentary or untrained healthy adults: 1.6–2.0 g/kg/day protein, 250–500 kcal/day deficit, moderate-intensity resistance or aerobic exercise. Resistance-trained athletes during aggressive cuts: 2.3–3.1 g/kg/day protein, up to 750 kcal/day deficit, 60–80% 1RM resistance training. Older adults (≥60 years): whey protein ≥15 g/day combined with resistance plus multicomponent exercise; deficit ≤500 kcal/day to limit FFM loss. Postmenopausal women: 250–750 kcal/day deficit, protein ≥0.8 g/kg/day minimum but 1.6+ g/kg preferred for LBM retention. Very-low-energy-diet contexts (≤800 kcal/day): exercise component is mandatory to mitigate disproportionate FFM loss. Adults with prediabetes or T2DM: intermittent fasting formats are interchangeable with continuous restriction provided protein and training targets are met; target ≥5% weight loss for normoglycemia reversion benefit.
**Safety bounds:** Caloric deficit must not exceed 1,000 kcal/day without clinical supervision and body composition monitoring. Protein above 3.5 g/kg/day is not recommended without prior renal function screening (eGFR, serum creatinine). Resistance training load must be individualized; do not prescribe 60–80% 1RM to individuals with uncontrolled hypertension, acute musculoskeletal injury, or recent cardiac event without medical clearance.

**Backing evidence (top 3 by population match):**
- The mean nitrogen requirement for healthy adults is 104.2 mg N/kg/day, with no significant differences observed based on sex, age group, climate, or protein source. ([10.3390/nu17162615])
- Protein requirements estimated by the indicator amino acid oxidation (IAAO) method are approximately 30% higher than those estimated by the nitrogen balance (NB) method in both non-athletes and athletes. ([10.1016/j.tjnut.2025.08.036])
- Protein timing does not importantly modify exercise-induced changes in lean body mass. ([10.3390/nu17132070])

## Training

### Pattern: RP-TRA-resistance-volume-hypertrophy-dose-response (sim=0.65)

**Applies because:** A graded dose-response links weekly resistance-training set volume to muscle hypertrophy (ES increment ≈0.023 per set; higher vs. lower volume grouping ES difference = 0.241), mediated by cumulative mechanical tension and metabolic stress that upregulate muscle protein synthesis proportionally to training stimulus up to the individual's recoverable threshold.
**Parameterization:** Older adults with sarcopenia: start low volume (≥2 sessions/week, ~49% 1RM, 3×/week for ≥19 weeks with 15 exercises, 6 sets, ~16 reps) and add balance/aerobic components for functional gains (TUG, chair-stand); metabolic disease (T2D, PCOS, CAD): use concurrent aerobic+resistance programming; untrained individuals: traditional progressive overload—advanced methods confer no added benefit; advanced athletes: higher volumes tolerated but with pronounced diminishing returns; patellofemoral pain: favor higher volume over lower volume; older adults targeting grip strength specifically: multicomponent or resistance-only at prescribed dose.
**Safety bounds:** Do not exceed 25–30 weekly sets per muscle group without experienced coach supervision; cap novice single-session volume at ≤6 sets per exercise; limit intensity to ≤80% 1RM in unsupervised older adults or those with cardiovascular comorbidities; require clinical clearance and supervised initiation for individuals with CAD, COPD, congenital heart disease, or sickle cell disease before commencing high-intensity or high-volume protocols.

**Backing evidence (top 3 by population match):**
- Advanced resistance training methods do not provide a clear benefit over traditional resistance training for inducing adaptations in untrained to moderately trained individuals. ([10.1007/s40279-026-02428-1])
- Supersets provide a time-efficient alternative to traditional resistance training, reducing session duration without compromising training volume, muscle activation, perceived recovery, or chronic adaptations in maximal strength, strength endurance, and muscle hypertrophy. ([10.1007/s40279-025-02176-8])
- Concurrent training significantly improves countermovement jump performance compared to resistance training alone in children and adolescents. ([10.1111/sms.14764])

## Conditioning

### Pattern: RP-CON-hiit-vo2max-broad-population (sim=0.64)

**Applies because:** HIIT drives superior mitochondrial biogenesis, stroke volume augmentation, and peripheral oxygen extraction versus lower-intensity modalities by repeatedly stressing the oxygen transport chain near its ceiling, as corroborated by consistent effect-size advantages (SMD/g 0.37–3.6 for VO2-related outcomes) across diverse meta-analyses spanning clinical, youth, and performance populations.
**Parameterization:** Healthy endurance athletes: standard normoxic HIIT; add hypoxic stimulus (live-high-train-low or hypoxic intervals) for an incremental VO2max gain of ~SMD 0.26 over normoxic HIIT alone. Racket-sport and team-sport athletes: HIIT or small-sided games (SSG) are interchangeable for VO2max; HIIT favored when sprint and power outcomes are co-primary. Youth athletes: apply age-appropriate volume scaling; effect sizes are large (g ≈ 0.97) so moderate session counts (2–3×/week) suffice. Post-stroke patients: begin at 50–60% HRR and progress to ≥80% HRR under supervised conditions; target VO2-VT improvements first (MD +2.20 mL/kg/min vs. MICT). HFpEF patients: combine HIIT with inspiratory muscle training (IMT) for additive VO2 peak benefit (IMT SMD 3.6, HIIT SMD 3.5 mL/kg·min); reduce session duration and increase rest intervals relative to healthy cohorts.
**Safety bounds:** Clinical populations require physician clearance before initiating HIIT; absolute contraindications include unstable angina, decompensated heart failure (NYHA IV), acute arrhythmia, or recent (≤3 months) cardiovascular event. Maximum session intensity should not exceed 90% HRmax without on-site medical supervision for cardiac patients. Hypoxic protocols are contraindicated in individuals with sickle-cell trait, severe anemia (Hb < 8 g/dL), or symptomatic pulmonary hypertension. Youth athletes: cap work intervals at ≤95% HRmax; mandatory warm-up ≥10 min.

**Backing evidence (top 3 by population match):**
- High-Intensity Interval Training (HIIT) improves VO2 max, running and repetitive sprint performance, jumping performance, and hitting speed in racket sports athletes. ([10.1371/journal.pone.0295362])
- In patients with heart failure with preserved ejection fraction (HFpEF), inspiratory muscle training, high-intensity interval training, and combined aerobic and resistance exercise are the most effective interventions for improving aerobic capacity (VO2 peak). ([10.1097/CRD.0000000000000447])
- Intermittent hypoxia (IH) protocols, including live high-train low (LHTL), repeated sprint training in hypoxia (RSH), and hypoxic interval training, effectively improve aerobic capacity, anaerobic performance, and muscular strength in both trained and untrained individuals. ([10.1186/s40798-025-00933-7])

## Supplements

### Pattern: RP-SUP-creatine-resistance-body-composition (sim=0.62)

**Applies because:** Creatine supplementation saturates intramuscular phosphocreatine stores, accelerating ATP resynthesis during repeated high-intensity bouts and enabling higher training volumes, thereby amplifying the anabolic stimulus of resistance training and producing consistent meta-analytic gains in fat-free mass (+0.82–1.39 kg) and strength across diverse populations.
**Parameterization:** Postmenopausal women: ≥5 g/day required to elicit lean mass gains (+0.37 kg) and lower-body strength (+7.5 kg leg-press 1RM); untrained individuals: expect larger absolute strength gains than trained athletes, who show greater absolute FFM gains (1.82 kg vs 1.23 kg); active females: performance responses are inconsistent and clients should set conservative expectations; combat sport and swimming athletes: use for sport-specific power and ergogenic outcomes; co-supplementation with β-alanine (divided 4–6.4 g/day) may further enhance repeated high-intensity bout performance without adding to maximal strength beyond creatine alone.
**Safety bounds:** Loading phase ceiling: 20 g/day for ≤7 days in 4 divided doses; maintenance ceiling: 5 g/day for healthy adults; expect a transient, clinically non-significant serum creatinine rise (~0.07 µmol/L) with no meaningful GFR change in healthy kidneys; clinical supervision and eGFR monitoring required if baseline eGFR < 60 mL/min/1.73 m²; do not use loading phase without medical clearance in individuals with hypertension or fluid-sensitive conditions.

**Backing evidence (top 3 by population match):**
- Creatine supplementation combined with resistance training increases lean body mass and reduces body fat percentage and mass compared to resistance training alone. ([10.1519/JSC.0000000000004862])
- Creatine supplementation significantly improves muscle strength in the general population, with untrained individuals showing greater improvements than trained ones, and low-to-moderate doses combined with high-intensity exercise yielding better effects. ([10.7717/peerj.20380])
- Creatine supplementation significantly increases body mass and fat-free mass while reducing body fat percentage, with effects enhanced when combined with resistance training. ([10.1080/15502783.2024.2380058])

## Recovery

### Pattern: RP-REC-exercise-sleep-quality (sim=0.60)

**Applies because:** Multiple systematic reviews and meta-analyses consistently report significant SMD improvements in subjective sleep quality (range ~0.47–1.56 across modalities), likely mediated by thermoregulatory normalization, hypothalamic-pituitary-adrenal axis down-regulation, and circadian rhythm entrainment via timed physical stimulation.
**Parameterization:** Adults ≥50 yr: combined aerobic + resistance training preferred (SMD −1.56); perinatal women: relaxation exercises 30–60 min/session, 1–2×/week, ≤4 weeks (SMD −2.54 to −3.13); cancer patients on chemotherapy: activity pacing plus progressive muscle relaxation first-line (ranked 98.6%), aerobic exercise or walking as alternatives; older adults with sleep disturbance or mild cognitive impairment: Tai Chi, Baduanjin-style Qigong (PSQI reduction −2.47), or rTMS+Tai Chi combination; perimenopausal women with insomnia: acupuncture or community-based traditional Chinese exercises as adjuncts; general adults: any aerobic, resistance, or mind-body modality scaled to baseline sleep impairment severity and intervention duration.
**Safety bounds:** Avoid vigorous exercise within 2–3 hours of intended sleep onset; obtain medical clearance before initiating resistance or aerobic programs in cancer patients, frail older adults, or individuals with cardiopulmonary comorbidities; rTMS must be administered by a licensed clinician and is contraindicated in individuals with implanted metallic devices, cochlear implants, or a personal or family history of seizures.

**Backing evidence (top 3 by population match):**
- Progressive muscle relaxation exercises are the preferred recommendation for sleep intervention in patients with cancer, with aerobic exercise and walking serving as alternative options. ([10.1002/pon.70466])
- Routine acupuncture combined with auricular acupuncture may be an effective intervention for treating insomnia in perimenopausal women. ([10.3389/fneur.2025.1726927])
- Dance interventions produce a statistically significant overall improvement in sleep quality with a small-to-approaching-moderate effect. ([10.3389/fpubh.2026.1776902])

- **EA-REC-4676** (sim 0.64, pop-match 1.00): Physical post-exercise recovery techniques produce a small to moderate positive effect on vagally-mediated heart rate variability (RMSSD), with cold water immersion showing a moderate to large effect and techniques following resistance exercise demonstrating a larger positive effect than those following cardiovascular exercise. ([10.1111/cpf.12855])
- **EA-REC-8163** (sim 0.60, pop-match 1.00): Cold water immersion (CWI) after exercise may have a positive acute effect on parasympathetic reactivation, as measured by heart rate variability (HRV). ([10.1002/pri.70033])
- **EA-REC-8071** (sim 0.59, pop-match 1.00): In offshore sailing, optimal sleep management strategies vary by crew size and race duration: for short regattas, 'banking sleep' beforehand is beneficial, while for long races, 4.5-5.5 h of daily sleep, in 30-min to 1-h episodes, is optimal. ([10.1007/s40279-025-02389-x])
- **EA-REC-7591** (sim 0.53, pop-match 1.00): Rehabilitation exercise adherence in patients following Total Hip Arthroplasty (THA) and Total Knee Arthroplasty (TKA) is influenced by facilitators such as self-motivation, effective strategies, and support networks, and barriers such as physical limitations, fear of movement, and lack of knowledge. ([10.1186/s12891-026-09789-8])

## Behavioral

### Pattern: RP-BEH-multicomponent-exercise-adherence (sim=0.70)

**Applies because:** COM-B model and TDF analyses establish that exercise adherence is co-determined by capability, opportunity, and motivational factors simultaneously, meaning isolated single-domain strategies produce insufficient and non-durable behavior change, while multi-component approaches address the full causal architecture of adherence.
**Parameterization:** Scale social support modality by setting and age: older adults benefit from AI-assisted or robotic social prompting to extend training duration and engagement; T2D populations require integration of glycemic self-monitoring feedback (HbA1c, fasting glucose, waist circumference targets) as motivational anchors; chronic pain populations should pair adherence strategies with high-value physiotherapy protocols and technology-based delivery where in-person access is limited; autonomy support and emotional experience management should be weighted more heavily when extrinsic motivation is low.
**Safety bounds:** Exercise intensity must remain within individually medically cleared ranges; patients with uncontrolled HbA1c >10%, unstable cardiovascular disease, acute musculoskeletal injury, or severe unmanaged chronic pain flares require direct clinical supervision before program enrollment; AI/robotic-assisted interventions must include human clinical oversight protocols.

**Backing evidence (top 3 by population match):**
- Flexible and personalized physical activity programs, multidimensional social support, participant education, enhancing self-efficacy and motivation, monitoring and feedback, and managing emotional experiences are key implementation strategies to improve adherence in individuals with type 2 diabetes. ([10.1007/s12529-025-10400-y])
- Technology-based interventions can improve exercise adherence in patients with chronic pain undergoing high-value physiotherapy. ([10.1093/pm/pnad134])
- Barriers and facilitators to exercise adherence in community-dwelling older adults can be categorized using the COM-B model and TDF, and effective implementation strategies include tailored exercise programs, appropriate environments, multidimensional social support, monitoring and feedback, managing emotional experiences, participant education, enhancing self-efficacy, and exerting participant autonomy. ([10.1016/j.ijnurstu.2024.104808])

### Pattern: RP-BEH-multicomponent-bct-physical-activity (sim=0.68)

**Applies because:** BCTs target the psychological, social, and environmental determinants of behavior simultaneously; multicomponent designs reduce barriers across all three levels at once, producing additive or synergistic effects on motivation, habit formation, and sustained behavior change that single-component approaches cannot match.
**Parameterization:** Adolescents (12–18 y): emphasize Social reward, Behavioral contract, and Prompts/cues alongside Social support for greatest effect on physical activity adherence; digital delivery of social support is a viable substitute when in-person access is limited. University students (18–25 y): structured physical activity programs alone yield large mental-health gains; pairing with self-monitoring apps amplifies wellbeing and depression/anxiety reductions. Middle-aged adults (40–60 y): add goal-setting and meditation BCTs to the core stack to generate co-benefits in sleep quality and cognitive function. Environmental or policy components (e.g., activity-friendly spaces, cue redesign) can be layered into any age cohort to further reduce sedentary behavior.
**Safety bounds:** BCT-based behavioral programs carry no known pharmacological risk; however, prescribed exercise intensity should remain within age-appropriate aerobic guidelines (moderate–vigorous, ≤60 min/day for youth per WHO) and must not substitute for clinical care in participants with diagnosed psychiatric or sleep disorders requiring pharmacological or psychotherapeutic treatment.

**Backing evidence (top 3 by population match):**
- Behavioral sleep interventions utilizing behavior change techniques (BCTs) such as goal setting and meditation are linked to positive outcomes for both sleep quality and cognitive function in middle-aged adults. ([10.1038/s41598-025-24009-4])
- Multicomponent interventions integrating educational, technological, exercise, or environmental strategies generally demonstrated improvements in physical activity or reductions in sedentary behavior in Thailand. ([10.1123/jpah.2025-0444])
- Behavioral change techniques such as Social support, Self-monitoring, Feedback, Social reward, Prompts/cues, and Behavioral contract are more frequently applied in effective physical activity interventions for adolescents. ([10.1186/s12889-025-25618-4])

- **EA-BEH-6255** (sim 0.64, pop-match 1.00): Goal-setting guidelines for return-to-work rehabilitation in Australia are inconsistent and primarily based on SMART goal principles. ([10.1071/PY25160])

## Metadata

- top_k_per_domain: 15
- applicability_threshold: 0.5
- total queries issued: 18
- total contraindication hits: 0
