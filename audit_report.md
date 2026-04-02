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

---

## Audit Results

**Protocol:** Methylated DNA Immunoprecipitation (MeDIP)
**Status:** Requires significant revision before use

---

### 1. Missing Steps

**Before immunoprecipitation:**

- DNA quantification after extraction is absent. Yield and quality must be confirmed before proceeding. Nanodrop plus Qubit or PicoGreen is standard.
- No DNA quality check by gel electrophoresis. Integrity should be verified before fragmentation.
- RNase A treatment is not mentioned. RNA contamination skews yield measurements and interferes with downstream steps.
- No fragmentation verification. The 200-600bp target must be confirmed by gel or Bioanalyzer before moving forward.
- No input sample reservation. Saving 5-10% of input DNA for normalization is required, not optional.
- No blocking step before antibody addition. BSA (0.1%) and salmon sperm DNA should be added to reduce non-specific binding.
- No pre-clearing step. Incubating with beads alone for 1h at 4C before adding antibody reduces background.

**After immunoprecipitation:**

- Proteinase K digestion is missing from the elution step. It is required to digest antibody and protein from the complex before DNA purification.
- No IgG isotype control. This is an essential negative control for assessing non-specific antibody binding.
- No positive control against a known methylated sequence. Without it there is no confirmation that the IP enriched methylated DNA.
- No DNA quantification after purification. Recovery must be confirmed before qPCR or sequencing.
- Library preparation is described only as "proceed to sequencing," which is not a protocol step.

---

### 2. Safety Concerns

**Sonication:** Probe sonication of blood-derived samples generates aerosols. Work should be performed in a biosafety cabinet or with aerosol containment. PPE required: face shield, lab coat, gloves. Human blood samples are BSL-2 material and require appropriate waste disposal. The protocol contains no biosafety or disposal guidance.

**Buffers:** The composition of the IP buffer and elution buffer is not stated. If elution uses SDS or NaOH, handling procedures must be specified. If phenol-chloroform is used in the purification step, a fume hood is required. This step is unspecified and therefore uncontrolled.

---

### 3. Quality Control Checkpoints

The following checkpoints should be treated as go/no-go decision points:

**After extraction:** A260/A280 should be 1.8-2.0. A260/A230 should be above 1.7. Minimum yield for MeDIP is 5 µg. No visible RNA contamination on gel. Fail: re-extract or treat with RNase A.

**After fragmentation:** Run 2% agarose gel or Bioanalyzer. Majority of fragments should fall in the 200-600bp range with no unsheared high-MW DNA remaining. Fail: adjust sonication cycles and repeat.

**Before IP:** Confirm single-stranded DNA. Transfer immediately to ice after denaturation. Do not allow re-annealing before antibody addition. Add blocking agents at this stage.

**After IP, before elution:** Bead pellet should be visible and consistent across samples. Save the final wash supernatant to assess non-specific losses.

**After purification:** Quantify with Qubit (fluorometric, not UV-based — yield will be low). Expected recovery is 0.1-5% of input. Run qPCR against a known methylated locus (LINE-1 or IAP) and a known unmethylated locus (GAPDH promoter). Enrichment ratio at methylated loci should be 5-fold or higher. Fail: repeat IP and investigate antibody lot or DNA quality.

---

### 4. Parameter Issues

**Fragmentation target (step 2):** 200-600bp is too wide for sequencing applications. Narrow to 200-400bp for MeDIP-seq and confirm empirically per sonication setup.

**Denaturation (step 3):** Temperature is correct but the protocol does not specify immediate transfer to ice. Re-annealing will destroy antibody accessibility. Add: transfer immediately to ice for 5 minutes.

**Antibody incubation (step 4):** Overnight at 4C is acceptable but the antibody amount is not stated. Standard is 1-2 µg anti-5mC antibody per 1 µg DNA. Validate per antibody lot.

**Protein A/G beads (step 5):** Temperature is not stated. Should be 4C with end-over-end rotation.

**Wash steps (step 6):** Three washes may be insufficient. Recommend 4-5 washes. Buffer composition and salt concentration are not defined. Standard is a 140-500mM NaCl gradient.

**DNA input amount:** Not stated anywhere in the protocol. Specify 1-5 µg sheared DNA per IP reaction.

**Elution (step 7):** Method is completely absent. Standard: 1% SDS with 0.1M NaHCO3, or a commercial elution buffer, at 65C for 30 minutes with vortexing.

---

### 5. Suggested Improvements

Add a CpG enrichment validation step after purification. A dot blot with anti-5mC antibody on input versus MeDIP fractions gives a visual confirmation of methylation enrichment before committing to sequencing costs.

Include spike-in controls. Adding unmethylated lambda DNA at the fragmentation step as an exogenous negative control lets you calculate non-specific pulldown rates across batches.

Specify antibody catalog number and lot. Performance varies significantly between lots. Test each new lot against validated positive and negative controls before use.

Switch to magnetic Protein A/G beads if not already using them. They reduce non-specific binding and allow more consistent wash procedures than agarose beads.

Specify end-over-end rotation at 4C for all IP incubation steps. Static incubation causes uneven bead settling.

Define the IP buffer composition. "IP buffer" as written is not reproducible.
