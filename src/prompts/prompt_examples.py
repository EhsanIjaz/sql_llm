



example_1 = f"""Example 1:
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
"""

example_2 = f"""Example 2:
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
"""

example_3 = """Example 3:
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
"""

example_4 = f"""Example 4:
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
"""

example_5 = f"""Example 5:
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
"""

example_6 = f"""Example 6:
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
"""





two_month_examples = """

Example 1:
Question: "Compare sales between January and February 2025 at city level."
[SQL]
SELECT region, city,
  SUM(CASE WHEN month = 1 AND year = 2025 THEN sales ELSE 0 END) AS sales_jan,
  SUM(CASE WHEN month = 2 AND year = 2025 THEN sales ELSE 0 END) AS sales_feb
FROM llm_df
WHERE year = 2025 AND month IN (1, 2)
GROUP BY region, city
ORDER BY sales_feb DESC
LIMIT 10;
[/SQL]

Example 2:
Question: "Compare MRO for distributors between July and August 2024."
[SQL]
SELECT distributor,
  SUM(CASE WHEN month = 7 AND year = 2024 THEN mro ELSE 0 END) AS mro_jul,
  SUM(CASE WHEN month = 8 AND year = 2024 THEN mro ELSE 0 END) AS mro_aug
FROM llm_df
WHERE year = 2024 AND month IN (7, 8)
GROUP BY distributor
ORDER BY mro_aug DESC
LIMIT 5;
[/SQL]

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

"""

# --- Three month examples ---
three_month_examples = """
Example 1:
Question: "Compare target values for March, April, and May 2024 across regions."
[SQL]
SELECT region,
  SUM(CASE WHEN month = 3 AND year = 2024 THEN target ELSE 0 END) AS target_mar,
  SUM(CASE WHEN month = 4 AND year = 2024 THEN target ELSE 0 END) AS target_apr,
  SUM(CASE WHEN month = 5 AND year = 2024 THEN target ELSE 0 END) AS target_may
FROM llm_df
WHERE year = 2024 AND month IN (3, 4, 5)
GROUP BY region
ORDER BY target_may DESC
LIMIT 10;
[/SQL]

Example 2:
Question: "Show stockout comparison for distributors in Oct, Nov, and Dec 2024."
[SQL]
SELECT distributor,
  COUNT(CASE WHEN month = 10 AND year = 2024 AND stockout > 0 THEN 1 END) AS stockout_oct,
  COUNT(CASE WHEN month = 11 AND year = 2024 AND stockout > 0 THEN 1 END) AS stockout_nov,
  COUNT(CASE WHEN month = 12 AND year = 2024 AND stockout > 0 THEN 1 END) AS stockout_dec
FROM llm_df
WHERE year = 2024 AND month IN (10, 11, 12)
GROUP BY distributor
ORDER BY stockout_dec DESC
LIMIT 5;
[/SQL]

Example 3:
Question: "Compare productivity percentage across July, Aug, and Sep 2025 at city level."
[SQL]
SELECT city,
  COUNT(DISTINCT CASE WHEN month = 7 AND year = 2025 AND productivity = 1 THEN customer END) * 100.0 / NULLIF(COUNT(DISTINCT CASE WHEN month = 7 AND year = 2025 THEN customer END), 0) AS productive_pct_jul,
  COUNT(DISTINCT CASE WHEN month = 8 AND year = 2025 AND productivity = 1 THEN customer END) * 100.0 / NULLIF(COUNT(DISTINCT CASE WHEN month = 8 AND year = 2025 THEN customer END), 0) AS productive_pct_aug,
  COUNT(DISTINCT CASE WHEN month = 9 AND year = 2025 AND productivity = 1 THEN customer END) * 100.0 / NULLIF(COUNT(DISTINCT CASE WHEN month = 9 AND year = 2025 THEN customer END), 0) AS productive_pct_sep
FROM llm_df
WHERE year = 2025 AND month IN (7, 8, 9)
GROUP BY city
ORDER BY productive_pct_sep DESC
LIMIT 10;
[/SQL]"""



filter_two_examples = """
Example 1:
[SQL]
SELECT distributor,
  COUNT(DISTINCT CASE WHEN month = 3 AND year = 2025 AND stockout = 1 THEN customer END) AS stockout_shops_mar,
  COUNT(DISTINCT CASE WHEN month = 3 AND year = 2025 AND stockout = 0 THEN customer END) AS not_stockout_shops_mar,
  COUNT(DISTINCT CASE WHEN month = 3 AND year = 2025 THEN customer END) AS total_shops_mar,
  (COUNT(DISTINCT CASE WHEN month = 3 AND year = 2025 AND stockout = 1 THEN customer END) * 100.0 /
   NULLIF(COUNT(DISTINCT CASE WHEN month = 3 AND year = 2025 THEN customer END), 0)) AS stockout_pct_mar,

  COUNT(DISTINCT CASE WHEN month = 4 AND year = 2025 AND stockout = 1 THEN customer END) AS stockout_shops_apr,
  COUNT(DISTINCT CASE WHEN month = 4 AND year = 2025 AND stockout = 0 THEN customer END) AS not_stockout_shops_apr,
  COUNT(DISTINCT CASE WHEN month = 4 AND year = 2025 THEN customer END) AS total_shops_apr,
  (COUNT(DISTINCT CASE WHEN month = 4 AND year = 2025 AND stockout = 1 THEN customer END) * 100.0 /
   NULLIF(COUNT(DISTINCT CASE WHEN month = 4 AND year = 2025 THEN customer END), 0)) AS stockout_pct_apr

FROM llm_df
WHERE year = 2025 AND month IN (3, 4)
GROUP BY distributor
ORDER BY stockout_pct_apr DESC;
[/SQL]

Example 2:
[SQL]
SELECT city,
  COUNT(DISTINCT CASE WHEN month = 7 AND year = 2025 AND stockout = 1 THEN customer END) AS stockout_shops_jul,
  COUNT(DISTINCT CASE WHEN month = 7 AND year = 2025 AND stockout = 0 THEN customer END) AS not_stockout_shops_jul,
  COUNT(DISTINCT CASE WHEN month = 7 AND year = 2025 THEN customer END) AS total_shops_jul,
  (COUNT(DISTINCT CASE WHEN month = 7 AND year = 2025 AND stockout = 1 THEN customer END) * 100.0 /
   NULLIF(COUNT(DISTINCT CASE WHEN month = 7 AND year = 2025 THEN customer END), 0)) AS stockout_pct_jul,

  COUNT(DISTINCT CASE WHEN month = 8 AND year = 2025 AND stockout = 1 THEN customer END) AS stockout_shops_aug,
  COUNT(DISTINCT CASE WHEN month = 8 AND year = 2025 AND stockout = 0 THEN customer END) AS not_stockout_shops_aug,
  COUNT(DISTINCT CASE WHEN month = 8 AND year = 2025 THEN customer END) AS total_shops_aug,
  (COUNT(DISTINCT CASE WHEN month = 8 AND year = 2025 AND stockout = 1 THEN customer END) * 100.0 /
   NULLIF(COUNT(DISTINCT CASE WHEN month = 8 AND year = 2025 THEN customer END), 0)) AS stockout_pct_aug

FROM llm_df
WHERE year = 2025 AND month IN (7, 8)
GROUP BY city
ORDER BY stockout_pct_aug DESC;
[/SQL]
"""


filter_three_examples = """
Example 1:
[SQL]
SELECT region,
  COUNT(DISTINCT CASE WHEN month = 1 AND year = 2025 AND stockout = 1 THEN customer END) AS stockout_shops_jan,
  COUNT(DISTINCT CASE WHEN month = 1 AND year = 2025 THEN customer END) AS total_shops_jan,
  (COUNT(DISTINCT CASE WHEN month = 1 AND year = 2025 AND stockout = 1 THEN customer END) * 100.0 /
   NULLIF(COUNT(DISTINCT CASE WHEN month = 1 AND year = 2025 THEN customer END), 0)) AS stockout_pct_jan,

  COUNT(DISTINCT CASE WHEN month = 2 AND year = 2025 AND stockout = 1 THEN customer END) AS stockout_shops_feb,
  COUNT(DISTINCT CASE WHEN month = 2 AND year = 2025 THEN customer END) AS total_shops_feb,
  (COUNT(DISTINCT CASE WHEN month = 2 AND year = 2025 AND stockout = 1 THEN customer END) * 100.0 /
   NULLIF(COUNT(DISTINCT CASE WHEN month = 2 AND year = 2025 THEN customer END), 0)) AS stockout_pct_feb,

  COUNT(DISTINCT CASE WHEN month = 3 AND year = 2025 AND stockout = 1 THEN customer END) AS stockout_shops_mar,
  COUNT(DISTINCT CASE WHEN month = 3 AND year = 2025 THEN customer END) AS total_shops_mar,
  (COUNT(DISTINCT CASE WHEN month = 3 AND year = 2025 AND stockout = 1 THEN customer END) * 100.0 /
   NULLIF(COUNT(DISTINCT CASE WHEN month = 3 AND year = 2025 THEN customer END), 0)) AS stockout_pct_mar

FROM llm_df
WHERE year = 2025 AND month IN (1, 2, 3)
GROUP BY region
ORDER BY stockout_pct_mar DESC;
[/SQL]

Example 2:
[SQL]
SELECT territory,
  COUNT(DISTINCT CASE WHEN month = 10 AND year = 2025 AND stockout = 1 THEN customer END) AS stockout_shops_oct,
  COUNT(DISTINCT CASE WHEN month = 10 AND year = 2025 THEN customer END) AS total_shops_oct,
  (COUNT(DISTINCT CASE WHEN month = 10 AND year = 2025 AND stockout = 1 THEN customer END) * 100.0 /
   NULLIF(COUNT(DISTINCT CASE WHEN month = 10 AND year = 2025 THEN customer END), 0)) AS stockout_pct_oct,

  COUNT(DISTINCT CASE WHEN month = 11 AND year = 2025 AND stockout = 1 THEN customer END) AS stockout_shops_nov,
  COUNT(DISTINCT CASE WHEN month = 11 AND year = 2025 THEN customer END) AS total_shops_nov,
  (COUNT(DISTINCT CASE WHEN month = 11 AND year = 2025 AND stockout = 1 THEN customer END) * 100.0 /
   NULLIF(COUNT(DISTINCT CASE WHEN month = 11 AND year = 2025 THEN customer END), 0)) AS stockout_pct_nov,

  COUNT(DISTINCT CASE WHEN month = 12 AND year = 2025 AND stockout = 1 THEN customer END) AS stockout_shops_dec,
  COUNT(DISTINCT CASE WHEN month = 12 AND year = 2025 THEN customer END) AS total_shops_dec,
  (COUNT(DISTINCT CASE WHEN month = 12 AND year = 2025 AND stockout = 1 THEN customer END) * 100.0 /
   NULLIF(COUNT(DISTINCT CASE WHEN month = 12 AND year = 2025 THEN customer END), 0)) AS stockout_pct_dec

FROM llm_df
WHERE year = 2025 AND month IN (10, 11, 12)
GROUP BY territory
ORDER BY stockout_pct_dec DESC;
[/SQL]
"""