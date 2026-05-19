# NLR Whole-Facility AI Workload Profiles

**Source dataset:** Vercellino et al. 2026, "Measurement of Generative AI Workload
Power Profiles for Whole-Facility Data Center Infrastructure Planning"
- **arXiv:** [2604.07345](https://arxiv.org/abs/2604.07345)
- **Dataset DOI:** [10.7799/3025227](https://doi.org/10.7799/3025227)
- **NLR Data Catalog landing page:** https://data.nlr.gov/submissions/312

## What is here

These are the simulated whole-facility power profiles extracted from the
`03_whole-facility_profiles/` folder of the 1 GB NLR dataset. We extracted
only the CSV time series and discarded the analysis notebooks + plots.

### Colocation facility (HPC + GenAI mixed)
- `colocation_10MW_2840nodes_{20u,40u,60u,80u}_power.csv`
- Capacity: 10 MW IT, 2,840 nodes
- Time span: 2018-01-01 to 2019-01-01 (one full year, 1-minute resolution)
- 525,601 rows × 3 columns: `timestamp`, `power_W`, `utilization`
- File size: 27-31 MB each

### Inference-only facility
- `inference_1MW_283nodes_{20u,40u,60u,80u}_power.csv`
- Capacity: 1 MW IT, 283 nodes (inference-only, no training)
- Same time span and resolution
- Note: pure inference is a small fraction of typical hyperscale AI mix; we use
  the colocation files (HPC + AI mixed) for the paper baseline

## How we transformed for the paper

Script: [data/_raw/build_real_ai_workload.py](../../_raw/build_real_ai_workload.py)

1. Selected the 10 MW colocation profile at 60u (60% utilization) as the
   paper baseline (representative of mixed-workload AI DC).
2. Multiplied power by ×20 to scale from 10 MW → 200 MW nameplate IT capacity.
3. Aggregated 1-minute → 1-hour via mean (525,600 rows → 8760 hourly rows).

Outputs at `data/workload/dc_200mw_real_{u}u_2018.csv` for all 4 utilization
variants; `data/workload/cooling_load_pue{110,130,150}.csv` for PUE-derived
cooling load; and `data/it_load.csv` (paper primary, copy of 60u variant).

## License

Public dataset per NLR Data Catalog (see source URL above). When using in
publications, cite the arXiv paper and dataset DOI:

> Vercellino, R., Willard, J., Campos, G., da Silva Pereira, W., Hull, O.,
> Selensky, M., & Mueller, J. (2026). Measurement of Generative AI Workload
> Power Profiles for Whole-Facility Data Center Infrastructure Planning.
> arXiv preprint arXiv:2604.07345. National Laboratory of the Rockies Data
> Catalog. DOI: 10.7799/3025227.
