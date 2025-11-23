import sqlite3
from openai import OpenAI
import ast
from db_functions import get_column_names, is_query_safe, search, contains_hebrew
from dotenv import load_dotenv
import os
from pathlib import Path

load_dotenv()

env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(env_path)
openai_api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=openai_api_key) 

def ask_gpt_employee_query(conversation, user_last_query, user_info):
    """
    Generates a structured response including SQL query, TARGET, and ERROR keys
    based on the user's natural language request and user_info context.
    """

    column_names = get_column_names()  # e.g. ['EMPLOYEE_ID', 'EMPLOYEE_NAME', 'EMPLOYEE_LAST_NAME', 'START_FIRST_VIDEO_DATE', ...]

    system_prompt = (
        "You are a Cybersecurity-Training SQLite Query Generator and all the queries must be in SQLite format and about this scope - otherwise forbidden.\n"
        "You receive NATURAL LANGUAGE queries from employees and the CISO.\n"
        "Your task is to convert the user's request into a structured dictionary with exactly 4 keys - not in python:\n\n"
        "1. 'SQL': a valid SQLite query in the format SELECT <columns> FROM employees WHERE <conditions>;\n"
        "2. 'TARGET': ['HIMSELF'] or ['OTHER']\n"
        "   - If the user asks only about himself (no comparison, no mention of others) → ['HIMSELF']\n"
        "   - Otherwise → ['OTHER']\n"
        "3. 'ERROR': ['OK'] or ['FORBIDDEN']\n"
        "   - If the user requests to modify, update, delete, insert, reset, or change data → ['FORBIDDEN']\n"
        "   - Otherwise → ['OK']\n\n"
        "4. 'SCOPE': ['yes'] - if you can assist and this is relevant to cybersecurity training program or ['no'] if it is not relevant.\n"
        "Available columns in the table:\n"
        f"{column_names}\n\n"
        "NOTES ABOUT DATA STRUCTURE:\n"
        "- There are columns for both EMPLOYEE_NAME and EMPLOYEE_LAST_NAME (first and last name).\n"
        "- Each video has two columns: START_<N>_VIDEO_DATE and FINISH_<N>_VIDEO_DATE.\n"
        "- There are exactly 4 videos: FIRST, SECOND, THIRD, and FOURTH.\n"
        "- The order of watching the videos is not important — each video is tracked independently.\n\n"
        "- START AND FINISH are datestrings in the format 'YYYY-MM-DD HH:MM:SS' so you need to use julianday for date calculations.\n\n"
        "ABOUT VALUE MEANING:\n"
        "- The values in START_ and FINISH_ columns are either DATETIME strings or NULL/None.\n"
        "- Interpretation rules:\n"
        "  • If START_x IS NULL → the employee has **not started** the video.\n"
        "  • If START_x IS NOT NULL and FINISH_x IS NULL → the employee is **in progress**.\n"
        "  • If FINISH_x IS NOT NULL → the employee **finished** the video.\n\n"
        "LOGICAL VALIDATION RULES:\n"
        "- When calculating min, max, avg at first ignore possible None values.\n"
        "- If the user asks **how long** it took → require both START_x IS NOT NULL AND FINISH_x IS NOT NULL and you have to present those columns also with the result (also in the select) also if he start and finished it.\n"
        "- if the user asked who is the fastest to complete videos x and y so he want MIN (FINISH_x - START_x + FINISH_y - START_y) so the fastest employee is (sum from 1 to 4 FINISH_I - START_I).\n"
        "- If the user asks whether he **started** → check START_x IS NOT NULL.\n"
        "- If the user asks whether he **finished** → check FINISH_x IS NOT NULL.\n"
        "- If the user asks who is **in progress** → require START_x IS NOT NULL AND FINISH_x IS NULL.\n"
        "- If the user asks who **did not start** → require START_x IS NULL.\n"
        "- If the user asks who **has not finished yet** → require FINISH_x IS NULL (regardless of start).\n"
        "- Always ensure logical consistency — do not produce conditions that contradict these rules.\n\n"
        "SECURITY GUARDRAILS:\n"
        "- Operate in READ-ONLY mode only.\n"
        "- Never suggest or include UPDATE / DELETE / INSERT / ALTER operations.\n"
        "- All SQL outputs must be valid for SQLite.\n"
        "- Return ONLY a Python dictionary with the 3 keys — no explanations, markdown, or comments.\n\n"
        "CONTEXTUAL USER INFO:\n"
        "- You receive a variable named `user_info`, which contains details about the current user.\n"
        "- If the user asks about 'himself', 'me', 'my progress', etc., you may use details from `user_info` "
        "to identify the user's EMPLOYEE_ID or EMPLOYEE_NAME/EMPLOYEE_LAST_NAME in the WHERE clause.\n"
        "- Example: if user_info = {'EMPLOYEE_NAME': 'Ravid', 'EMPLOYEE_LAST_NAME': 'Gersh', 'EMPLOYEE_ID': '12345'}, "
        "you may use WHERE EMPLOYEE_ID = '12345' or WHERE (EMPLOYEE_NAME='Ravid' AND EMPLOYEE_LAST_NAME='Gersh') "
        "when TARGET=['HIMSELF'].\n"
    )

    user_prompt = (
        f"Conversation context: {conversation}\n\n"
        f"User info: {user_info}\n\n"
        f"User last query: {user_last_query}\n\n"
        "Return only the Python dictionary."
    )

    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0,
    )

    response_text = completion.choices[0].message.content.strip()
    return response_text


def generated_answear(user_info, user_message, sql_query, retrieved_data):
    """
    Generates a natural-language answer based on the user's question, 
    the executed SQL query, and the retrieved data from the database.
    """
    system_prompt = (
        "You are a cybersecurity training assistant.\n"
        "Your task is to generate a short, clear, and human-like response to the user's query.\n"
        "You will receive:\n"
        "- user_info: information about the employee (name, id, etc.)\n"
        "- user_message: the original question they asked\n"
        "- sql_query: the SQL query that was executed to retrieve the answer\n"
        "- retrieved_data: the actual data retrieved from the database.\n\n"
        "Guidelines:\n"
        "- Base your answer ONLY on retrieved_data.\n"
        "- If retrieved_data is None, empty, or contains NULL/None → explain that it likely means the condition was not met.\n"
        "- NEVER show SQL queries or database structure to the user.\n"
        "- If there is numeric data (like duration), phrase it naturally (e.g., 'it took you about 3 hours').\n"
        "- If multiple results exist, summarize concisely.\n"
        "- Respond naturally in English unless the user's question is in Hebrew — then answer in Hebrew.\n"
    )

    # Construct the message 
    user_prompt = (
        f"User info: {user_info}\n"
        f"User message: {user_message}\n"
        f"SQL query used: {sql_query}\n"
        f"Retrieved data: {retrieved_data}\n\n"
        "Generate the final answer for the user."
    )

    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.6,
    )

    # Return the generated text
    return completion.choices[0].message.content.strip()




def run_rag_agent(user_info, user_message, conversation ):

    conversation.append({"role": "user", "content": user_message}) # keep history conversation for continues conversation
    system_reply = ask_gpt_employee_query(user_info, conversation , user_message)

    try: # mabey gpt didn't return it in the desired format so we will ask him again
        system_reply = ast.literal_eval(system_reply)
    except Exception:
        try: # mabey gpt didn't return it in the desired format so we will ask him again
            system_reply = ask_gpt_employee_query(user_info, conversation , user_message)
            system_reply = ast.literal_eval(system_reply)
        except Exception: 
            if contains_hebrew(user_message):
                system_reply = "יש בעיית מערכת בבקשה תנסח שוב את ההודעה"
            else:
                system_reply = "Internal parsing error. Please rephrase."
            conversation.append({"role": "assistant", "content": system_reply})
            return user_message, conversation, system_reply

    
    # if "ERROR" in system_reply:
    if system_reply["ERROR"][0] == 'FORBIDDEN' or (is_query_safe(system_reply['SQL'])) == False: # the user asks illegal action that will change the database
        if contains_hebrew(user_message):
            system_reply = "אני לא יכול לבצע שינויים במסד הנתונים, בבקשה תנסח את השאלה מחדש."
        else:    
            system_reply = "I can't make any changes in the data, Please rephrase your question."
        conversation.append({"role": "assistant", "content": system_reply})
        return user_message,  conversation, system_reply  
            
    
    elif system_reply["TARGET"][0] == 'OTHER' and user_info["division"] != 'CISO': # regular employee asks about someone else
        if contains_hebrew(user_message):
            system_reply = "מותר לך לשאול רק על המידע שקשור לגביך. בבקשה תנסח את השאלה מחדש."
        else:
            system_reply = "You are allowed to ask only about your own data. Please rephrase your question."
        conversation.append({"role": "assistant", "content": system_reply})
        return user_message,  conversation, system_reply 


    elif system_reply["SCOPE"][0] == 'no': # the user ask something that out of the relevant agent scope
        if contains_hebrew(user_message):
            system_reply = "מותר לך לשאול רק על אימוני אבטחת סייבר."
        else:
            system_reply = "You are allowed to ask only about cybersecurity training."
        conversation.append({"role": "assistant", "content": system_reply})
        return user_message,  conversation, system_reply 
    
    # we can search in the database
    else:
        col_names, rows  = (search(system_reply['SQL'])) #TODO examine wheter it is work
        retrived_data = {"columns": col_names, "rows": rows}

        ## TODO if i will not do the other changes 
        system_reply = generated_answear(user_info, user_message, system_reply['SQL'], retrived_data)
        conversation.append({"role": "assistant", "content": system_reply})
        return user_message,  conversation, system_reply 








