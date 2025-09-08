prompt = """
### Task
Generate a SQL query to answer [QUESTION]{question}[/QUESTION].

### Instructions
- If the schema cannot answer the question, return "I do not know."
- The database contains `llm_df` table.Customer data is monthly. Current year is {latest_year} and latest month is {latest_month}.
- Do not use `TO_DATE`, `CAST`, or `EXTRACT` functions for dates. Instead, use `year` (integer) and `month` (1-12) directly in comparisons or filters.
- Always use `SUM()` for `sales` , `mto`,`mro` and `targets` columns unless the question explicitly asks for `AVG()`, `MIN()` or `MAX()`.  Never use `AVG()` by default.
- For "worst" always interpret them as 'lowest' values.
- Interpret "top" or "best" as ORDER BY ... DESC and "worst" as ORDER BY ... ASC
- IMPORTANT If question have `city`, SELECT region, city, GROUP BY region, city or question have `area`, SELECT region, city, area, GROUP BY region, city, area or question have "territory" `territory`, SELECT region, city, area, territory,  GROUP BY region, city, area, territory or question have `distributor`, SELECT region, city, area, territory, distributor, GROUP BY region, city, area, territory, distributor or question have `route`, SELECT region, city, area, territory, distributor, route GROUP BY region, city, area, territory, distributor, route
- For `mro` column (Missed Revenue Opportunity) Synonyms: "Potential Improvement," "Growth Opportunity," "Growth Potential," "Missed financial gain," "Untapped potential," "Lost earning potential."
- For `mto` column (Missed Target Opportunity) Synonyms: "Lowest sales achievement," "Sales shortfall," "Performance gap," "missed target," "Shortfall in goals." 
- For `sales` column Synonyms: "contribution," and "contributed" (in terms of sales).

- If {question} has to `productivity`, `assortment`, or `stockout` word then Always calculate the total number of unique customers without applying the month and year filter `COUNT(DISTINCT customer)` 
  - Always calculate numbers of unique customers for the required month (e.g., month october) where productivity = 1 `COUNT(DISTINCT CASE WHEN month = 10 AND year = 2024 AND productivity = 1 THEN customer END) * 100`, where stockout = 1 `COUNT(DISTINCT CASE WHEN month = 10 AND year = 2024 AND stockout = 1 THEN customer END) * 100`, where assortment = 1 `COUNT(DISTINCT CASE WHEN month = 10 AND year = 2024 AND assortment = 1 THEN customer END) * 100`

### Database Schema  
CREATE TABLE `llm_df` (  
  `month` INTEGER, -- Month (1-12)  
  `year` INTEGER, -- Year  
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
  `packtype` VARCHAR(50), -- SKU packaging type  
  `sales` DECIMAL, -- Net sales value  
  `primary sales` DECIMAL, -- Primary sales value  
  `target` DECIMAL, -- Target sales value  
  `mto` DECIMAL, -- Missing Target Opportunity  
  `productivity` INTEGER, -- Customer productivity (1 = productive, 0 = not productive)  
  `mro` DECIMAL, -- Missed Revenue Opportunity  
  `stockout` INTEGER, -- Customer Stockout status (1 = stockout, 0 = no stockout)  
  `assortment` INTEGER, -- Customer Assortment status (1 = full, 0 = not available)  
  PRIMARY KEY (`month`, `year`, `customer`, `sku`)  
); 

-- - `productivity`: 1 = productive, 0 = not productive.  
-- - `stockout`: 1 = stockout occurred, 0 = no stockout.  
-- - `assortment`: 1 = full assortment available, 0 = not available.


### Example
-For route:
Question: "Which route has the highest sales?"
```sql
SELECT region, city, area, territory, distributor, route, SUM(sales) AS total_sales
FROM llm_df
WHERE month = 12 AND year = 2024
GROUP BY region, city, area, territory, distributor, route;
ORDER BY total_sales DESC
LIMIT 1;
For city:
Question: "Which city has the highest sales in October?"
```sql
SELECT region, city, SUM(mro) AS total_mro
FROM llm_df
WHERE month = 9 AND year = 2024
GROUP BY region, city;
ORDER BY total_mro DESC
LIMIT 1;

Question:"Total sales of brand gala in each territory during the month of october?"
sql```
SELECT region, city, area, territory, SUM(sales) AS total_sales
FROM llm_df
WHERE brand = 'gala' AND month = 10 AND year = 2024
GROUP BY region, city, area, territory
ORDER BY total_sales DESC NULLS LAST;

Question:"Give me the stockout of the route D0475OB15 in month 10"
sql```
SELECT route,
       (COUNT(DISTINCT CASE WHEN month = 10 AND year = 2024 AND stockout = 1 THEN customer END) * 100.0 / COUNT(DISTINCT customer)) AS stockout_percentage
FROM llm_df
WHERE route = 'd0475ob15'
GROUP BY route;

Question:"Give me the assortment of the route D0475OB15 in month 10"
sql```
SELECT route,
       (COUNT(DISTINCT CASE WHEN month = 10 AND year = 2024 AND assortment = 1 THEN customer END) * 100.0 / COUNT(DISTINCT customer)) AS assortment_percentage
FROM llm_df
WHERE route = 'd0475ob15'
GROUP BY route;

Question:"what is th productivity of the distributor D0475 in month 10"
sql```
SELECT 
    (COUNT(DISTINCT CASE WHEN month = 10 AND year = 2024 AND productivity = 1 THEN customer END) * 100.0 /
     COUNT(DISTINCT customer)) AS productivity_percentage
FROM llm_df
WHERE distributor = 'd0475';


### Answer
Given the database schema, here is the SQL query that answers [QUESTION]{question}{latest_month}{latest_year}[/QUESTION]:
[SQL]



~~~~~~~
Question: "what is the total sales of brand sooper for distributor: 'D0371' in october?"
```sql
SELECT region, city, area, territory, distributor, SUM(sales) AS total_sales
FROM llm_df
WHERE brand = 'sooper'
  AND distributor = 'd0371'
  AND month = 10
  AND year = 2024
GROUP BY region, city, area, territory, distributor;
ORDER BY region DESC,
         city DESC,
         area DESC,
         territory DESC;"
`````



answer should always top to given region hierarchy

- IMPORTANT If question have `city`, SELECT region, city, GROUP BY region, city or question have `area`, SELECT region, city, area, GROUP BY region, city, area or question have "territory" `territory`, SELECT region, city, area, territory,  GROUP BY region, city, area, territory or question have `distributor`, SELECT region, city, area, territory, distributor, GROUP BY region, city, area, territory, distributor or question have `route`, SELECT region, city, area, territory, distributor, route GROUP BY region, city, area, territory, distributor, route
- For `mro` column (Missed Revenue Opportunity) Synonyms: "Potential Improvement," "Growth Opportunity," "Growth Potential," "Missed financial gain," "Untapped potential," "Lost earning potential."
- For `mto` column (Missed Target Opportunity) Synonyms: "Lowest sales achievement," "Sales shortfall," "Performance gap," "missed target," "Shortfall in goals." 
- For `sales` column Synonyms: "contribution," and "contributed" (in terms of sales).




- For geographic terms like `city`, `area`, or `territory`, always use the full hierarchy (`region`, `city`, `area`, `territory`, `distributor`, `route`) in the SELECT and GROUP BY clauses. Use this exact order.
  - Example hierarchy: 
    - For `city`: SELECT region, city GROUP BY region, city.
    - For `area`: SELECT region, city, area GROUP BY region, city, area.
    - For `territory`: SELECT region, city, area, territory GROUP BY region, city, area, territory.
    - For `distributor`: SELECT region, city, area, territory, distributor GROUP BY region, city, area, territory, distributor.
    - For `route`: SELECT region, city, area, territory, distributor, route GROUP BY region, city, area, territory, distributor, route.

- If the question involves geographic scope (e.g., city, area, or territory), always SELECT region, city, area, territory in that order and include GROUP BY region, city, area, territory.

"""


# - IMPORTANT If question have `city`, SELECT region, city, GROUP BY region, city or question have `area`, SELECT region, city, area, GROUP BY region, city, area or question have "territory" `territory`, SELECT region, city, area, territory,  GROUP BY region, city, area, territory or question have `distributor`, SELECT region, city, area, territory, distributor, GROUP BY region, city, area, territory, distributor or question have `route`, SELECT region, city, area, territory, distributor, route GROUP BY region, city, area, territory, distributor, route