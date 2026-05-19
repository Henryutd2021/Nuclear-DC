# Licenses & Attribution — Upstream Data Sources

The Nuclear-DC repository itself is licensed under MIT (see [LICENSE](LICENSE)).
This document records the licenses and attribution requirements for **every
upstream data source** used in `data/`. When the paper cites a number, it
traces back to a row here.

The data archived in this repository is either:

- **Public domain** — U.S. government works (no license required, but cited)
- **CC-BY 4.0** — must attribute the source on use
- **Open-access peer-reviewed** — cite the paper per academic convention
- **Vendor specifications** — cite the manufacturer

---

## 1. Government & Inter-Governmental (Public Domain or Open License)

| Source | Used for | Cite | License |
|---|---|---|---|
| **ERCOT MIS** (NP4-183-CD, NP6-905-CD) | DA-LMP + RT-LMP 2022-2024 | ERCOT 2024 | Public, ERCOT MIS terms of use |
| **EIA Form 930** | ERCOT hourly load + generation mix 2022-2024 | EIA 2024 | Public domain (U.S. Government work) |
| **EIA Form 923** | Nuclear fleet fuel cost | EIA 2024 | Public domain |
| **EIA Henry Hub Spot** (NG.RNGWHHD.D) | Natural gas daily price 2022-2024 | EIA 2024 | Public domain |
| **EPA AVERT** | ERCOT regional emission factors | EPA 2024 | Public domain |
| **NREL ATB 2024** | Nuclear, NGCC, BESS, Geothermal-Binary techno-economic | NREL 2024 | Public, openly licensed |
| **NREL/Macknick 2012** (ERL 7:045802) | Water consumption factors | Macknick et al. 2012 | DOE-funded, CC-BY |
| **Cole & Karmakar 2024** (NREL TP-6A40-89625) | BESS cost projections | Cole & Karmakar 2024 | Public, openly licensed |
| **MIT ANP-201** (Shirvan 2024) | Nuclear LCOE FOAK/NOAK | Shirvan 2024 | Academic open report |
| **INL/RPT-24-77048** | SMR cost meta-analysis | INL 2024 | DOE-funded, public |
| **UNECE 2022 LCA** | Nuclear + grid lifecycle emissions | UNECE 2022 | Public, UN open access |
| **IAEA ARIS 2024** | BWRX-300 standardized spec page | IAEA 2024 | Public, UN open access |
| **U.S. NRC** | BWRX-300 regulatory status page | NRC 2024 | Public domain |
| **CNSC / OPG Darlington** | OPG 2024 budget announcement | OPG 2024 | Public, Canadian govt + provincial Crown corporation |
| **NOAA NCEI 1991-2020 Normals** | Houston KIAH climate baseline | NCEI 2021 | Public domain |

## 2. Reanalysis Data (CC-BY)

| Source | Used for | Attribution required |
|---|---|---|
| **Open-Meteo Historical Weather API** | Houston hourly 2022-2024 (T, RH, wet-bulb derived) | Yes — CC-BY-4.0; cite Open-Meteo and ERA5 (Hersbach et al. 2020) |
| **ECMWF ERA5** (upstream of Open-Meteo) | Same | Yes — cite Hersbach et al. 2020 QJRMS |

**Attribution text for paper:**
> Weather data from Open-Meteo (open-meteo.com), based on ECMWF ERA5
> reanalysis (Hersbach et al. 2020). CC-BY 4.0.

## 3. Peer-Reviewed Open-Access Journals (CC-BY)

| Source | Used for | DOI |
|---|---|---|
| **Quoilin et al. 2013** (RSER) | ORC techno-economic baseline + η(T_hot) curve | 10.1016/j.rser.2013.01.028 |
| **Lemmens 2016** (Energies, MDPI) | ORC CAPEX range + part-load curve | 10.3390/en9070485 (CC-BY) |
| **Shahzad et al. 2021** (Energies, MDPI) | Absorption chiller TEA, DC-deployment direct | 10.3390/en14092433 (CC-BY) |
| **Alvarez et al. 2018** (Science) | NGCC upstream CH4 emissions | 10.1126/science.aar7204 |
| **Patterson et al. 2022** (arXiv 2104.10350) | AI workload diurnal pattern context | arxiv preprint |
| **Stull 2011** (J. Appl. Meteor. Climatol.) | Wet-bulb derivation formula | 10.1175/JAMC-D-11-0143.1 |
| **Vercellino et al. 2026** (arXiv 2604.07345) | NLR AI workload power profiles dataset (Tier 3) | 10.48550/arXiv.2604.07345 |
| **Hersbach et al. 2020** (QJRMS) | ERA5 reanalysis primary reference | 10.1002/qj.3803 |

## 4. Vendor & Industry Specifications

These are publicly available company documents. We cite for nameplate specs
only; no redistribution of vendor data files.

| Source | Used for |
|---|---|
| **GE-Vernova/Hitachi BWRX-300 General Description** | Reactor technical spec |
| **NVIDIA H100 Datasheet** | AI hardware reference for framing |
| **OCP 2024 Meta Catalina** (open compute spec) | Blackwell GB200 rack density |
| **Shuangliang / Thermax / York / Broad chiller datasheets** | Absorption chiller drive temp + chilled water envelope |
| **Trane CenTraVac / York YMC2** | Electric chiller COP at design |
| **ASHRAE Handbook** (Refrigeration), **AHRI 550/590** | Chiller part-load standard |
| **ORNL Pub14546** (CHP in DCs) | Absorption deployment data, free public PDF |
| **DOE CHP 2017 Fact Sheet** | Absorption chiller technology fact sheet, public |
| **World Nuclear Association** | Nuclear fuel cost components, public web |
| **World Nuclear News** | OPG Darlington budget reporting |

## 5. Third-Party Dataset — NLR AI Workload (TIER 3, NOT REDISTRIBUTED)

The most significant third-party dataset is the **NLR Generative AI Workload
Power Profiles** dataset (Vercellino et al. 2026, DOI 10.7799/3025227). Its
~1 GB raw file is **NOT included** in this repo:

- The full 1 GB zip is downloaded from https://data.nlr.gov/submissions/312
- Our `data/workload/raw_nlr_colocation/*.csv` directory holds only the
  subset we transformed (8 CSVs total, ~226 MB), with original NLR README
- We DO redistribute the **8760-hour aggregates** we derive
  (`data/workload/dc_200mw_real_*u_2018.csv`) which are a small transformation
  of the public dataset — this is permitted per the NLR Data Catalog license
- Users must re-download the raw NLR data themselves to fully re-derive the
  aggregates from scratch (see `data/MANUAL_COLLECTION.md`)

## 6. Our Original Contributions

| Artifact | License |
|---|---|
| All YAML parameter files (`reactor/`, `equipment/`, `economics/`, `environmental/`) | MIT (this repo) |
| All Python scripts (`src/`, `data/_raw/`) | MIT (this repo) |
| Performance curves (`data/perf/*.csv`) — derived from public formulas | MIT (this repo, derivation is ours) |
| Documentation (`data/*.md`, `README.md`) | MIT (this repo) |

The YAMLs and derived CSVs encode publicly available numerical values from the
sources above; the derivations and structure are our original work. Numerical
values themselves are not copyrightable; the curation, code, and documentation
are our contribution.

---

## Paper Data Availability Statement (draft for AE submission)

> All input data used in this study are publicly available. The raw ERCOT
> Day-Ahead and Real-Time market prices and ERCOT system load were obtained
> from the ERCOT Market Information System and EIA-930 Hourly Electric Grid
> Monitor, respectively. Houston hourly weather data were obtained from the
> Open-Meteo Historical Weather API based on ECMWF ERA5 reanalysis (Hersbach
> et al. 2020). AI data-center workload profiles were obtained from the
> National Laboratory of the Rockies Generative AI Workload Power Profiles
> dataset (Vercellino et al. 2026, DOI: 10.7799/3025227). All reactor, equipment,
> and economic parameters were compiled from public technical reports cited
> in Section 2 and listed in the Supplementary Information.
>
> The complete processed dataset and analysis code are archived at
> [Zenodo DOI to be assigned at submission] and openly available on GitHub
> at https://github.com/[author]/Nuclear-DC.

---

*Last updated: 2026-05-19.*
