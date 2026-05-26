# Personalized Evidence Pack — test_v2_jackson_white

- Compiled at: 2026-05-26T13:35:11.130878+00:00
- Library version: 0.1.0

---

## Client context

- **Profile:** M, 30y, 83.9 kg, 185 cm, training status: trained
- **Goals:** hypertrophy, recomposition
- **Constraints:**
  - *injury*: Low-back sensitivity from boxing; recurring tweaks under heavy axial load + rotation when fatigued. Hypertonic QL/erectors, glute inhibition, hip-flexor tightness pattern.
  - *schedule*: 8-week film role; Wks 3–8 on set: 4 AM call times, disrupted sleep, catering-truck meals
  - *dietary*: Minimal fish intake — omega-3 supplemented instead

## Nutrition

### Pattern: RP-NUT-protein-band (sim=0.80)

**Applies because:** Resistance-trained adults in an energy deficit.
**Parameterization:** 2.3-3.1 g/kg/day for resistance-trained adults in a hypocaloric period; pick upper end in steeper deficits or higher training volume.
**Safety bounds:** Flag renal history before recommending; daily intakes above ~3.1 g/kg/d are not supported by the cited evidence for additional FFM benefit.

**Backing evidence (top 3 by population match):**
- Protein intakes of 2.3-3.1 g/kg/day may be needed to maximize retention of lean body mass in resistance-trained subjects during hypocaloric periods. ([10.1186/s12970-017-0177-8])

### Pattern: RP-NUT-hypertrophy-surplus-lean-mass (sim=0.79)

**Applies because:** Positive energy balance provides substrate availability that allows mTOR-mediated MPS to exceed muscle protein breakdown without substrate competition; elevated protein intake across the day saturates fractional synthetic rate repeatedly; resistance training creates the mechanical stimulus that directs surplus calories toward lean tissue rather than adipose deposition.
**For this client (M, 30y, trained):** Resistance-trained adults (1-3 years, 18-49 y): 10-15% caloric surplus; protein 1.8-2.2 g/kg/day; carbohydrate intake does not significantly enhance hypertrophy beyond adequate protein under isonitrogenous conditions; prioritize carbohydrate for training performance rather than anabolic effect.
<details><summary>All populations covered by this pattern</summary>

Untrained adults (0-12 months resistance training): 10-15% caloric surplus above TDEE; protein 1.6-1.8 g/kg/day; untrained responders gain lean mass rapidly even at lower surpluses due to high neuromuscular adaptation rate; do not exceed 20% surplus as excess fat gain is disproportionate to lean mass benefit at this stage. Resistance-trained adults (1-3 years, 18-49 y): 10-15% caloric surplus; protein 1.8-2.2 g/kg/day; carbohydrate intake does not significantly enhance hypertrophy beyond adequate protein under isonitrogenous conditions; prioritize carbohydrate for training performance rather than anabolic effect. Advanced resistance-trained adults (3+ years, hypertrophy plateau): 15-20% surplus; protein 2.0-2.2 g/kg/day; lean mass gain rate slows to 0.5-1 kg/month max; minimize surplus duration to 6-12 week mesocycles to control fat accretion; monitor body composition with DEXA or skinfold every 4-6 weeks. Older adults (>=60 y): protein requirements are higher per unit of lean mass stimulus; 1.6-2.0 g/kg/day minimum; surplus 10-15% above maintenance; combine with whey protein and resistance training for optimal anabolic biomarker response including IGF-1 upregulation and myostatin suppression. Trained females (18-49 y): surplus 10-15% above TDEE; protein 1.6-2.0 g/kg/day; lean mass gain rates are lower than males but relative rate of improvement is comparable; carbohydrate periodization around training sessions improves performance without requiring higher absolute surplus.

</details>
**Safety bounds:** Caloric surplus should not exceed 500 kcal/day without monthly body composition monitoring; individuals with metabolic syndrome, T2DM, or significant cardiovascular risk should not pursue aggressive bulking phases without clinical guidance; protein above 3.1 g/kg/day offers no additional lean mass benefit and requires renal screening.

**Backing evidence (top 3 by population match):**
- Protein intakes of 2.3-3.1 g/kg/day may be needed to maximize retention of lean body mass in resistance-trained subjects during hypocaloric periods. ([10.1186/s12970-017-0177-8])

### Pattern: RP-NUT-caloric-restriction-rt-protein-body-comp (sim=0.77)

**Applies because:** Caloric restriction alone induces negative nitrogen balance and upregulates muscle-protein catabolism, while resistance training activates mTOR-mediated myofibrillar synthesis and high protein intake saturates muscle fractional synthetic rate, together creating a net anabolic intramuscular environment that counteracts the catabolic energy deficit.
**For this client (M, 30y, trained):** Resistance-trained athletes during aggressive cuts: 2.3–3.1 g/kg/day protein, up to 750 kcal/day deficit, 60–80% 1RM resistance training.
<details><summary>All populations covered by this pattern</summary>

Sedentary or untrained healthy adults: 1.6–2.0 g/kg/day protein, 250–500 kcal/day deficit, moderate-intensity resistance or aerobic exercise. Resistance-trained athletes during aggressive cuts: 2.3–3.1 g/kg/day protein, up to 750 kcal/day deficit, 60–80% 1RM resistance training. Older adults (≥60 years): whey protein ≥15 g/day combined with resistance plus multicomponent exercise; deficit ≤500 kcal/day to limit FFM loss. Postmenopausal women: 250–750 kcal/day deficit, protein ≥0.8 g/kg/day minimum but 1.6+ g/kg preferred for LBM retention. Very-low-energy-diet contexts (≤800 kcal/day): exercise component is mandatory to mitigate disproportionate FFM loss. Adults with prediabetes or T2DM: intermittent fasting formats are interchangeable with continuous restriction provided protein and training targets are met; target ≥5% weight loss for normoglycemia reversion benefit.

</details>
**Safety bounds:** Caloric deficit must not exceed 1,000 kcal/day without clinical supervision and body composition monitoring. Protein above 3.5 g/kg/day is not recommended without prior renal function screening (eGFR, serum creatinine). Resistance training load must be individualized; do not prescribe 60–80% 1RM to individuals with uncontrolled hypertension, acute musculoskeletal injury, or recent cardiac event without medical clearance.

**Backing evidence (top 3 by population match):**
- Protein intakes of 2.3-3.1 g/kg/day may be needed to maximize retention of lean body mass in resistance-trained subjects during hypocaloric periods. ([10.1186/s12970-017-0177-8])
- Calorie restriction combined with exercise is the most effective strategy for reducing weight and fat percentage while maintaining lean body mass in healthy adults. ([10.3390/nu16173007])
- Intermittent fasting and calorie restriction combined with exercise can be effectively integrated without negatively impacting most measures of physical performance, while significantly enhancing weight loss and adiposity-related outcomes. ([10.3390/nu17121992])

- **EA-NUT-4389** (sim 0.66, pop-match 1.00): Meta-analysis quantifies the accuracy of blood glucose prediction models across various horizons and the performance of meal and physical activity detection models. ([10.1088/2516-1091/ae39b9])
- **EA-NUT-1139** (sim 0.73, pop-match 0.80): Time-restricted feeding reduces body mass and improves nutrient metabolism in both normal-weight and overweight individuals without altering fat-free mass or impairing aerobic fitness and muscular performance among physically active adults. ([10.1080/07315724.2021.1958719])

## Training

**For this client — constraint-aware notes:**
- Low-back sensitivity: substitute trap-bar / front squat / SSB for conventional back squat; chest-supported rows; anti-extension + anti-rotation core 2x/wk. Avoid heavy axial loading when fatigued.
- Low-back constraint: substitute trap-bar / front squat / SSB for conventional back squat; chest-supported rows; anti-extension + anti-rotation core 2x/wk.

### Pattern: RP-TRA-recomposition-progressive-overload-trained (sim=0.86)

**Applies because:** Body recomposition requires simultaneous mechanical-tension stimulus to preserve / build muscle protein synthesis AND caloric deficit to drive fat oxidation; resistance-trained adults retain lean mass under deficit primarily by maintaining training load and protein intake, whereas reducing volume disproportionately accelerates lean mass loss while only modestly increasing rate of fat loss.
**For this client (M, 30y, trained):** Resistance-trained adults pursuing body recomposition under moderate caloric deficit (250-500 kcal/day): maintain 10-15 weekly hard sets per major muscle group at 6-12 rep range; keep heavy compound exposures at 4-8 reps weekly to preserve strength; protein intake 2.0-2.4 g/kg/day.
<details><summary>All populations covered by this pattern</summary>

Resistance-trained adults pursuing body recomposition under moderate caloric deficit (250-500 kcal/day): maintain 10-15 weekly hard sets per major muscle group at 6-12 rep range; keep heavy compound exposures at 4-8 reps weekly to preserve strength; protein intake 2.0-2.4 g/kg/day. Trained adults in aggressive deficit (500-750 kcal/day): reduce weekly accessory volume by 20-30% but preserve heavy compound exposures and rep ranges; sleep and stress management become limiting factors. Concurrent body recomposition + conditioning (e.g., hybrid weekly schedule): separate resistance sessions from high-intensity conditioning by at least 6 h or alternate days; cap conditioning at 2-3 sessions weekly to limit interference effect on strength retention. Older trained adults (50+ y): emphasize the upper end of the rep range (8-12 reps) and 2-3 sessions per week per muscle to support recovery; consider 10-15% lower deficit than younger adults; resistance volume retention is the highest predictor of lean mass preservation. Trained females in recomposition: cycle-aware micro-loading is reasonable but recomposition timeline should plan for 4-8% body composition shift over 12-20 weeks at sustainable deficit rates.

</details>
**Safety bounds:** Cap deficit at 750 kcal/day without clinical supervision; halt aggressive volume reduction if strength regression exceeds 10% on primary lifts within 4 weeks; require body-composition tracking (DXA, InBody, or consistent skinfold protocol) every 4-6 weeks to verify lean mass retention; do not initiate recomposition in adults with active eating disorder history without clinical co-management.

**Backing evidence (top 3 by population match):**
- Resistance training significantly improves muscle strength, hypertrophy, power, and physical function in healthy adults, with specific adaptations enhanced by manipulating load, volume, and velocity. ([10.1249/MSS.0000000000003897])
- Higher weekly resistance-training volume produces greater muscle hypertrophy in a graded dose-response, with each additional weekly set associated with ~0.37% greater gain. ([10.1080/02640414.2016.1210197])
- Increases in weekly training set volume are associated with increases in both muscle hypertrophy and strength, though both exhibit diminishing returns. ([10.1007/s40279-025-02344-w])

### Pattern: RP-TRA-hypertrophy-frequency-volume-trained (sim=0.79)

**Applies because:** In resistance-trained adults, hypertrophy follows a graded dose-response to weekly volume (~0.023 effect-size increment per added weekly set per muscle), with training frequency of 2-3x/week per muscle producing greater hypertrophy than 1x/week at matched volume due to distributed mechanical tension and higher per-session quality enabled by inter-session recovery.
**For this client (M, 30y, trained):** Trained adults (1+ year consistent resistance training): 10-20 weekly hard sets per muscle group distributed across 2-3 sessions per week, 6-15 reps at RIR 1-3, with primary compound lifts driving 50-70% of weekly set volume.
<details><summary>All populations covered by this pattern</summary>

Trained adults (1+ year consistent resistance training): 10-20 weekly hard sets per muscle group distributed across 2-3 sessions per week, 6-15 reps at RIR 1-3, with primary compound lifts driving 50-70% of weekly set volume. Advanced trainees (3+ years, hypertrophy plateau): consider 16-22 weekly sets with frequency 2-3x/week per muscle and 25-30% of volume at 5-8 reps for stimulus diversity. Older trained adults (50+ y): same weekly volume framework but extend recovery to 48-72 h between same-muscle sessions; prioritize machine-supported variants for axial-loading-sensitive joints. Body recomposition during caloric deficit: cap weekly volume at 12-15 sets per muscle to preserve recovery quality; emphasize the higher-load end of the rep range (6-10 reps) to maintain strength under reduced calories. Hypertrophy-focused phase during caloric surplus: progress toward upper bound (15-20 sets) over 4-6 week mesocycles with weekly volume increase of 10-15% from baseline. Recreational lifters (less than 1 yr): start at the lower end (6-10 weekly sets per muscle) and add 1-2 sets weekly until reaching 10-12 sets before plateauing volume.

</details>
**Safety bounds:** Cap weekly sets per muscle group at 25 without experienced coach supervision; reduce volume by 20-30% during planned deload weeks every 4-8 weeks; halt volume progression and reassess if joint pain, sleep deterioration, or chronically elevated session RPE (>9 across multiple sessions) emerge; do not escalate volume across multiple muscles simultaneously when recovery markers are trending unfavorably.

**Backing evidence (top 3 by population match):**
- Resistance training significantly improves muscle strength, hypertrophy, power, and physical function in healthy adults, with specific adaptations enhanced by manipulating load, volume, and velocity. ([10.1249/MSS.0000000000003897])
- Higher weekly resistance-training volume produces greater muscle hypertrophy in a graded dose-response, with each additional weekly set associated with ~0.37% greater gain. ([10.1080/02640414.2016.1210197])
- Increases in weekly training set volume are associated with increases in both muscle hypertrophy and strength, though both exhibit diminishing returns. ([10.1007/s40279-025-02344-w])

### Pattern: RP-TRA-weight-loss-resistance-training-adults (sim=0.78)

**Applies because:** Caloric deficit alone induces negative nitrogen balance and accelerates lean mass loss especially in untrained or low-protein conditions; resistance training combined with adequate protein provides the mechanical stimulus to maintain muscle protein synthesis and defend lean body mass, preserving resting metabolic rate during weight loss and improving body composition outcomes vs caloric restriction alone.
**For this client (M, 30y, trained):** Trained adults during caloric deficit (250-500 kcal/day) pursuing weight loss: maintain 10-15 weekly hard sets per major muscle group at 6-12 reps, with at least one heavy session per week per muscle at 4-6 reps; 2-3 full-body or upper/lower splits per week minimum.
<details><summary>All populations covered by this pattern</summary>

Trained adults during caloric deficit (250-500 kcal/day) pursuing weight loss: maintain 10-15 weekly hard sets per major muscle group at 6-12 reps, with at least one heavy session per week per muscle at 4-6 reps; 2-3 full-body or upper/lower splits per week minimum. Trained adults in aggressive deficit (500-750 kcal/day): preserve heavy load exposures (4-6 reps), reduce accessory volume by 20-25%, monitor for strength regression. Recreational lifters pursuing weight loss: prioritize 2-3 full-body resistance sessions per week with compound focus (squat, hinge, push, pull, carry); progressive overload by adding load before adding volume. Older adults pursuing weight loss (50+ y): mandatory 2-3 resistance sessions weekly to defend muscle mass and metabolic rate; cap aerobic volume at 150-250 min/week of moderate intensity; protein 2.0-2.4 g/kg/day. Post-bariatric or significant weight-loss maintenance phase: emphasize resistance training over additional cardiovascular volume; volume-driven protein turnover is the metabolic protector at the new body weight.

</details>
**Safety bounds:** Require clinical clearance for resistance training in adults with uncontrolled hypertension, recent cardiac event (<6 months), or CAD without prior cardiac rehab clearance; cap aerobic + resistance combined weekly minutes at 5-6 hours total without supervised programming; halt program adjustment if rapid weight loss exceeds 1% body weight per week sustained over 4 weeks (suggests insufficient protein, sleep, or recovery).

**Backing evidence (top 3 by population match):**
- Resistance training significantly improves muscle strength, hypertrophy, power, and physical function in healthy adults, with specific adaptations enhanced by manipulating load, volume, and velocity. ([10.1249/MSS.0000000000003897])
- Aerobic and resistance training significantly improve quality of life, fatigue, body composition, and functional capacity in patients across various cancer types. ([10.1007/s00520-026-10363-0])

- **EA-TRA-1931** (sim 0.74, pop-match 1.00): Resistance training under hypoxic conditions (RTH) results in trivial benefits for muscle strength gains compared to normoxic conditions (RTN), with specific programming variables like non-full-body routines and higher weekly volumes potentially enhancing this effect. ([10.1080/02640414.2024.2425536])
- **EA-TRA-9632** (sim 0.69, pop-match 1.00): Linear and undulating periodization resistance training have comparable effects on enhancing athletic capacity, improving body composition, and regulating blood glucose and insulin resistance. ([10.3389/fpubh.2026.1707627])
- **EA-TRA-8464** (sim 0.66, pop-match 1.00): High-intensity interval training (HIIT) significantly improves aerobic capacity, athletic performance, and body composition in martial arts athletes. ([10.3389/fnut.2026.1792680])

## Conditioning

### Pattern: RP-CON-hiit-vo2max-broad-population (sim=0.68)

**Applies because:** HIIT drives superior mitochondrial biogenesis, stroke volume augmentation, and peripheral oxygen extraction versus lower-intensity modalities by repeatedly stressing the oxygen transport chain near its ceiling, as corroborated by consistent effect-size advantages (SMD/g 0.37–3.6 for VO2-related outcomes) across diverse meta-analyses spanning clinical, youth, and performance populations.
**Parameterization:** Healthy endurance athletes: standard normoxic HIIT; add hypoxic stimulus (live-high-train-low or hypoxic intervals) for an incremental VO2max gain of ~SMD 0.26 over normoxic HIIT alone. Racket-sport and team-sport athletes: HIIT or small-sided games (SSG) are interchangeable for VO2max; HIIT favored when sprint and power outcomes are co-primary. Youth athletes: apply age-appropriate volume scaling; effect sizes are large (g ≈ 0.97) so moderate session counts (2–3×/week) suffice. Post-stroke patients: begin at 50–60% HRR and progress to ≥80% HRR under supervised conditions; target VO2-VT improvements first (MD +2.20 mL/kg/min vs. MICT). HFpEF patients: combine HIIT with inspiratory muscle training (IMT) for additive VO2 peak benefit (IMT SMD 3.6, HIIT SMD 3.5 mL/kg·min); reduce session duration and increase rest intervals relative to healthy cohorts.
**Safety bounds:** Clinical populations require physician clearance before initiating HIIT; absolute contraindications include unstable angina, decompensated heart failure (NYHA IV), acute arrhythmia, or recent (≤3 months) cardiovascular event. Maximum session intensity should not exceed 90% HRmax without on-site medical supervision for cardiac patients. Hypoxic protocols are contraindicated in individuals with sickle-cell trait, severe anemia (Hb < 8 g/dL), or symptomatic pulmonary hypertension. Youth athletes: cap work intervals at ≤95% HRmax; mandatory warm-up ≥10 min.

**Backing evidence (top 3 by population match):**
- In patients with heart failure with preserved ejection fraction (HFpEF), inspiratory muscle training, high-intensity interval training, and combined aerobic and resistance exercise are the most effective interventions for improving aerobic capacity (VO2 peak). ([10.1097/CRD.0000000000000447])
- High-intensity interval training (HIIT) performed under hypoxic conditions results in greater improvements in VO2 max compared to normoxic conditions in distance runners. ([10.14814/phy2.70349])
- Small-sided games (SSGs) and high-intensity interval training (HIIT) produce similar effects on improving endurance performance and VO2max in soccer players. ([10.1055/a-2171-3255])

- **EA-CON-9235** (sim 0.61, pop-match 1.00): Greater age is associated with longer phosphocreatine (PCr) recovery times in upper leg muscles, and more acidic end-of-exercise pH correlates with longer PCr recovery times across muscle groups in healthy individuals. ([10.1002/nbm.70023])

## Supplements

### Pattern: RP-SUP-creatine-resistance-body-composition (sim=0.68)

**Applies because:** Creatine supplementation saturates intramuscular phosphocreatine stores, accelerating ATP resynthesis during repeated high-intensity bouts and enabling higher training volumes, thereby amplifying the anabolic stimulus of resistance training and producing consistent meta-analytic gains in fat-free mass (+0.82–1.39 kg) and strength across diverse populations.
**Parameterization:** Postmenopausal women: ≥5 g/day required to elicit lean mass gains (+0.37 kg) and lower-body strength (+7.5 kg leg-press 1RM); untrained individuals: expect larger absolute strength gains than trained athletes, who show greater absolute FFM gains (1.82 kg vs 1.23 kg); active females: performance responses are inconsistent and clients should set conservative expectations; combat sport and swimming athletes: use for sport-specific power and ergogenic outcomes; co-supplementation with β-alanine (divided 4–6.4 g/day) may further enhance repeated high-intensity bout performance without adding to maximal strength beyond creatine alone.
**Safety bounds:** Loading phase ceiling: 20 g/day for ≤7 days in 4 divided doses; maintenance ceiling: 5 g/day for healthy adults; expect a transient, clinically non-significant serum creatinine rise (~0.07 µmol/L) with no meaningful GFR change in healthy kidneys; clinical supervision and eGFR monitoring required if baseline eGFR < 60 mL/min/1.73 m²; do not use loading phase without medical clearance in individuals with hypertension or fluid-sensitive conditions.

**Backing evidence (top 3 by population match):**
- Creatine supplementation increases intramuscular creatine concentrations and improves high-intensity exercise performance, leading to greater training adaptations. ([10.1186/s12970-017-0173-z])
- Individual studies indicate that sodium citrate, creatine monohydrate, spirulina, green tea and oolong tea extracts, and branched-chain amino acids can significantly affect body mass or composition in wrestlers. ([10.1007/s13668-025-00672-x])
- Creatine supplementation significantly improves muscle strength in the general population, with untrained individuals showing greater improvements than trained ones, and low-to-moderate doses combined with high-intensity exercise yielding better effects. ([10.7717/peerj.20380])

## Recovery

### Pattern: RP-REC-exercise-sleep-quality (sim=0.59)

**Applies because:** Multiple systematic reviews and meta-analyses consistently report significant SMD improvements in subjective sleep quality (range ~0.47–1.56 across modalities), likely mediated by thermoregulatory normalization, hypothalamic-pituitary-adrenal axis down-regulation, and circadian rhythm entrainment via timed physical stimulation.
**Parameterization:** Adults ≥50 yr: combined aerobic + resistance training preferred (SMD −1.56); perinatal women: relaxation exercises 30–60 min/session, 1–2×/week, ≤4 weeks (SMD −2.54 to −3.13); cancer patients on chemotherapy: activity pacing plus progressive muscle relaxation first-line (ranked 98.6%), aerobic exercise or walking as alternatives; older adults with sleep disturbance or mild cognitive impairment: Tai Chi, Baduanjin-style Qigong (PSQI reduction −2.47), or rTMS+Tai Chi combination; perimenopausal women with insomnia: acupuncture or community-based traditional Chinese exercises as adjuncts; general adults: any aerobic, resistance, or mind-body modality scaled to baseline sleep impairment severity and intervention duration.
**Safety bounds:** Avoid vigorous exercise within 2–3 hours of intended sleep onset; obtain medical clearance before initiating resistance or aerobic programs in cancer patients, frail older adults, or individuals with cardiopulmonary comorbidities; rTMS must be administered by a licensed clinician and is contraindicated in individuals with implanted metallic devices, cochlear implants, or a personal or family history of seizures.

**Backing evidence (top 3 by population match):**
- Exercise improves subjective sleep quality in adults, with the magnitude of benefit influenced by baseline sleep quality and intervention duration. ([10.1016/j.smrv.2026.102239])
- Dance interventions produce a statistically significant overall improvement in sleep quality with a small-to-approaching-moderate effect. ([10.3389/fpubh.2026.1776902])
- Relaxation exercises performed for 30-60 minutes per session, 1-2 times per week, for a duration of 4 weeks or less, are the most effective regimen for improving sleep quality in perinatal women. ([10.1186/s12884-026-08673-6])

- **EA-REC-4676** (sim 0.65, pop-match 1.00): Physical post-exercise recovery techniques produce a small to moderate positive effect on vagally-mediated heart rate variability (RMSSD), with cold water immersion showing a moderate to large effect and techniques following resistance exercise demonstrating a larger positive effect than those following cardiovascular exercise. ([10.1111/cpf.12855])
- **EA-REC-8562** (sim 0.59, pop-match 1.00): Cold-water immersion is significantly more effective than body cryotherapy for alleviating delayed onset muscle soreness within 24 hours post-exercise. ([10.1097/MD.0000000000046781])
- **EA-REC-8163** (sim 0.59, pop-match 1.00): Cold water immersion (CWI) after exercise may have a positive acute effect on parasympathetic reactivation, as measured by heart rate variability (HRV). ([10.1002/pri.70033])
- **EA-REC-1657** (sim 0.57, pop-match 1.00): Sleep and circadian interventions in athletes have a more substantial impact on positive affect compared to negative affect. ([10.1007/s40279-025-02387-z])

## Behavioral

### Pattern: RP-BEH-multicomponent-exercise-adherence (sim=0.72)

**Applies because:** COM-B model and TDF analyses establish that exercise adherence is co-determined by capability, opportunity, and motivational factors simultaneously, meaning isolated single-domain strategies produce insufficient and non-durable behavior change, while multi-component approaches address the full causal architecture of adherence.
**Parameterization:** Scale social support modality by setting and age: older adults benefit from AI-assisted or robotic social prompting to extend training duration and engagement; T2D populations require integration of glycemic self-monitoring feedback (HbA1c, fasting glucose, waist circumference targets) as motivational anchors; chronic pain populations should pair adherence strategies with high-value physiotherapy protocols and technology-based delivery where in-person access is limited; autonomy support and emotional experience management should be weighted more heavily when extrinsic motivation is low.
**Safety bounds:** Exercise intensity must remain within individually medically cleared ranges; patients with uncontrolled HbA1c >10%, unstable cardiovascular disease, acute musculoskeletal injury, or severe unmanaged chronic pain flares require direct clinical supervision before program enrollment; AI/robotic-assisted interventions must include human clinical oversight protocols.

**Backing evidence (top 3 by population match):**
- Therapeutic patient education interventions in the Eastern Mediterranean Region produce significant improvements in diabetes self-management outcomes, specifically waist circumference, HbA1c, and fasting blood glucose. ([10.1186/s12889-025-24721-w])
- Flexible and personalized physical activity programs, multidimensional social support, participant education, enhancing self-efficacy and motivation, monitoring and feedback, and managing emotional experiences are key implementation strategies to improve adherence in individuals with type 2 diabetes. ([10.1007/s12529-025-10400-y])

### Pattern: RP-BEH-multicomponent-bct-physical-activity (sim=0.66)

**Applies because:** BCTs target the psychological, social, and environmental determinants of behavior simultaneously; multicomponent designs reduce barriers across all three levels at once, producing additive or synergistic effects on motivation, habit formation, and sustained behavior change that single-component approaches cannot match.
**Parameterization:** Adolescents (12–18 y): emphasize Social reward, Behavioral contract, and Prompts/cues alongside Social support for greatest effect on physical activity adherence; digital delivery of social support is a viable substitute when in-person access is limited. University students (18–25 y): structured physical activity programs alone yield large mental-health gains; pairing with self-monitoring apps amplifies wellbeing and depression/anxiety reductions. Middle-aged adults (40–60 y): add goal-setting and meditation BCTs to the core stack to generate co-benefits in sleep quality and cognitive function. Environmental or policy components (e.g., activity-friendly spaces, cue redesign) can be layered into any age cohort to further reduce sedentary behavior.
**Safety bounds:** BCT-based behavioral programs carry no known pharmacological risk; however, prescribed exercise intensity should remain within age-appropriate aerobic guidelines (moderate–vigorous, ≤60 min/day for youth per WHO) and must not substitute for clinical care in participants with diagnosed psychiatric or sleep disorders requiring pharmacological or psychotherapeutic treatment.

**Backing evidence (top 3 by population match):**
- Behavioral change techniques such as Social support, Self-monitoring, Feedback, Social reward, Prompts/cues, and Behavioral contract are more frequently applied in effective physical activity interventions for adolescents. ([10.1186/s12889-025-25618-4])

- **EA-BEH-0513** (sim 0.60, pop-match 1.00): Exercise may be moderately more effective than a control intervention for reducing symptoms of depression. ([10.1002/14651858.CD004366.pub7])
- **EA-BEH-8816** (sim 0.53, pop-match 1.00): Interactive conversational agents can improve specific dietary behaviors, including fruit and vegetable intake and adherence to the Mediterranean diet, while also enhancing nutritional knowledge. ([10.2196/78220])
- **EA-BEH-2322** (sim 0.52, pop-match 1.00): Higher quality health coaching interventions, as assessed by the Health Coaching Quality Index (HCQI), appear to be associated with a greater proportion of positive outcomes. ([10.1007/s12529-025-10419-1])
- **EA-BEH-6471** (sim 0.51, pop-match 1.00): mHealth interventions significantly improve self-care ability and reduce rehospitalization rates among organ transplant recipients. ([10.2196/69795])

## Metadata

- top_k_per_domain: 30
- applicability_threshold: 0.5
- total queries issued: 25
- total contraindication hits: 0
