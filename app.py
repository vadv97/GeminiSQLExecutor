from dotenv import load_dotenv
import os
load_dotenv()
import google.generativeai as genai
import pandas as pd
import mysql.connector
from langchain_community.utilities import SQLDatabase
from langchain_experimental.sql import SQLDatabaseChain
from datetime import datetime
import streamlit as st

genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

# Function to set Gemini model
def callGemini(question, prompt):
    llm = genai.GenerativeModel(model_name="gemini-pro")
    response = llm.generate_content([prompt[0], question])
    return response.text

# Function to run query on the mySQL db
def readSQL(query, db_user="root", db_password="VA9999", db_host="localhost", db_name="hospital"):
    try:
        # Establish a connection
        connection = mysql.connector.connect(
            user=db_user,
            password=db_password,
            host=db_host,
            database=db_name
        )

        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query)
            rows = cursor.fetchall()

            return rows

    except mysql.connector.Error as err:
        print(f"Error: {err}")

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


# Function to take a snapshot of the table and column names as a guide on streamlit's sidepanel
def captureSchema(db_user="root", db_password="VA9999", db_host="localhost", db_name="hospital"):
    schema = {}
    try:
        connection = mysql.connector.connect(
            user=db_user,
            password=db_password,
            host=db_host,
            database=db_name
        )

        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SHOW TABLES")
            tables = [table['Tables_in_' + db_name] for table in cursor.fetchall()]

            # Get columns for each table and store in a dictionary
            for table in tables:
                cursor.execute(f"DESCRIBE {table}")
                columns = [column['Field'] for column in cursor.fetchall()]
                schema[table] = columns

    except mysql.connector.Error as err:
        print(f"Error: {err}")

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

    return schema


# Creating the prompt with example queries for the callGemini function
prompt = ["""Generate a MySQL query based on the given English question to retrieve information from my local database. 
Ensure that the generated query references the correct columns. 
    Instructions:
    1. Read the names of the tables in the schema and strictly only use tables that exist, 
    2. Reference columns from the tables they exist in, especially when using `JOIN` or `WHERE` clauses,  
    3. Pay close attention to how the data looks inside the columns by taking note of the datatype, 
    4. Pay close attention to norms of values in the columns, for example: State column in hospital_data, and HomeState column in patient_data have the names of the US states as a two-letter standard abbreviation,    
    5. The sql code should not have ``` in beginning or end and sql word in the output,
    6. If the English question requests information that does not exist, in part or in whole, in the database reply with 'I am not sure if that exists in the database. Please provide more information, or refer to the schema.' but do not create tables that don't exist. 
    

    The SQL queries should look like the following examples,
    Example 1 - 
    Question: "What is the most expensive hospital for employed smokers in Florida?", 
    SQLQuery: "SELECT hospital_data.HospitalName, patient_data.InvoiceAmount FROM patient_data JOIN hospital_data ON patient_data.HospitalID = hospital_data.ProviderNo WHERE patient_data.Smoker = 1 AND hospital_data.State = 'FL' AND patient_data.Employed = 1 ORDER BY patient_data.InvoiceAmount DESC LIMIT 1;",
    
    Example 2 -
    Question: "What was the largest discount when compared to the state average and provided negative feedback?", 
    SQLQuery : "SELECT patient_data.PatientID, patient_data.InvoiceAmount, hospital_data.StateAvgSpend, patient_data.Feedback,
       (hospital_data.StateAvgSpend - patient_data.InvoiceAmount) AS Discount FROM patient_data JOIN hospital_data ON patient_data.HospitalID = hospital_data.ProviderNo WHERE patient_data.Feedback = -1 ORDER BY Discount DESC LIMIT 1;",
    
    Example 3 - 
    Question :"which state has the longest diabetic patient stay if duration of stay is the difference between the coverage end date and coverage start date?",
    SQLQuery  :"SELECT patient_data.HomeState, DATEDIFF(hospital_data.EndDate, hospital_data.StartDate) AS DurationOfStay FROM patient_data JOIN hospital_data ON patient_data.HospitalID = hospital_data.ProviderNo WHERE patient_data.Diabetic = 1 ORDER BY DurationOfStay DESC LIMIT 1;",
    
    Example 4 -
    Question : "which state has the highest percentage spend for claims paid between 1-30 days after discharge?",
    SQLQuery :"SELECT State, MAX(`StateSpendingPercentage`) AS HighestPercentageSpend FROM hospital_data WHERE `Period` = '1 through 30 days After Discharge from Index Hospital Admission' GROUP BY `State` ORDER BY HighestPercentageSpend DESC LIMIT 1;",

    Example 5 -    
    Question : "which was the busiest month (had the most number of patients) for claims based on the coverage start and end dates?",
    SQLQuery:"SELECT EXTRACT(MONTH FROM `StartDate`) AS Month,EXTRACT(YEAR FROM `StartDate`) AS Year,COUNT(*) AS ClaimCount FROM hospital_data WHERE `StartDate` IS NOT NULL AND `EndDate` IS NOT NULL GROUP BY Month, Year ORDER BY `ClaimCount` DESC LIMIT 1;",
    
    Example 6 -
    Question : "what is max discount received for any patient when comparing invoiced amount to the national average",
    SQLQuery :"SELECT (hospital_data.`NationalAvgSpend` - patient_data.`InvoiceAmount`) as Discount FROM patient_data LEFT JOIN hospital_data ON `patient_data.HospitalID` = hospital_data.`ProviderNo` ORDER BY `Discount` LIMIT 1;",
        
    Example 7 -
    Question : "what is the most common claim for drug or alcohol users from Colorado",
    SQLQuery :"SELECT patient_data.`DrugsAlc`, hospital_data.`ClaimType`, COUNT(*) AS ClaimCount FROM patient_data JOIN hospital_data ON patient_data.`HospitalID` = hospital_data.`ProviderNo WHERE patient_data.`DrugsAlc` = 1 GROUP BY patient_data.`DrugsAlc`, hospital_data.`ClaimType` ORDER BY `ClaimCount` DESC LIMIT 1",
        
    Example 8 -
    Question : "What was the largest discount when compared to state average and provided negative feedback?",
    SQLQuery :"SELECT patient_data.`PatientID`, patient_data.`InvoiceAmount`, hospital_data.`StateAvgSpend`, patient_data.`Feedback`,(hospital_data.`StateAvgSpend` - patient_data.`InvoiceAmount`) AS Discount FROM patient_data JOIN hospital_data ON patient_data.`HospitalID` = hospital_data.`ProviderNo` WHERE patient_data.`Feedback` = -1 ORDER BY Discount DESC LIMIT 1",
        
    Example 9 -
    Question : "how many patients paid more than the average hospital amount during a complete episode",
    SQLQuery :"SELECT COUNT(*) AS NumPatientsPaidMoreThanAvg FROM patient_data JOIN hospital_data ON patient_data.`HospitalID` = hospital_data.`ProviderNo` WHERE patient_data.`InvoiceAmount` > hospital_data.`HospitalAvgSpend`   AND hospital_data.`Period` = 'Complete Episode' LIMIT 0, 1000",
        
    Example 10 -
    Question : "Top 3 hospitals which charged an invoice amount from their patients lower than the national average for outpatient?",
    SQLQuery :"SELECT hospital_data.`HospitalName`,patient_data.`InvoiceAmount`, hospital_data.`NationalAvgSpend` FROM hospital_data JOIN patient_data ON patient_data.`HospitalID` = hospital_data.`ProviderNo` WHERE hospital_data.`ClaimType` = 'Outpatient'   AND patient_data.`InvoiceAmount` < hospital_data.`NationalAvgSpend` LIMIT 0, 1000",
        
    Example 11 -
    Question : "how many patients are smokers or pregnant from Texas? How many hospitals in the same?",
    SQLQuery :"SELECT (SELECT COUNT(*) FROM patient_data WHERE (`Smoker` = 1 OR `Pregnant` = 1) AND `HomeState` = 'TX') AS NumPatients, (SELECT COUNT(*) FROM hospital_data WHERE `State` = 'TX') AS NumHospitals LIMIT 0, 100",
        
    Example 12 -
    Question : "how many patients with a smoking habit and went to hospitals in their home state during index admission?",
    SQLQuery :"SELECT COUNT(*) AS NumSmokerOutpatientPatientsInHomeState FROM patient_data JOIN hospital_data ON patient_data.`HospitalID` = hospital_data.`ProviderNo` WHERE patient_data.`Smoker` = 1   AND patient_data.`HomeState` = hospital_data.`State`   AND hospital_data.`Period` = 'During Index Hospital Admission' LIMIT 0, 100",
        
    Example 13 -
    Question :"find the number of unemployed patients got treated outside their home state, and ended up getting invoiced for an amount 50% higher than the state average",
    SQLQuery :"SELECT COUNT(*) AS NumPatients FROM patient_data JOIN hospital_data ON patient_data.`HospitalID` = hospital_data.`ProviderNo` WHERE patient_data.`Employed` = 0   AND patient_data.`HomeState` != hospital_data.`State`   AND patient_data.`InvoiceAmount` > 1.5 * hospital_data.`StateAvgSpend` LIMIT 0, 1000",
        
    Example 14 -
    Question :"which state had the most number of Drug/Alcohol users as patients",
    SQLQuery :"SELECT hospital_data.`State`, COUNT(*) AS NumDrugAlcUsers FROM patient_data JOIN hospital_data ON patient_data.`HospitalID` = hospital_data.`ProviderNo` WHERE patient_data.`DrugsAlc` = 1 GROUP BY hospital_data.`State` ORDER BY NumDrugAlcUsers DESC LIMIT 1",
        
    Example 15 -
    Question :"what is the average BMI for outpatients in 2022",
    SQLQuery :"SELECT AVG(patient_data.`BMI`) AS AvgBMI FROM patient_data JOIN hospital_data ON patient_data.`HospitalID` = hospital_data.`ProviderNo` WHERE hospital_data.`ClaimType` = 'Outpatient'   AND YEAR(hospital_data.`StartDate`) = 2022 LIMIT 0, 1000",

    """]

# Creating a Streamlit App for front-end 
st.set_page_config(page_title="Front end app", layout="wide")
st.title("Gemini-wrapper for SQL")

# Input for question
question = st.text_area("Enter your question:")

# Button to generate SQL and execute query
if st.button("Generate SQL and Execute"):
    if question:
        # Generate SQL using callGemini
        generated_sql = callGemini(question, prompt)

        # Display SQL
        st.subheader("Generated SQL:")
        st.code(generated_sql, language="sql")

        # Execute SQL
        try:
            sql_result = readSQL(generated_sql)
            st.subheader("SQL Result:")

            # Creating table from the results
            df = pd.DataFrame(sql_result)
            df = df.applymap(lambda x: x.decode('utf-8') if isinstance(x, bytes) else x)
            st.write(df)
        except Exception as e:
            st.error(f"Error executing SQL query: {e}")
    else:
        st.warning("Please enter a question")

# Sidebar with MySQL schema inspection
st.sidebar.header("Need help with the prompt?")
dropdown = st.sidebar.expander("Inspect Database")

# Display schema information when the expander is open
with dropdown:
    schema = captureSchema(db_user="root", db_password="VA9999", db_host="localhost", db_name="hospital")
    for table, columns in schema.items():
        st.write(f"{table}:\n    {', '.join(columns)}")


# Instructions
st.sidebar.markdown("## Instructions:")
st.sidebar.markdown(
    """
    1. Enter a question in English.
    2. Click the 'Generate SQL and Execute' button to generate SQL and execute the query.
    3. View the generated SQL and the result of the SQL execution.
    4. Expand 'Inspect Database' to see the schema information.
    """
)