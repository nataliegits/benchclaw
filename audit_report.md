# BenchClaw Audit Report

## Protocol Input

```

MeDIP Protocol:
1. Extract genomic DNA from blood samples
2. Fragment DNA by sonication to 200-600bp
3. Denature DNA at 95C for 10 minutes
4. Incubate with anti-5mC antibody overnight at 4C
5. Add protein A/G beads and incubate 2 hours
6. Wash beads 3x with IP buffer
7. Elute DNA and purify
8. Proceed to qPCR or sequencing

```

## Audit Results

# MeDIP Protocol Audit Report

**Protocol:** Methylated DNA Immunoprecipitation (MeDIP)
**Auditor:** Senior Epigenetics Specialist
**Status:** ⚠️ REQUIRES SIGNIFICANT REVISION BEFORE USE

---

## 1. 🔴 MISSING STEPS (Critical)

### Pre-Immunoprecipitation
| Missing Step | Why It's Critical |
|---|---|
| **DNA quantification after extraction** | Must confirm yield/quality before proceeding; recommend Nanodrop + PicoGreen or Qubit |
| **DNA quality assessment (gel electrophoresis)** | Verify DNA integrity before fragmentation |
| **RNase A treatment during extraction** | RNA contamination will skew yield measurements and interfere with downstream steps |
| **Fragmentation verification by gel/Bioanalyzer** | No confirmation that 200-600bp target was achieved before proceeding |
| **Input sample reservation** | No mention of saving 5-10% input DNA — this is **non-negotiable** for normalization |
| **Blocking step before antibody addition** | BSA (0.1%) and salmon sperm DNA should be added to prevent non-specific binding |
| **Pre-clearing of chromatin with beads** | Reduces non-specific background; incubate with beads alone for 1h at 4°C before antibody step |

### Post-Immunoprecipitation
| Missing Step | Why It's Critical |
|---|---|
| **Proteinase K digestion during elution** | Required to digest antibody/protein from immunoprecipitated complex before DNA purification |
| **IgG isotype control IP** | Absent entirely — essential negative control to assess non-specific antibody binding |
| **Positive control (e.g., known methylated sequence)** | No confirmation that IP actually enriched methylated DNA |
| **DNA quantification after purification** | Must confirm recovery before qPCR/sequencing |
| **Library preparation steps (if sequencing)** | "Proceed to sequencing" is insufficiently described |

---

## 2. 🟠 SAFETY CONCERNS

```
⚠️ SONICATION HAZARDS
```
- Sonication generates **aerosols** — must be performed in a biosafety cabinet or with
  aerosol containment, especially with blood-derived samples (biohazard risk)
- **PPE required:** face shield, lab coat, gloves during sonication
- Hearing protection if using probe sonicator in open bench environment
- All blood samples should be treated as **BSL-2 material**

```
⚠️ CHEMICAL HAZARDS
```
- Specify composition of IP buffer and elution buffer
- If elution uses **SDS or NaOH**, appropriate chemical handling procedures must be stated
- Phenol-chloroform (if used in DNA purification) requires fume hood — this step is
  unspecified and therefore uncontrolled

```
⚠️ BIOLOGICAL MATERIAL
```
- Human blood samples require proper **biohazardous waste disposal**
- Protocol lacks **any** biosafety or waste disposal guidance

---

## 3. 🟡 QUALITY CONTROL CHECKPOINTS

The following QC gates should be inserted as **GO/NO-GO decision points:**

```
CHECKPOINT 1 — After DNA Extraction
  ✓ A260/A280 ratio: 1.8–2.0
  ✓ A260/A230 ratio: >1.7
  ✓ Minimum yield: ≥5 µg recommended for MeDIP
  ✓ No visible RNA contamination on gel
  → FAIL: Re-extract or treat with RNase A
```

```
CHECKPOINT 2 — After Fragmentation
  ✓ Run 2% agarose gel or Bioanalyzer
  ✓ Target: majority of fragments 200–600bp
  ✓ No unsheared high-MW DNA remaining
  → FAIL: Adjust sonication cycles and re-run
```

```
CHECKPOINT 3 — After Denaturation/Pre-IP
  ✓ Confirm single-stranded DNA (critical for antibody accessibility)
  ✓ Transfer immediately to ice — do NOT allow re-annealing before antibody addition
  ✓ Add blocking agents at this stage
```

```
CHECKPOINT 4 — After IP / Before Elution
  ✓ Check bead pellet is visible and consistent across samples
  ✓ Save final wash supernatant to assess non-specific losses
```

```
CHECKPOINT 5 — After Purification
  ✓ Quantify with Qubit (fluorometric, not UV-based — low yield expected)
  ✓ Expected recovery: 0.1–5% of input
  ✓ Run qPCR against known methylated locus (e.g., LINE-1, IAP) AND
    known unmethylated locus (e.g., GAPDH promoter) to confirm enrichment
  ✓ Calculate enrichment ratio: MeDIP/Input ≥ 5-fold at methylated loci
  → FAIL: Repeat IP; investigate antibody lot or DNA quality
```

---

## 4. 🔴 PARAMETER ISSUES

| Step | Current Parameter | Problem | Recommended Correction |
|---|---|---|---|
| **Fragmentation target** | 200–600bp | Range is too wide for sequencing applications | Narrow to **200–400bp** for MeDIP-seq; confirm empirically |
| **Denaturation** | 95°C, 10 min | ⚠️ **Temperature is correct BUT** — protocol does not specify immediate transfer to ice; re-annealing will destroy antibody accessibility | Add: *"immediately place on ice for 5 min"* |
| **Antibody incubation** | Overnight, 4°C | Overnight is acceptable but antibody amount is **completely unspecified** | Specify: typically **1–2 µg anti-5mC antibody per 1 µg DNA** (validate per antibody lot) |
| **Protein A/G beads** | 2 hours incubation | Temperature not stated | Should be **4°C with rotation**; 2h is acceptable but 4°C is critical |
| **Wash steps** | 3× washes | Number may be insufficient; wash stringency not defined | Recommend **4–5 washes**; specify buffer composition and salt concentration (typically 140–500mM NaCl gradient) |
| **DNA input amount** | Not stated | ⚠️ **Critical omission** — MeDIP requires careful input calibration | Specify: **1–5 µg sheared DNA** per IP reaction |
| **Elution** | Not specified | Method completely absent | Specify: 1% SDS + 0.1M NaHCO₃ OR commercial elution buffer; **65°C, 30 min with vortexing** |

---

## 5. 💡 SUGGESTED IMPROVEMENTS

### Experimental Design
> **▶ Add a CpG enrichment validation step**
> After purification, perform dot blot with anti-5mC antibody on input vs. MeDIP fractions
> to visually confirm methylation enrichment before committing to expensive sequencing

> **▶ Include spike-in controls**
> Add unmethylated lambda DNA (exogenous) at the fragmentation step as a negative control
> to calculate non-specific pulldown rates across batches

> **▶ Antibody validation**
> Specify antibody clone and catalog number (e.g., Diagenode #C15200081)
> Note antibody lot number — performance varies significantly between lots
> Test each new lot against validated positive/negative controls before use

### Technical Improvements
> **▶ Use magnetic vs. agarose beads**
> Magnetic Protein A/G beads significantly reduce non-specific binding and
> allow more consistent wash procedures than agarose beads — strongly recommended

> **▶ Rotation during all incubation steps**
> Specify end-over-end rotation at 4°C for all IP incubation steps;
> static incubation causes uneven bead settling and reduces efficiency

> **▶ Parallel negative controls**
> Run IgG control IP in parallel with every experiment, not just during method validation

### Documentation & Reproducibility
> **▶ Buffer recipes must be explicitly defined**
> "IP buffer" is undefined — provide exact composition