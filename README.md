# Survival of Notability

<a target="_blank" href="https://cookiecutter-data-science.drivendata.org/">
    <img src="https://img.shields.io/badge/CCDS-Project%20template-328F97?logo=cookiecutter" />
</a>

Web communities depend on open forums for tasks like governance, information sharing, and decision-making, but these can yield biased outcomes. In Wikipedia's Articles for Deletion (AfD) discussions, biographies of women face faster deletion nominations, longer consensus times, and are more often redirected or merged into men’s biographies, highlighting gender asymmetries. Our study employs a competing risk survival framework to illuminate AfD’s role in Wikipedia’s gender gap, offering insights for open knowledge governance.

## Steps to follow
1. Clone the project repository.

2. Create requirment.txt file
```
    make create_requirement
```
3. Then create virtual environment
```
    make create_environment
```
4. Then prepare dataset
```
    make data
```
All the outputs will be stored in folder "processed".

5. Then prepare dataset for retrospective analysis
```
    make retrospective_data
```
All the outputs will be stored in folder "interim" and "processed".


6. To explore and visualize the results of the survival analysis, refer to the notebook: Survival Analysis.ipynb
7. To model competing risk (both Multi-state and Single-state models) and create visualization
```
    make compete_risk
```
The report will be stored in file "reports/figures/Fig5-All_models.pdf".

## (Optional) Steps to build dataset from scratch
If you want to extract raw dataset and store in folders "raw" and "petscan", follow the [Manual](docs/docs/index.md). 
    

## Project Organization

```
├── LICENSE            <- Open-source license.
├── Makefile           <- Makefile with convenience commands like `make data`
├── README.md          <- The top-level README for developers using this project.
├── data
│   ├── petscan        <- Data from third party sources "PetScan".
│   ├── interim        <- Intermediate data that has been transformed.
│   ├── processed      <- The final, canonical data sets for "Survival Analysis" .
│   └── raw            <- The original, immutable data dump.
│       ├── Quarry     <- immutable datasets extracted from "Quarry": Biographies with creation dates, Articles from Archive, Articles nominated in Article for Deletion with nomination dates .
│       └── Wikidata   <- The original, immutable datasets extracted from "Wikidata": data with vital information such as gender, date of birth and date of death .
│                 
│
├── docs               <- A default mkdocs project; see www.mkdocs.org for details
│
├── Survival Analysis.ipynb          <- Jupyter notebook to data exploration and create visualization.
│
├── pyproject.toml     <- Project configuration file with package metadata for 
│                         survival_of_notability and configuration for tools like black
│
├── references         <- Data dictionaries, manuals, and all other explanatory materials.
│
├── reports            <- Generated analysis as HTML, PDF, LaTeX, etc.
│   └── figures        <- Generated graphics and figures to be used in reporting
│
├── requirements.in   <- The requirements file for reproducing the analysis environment.
│
├── setup.cfg          <- Configuration file for flake8
│
└── survival_of_notability   <- Source code for use in this project.
    │
    ├── __init__.py             <- Makes survival_of_notability a Python module
    │
    ├── config.py               <- Store useful variables and configuration
    │
    ├── dataset.py              <- Scripts to download or generate data
    │
    └── features.py             <- Code to create features for modeling.
    
```

--------



