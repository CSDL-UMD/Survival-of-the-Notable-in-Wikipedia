# Survival of Notability

<a target="_blank" href="https://cookiecutter-data-science.drivendata.org/">
    <img src="https://img.shields.io/badge/CCDS-Project%20template-328F97?logo=cookiecutter" />
</a>

Web communities depend on open forums for tasks like governance, information sharing, and decision-making, but these can yield biased outcomes. In Wikipedia's Articles for Deletion (AfD) discussions, biographies of women face faster deletion nominations, longer consensus times, and are more often redirected or merged into men’s biographies, highlighting gender asymmetries. Our study applies both survival analysis and a competing risk framework to examine the role of Articles for Deletion (AfD) in Wikipedia’s gender gap, offering insights for the governance of open knowledge platforms. Our paper describing this work is available on [arXiv](https://doi.org/10.48550/arXiv.2411.04340).

## Steps to follow
1. Clone the project repository.
```
    git clone https://github.com/CSDL-UMD/Survival-of-the-Notable-in-Wikipedia.git
```    

2. Create requirment.txt file
```
    make create_requirement
```
3. Then create virtual environment
```
    make create_environment
```
4. Download raw datasets from [Zenodo](https://zenodo.org/records/15259030). Then unzip "data.zip" and place the contents into this project folder. 

(Optional) Steps to build dataset from scratch:
If you want to extract raw dataset and store in folders "data/raw" and "data/petscan", follow the [Manual](docs/docs/index.md). 
    

5. Then, using Python scripts, prepare dataset for survival analysis 
```
    make data
```
This script will prepare datasets for: a) Kaplan-Meier estimation, b) Cox proportional hazards model analysis, and c) Competing Risk model. All the outputs will be stored in folder "data/interim" (for retrospective analysis) and "data/processed" (for the rest).

6. Then, using R scripts, employ competing risk model (both Multi-state and Single-state models) and create visualization
```
    make compete_risk
```
The report will be stored in file "reports/figures/Fig5-All_models.pdf".

7. Then, using R scripts, prepare dataset for retrospective analysis
```
    make retrospective_data
```
All the outputs will be stored in "data/processed".


8. Finally, to explore and visualize the results of the survival analysis and competing risk models, use the notebook: "Survival Analysis.ipynb". All the visualizations will be stored in folder "reports/figures/".




## Project Organization

```
├── LICENSE            <- Open-source license.
├── Makefile           <- Makefile with convenience commands like `make data`
├── README.md          <- The top-level README for developers using this project.
├── data
│   ├── petscan        <- The immutable datasets from third party sources "PetScan".
│   ├── interim        <- Intermediate data that has been transformed.
│   ├── processed      <- The final, canonical data sets for "Survival Analysis" .
│   └── raw            <- The original, immutable data: conversation logs of AfD
│       │                  from 2005 to 2023, types and gender information of the 
│       │                   articles the nominated articles are redirected or merged to.   
│       ├── Quarry     <- The original, immutable datasets extracted from 
│       │                  "Quarry": Biographies with creation dates, Articles from Archive, 
│       │                  Articles nominated in Article for Deletion with nomination dates .
│       └── Wikidata   <- The original, immutable datasets extracted from 
│                            "Wikidata": data with vital information such as gender, 
│                            date of birth and date of death .
│                 
│
├── docs               <- Data manuals, and all other explanatory materials. 
│                          This is a default mkdocs project; see www.mkdocs.org for details
│
├── Survival Analysis.ipynb          <- Jupyter notebook to data exploration, survival analysis and create visualization.
│
├── pyproject.toml     <- Project configuration file with package metadata for 
│                         survival_of_notability and configuration for tools like black
├── reports            <- Generated analysis as HTML, PDF, LaTeX, etc.
│   └── figures         <- Generated graphics and figures to be used in reporting
│
├── requirements.in    <- The requirements file for reproducing the analysis environment.
│
├── setup.cfg          <- Configuration file for flake8
│
└── survival_of_notability   <- Source code for use in this project.
    ├── __init__.py             <- Makes survival_of_notability a Python module.
    │
    ├── config.py               <- Store useful variables and configuration.
    │
    ├── dataset.py              <- Python scripts to prepare data for survival analysis.
    │
    ├── Survival Analysis.R     <- R scripts to generate and analysis of Multi-state and Single-state competing risk model.
    │
    ├── Compete.R               <- R scripts for retrospective analysis using competing risk model. 
    │
    └── features.py             <- Code to create features for modeling.
    
```


## 📄 Citation

If you use this code or build upon this work, please cite the following paper:

> Khandaker Tasnim Huq and Giovanni Luca Ciampaglia.  
> *"Survival of the Notable: Gender Asymmetry in Wikipedia Collective Deliberations."*  
> arXiv preprint arXiv:2411.04340 (2024).
> [https://doi.org/10.48550/arXiv.2411.04340](https://doi.org/10.48550/arXiv.2411.04340)

### BibTeX
```bibtex
@article{huq2024survival,
  title={Survival of the Notable: Gender Asymmetry in Wikipedia Collective Deliberations},
  author={Huq, Khandaker Tasnim and Ciampaglia, Giovanni Luca},
  journal={arXiv preprint arXiv:2411.04340},
  year={2024}
}

--------



