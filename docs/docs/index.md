# Description

Web communities depend on open forums for tasks like governance, information sharing, and decision-making, but these can yield biased outcomes. In Wikipedia's Articles for Deletion (AfD) discussions, biographies of women face faster deletion nominations, longer consensus times, and are more often redirected or merged into men’s biographies, highlighting gender asymmetries. Our study applies both survival analysis and a competing risk framework to examine the role of Articles for Deletion (AfD) in Wikipedia’s gender gap, offering insights for the governance of open knowledge platforms. Our paper describing this work is available on [arXiv](https://doi.org/10.48550/arXiv.2411.04340).

# Manual

This manual outlines the step-by-step process to collect, process, and analyze the lifecycle of biographies in Wikipedia, focusing on their creation and nomination in Article for Deletion (AfD). Follow these steps carefully for successful execution.

## Step 1: Collect List of Biographies
- Use [Quarry](https://meta.wikimedia.org/wiki/Research:Quarry), a public querying interface for live replica SQL databases for public Wikimedia Wikis, to retrieve biographical articles.
- Choose Database: enwiki_p or enwiki. Then, focus on articles from WikiProject “Biography,” which exclusively covers actual human beings, excluding fictional or non-human entities.
- SQL Query in Quarry:
```
SELECT article.page_title, rev_timestamp
FROM page
INNER JOIN page article
ON page.page_title = article.page_title
INNER JOIN revision
ON revision.rev_page = page.page_id
INNER JOIN categorylinks
ON cl_from = page.page_id
AND categorylinks.cl_to = "WikiProject_Biography_articles"
WHERE page.page_namespace = 1
AND article.page_namespace = 0
AND rev_parent_id = 0;
```

## Step 2: Identify Articles Nominated for Deletion in AfD
- Use [Quarry](https://meta.wikimedia.org/wiki/Research:Quarry) to retrieve nominated articles of all categories on AfD deliberations.
- Extract timestamps for AfD nominations.
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
- Save the results in the file "raw/Quarry/All_AfDs_3_Nov_2.csv."

## Step 3: Retrieve Creation Dates
#### For Entries Without Deletion Nominations:
- Use the [Wikipedia REST API](https://www.mediawiki.org/wiki/API:Query) to extract the creation dates of the articles from which are recieved from Step 1.
- Save the results in the file "raw/Quarry/Wikiproject_Bio2_creation_dates.csv."

#### For Entries With Deletion Nominations:
- Apply the same API method for kept or redirected articles.
- For deleted or merged articles whose creation dates cannot be found in the page table, follow step 4.

## Step 4: Extract Creation dates of Deleted or Merged Articles
- Query the archive table from [Quarry](https://meta.wikimedia.org/wiki/Research:Quarry) to extract the original creation dates of the deleted or merged entries.
- SQL Query in Quarry:
```
SELECT ar_title, ar_timestamp
FROM archive
WHERE ar_namespace = 0
AND ar_parent_id = 0;
```
- Save the data in the file "raw/Quarry/Archive_all_8_Nov.csv."

## Step 5: Extract Vital Information of Biography Subjects
#### Use SPARQL for Bulk Data Extraction:
- Go to [SPARQL Query Editor](https://wikidata.demo.openlinksw.com/sparql).
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
- Set execution timeout at least 120000 milliseconds. 
- Adjust Offset for batch processing. Increase the Offset by 1000000 for each query execution and run until the offset reaches 20000000.
#### Refine Data Using [Wikidata Client API](https://www.mediawiki.org/wiki/Wikibase/API):
- Validate or enrich missing attributes (gender, birth, death dates). Save the final dataset in "raw/Wikidata/wikidata_page_id_all2_merged.csv."
- To filter out AfDs of non-biographical content, parse the entry title from the title of the AfD discussion page. Then, use the API to extract attributes (instance of, gender, birth, death dates). Select the data with the “Human” attributes and save the dataset in "raw/Wikidata/Wikidata_Gender_Birth_Death_nominated.csv."

## Step 6: Extract Data from PetScan
[PetScan](https://meta.wikimedia.org/wiki/PetScan/en) is a tool that allows you to extract lists of Wikipedia pages based on specific criteria or categories. Follow the instructions below to collect data to categorize individuals into Living People, Contemporary Dead, and Historical People. This method will help you identify individuals for whom no vital information has been recorded in Wikidata. All of the following datasets are stored in folder "petscan".
#### Living People
To gather data for contemporary living people, follow these steps:

- Category Field: Set the category field to "Living people", which includes all Wikipedia articles about people who are still alive.
- Depth: Set the depth to 0. This ensures the query will only return pages directly in the "Living people" category, without including any subcategories.
- Combination: Select the Union combination option. This will combine all the pages that belong to the "Living people" category, ensuring you capture all relevant entries in this category.


This query will help you efficiently collect a list of individuals who are contemporary and alive.
#### Contemporary Dead and Historical People
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

### Step 7: Extract Conversation logs of the Article for Deletion
Parse the contents of each AfD discussion using [Wikipedia REST API](https://www.mediawiki.org/wiki/API:Query) to extract the title of the discussed entry, the rationale provided for nominating the entry, the final outcome of the deliberation, and the timestamp of the closing of the discussion.  Save the data in the file “raw/From_Begin_Afd_Conversation3.csv”.

