# Survival of Notability

<a target="_blank" href="https://cookiecutter-data-science.drivendata.org/">
    <img src="https://img.shields.io/badge/CCDS-Project%20template-328F97?logo=cookiecutter" />
</a>

Web communities depend on open forums for tasks like governance, information sharing, and decision-making, but these can yield biased outcomes. In Wikipedia's Articles for Deletion (AfD) discussions, biographies of women face faster deletion nominations, longer consensus times, and are more often redirected or merged into men’s biographies, highlighting gender asymmetries. Our study applies both survival analysis and a competing risk framework to examine the role of Articles for Deletion (AfD) in Wikipedia’s gender gap, offering insights for the governance of open knowledge platforms. Our paper describing this work is available on [Proceedings of the ACM on Human-Computer Interaction (CSCW)](https://dl.acm.org/doi/10.1145/3757663).

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
    ├── get_creation_dates.py   <- Code to extract creation dates of the articles. 
    │
    ├── prepare_wikidata.py     <- Python scripts to integrate creation dates of articles and metadata from Wikidata (Details in "Manual"). 
    │
    ├── get_needed_wikidata.py  <- Python scripts to extract missing metadata from Wikidata (Details in "Manual"). 
    │
    ├── get_needed_creation_dates.py   <- Python scripts to extract missing creation dates of articles (Details in "Manual"). 
    │
    └── AfD_Parse.py            <- Python scripts to extract conversation logs from Article for Deletion (Details in "Manual").
    
    
```


## 📄 Citation

If you use this code or build upon this work, please cite the following paper:

> Khandaker Tasnim Huq and Giovanni Luca Ciampaglia.  
> *"Survival of the Notable: Gender Asymmetry in Wikipedia Collective Deliberations."*  
> [Proceedings of the ACM on Human-Computer Interaction (CSCW)](https://dl.acm.org/doi/10.1145/3757663)

### BibTeX
```bibtex
@article{10.1145/3757663,
author = {Huq, Khandaker Tasnim and Ciampaglia, Giovanni Luca},
title = {Survival of the Notable: Gender Asymmetry in Wikipedia Collective Deliberations},
year = {2025},
issue_date = {November 2025},
publisher = {Association for Computing Machinery},
address = {New York, NY, USA},
volume = {9},
number = {7},
url = {https://doi.org/10.1145/3757663},
doi = {10.1145/3757663},
abstract = {Communities on the web rely on open conversation forums for a number of tasks, including governance, information sharing, and decision making. However these forms of collective deliberation can often result in biased outcomes. A prime example are Articles for Deletion (AfD) discussions on Wikipedia, which allow editors to gauge the notability of existing articles, and that, as prior work has suggested, may play a role in perpetuating the notorious gender gap of Wikipedia. Prior attempts to address this question have been hampered by access to narrow observation windows, reliance on limited subsets of both biographies and editorial outcomes, and by potential confounding factors. To address these limitations, here we adopt a competing risk survival framework to fully situate biographical AfD discussions within the full editorial cycle of Wikipedia content. We find that biographies of women are nominated for deletion faster than those of men, despite editors taking longer to reach a consensus for deletion of women, even after controlling for the size of the discussion. Furthermore, we find that AfDs about historical figures show a strong tendency to result into the redirecting or merging of the biography under discussion into other encyclopedic entries, and that there is a striking gender asymmetry: biographies of women are redirected or merged into biographies of men more often than the other way round. Our study provides a more complete picture of the role of AfD in the gender gap of Wikipedia, with implications for the governance of the open knowledge infrastructure of the web.},
journal = {Proc. ACM Hum.-Comput. Interact.},
month = oct,
articleno = {CSCW482},
numpages = {29},
keywords = {article for deletion, collective deliberation, competing risks analysis, gender gap, wikipedia}
}

--------



