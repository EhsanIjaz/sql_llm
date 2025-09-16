prompt = """

### Task
Generate a SQL query to answer [QUESTION]{question}[/QUESTION].
Follow ALL rules below EXACTLY. Deviations will cause errors.
Use SUM() instead of MAX() for aggregation.

**Rules***
- Always filter by `month` and `year`.  
  • If year is missing, use {latest_year}.
- Use SUM() for `sales`, `mto`, `mro`, and `target` unless COUNT(), MAX(), MIN(), or AVG() is explicitly asked.  
- Do not use TO_DATE, CAST, or EXTRACT for dates.
- For ranking questions, always add ORDER BY with LIMIT (default 1 if not mentioned).
- Interpret keywords:  
  • "worst" → lowest (ORDER BY ... ASC)  
  • "top", "best", "highest" → ORDER BY ... DESC  
- "growth", "expansion", "grow", "growing" → use growth logic as in Examples 2 & 3. 
- If the schema cannot answer the question, return "I do not know."
- The database contains only `llm_df` with monthly customer data.

### Synonyms
- `mro`: Missed Revenue Opportunity → Potential Improvement, Missed Gain, Untapped Potential, Lost Earnings and related words
- `mto`: Missed Target Opportunity → Sales Shortfall, Performance Gap, Missed Goals, Highest Target Missed and related words
- `sales`: Contribution / Contributed and related words

### Database Schema
CREATE TABLE `llm_df` (
  `month` INTEGER,
  `year` INTEGER,
  `region` VARCHAR(50), -- Top-level region
  `city` VARCHAR(50), -- City within the region
  `area` VARCHAR(50), -- Area within the city
  `territory` VARCHAR(50), -- Territory within the area
  `distributor` VARCHAR(50), -- Distributor in the territory
  `route` VARCHAR(50), -- Route within the distributor
  `customer` VARCHAR(50), -- Unique customer ID
  `sku` VARCHAR(50), -- SKU identifier
  `brand` VARCHAR(50), -- Brand name
  `variant` VARCHAR(50), -- SKU variant
  `packtype` VARCHAR(50), -- SKU packtype
  `sales` DECIMAL, -- Net sales
  `primary sales` DECIMAL, -- Primary sales
  `target` DECIMAL, -- Target sales
  `mto` DECIMAL, -- Missed Target Opportunity
  `productivity` INTEGER, -- Customer productivity (1 = productive, 0 = not productive)
  `mro` DECIMAL, -- Missed Revenue Opportunity
  `unproductive_mro` INTEGER -- Unproductive MRO,
  `unassorted_mro` INTEGER -- Unassorted MRO,
  `stockout_mro` INTEGER -- Stockout MRO,
  `stockout` INTEGER, -- Customer Stockout (1 = stockout, 0 = no stockout)
  `assortment` INTEGER, -- Customer Assortment (1 = full, 0 = not available)
  PRIMARY KEY (`month`, `year`, `customer`, `sku`)
);

### Examples

Example 1:  
Question: "Which city has the highest sales in October?"  
```sql
SELECT region, city, 
  SUM(sales) AS total_sales
FROM llm_df
WHERE month = 10 AND year = 2024
GROUP BY region, city
ORDER BY total_sales DESC
LIMIT 1;

Example 2:
Question: "what the growth of city lahore?"
```sql
SELECT region, city,
  SUM(CASE WHEN month = 11 THEN sales ELSE 0 END) AS sales_current_month, 
  SUM(CASE WHEN month = 10 THEN sales ELSE 0 END) AS sales_previous_month,
  ((SUM(CASE WHEN month = 11 THEN sales ELSE 0 END) - SUM(CASE WHEN month = 10 THEN sales ELSE 0 END)) 
  / NULLIF(SUM(CASE WHEN month = 10 THEN sales ELSE 0 END), 0)) * 100 AS sales_growth_percentage
FROM llm_df
WHERE city = 'lahore'
  AND year = 2024
  AND month IN (10, 11)
GROUP BY region, city;

Example 3:
Question: "Show me the 5 territories that have experienced the most significant growth."
```sql
SELECT region, city, area, territory,
  SUM(CASE WHEN month = 11 THEN sales ELSE 0 END) AS sales_current_month, 
  SUM(CASE WHEN month = 10 THEN sales ELSE 0 END) AS sales_previous_month,
  (((SUM(CASE WHEN month = 11 THEN sales ELSE 0 END) - SUM(CASE WHEN month = 10 THEN sales ELSE 0 END)) 
  / NULLIF(SUM(CASE WHEN month = 10 THEN sales ELSE 0 END), 0)) * 100) AS sales_growth_percentage
FROM llm_df
WHERE year = 2024 AND month IN (10, 11)
GROUP BY region, city, area, territory
ORDER BY sales_growth_percentage DESC
LIMIT 5;

Example 4:
Question : Which distributor had the highest total MTO in the 'South A' region in December 2024?
```sql
SELECT region, city, area, territory, distributor,
  SUM(mto) AS total_mto
FROM llm_df
WHERE region = 'south a'
  AND month = 12
  AND year = 2024
GROUP BY region, city, area, territory, distributor
ORDER BY total_mto DESC
LIMIT 1;

### Answer
Given the database schema, here is the SQL query that answers [QUESTION]{question}[/QUESTION]:
[SQL]

Important formatting rule:  
- Return the SQL **inside [SQL] … [/SQL] tags only**.  
- Do NOT use Markdown fences (```sql … ```).  
- Do NOT add explanations outside the tags. 
"""


prompt_2 = """

### Task
Generate a SQL query to answer [QUESTION]{question}[/QUESTION].
Follow ALL rules below EXACTLY. Deviations will cause errors.

**Rules**
- Always filter queries by month and year if not specified in the question.
- If year is not mentioned, use the latest year ({latest_year}).
- For `productivity`, `assortment`, or `stockout`, always use COUNT() (not SUM()).
- The database contains only `llm_df` with monthly customer data.
- Avoid `TO_DATE`, `CAST`, or `EXTRACT` functions for dates.
- Interpret keywords:  
  • "worst" → lowest (ORDER BY ... ASC)  
  • "top", "best", "highest" → ORDER BY ... DESC 
- Always enforce a LIMIT, defaulting to 1.
- Only include attributes and metrics that are relevant to the user’s question. 
  Do not add extra columns or percentages unless explicitly required.

### Database Schema
CREATE TABLE `llm_df` (
  `month` INTEGER,
  `year` INTEGER,
  `region` VARCHAR(50), -- Top-level region
  `city` VARCHAR(50), -- City within the region
  `area` VARCHAR(50), -- Area within the city
  `territory` VARCHAR(50), -- Territory within the area
  `distributor` VARCHAR(50), -- Distributor in the territory
  `route` VARCHAR(50), -- Route within the distributor
  `customer` VARCHAR(50), -- Unique customer ID
  `sku` VARCHAR(50), -- SKU identifier
  `brand` VARCHAR(50), -- Brand name
  `variant` VARCHAR(50), -- SKU variant
  `packtype` VARCHAR(50), -- SKU packtype
  `sales` DECIMAL, -- Net sales
  `primary sales` DECIMAL, -- Primary sales
  `target` DECIMAL, -- Target sales
  `mto` DECIMAL, -- Missed Target Opportunity
  `productivity` INTEGER, -- Customer productivity (1 = productive, 0 = not productive)
  `mro` DECIMAL, -- Missed Revenue Opportunity
  `unproductive_mro` INTEGER -- Unproductive MRO,
  `unassorted_mro` INTEGER -- Unassorted MRO,
  `stockout_mro` INTEGER -- Stockout MRO,
  `stockout` INTEGER, -- Customer Stockout (1 = stockout, 0 = no stockout)
  `assortment` INTEGER, -- Customer Assortment (1 = full, 0 = not available)
  PRIMARY KEY (`month`, `year`, `customer`, `sku`)
);

### Examples
(The following are illustrative. Use only the patterns that match the user’s question.)

Example 1:
Question: Which distributor had the lowest productivity percentage in Lahore city in September?
```sql
SELECT region, city, area, territory, distributor,
  COUNT(DISTINCT CASE WHEN month = 9 AND year = 2024 AND productivity = 1 THEN customer END) AS productive_shops,
  COUNT(DISTINCT CASE WHEN month = 9 AND year = 2024 AND productivity = 0 THEN customer END) AS un_productive_shops,
  COUNT(DISTINCT customer) AS total_shops,
  (COUNT(DISTINCT CASE WHEN month = 9 AND year = 2024 AND productivity = 1 THEN customer END) * 100.0 / COUNT(DISTINCT customer)) AS productive_percentage,
  (COUNT(DISTINCT CASE WHEN month = 9 AND year = 2024 AND productivity = 0 THEN customer END) * 100.0 / COUNT(DISTINCT customer)) AS un_productive_percentage
FROM llm_df
WHERE city = 'lahore'
GROUP BY region, city, area, territory, distributor
ORDER BY productive_percentage ASC
LIMIT 1;

Example 2:
Question: Which area had the highest unproductivity percentage in February 2024?
sql```
SELECT region, city, area,
  COUNT(DISTINCT CASE WHEN month = 2 AND year = 2024 AND productivity = 1 THEN customer END) AS productive_shops,
  COUNT(DISTINCT CASE WHEN month = 2 AND year = 2024 AND productivity = 0 THEN customer END) AS un_productive_shops,
  COUNT(DISTINCT customer) AS total_shops,
  (COUNT(DISTINCT CASE WHEN month = 2 AND year = 2024 AND productivity = 1 THEN customer END) * 100.0 / COUNT(DISTINCT customer)) AS productive_percentage,
  (COUNT(DISTINCT CASE WHEN month = 2 AND year = 2024 AND productivity = 0 THEN customer END) * 100.0 / COUNT(DISTINCT customer)) AS un_productive_percentage
FROM llm_df
GROUP BY region, city, area
ORDER BY un_productive_percentage DESC
LIMIT 1;

Example 3:
Question: Which distributor had the best assortment percentage in June 2024?
sql```
SELECT region, city, area, territory, distributor,
  COUNT(DISTINCT CASE WHEN month = 6 AND year = 2024 AND assortment = 1 THEN customer END) AS assorted_shops,
  COUNT(DISTINCT CASE WHEN month = 6 AND year = 2024 AND assortment = 0 THEN customer END) AS un_assorted_shops,
  COUNT(DISTINCT customer) AS total_shops,
  (COUNT(DISTINCT CASE WHEN month = 6 AND year = 2024 AND assortment = 1 THEN customer END) * 100.0 / COUNT(DISTINCT customer)) AS assorted_percentage,
  (COUNT(DISTINCT CASE WHEN month = 6 AND year = 2024 AND assortment = 0 THEN customer END) * 100.0 / COUNT(DISTINCT customer)) AS un_assorted_percentage
FROM llm_df
GROUP BY region, city, area, territory, distributor
ORDER BY assorted_percentage DESC
LIMIT 1;

Example 4:
Question: Which route had the worst unassorted percentage in September 2024?
sql```
SELECT region, city, area, territory, distributor, route,
  COUNT(DISTINCT CASE WHEN month = 9 AND year = 2024 AND assortment = 1 THEN customer END) AS assorted_shops,
  COUNT(DISTINCT CASE WHEN month = 9 AND year = 2024 AND assortment = 0 THEN customer END) AS un_assorted_shops,
  COUNT(DISTINCT customer) AS total_shops,
  (COUNT(DISTINCT CASE WHEN month = 9 AND year = 2024 AND assortment = 1 THEN customer END) * 100.0 / COUNT(DISTINCT customer)) AS assorted_percentage,
  (COUNT(DISTINCT CASE WHEN month = 9 AND year = 2024 AND assortment = 0 THEN customer END) * 100.0 / COUNT(DISTINCT customer)) AS un_assorted_percentage
FROM llm_df
GROUP BY region, city, area, territory, distributor, route
ORDER BY un_assorted_percentage DESC
LIMIT 1;

Example 5:
Question: Which distributor had the worst stockout percentage in May 2024?
sql```
SELECT region, city, area, territory, distributor,
  COUNT(DISTINCT CASE WHEN month = 5 AND year = 2024 AND stockout = 1 THEN customer END) AS stockout_shops,
  COUNT(DISTINCT CASE WHEN month = 5 AND year = 2024 AND stockout = 0 THEN customer END) AS not_stockout_shops,
  COUNT(DISTINCT customer) AS total_shops,
  (COUNT(DISTINCT CASE WHEN month = 5 AND year = 2024 AND stockout = 1 THEN customer END) * 100.0 / COUNT(DISTINCT customer)) AS stockout_percentage,
  (COUNT(DISTINCT CASE WHEN month = 5 AND year = 2024 AND stockout = 0 THEN customer END) * 100.0 / COUNT(DISTINCT customer)) AS not_stockout_percentage
FROM llm_df
GROUP BY region, city, area, territory, distributor
ORDER BY stockout_percentage DESC
LIMIT 1;

Example 6:
Question: Which area had the highest not-stockout percentage in April
sql```
SELECT region, city, area,
  COUNT(DISTINCT CASE WHEN month = 4 AND year = 2024 AND stockout = 1 THEN customer END) AS stockout_shops,
  COUNT(DISTINCT CASE WHEN month = 4 AND year = 2024 AND stockout = 0 THEN customer END) AS not_stockout_shops,
  COUNT(DISTINCT customer) AS total_shops,
  (COUNT(DISTINCT CASE WHEN month = 4 AND year = 2024 AND stockout = 1 THEN customer END) * 100.0 / COUNT(DISTINCT customer)) AS stockout_percentage,
  (COUNT(DISTINCT CASE WHEN month = 4 AND year = 2024 AND stockout = 0 THEN customer END) * 100.0 / COUNT(DISTINCT customer)) AS not_stockout_percentage
FROM llm_df
GROUP BY region, city, area
ORDER BY not_stockout_percentage DESC
LIMIT 1;

### Answer
Given the database schema and user’s request, generate the **most relevant SQL query**.  
Only include the **columns, calculations, and groupings directly required** to answer [QUESTION]{question}[/QUESTION].  

Important formatting rule:  
- Return the SQL **inside [SQL] … [/SQL] tags only**.  
- Do NOT use Markdown fences (```sql … ```).  
- Do NOT add explanations outside the tags. 
"""


prompt_comparison = """

### Task
Generate a SQL query to compare metrics across multiple months for [QUESTION]{question}[/QUESTION].
Follow ALL rules below EXACTLY. Deviations will cause errors.

**Rules**
- Always filter queries by `month` and `year`.  
- If year is missing, use {latest_year}.  
- For sales, mto, mro, target → use SUM().  
- For productivity, assortment, stockout → use COUNT() and percentages.  
- Do not use TO_DATE, CAST, or EXTRACT for dates.  
- Always show values for each requested month side-by-side in separate columns.  
- Comparison should work for 2 months, 3 months, or more (dynamically).  
- Include growth % only if explicitly asked.  
- Always group by the most relevant level (region, city, area, etc. depending on question).  
- Return results ordered logically (DESC for top/best, ASC for worst/lowest).  
- Always apply LIMIT (default 5 if not specified).  

### Database Schema
CREATE TABLE `llm_df` (
  `month` INTEGER,
  `year` INTEGER,
  `region` VARCHAR(50), -- Top-level region
  `city` VARCHAR(50), -- City within the region
  `area` VARCHAR(50), -- Area within the city
  `territory` VARCHAR(50), -- Territory within the area
  `distributor` VARCHAR(50), -- Distributor in the territory
  `route` VARCHAR(50), -- Route within the distributor
  `customer` VARCHAR(50), -- Unique customer ID
  `sku` VARCHAR(50), -- SKU identifier
  `brand` VARCHAR(50), -- Brand name
  `variant` VARCHAR(50), -- SKU variant
  `packtype` VARCHAR(50), -- SKU packtype
  `sales` DECIMAL, -- Net sales
  `primary sales` DECIMAL, -- Primary sales
  `target` DECIMAL, -- Target sales
  `mto` DECIMAL, -- Missed Target Opportunity
  `productivity` INTEGER, -- Customer productivity (1 = productive, 0 = not productive)
  `mro` DECIMAL, -- Missed Revenue Opportunity
  `unproductive_mro` INTEGER -- Unproductive MRO,
  `unassorted_mro` INTEGER -- Unassorted MRO,
  `stockout_mro` INTEGER -- Stockout MRO,
  `stockout` INTEGER, -- Customer Stockout (1 = stockout, 0 = no stockout)
  `assortment` INTEGER, -- Customer Assortment (1 = full, 0 = not available)
  PRIMARY KEY (`month`, `year`, `customer`, `sku`)
);

### Examples

Example 1:  
Question: "Compare sales between September and October for all cities."  
[SQL]
SELECT region, city,
  SUM(CASE WHEN month = 9 AND year = 2024 THEN sales ELSE 0 END) AS sales_sep,
  SUM(CASE WHEN month = 10 AND year = 2024 THEN sales ELSE 0 END) AS sales_oct
FROM llm_df
WHERE year = 2024 AND month IN (9, 10)
GROUP BY region, city
ORDER BY sales_oct DESC
LIMIT 10;
[/SQL]

Example 2:  
Question: "Compare MTO for distributors across July, August, and September 2024."  
[SQL]
SELECT region, city, area, territory, distributor,
  SUM(CASE WHEN month = 7 AND year = 2024 THEN mto ELSE 0 END) AS mto_jul,
  SUM(CASE WHEN month = 8 AND year = 2024 THEN mto ELSE 0 END) AS mto_aug,
  SUM(CASE WHEN month = 9 AND year = 2024 THEN mto ELSE 0 END) AS mto_sep
FROM llm_df
WHERE year = 2024 AND month IN (7, 8, 9)
GROUP BY region, city, area, territory, distributor
ORDER BY mto_sep DESC
LIMIT 5;
[/SQL]

Example 3:  
Question: "Show me productivity comparison between Jan, Feb, and Mar 2024 at city level."  
[SQL]
SELECT region, city,
  COUNT(DISTINCT CASE WHEN month = 1 AND year = 2024 AND productivity = 1 THEN customer END) * 100.0 / NULLIF(COUNT(DISTINCT CASE WHEN month = 1 AND year = 2024 THEN customer END), 0) AS productive_pct_jan,
  COUNT(DISTINCT CASE WHEN month = 2 AND year = 2024 AND productivity = 1 THEN customer END) * 100.0 / NULLIF(COUNT(DISTINCT CASE WHEN month = 2 AND year = 2024 THEN customer END), 0) AS productive_pct_feb,
  COUNT(DISTINCT CASE WHEN month = 3 AND year = 2024 AND productivity = 1 THEN customer END) * 100.0 / NULLIF(COUNT(DISTINCT CASE WHEN month = 3 AND year = 2024 THEN customer END), 0) AS productive_pct_mar
FROM llm_df
WHERE year = 2024 AND month IN (1, 2, 3)
GROUP BY region, city
ORDER BY productive_pct_mar DESC
LIMIT 10;
[/SQL]

### Answer
Generate the SQL query that answers [QUESTION]{question}[/QUESTION] with month-by-month comparison.  
Always return SQL inside [SQL] … [/SQL] only.  
No markdown fences.  
No explanations.
"""
