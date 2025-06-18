# Description

Web communities depend on open forums for tasks like governance, information sharing, and decision-making, but these can yield biased outcomes. In Wikipedia's Articles for Deletion (AfD) discussions, biographies of women face faster deletion nominations, longer consensus times, and are more often redirected or merged into men’s biographies, highlighting gender asymmetries. Our study applies both survival analysis and a competing risk framework to examine the role of Articles for Deletion (AfD) in Wikipedia’s gender gap, offering insights for the governance of open knowledge platforms. Our paper describing this work is available on [arXiv](https://doi.org/10.48550/arXiv.2411.04340).

# Manual

This manual outlines the step-by-step process to collect, process, and analyze the lifecycle of biographies in Wikipedia, focusing on their creation and nomination in Article for Deletion (AfD). Follow these steps carefully for successful execution.

## Step 1: Collect List of Biographies and their creation dates
### Step 1.1: Collect List of Biographies
#### English
- Use [Quarry](https://meta.wikimedia.org/wiki/Research:Quarry), a public querying interface for live replica SQL databases for public Wikimedia Wikis, to retrieve biographical articles.
  - Choose Database: enwiki_p or enwiki. Then, focus on articles from WikiProject “Biography,” which exclusively covers actual human beings, excluding fictional or non-human entities.
  - SQL Query in Quarry:
  ```
  SELECT article.page_title
  FROM page
  INNER JOIN page article
  ON page.page_title = article.page_title
  INNER JOIN categorylinks
  ON cl_from = page.page_id
  AND categorylinks.cl_to = "WikiProject_Biography_articles"
  WHERE page.page_namespace = 1
  AND article.page_namespace = 0

  ```
  Query and result snapshots are available on Quarry: https://quarry.wmcloud.org/query/93088.
  The running time: ~30 minutes.

#### Italian
  - [PetScan](https://meta.wikimedia.org/wiki/PetScan/en) is a tool that allows you to extract lists of Wikipedia pages based on specific criteria or categories. Follow [this link](https://petscan.wmcloud.org/?psid=33977428) to get access to the snapshots of the results in PetScan and download it directly. 


- Save the data in file "interim/Wikiproject_Bio.csv".

### Step 1.2: Retrieve Creation Dates
- Use the [Wikipedia REST API](https://www.mediawiki.org/wiki/API:Query) to extract the creation dates of the articles from which are recieved from Step 1.1.
```
  make creation_date
```
- Save the results in the file "raw/Quarry/Wikiproject_Bio2_creation_dates.csv."

## Step 2: Identify Articles Nominated for Deletion in AfD
- Use [Quarry](https://meta.wikimedia.org/wiki/Research:Quarry) to retrieve nominated articles of all categories on AfD deliberations.
- Extract timestamps for AfD nominations.
### English
  - Select "enwiki_p" in the database field.
  - SQL Query in Quarry:
  ```
  SELECT TRIM('Articles_for_deletion/' FROM page_title) AS Entry, rev_timestamp
  FROM revision
  JOIN page
  ON revision.rev_page = page.page_id
  WHERE page_title LIKE '%Articles_for_deletion%'
  AND page_title NOT LIKE 'Articles_for_deletion/Log/%'
  AND page_namespace = 4
  AND page_is_redirect = 0
  AND rev_parent_id = 0;
  ```
  Query and result snapshots are available on Quarry: https://quarry.wmcloud.org/query/93107. The running time: ~16 minutes

### Italian
  - Select "itwiki_p" in the database field.
  - SQL Query in Quarry:
  ```
  SELECT TRIM('Pagine_da_cancellare/' from page_title) as Entry, rev_timestamp
  FROM revision
  JOIN page ON revision.rev_page = page.page_id
  WHERE page_title LIKE '%Pagine_da_cancellare%'
  AND	 page_title NOT LIKE 'Pagine_da_cancellare/Log/%'
  AND	 page_title NOT LIKE 'Pagine_da_cancellare/Conta/%'
  AND page_namespace = 4
  AND page_is_redirect = 0
  AND rev_parent_id = 0;
  ```
  Query and result snapshots are available on Quarry: https://quarry.wmcloud.org/query/93203. The running time: ~76.42 seconds

- Save the results in the file "raw/Quarry/All_AfDs_3_Nov_2.csv." Recommendation: Save the date of the retrieval of the data in the name of the file and edit it accordingly in python script "survival/of/notabilty/dataset.py". 


## Step 3: Extract Vital Information of Biography Subjects
Follow the instructions below to collect vital information of the subjects of biographies to categorize individuals into Living People, Contemporary Dead, and Historical People.

#### Step 3.1: Use SPARQL for Bulk Data Extraction:
- Go to one of following public endpoints of Wikidata ([According to this paper](https://zenodo.org/records/7185889)):
  1. [Qlever](https://qlever.cs.uni-freiburg.de/wikidata). (Smoothest, no time limit).
  2. [Virtuoso](https://wikidata.demo.openlinksw.com/sparql). (Smooth, no time limit, need to tweak the execution timeout option)
  3. [Wikimedia/Blazegraph](https://query.wikidata.org/) (Time limit error will occur. Recommend to use pagination method.)
- Retrieve attributes like gender, date of birth, and date of death for human subjects (Q5 items).
- SPARQL Query:
```
SELECT ?sitelink ?item ?label ?Gender ?birth ?death
WHERE {
  ?item wdt:P31 wd:Q5;       # Instance of: Human
        wdt:P21 ?Gen.        # Gender

  ?sitelink schema:about ?item;
           schema:isPartOf <https://en.wikipedia.org/>.

  OPTIONAL {
    ?item rdfs:label ?label FILTER (lang(?label) = "en").  # Fetch English label
  }
  OPTIONAL {
    ?Gen rdfs:label ?Gender FILTER (lang(?Gender) = "en"). # Fetch English gender label
  }
  OPTIONAL {
    ?item wdt:P569 ?birth.    # Fetch the birth date if it exists
  }
  OPTIONAL {
    ?item wdt:P570 ?death.    # Fetch the death date if it exists
  }
}
LIMIT 1000000 OFFSET 0
```
- For option 2, set execution timeout at least 120000 milliseconds. 
- Adjust Offset for batch processing. Increase the Offset by 1000000 for each query execution and run until the offset reaches 20000000.
- Save the data in file: "interim/wikidata_en.csv"

#### Step 3.2: Wikidata-Wikipedia Integration
The following script prepares a merged dataset linking Wikipedia article creation data, AfD nomination records, and Wikidata metadata (e.g., QIDs, gender, birth/death dates) for human subjects. It identifies which articles, for both nominated and not-nominated, have missing creation timestamps or metadata from Wikidata, and outputs cleaned CSVs for further analysis.

```
python survival_of_notability/prepare_wikidata.py 

```

Outputs produced:

- raw/Wikidata/wikidata_page_id_all2_merged.csv: Articles with both Wikidata (gender/birth/death/QID) and creation date data

- raw/Wikidata/Wikidata_Gender_Birth_Death_nominated.csv: Nominated articles with gender/birth/death/QID

- interim/need_creation.csv: Articles with Wikidata but missing creation metadata

- interim/need_wikidata.csv: Articles missing Wikidata info or unmatched in nomination list

#### Step 3.3: Wikidata Metadata Enrichment and Missing Creation Detection
By using [Wikidata Client API](https://www.mediawiki.org/wiki/Wikibase/API), this script enriches Wikipedia page titles with Wikidata metadata—such as QIDs, gender, birth/death dates, and instance types—specifically focusing on identifying human subjects. It attempts to resolve missing entries by querying Wikidata directly using fallback language sitelinks when needed. The script filters for human instances (e.g., biographies), cleans up malformed page titles, and writes structured information to appropriate output files. It also checks whether the nominated articles are missing creation timestamps and logs those entries for further processing.

```
python survival_of_notability/get_needed_wikidata.py 

```

Outputs produced:

- raw/Wikidata/wikidata_page_id_all2_merged.csv: Metadata for articles successfully matched to Wikidata and with known page IDs

- raw/Wikidata/Wikidata_Gender_Birth_Death_nominated.csv: Metadata for nominated articles that couldn't be linked to existing page IDs

- interim/need_creation.csv: Articles with Wikidata metadata but missing creation timestamps in the existing dataset

#### Step 3.4: Wikipedia Page Creation Timestamp
This script retrieves the creation timestamps for Wikipedia articles with missing creation dates. It uses the [Wikipedia REST API](https://www.mediawiki.org/wiki/API:Query) to extract the oldest revision (i.e., article creation date) for each entry. The output is a cleaned and structured dataset with page ID, title, human-readable title, and creation time, used to fill missing metadata for previously unmatched articles.

```
python survival_of_notability/get_needed_creation_dates.py 

```

Outputs produced:

- raw/Quarry/Wikiproject_Bio2_creation_dates.csv: Contains page ID, original and readable page titles, and creation timestamps for articles listed in need_creation.csv.


## Step 4: Extract Creation dates of Deleted or Merged Articles
For articles (specially deleted or merged) whose creation dates cannot be found in the page table via step 1 and 3 using Wikipedia API, follow this step:
- Query the archive table from [Quarry](https://meta.wikimedia.org/wiki/Research:Quarry) to extract the original creation dates of the deleted or merged entries.

- For English, select 
- SQL Query in Quarry:
```
SELECT ar_title, ar_timestamp
FROM archive
WHERE ar_namespace = 0
AND ar_parent_id = 0;
```
- Save the data in the file "raw/Quarry/Archive_all_8_Nov.csv."


## Step 5: Extract Data from PetScan
Follow the instructions below to collect data to categorize individuals into Living People, Contemporary Dead, and Historical People, and will help you identify individuals for whom no vital information has been recorded in Wikidata (in Step 4). [PetScan](https://meta.wikimedia.org/wiki/PetScan/en) is a tool that allows you to extract lists of Wikipedia pages based on specific criteria or categories. All of the following datasets are stored in folder "petscan".

### Living People
This method will help you efficiently collect a list of individuals who are contemporary and alive. To gather data for contemporary living people, follow these steps:
#### English
  - Language Field: en
  - Category Field: Set the category field to "Living people".
  - The snapshot of the result: https://petscan.wmcloud.org/?psid=34572731
#### Italian
  - Language Field: it
  - Category Field: Set the category field to "Persone viventi".
  - The snapshot of the result: https://petscan.wmcloud.org/?psid=34572788

- Depth: Set the depth to 0. This ensures the query will only return pages directly in the "Living people" category, without including any subcategories.
- Combination: Select the Union combination option. This will combine all the pages that belong to the "Living people" category, ensuring you capture all relevant entries in this category.


### Contemporary Dead and Historical People
To classify Contemporary Dead and Historical People, use a heuristic approach based on the "People by millennium" category. This category tree organizes individuals based on their birth or death period, including subcategories like deaths or births by decades, centuries, and millennia.
Follow these steps:
- Category Field: Set the category field to "People by millennium". This category includes individuals grouped by their birth or death in different time periods, such as the 20th century or 21st century.


- Depth: Set the depth to 10. This ensures the query captures not only the main categories but also deeper subcategories, such as births and deaths by decades or centuries within a millennium.


- Combination: Select the Union combination option. This will include both the "People by millennium" category and its subcategories, capturing data on people from various time periods, including those born or died in different decades, centuries, and millennia.


- Negative Categories: To refine your results and exclude certain individuals, use negative categories. For example, if you want to collect all people born in the 20th century but exclude those born in 1907, 1908, and 1909, you would:


    - Include the category "20th-century births".
    - Add "1907 births", "1908 births", and "1909 births" to the negative categories field. This ensures that those specific years are excluded from your query results.

- Folder Organization: 
    - Create a folder named "PetScan" to save all the datasets.
    - Ensure that each dataset is named appropriately based on its contents. For example:
    - "Living_people" for the dataset of living people.
    - "dead_people_from_1900_to_1977" for the dataset of deceased people from 1900 to 1977.
Using PetScan in this way, you can efficiently gather and filter data based on category membership and time periods, allowing you to categorize individuals as living, contemporary dead, or historical people.

## Step 6: Extract Conversation logs of the Article for Deletion
Parse the contents of each AfD discussion using [Wikipedia REST API](https://www.mediawiki.org/wiki/API:Query) to extract the title of the discussed entry, the rationale provided for nominating the entry, the final outcome of the deliberation, and the timestamp of the closing of the discussion.  Save the data in the file “raw/From_Begin_Afd_Conversation3.csv”.

```
python survival_of_notability/AfD_Parse.py 

```

