sample_questions_prompt = """Generate exactly five insightful questions about the {platform} platform data. 
        The dataset schema is: {schema}
        
        Requirements:
        1. Questions should be specific to {platform} platform data
        2. Each question should reveal important business insights
        3. Every question should be in {language}
        4. Do not include code in the questions
        5. Format each question on a new line without numbering
        6. Questions should cover different aspects of the data (e.g., trends, patterns, comparisons)
        7. Make questions specific enough to be answerable with the available data
        8. The questions shouldn't be too simple or too complex
        9. EACH QUESTION MUST BE A SINGLE-PART QUESTION WITHOUT ANY ADDITIONAL SUB-QUESTIONS OR FACTORS
        10. Each question should fall into one of these categories:
            - Time-based analysis (trends, seasonality, growth)
            - Comparative analysis (between entities, periods, categories)
            - Performance metrics (KPIs, efficiency, effectiveness)
            - Anomaly detection (outliers, unusual patterns)
            - Predictive insights (forecasting, future trends)
        
        Question Templates (use these as inspiration but create unique questions):
        Time-based:
        - How has [metric] changed over [time period]?
        - What is the trend of [metric] across different [time periods]?
        - Which [time period] shows the highest/lowest [metric]?
        
        Comparative:
        - How does [metric] compare between [entity A] and [entity B]?
        - What is the difference in [metric] across different [categories]?
        - Which [entity] performs best/worst in terms of [metric]?
        
        Performance:
        - What is the average [metric] for [category]?
        - How efficient is [process] based on [metric]?
        - What is the success rate of [activity]?
        
        Anomaly:
        - Are there any unusual patterns in [metric]?
        - Which [entities] show significantly different [metric]?
        - What are the outliers in [metric] distribution?
        
        Predictive:
        - What is the expected [metric] for [future period]?
        - How might [metric] change based on current trends?
        - What factors influence [metric] the most?
        
        Good vs Bad Examples:
        Good (Single-part questions):
        - Which department has the highest rate of employee turnover?
        - What is the average response time for customer support tickets?
        - How has monthly revenue changed over the past year?
        
        Bad (Multi-part or complex questions):
        - Which department has the highest rate of employee turnover, and what factors contribute to this trend?
        - What is the average response time for customer support tickets, and how does it vary by priority level?
        - How has monthly revenue changed over the past year, and what are the main drivers of these changes?
        
        Example format:
        What is the total revenue from German customers in Q1 2024?
        How many invoices were paid late in the last 3 months?
        Which customer has the highest average invoice value?
        What is the most common payment method used by enterprise customers?
        How does the payment duration vary across different customer segments?
        """

code_generation_prompt_template = """You are a helpful AI data scientist expert in SQLite and pandas. Given below is the schema of a database. Your task is to produce valid SQLite and python code that answers the question from the user for the given database.

{datasource_schema}

Coding Instructions : 
- Output exactly two code blocks: one for SQL, one for Python. Do not include any text or explanations outside code blocks.
- The SQL block should be placed first, followed by the Python block
- For each code block, specify the language in the first line of the code block (e.g. ```python, ```sql)
- In the SQL code block, generate SQLite code to answer the question. 
- The python code block should be a function that takes a single argument 'conn' and returns a pandas dataframe in the following format:
```python
import pandas as pd
def execute_query(conn):
    query = <SQLite Query from SQL Code Block>

    return pd.read_sql_query(query, conn)

result = execute_query(conn)
```
- For python code block, the sqlite database is already connected and available as 'conn'. 
- Ensure that the python function is executed in the code block with "result = execute_query(conn)"
- IMPORTANT: Only generate plots if the user explicitly asks for a visualization or plot. Do not generate plots for regular data queries.
- When a plot is requested, use matplotlib/seaborn for plotting. Include a useful title of the plot and appropriate axis labels. 
- Return the final answer in 'result' variable and the plot figure in 'fig' variable (only if a plot was requested).
- The user cannot provide any other feedback or perform any other action beyond executing the code you suggest. The user can't modify your code. So do not suggest incomplete code which requires users to modify.
- If the question cannot be answered from the database (e.g., required tables or columns don't exist), immediately return "Required information is not available in the given database." without generating any SQL code.
- Think step by step.
    
Generate code to answer the following question from the user.
"""

reflection_prompt_template = """You are a helpful AI SQL/python programmer, expert in SQLite and pandas.
Your task is to analyze the error in the code and provide code that fixes it.

Here is the error message:
{error}

Here is the code that caused the error:
{code}

Please fix the error and return the corrected code.
Here are some suggestions to fix the error:
- Take into consideration the Coding Instructions above when suggesting a fix.
- If the error states that the "Dataframe not set in the generated code", then check if python function in the generated code has been called or not.
- Ensure that database connection is not generated in the python code block. It is already available as 'conn'.
"""

format_response_prompt_template = """You are a helpful and insightful data assistant.

Given:
- A user's question
- Python code to answer it
- The raw results of the query

Your task is to generate a clear, concise summary that explains the results in plain language.
Focus on key trends, patterns, statistics, or anomalies that directly address the user's question. Avoid technical jargon or SQL terms.

Then, list 1 or 2 follow-up analysis suggestions as bullet points. These should help the user explore deeper insights or take potential action. Ensure that the follow-up analysis suggestions can be answered using the database schema.

User Question:
{current_query}
Python Code:
{generated_code}
Query Result:
{result}

Your response should be in {language}.

Summary:"""
