import sqlite3
from openai import OpenAI
import ast
from db_functions import exist_employee, get_user_division, contains_hebrew
from dotenv import load_dotenv
import os
from pathlib import Path

load_dotenv()

env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(env_path)

openai_api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=openai_api_key) 

def ask_gpt_ids_and_names(system_last_message , user_query):
    system_prompt = (

        "You are an internal employee-database assistant. \n"
        "Return ONLY a Dictionary with keys 'id' and 'name'. \n"
        "Never invent employees. Use only information explicitly mentioned by the user. \n"
        "If the user does not provide any identifiable employee information, return None. \n"
        "If no employees match the request, return {'id': '', 'name': ''}. \n"
        "You may use the system message that appears before the user query to understand the user's intent (i.e if the system ask for id and the user replied only with numbers it might be his id).\n"
        "Do not return explanations or code blocks.\n\n"

        "Example 1:\n"
        "User: 'My name is Alice with id 123'\n"
        "Output: {'id': '123', 'name': 'Alice'}\n"

        "Example 2:\n"
        "User: 'Hi I am Alice'\n"
        "Output: {'id': "", 'name': 'Alice'}\n"

        "Example 3:\n"
        "User: 'Which videos did I finished?'\n"
        "Output: {'id': "", 'name': ""}\n"
    )

            
    

    user_prompt = (
        f"The system msesage before the user query is: {system_last_message}\n\n"
        f"User query: {user_query}\n\n"
        "Return only the Python structure."
    )

    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0,
    )

    reply = completion.choices[0].message.content.strip()
    return reply


def run_auth_agent(user_message, user_info, system_last_message ):
 
    reply = ask_gpt_ids_and_names(system_last_message, user_message)

    print(f"reply before {reply}")
    reply = ast.literal_eval(reply) # Convert string representation of dict to actual dict

    print(reply)
    if reply != None:
        if reply['name'] != '': # update his details also if the user corrected his name in this turn.
            user_info['name'] = reply['name']
        if reply['id'] != '':
            user_info['id'] = reply['id']


    # Update the user's information based on the GPT response and the information we had from previous messages
    if user_info['name'] == None and user_info['id'] == None:
        if contains_hebrew(user_message):
            system_last_message = "אתה צריך לספר לי את השם שלך ואת תעודת הזהות כדי להמשיך בשיחה."
        else:
            system_last_message = "You must provide your name and ID in order to continue this conversation."
        return system_last_message, user_info, False # TODO : Sent it as a message to the user interface
    
    elif user_info['name'] == None:
        if contains_hebrew(user_message):
            system_last_message = "היי יש לי את מספר הזהות שלך, אני צריך גם את השם."
        else:
            system_last_message = "I have your ID, I must get your name also"
        return system_last_message, user_info, False

    elif user_info['id'] == None:
        if contains_hebrew(user_message):
            system_last_message = f"  אני צריך גם את מספר הזהות שלך ,{user_info['name']} "
        else:    
            system_last_message = f"Hey {user_info['name']}, I must get your ID also"
        
        return system_last_message, user_info, False
    
    elif user_info['name'] != None and user_info['id'] != None: # we have both name and id we can continue to the next stage

        if exist_employee(user_info['name'], user_info['id']): # the user exist
            user_info['division'] = get_user_division(user_info["id"]) 
            if contains_hebrew(user_message):
                system_last_message = "היי, איך אפשר לעזור לך?"
            else:
                system_last_message = f"Hi {user_info['name']}, how can I help you?"
            return system_last_message, user_info, True
            

        else:
            user_info = {'name': None, 'id': None} # reset the info in order to start over
            if contains_hebrew(user_message):
                system_last_message = "העובד לא נמצא במסד הנתונים. תנסה בבקשה שוב."
            else:    
                system_last_message = "Employee not found in the database. Please try again." # reset the system message
            return system_last_message, user_info, False

    
