# Personalized Evidence Pack — amy_runner

- Compiled at: 2026-05-24T18:27:31.928668+00:00
- Library version: 0.1.0

---

## Client context

- **Profile:** F, 32y, 58.0 kg, 168 cm, training status: recreational
- **Goals:** endurance, performance
- **Constraints:**
  - *injury*: left knee mild patellar tendinopathy

## Nutrition

### Pattern: RP-NUT-protein-band (sim=0.73)

**Applies because:** Resistance-trained adults in an energy deficit.
**Parameterization:** 2.3-3.1 g/kg/day for resistance-trained adults in a hypocaloric period; pick upper end in steeper deficits or higher training volume.
**Safety bounds:** Flag renal history before recommending; daily intakes above ~3.1 g/kg/d are not supported by the cited evidence for additional FFM benefit.

**Backing evidence (top 3 by population match):**
- Protein intakes of 2.3-3.1 g/kg/day may be needed to maximize retention of lean body mass in resistance-trained subjects during hypocaloric periods. ([10.1186/s12970-017-0177-8])

### Pattern: RP-NUT-caloric-restriction-rt-protein-body-comp (sim=0.71)

**Applies because:** Caloric restriction alone induces negative nitrogen balance and upregulates muscle-protein catabolism, while resistance training activates mTOR-mediated myofibrillar synthesis and high protein intake saturates muscle fractional synthetic rate, together creating a net anabolic intramuscular environment that counteracts the catabolic energy deficit.
**Parameterization:** Sedentary or untrained healthy adults: 1.6–2.0 g/kg/day protein, 250–500 kcal/day deficit, moderate-intensity resistance or aerobic exercise. Resistance-trained athletes during aggressive cuts: 2.3–3.1 g/kg/day protein, up to 750 kcal/day deficit, 60–80% 1RM resistance training. Older adults (≥60 years): whey protein ≥15 g/day combined with resistance plus multicomponent exercise; deficit ≤500 kcal/day to limit FFM loss. Postmenopausal women: 250–750 kcal/day deficit, protein ≥0.8 g/kg/day minimum but 1.6+ g/kg preferred for LBM retention. Very-low-energy-diet contexts (≤800 kcal/day): exercise component is mandatory to mitigate disproportionate FFM loss. Adults with prediabetes or T2DM: intermittent fasting formats are interchangeable with continuous restriction provided protein and training targets are met; target ≥5% weight loss for normoglycemia reversion benefit.
**Safety bounds:** Caloric deficit must not exceed 1,000 kcal/day without clinical supervision and body composition monitoring. Protein above 3.5 g/kg/day is not recommended without prior renal function screening (eGFR, serum creatinine). Resistance training load must be individualized; do not prescribe 60–80% 1RM to individuals with uncontrolled hypertension, acute musculoskeletal injury, or recent cardiac event without medical clearance.

**Backing evidence (top 3 by population match):**
- Calorie restriction combined with exercise is the most effective strategy for reducing weight and fat percentage while maintaining lean body mass in healthy adults. ([10.3390/nu16173007])
- Combining exercise with very low energy diets (VLEDs) results in higher retention of fat free mass (FFM) compared to VLED alone during rapid weight loss. ([10.1016/j.orcp.2025.10.001])
- Interventions leveraging gamification, social interaction, and goal-setting have shown greater efficacy in improving body-nutrition profile. ([10.3390/nu17223542])

- **EA-NUT-4389** (sim 0.63, pop-match 1.00): Meta-analysis quantifies the accuracy of blood glucose prediction models across various horizons and the performance of meal and physical activity detection models. ([10.1088/2516-1091/ae39b9])
- **EA-NUT-7737** (sim 0.58, pop-match 1.00): Even mild iron deficiency may result in decreased endurance and increased irritability and withdrawal behavior among women. ([10.1016/j.physbeh.2018.09.012])

## Training

**For this client — constraint-aware notes:**
- Patellar tendinopathy: emphasize slow eccentric tempo (3-5s down) on lower-body work; avoid plyometric volume escalation until pain-free; consider isometric loading for rehab phases.
- Knee constraint: reduce impact volume; emphasize controlled eccentric tempo; avoid jumping volume escalation in tendinopathy contexts.

### Pattern: RP-TRA-endurance-concurrent-trained (sim=0.80)

**Applies because:** Concurrent endurance and resistance training trigger conflicting intracellular signaling cascades (AMPK vs mTOR) that can attenuate hypertrophic adaptations from resistance training when scheduled too closely; this interference effect is dose-dependent and modifiable by session separation, intensity selection, and exercise specificity, allowing trained adults to develop both strength and endurance capacities concurrently with appropriate programming.
**Parameterization:** Endurance-trained adults adding resistance training (e.g., distance runners, cyclists, triathletes): 2 strength sessions per week, 30-45 min each, focused on compound movements (squat, deadlift, lunge, single-leg work) at 4-8 reps and 75-85% 1RM; cap weekly resistance volume at 8-12 hard sets per major lower-body muscle group during peak endurance training phases. Concurrent training schedule: separate endurance and strength sessions by at least 6 hours, ideally morning endurance / evening strength or alternate days; if same-day required, strength should precede endurance for maximal-strength outcomes or follow for endurance-priority outcomes. Athletes in offseason / build phase: temporarily increase strength volume to 15-18 weekly sets per muscle and reduce endurance volume by 30-50% to drive strength adaptations before returning to specificity. Performance-oriented hybrid (e.g., bradley pattern, sebastian pattern): pair 2.5x strength + 2.5x conditioning weekly with one full rest day; use heart rate variability and session RPE to autoregulate weekly load.
**Safety bounds:** Cap weekly concurrent training hours at 10-12 without dedicated recovery protocols; require sleep monitoring at >= 7 h/night sustained or reduce overall training volume; halt strength volume escalation if endurance performance regresses by more than 5% over 3 weeks; do not add high-impact running or jumping volume in trainees with prior tendinopathy without progressive return-to-impact program.

**Backing evidence (top 3 by population match):**
- Aerobic and resistance training significantly improve quality of life, fatigue, body composition, and functional capacity in patients across various cancer types. ([10.1007/s00520-026-10363-0])
- Resistance training significantly improves muscle strength, hypertrophy, power, and physical function in healthy adults, with specific adaptations enhanced by manipulating load, volume, and velocity. ([10.1249/MSS.0000000000003897])
- Concurrent training significantly improves countermovement jump performance compared to resistance training alone in children and adolescents. ([10.1111/sms.14764])

### Pattern: RP-TRA-resistance-volume-hypertrophy-dose-response (sim=0.74)

**Applies because:** A graded dose-response links weekly resistance-training set volume to muscle hypertrophy (ES increment ≈0.023 per set; higher vs. lower volume grouping ES difference = 0.241), mediated by cumulative mechanical tension and metabolic stress that upregulate muscle protein synthesis proportionally to training stimulus up to the individual's recoverable threshold.
**Parameterization:** Older adults with sarcopenia: start low volume (≥2 sessions/week, ~49% 1RM, 3×/week for ≥19 weeks with 15 exercises, 6 sets, ~16 reps) and add balance/aerobic components for functional gains (TUG, chair-stand); metabolic disease (T2D, PCOS, CAD): use concurrent aerobic+resistance programming; untrained individuals: traditional progressive overload—advanced methods confer no added benefit; advanced athletes: higher volumes tolerated but with pronounced diminishing returns; patellofemoral pain: favor higher volume over lower volume; older adults targeting grip strength specifically: multicomponent or resistance-only at prescribed dose.
**Safety bounds:** Do not exceed 25–30 weekly sets per muscle group without experienced coach supervision; cap novice single-session volume at ≤6 sets per exercise; limit intensity to ≤80% 1RM in unsupervised older adults or those with cardiovascular comorbidities; require clinical clearance and supervised initiation for individuals with CAD, COPD, congenital heart disease, or sickle cell disease before commencing high-intensity or high-volume protocols.

**Backing evidence (top 3 by population match):**
- Aerobic and resistance training significantly improve quality of life, fatigue, body composition, and functional capacity in patients across various cancer types. ([10.1007/s00520-026-10363-0])
- Resistance training significantly improves muscle strength, hypertrophy, power, and physical function in healthy adults, with specific adaptations enhanced by manipulating load, volume, and velocity. ([10.1249/MSS.0000000000003897])
- Low-intensity endurance training (LIT) produces a large effect on relative VO2max and a moderate effect on the first lactate/ventilatory threshold (VT1) in healthy adults. ([10.1111/sms.70208])

### Pattern: RP-TRA-hypertrophy-frequency-volume-trained (sim=0.74)

**Applies because:** In resistance-trained adults, hypertrophy follows a graded dose-response to weekly volume (~0.023 effect-size increment per added weekly set per muscle), with training frequency of 2-3x/week per muscle producing greater hypertrophy than 1x/week at matched volume due to distributed mechanical tension and higher per-session quality enabled by inter-session recovery.
**For this client (F, 32y, recreational):** Recreational lifters (less than 1 yr): start at the lower end (6-10 weekly sets per muscle) and add 1-2 sets weekly until reaching 10-12 sets before plateauing volume.
<details><summary>All populations covered by this pattern</summary>

Trained adults (1+ year consistent resistance training): 10-20 weekly hard sets per muscle group distributed across 2-3 sessions per week, 6-15 reps at RIR 1-3, with primary compound lifts driving 50-70% of weekly set volume. Advanced trainees (3+ years, hypertrophy plateau): consider 16-22 weekly sets with frequency 2-3x/week per muscle and 25-30% of volume at 5-8 reps for stimulus diversity. Older trained adults (50+ y): same weekly volume framework but extend recovery to 48-72 h between same-muscle sessions; prioritize machine-supported variants for axial-loading-sensitive joints. Body recomposition during caloric deficit: cap weekly volume at 12-15 sets per muscle to preserve recovery quality; emphasize the higher-load end of the rep range (6-10 reps) to maintain strength under reduced calories. Hypertrophy-focused phase during caloric surplus: progress toward upper bound (15-20 sets) over 4-6 week mesocycles with weekly volume increase of 10-15% from baseline. Recreational lifters (less than 1 yr): start at the lower end (6-10 weekly sets per muscle) and add 1-2 sets weekly until reaching 10-12 sets before plateauing volume.

</details>
**Safety bounds:** Cap weekly sets per muscle group at 25 without experienced coach supervision; reduce volume by 20-30% during planned deload weeks every 4-8 weeks; halt volume progression and reassess if joint pain, sleep deterioration, or chronically elevated session RPE (>9 across multiple sessions) emerge; do not escalate volume across multiple muscles simultaneously when recovery markers are trending unfavorably.

**Backing evidence (top 3 by population match):**
- Resistance training significantly improves muscle strength, hypertrophy, power, and physical function in healthy adults, with specific adaptations enhanced by manipulating load, volume, and velocity. ([10.1249/MSS.0000000000003897])
- Increases in weekly training set volume are associated with increases in both muscle hypertrophy and strength, though both exhibit diminishing returns. ([10.1007/s40279-025-02344-w])

## Conditioning

### Pattern: RP-CON-hiit-vo2max-broad-population (sim=0.71)

**Applies because:** HIIT drives superior mitochondrial biogenesis, stroke volume augmentation, and peripheral oxygen extraction versus lower-intensity modalities by repeatedly stressing the oxygen transport chain near its ceiling, as corroborated by consistent effect-size advantages (SMD/g 0.37–3.6 for VO2-related outcomes) across diverse meta-analyses spanning clinical, youth, and performance populations.
**Parameterization:** Healthy endurance athletes: standard normoxic HIIT; add hypoxic stimulus (live-high-train-low or hypoxic intervals) for an incremental VO2max gain of ~SMD 0.26 over normoxic HIIT alone. Racket-sport and team-sport athletes: HIIT or small-sided games (SSG) are interchangeable for VO2max; HIIT favored when sprint and power outcomes are co-primary. Youth athletes: apply age-appropriate volume scaling; effect sizes are large (g ≈ 0.97) so moderate session counts (2–3×/week) suffice. Post-stroke patients: begin at 50–60% HRR and progress to ≥80% HRR under supervised conditions; target VO2-VT improvements first (MD +2.20 mL/kg/min vs. MICT). HFpEF patients: combine HIIT with inspiratory muscle training (IMT) for additive VO2 peak benefit (IMT SMD 3.6, HIIT SMD 3.5 mL/kg·min); reduce session duration and increase rest intervals relative to healthy cohorts.
**Safety bounds:** Clinical populations require physician clearance before initiating HIIT; absolute contraindications include unstable angina, decompensated heart failure (NYHA IV), acute arrhythmia, or recent (≤3 months) cardiovascular event. Maximum session intensity should not exceed 90% HRmax without on-site medical supervision for cardiac patients. Hypoxic protocols are contraindicated in individuals with sickle-cell trait, severe anemia (Hb < 8 g/dL), or symptomatic pulmonary hypertension. Youth athletes: cap work intervals at ≤95% HRmax; mandatory warm-up ≥10 min.

**Backing evidence (top 3 by population match):**
- In patients with heart failure with preserved ejection fraction (HFpEF), inspiratory muscle training, high-intensity interval training, and combined aerobic and resistance exercise are the most effective interventions for improving aerobic capacity (VO2 peak). ([10.1097/CRD.0000000000000447])
- High-intensity interval training (HIIT) performed under hypoxic conditions results in greater improvements in VO2 max compared to normoxic conditions in distance runners. ([10.14814/phy2.70349])
- Small-sided games (SSGs) and high-intensity interval training (HIIT) produce similar effects on improving endurance performance and VO2max in soccer players. ([10.1055/a-2171-3255])

- **EA-CON-9235** (sim 0.57, pop-match 1.00): Greater age is associated with longer phosphocreatine (PCr) recovery times in upper leg muscles, and more acidic end-of-exercise pH correlates with longer PCr recovery times across muscle groups in healthy individuals. ([10.1002/nbm.70023])

## Supplements

- **EA-SUP-9444** (sim 0.73, pop-match 1.00): Pre-exercise caffeinated chewing gum supplementation is effective in improving endurance, repetitive sprinting, lower limb strength, and sport-specific performance, as well as lowering rating of perceived exertion (RPE) or fatigue index even with lower dosages of caffeine. ([10.3390/nu16213611])
- **EA-SUP-8071** (sim 0.70, pop-match 1.00): Creatine supplementation significantly improves muscle strength in the general population, with untrained individuals showing greater improvements than trained ones, and low-to-moderate doses combined with high-intensity exercise yielding better effects. ([10.7717/peerj.20380])
- **EA-SUP-7073** (sim 0.66, pop-match 1.00): Caffeine supplementation enhances athletic performance in individuals with the CYP1A2 AA genotype, shows marginal improvement in AC individuals, and has null or detrimental effects in CC individuals. ([10.1016/j.nutres.2025.10.005])
- **EA-SUP-1368** (sim 0.66, pop-match 1.00): Creatine supplementation does not consistently improve exercise performance in active females, with most studies showing no improvement compared to placebo. ([10.3390/nu17020238])
- **EA-SUP-8400** (sim 0.65, pop-match 1.00): Creatine use during resistance training can safely increase total and lean body mass, strength, and performance in high-intensity, short-duration, repetitive tasks. ([10.1177/19417381231197389])

## Recovery

### Pattern: RP-REC-exercise-sleep-quality (sim=0.67)

**Applies because:** Multiple systematic reviews and meta-analyses consistently report significant SMD improvements in subjective sleep quality (range ~0.47–1.56 across modalities), likely mediated by thermoregulatory normalization, hypothalamic-pituitary-adrenal axis down-regulation, and circadian rhythm entrainment via timed physical stimulation.
**Parameterization:** Adults ≥50 yr: combined aerobic + resistance training preferred (SMD −1.56); perinatal women: relaxation exercises 30–60 min/session, 1–2×/week, ≤4 weeks (SMD −2.54 to −3.13); cancer patients on chemotherapy: activity pacing plus progressive muscle relaxation first-line (ranked 98.6%), aerobic exercise or walking as alternatives; older adults with sleep disturbance or mild cognitive impairment: Tai Chi, Baduanjin-style Qigong (PSQI reduction −2.47), or rTMS+Tai Chi combination; perimenopausal women with insomnia: acupuncture or community-based traditional Chinese exercises as adjuncts; general adults: any aerobic, resistance, or mind-body modality scaled to baseline sleep impairment severity and intervention duration.
**Safety bounds:** Avoid vigorous exercise within 2–3 hours of intended sleep onset; obtain medical clearance before initiating resistance or aerobic programs in cancer patients, frail older adults, or individuals with cardiopulmonary comorbidities; rTMS must be administered by a licensed clinician and is contraindicated in individuals with implanted metallic devices, cochlear implants, or a personal or family history of seizures.

**Backing evidence (top 3 by population match):**
- Relaxation exercises performed for 30-60 minutes per session, 1-2 times per week, for a duration of 4 weeks or less, are the most effective regimen for improving sleep quality in perinatal women. ([10.1186/s12884-026-08673-6])
- Dance interventions produce a statistically significant overall improvement in sleep quality with a small-to-approaching-moderate effect. ([10.3389/fpubh.2026.1776902])
- Exercise improves subjective sleep quality in adults, with the magnitude of benefit influenced by baseline sleep quality and intervention duration. ([10.1016/j.smrv.2026.102239])

- **EA-REC-4676** (sim 0.63, pop-match 1.00): Physical post-exercise recovery techniques produce a small to moderate positive effect on vagally-mediated heart rate variability (RMSSD), with cold water immersion showing a moderate to large effect and techniques following resistance exercise demonstrating a larger positive effect than those following cardiovascular exercise. ([10.1111/cpf.12855])
- **EA-REC-8562** (sim 0.59, pop-match 1.00): Cold-water immersion is significantly more effective than body cryotherapy for alleviating delayed onset muscle soreness within 24 hours post-exercise. ([10.1097/MD.0000000000046781])
- **EA-REC-1657** (sim 0.55, pop-match 1.00): Sleep and circadian interventions in athletes have a more substantial impact on positive affect compared to negative affect. ([10.1007/s40279-025-02387-z])
- **EA-REC-8163** (sim 0.61, pop-match 0.88): Cold water immersion (CWI) after exercise may have a positive acute effect on parasympathetic reactivation, as measured by heart rate variability (HRV). ([10.1002/pri.70033])

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

- **EA-BEH-8816** (sim 0.53, pop-match 1.00): Interactive conversational agents can improve specific dietary behaviors, including fruit and vegetable intake and adherence to the Mediterranean diet, while also enhancing nutritional knowledge. ([10.2196/78220])
- **EA-BEH-6471** (sim 0.47, pop-match 1.00): mHealth interventions significantly improve self-care ability and reduce rehospitalization rates among organ transplant recipients. ([10.2196/69795])

## Metadata

- top_k_per_domain: 30
- applicability_threshold: 0.5
- total queries issued: 22
- total contraindication hits: 0
