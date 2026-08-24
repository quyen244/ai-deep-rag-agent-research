from dotenv import load_dotenv
import os 

load_dotenv()

class Config:
    # API KEY
    OPENROUTER_API_KEY = os.getenv('OPPENROUTER_API_KEY' , "sh-")
    MODEL_NAME = os.getenv('MODEL_NAME' , 'nemotrion-flash')
    temperature = 0.3
    top_p = 0.9

    