# GeminiSQLExecutor

## Project Overview
This project is a Streamlit application that leverages Google’s Gemini model to translate English language questions into SQL queries to run on a local database. 

## Functions

The project consists of the following Python functions:

1. **callGemini(question, prompt)**: This function uses the Gemini model to generate SQL queries from English language questions.
2. **readSQL(query, db_user, db_password, db_host, db_name)**: This function executes the generated SQL query on a MySQL database and returns the results.
3. **captureSchema(db_user, db_password, db_host, db_name)**: This function captures the schema of the MySQL database, which can be helpful for users to formulate their questions.

## Flow of the Streamlit App

The Streamlit app is the front end of the project and interacts with the user:

1. **Question Input**: Users input their questions in English via a text area.
2. **SQL Generation**: Upon clicking a button, the `callGemini` function is invoked to generate an SQL query based on the user's question.
3. **SQL Execution**: The `readSQL` function is then invoked to execute the generated SQL query on a local MySQL database.
4. **Result Display**: The results of the SQL query execution are displayed in a table format.
5. **Schema Inspection**: The `captureSchema` function is used to provide a sidebar for inspecting the schema of the MySQL database.

This project takes advantage of:

- **Natural Language Processing (NLP)**: The project uses Google's Gemini model, which is a state-of-the-art language model for generating SQL queries from English language questions.
- **Web Development**: The project uses Streamlit, a popular open-source app framework for Machine Learning and Data Science teams.
- **Database Management**: The project involves executing SQL queries on a MySQL database, providing hands-on experience with database management systems.
- **Language Models**: Google's Gemini model, a transformer-based language model, is used to generate SQL queries from English language questions.
- **Multimodal Learning**: Gemini's multimodal capabilities enable it to process and generate content from various sources, including text, images, and code.
- **Transfer Learning**: Gemini also benefits from transfer learning, where knowledge gained from pre-trained models on specific tasks is transferred to new tasks. This helps it learn faster and achieve better performance.

![image](https://github.com/vadv97/GeminiSQLExecutor/assets/85503358/e25a35a1-18be-463c-8547-6965fbad5e1d)
