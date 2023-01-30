import requests
import json
import sys
import os
import openai
import wandb
from string import Template

def load_config_or_exit():
    """Loads config.json."""
    try:
        config_file = open('config.json', 'r')
        config_data = json.load(config_file)
        config_file.close()
        # Access some values to throw exceptions if not found
        config_data['home_assistant_token']
        config_data['openai_api_key']
        return config_data
    except FileNotFoundError:
        print("Copy config.example.json to config.json and complete it.", file=sys.stderr)
        exit(1)
    except Exception as e:
        print("Invalid config.json: %s" % str(e), file=sys.stderr)
        exit(1)

def read_user_query_or_exit():
    try:
        line = input("HomeGPT > ")
    except EOFError:
        exit(0)

    if line == "exit":
        exit(0)
    elif line == "demo":
        return "Which lights are on?"

    return line;

def load_prompt_or_exit():
    """Loads prompt.txt."""
    try:
        prompt_file = open('prompt.txt', 'r')
        prompt_text = prompt_file.read()
        prompt_file.close()
        return prompt_text
    except FileNotFoundError:
        print("Couldn't find prompt file prompt.txt", file=sys.stderr)
        exit(1)
    except Exception as e:
        print("Failed to read prompt file prompt.txt: %s" % str(e), file=sys.stderr)
        exit(1)

def finish_initial_prompt(base_prompt):
    data = dict()
    return Template(base_prompt).substitute(data)

def execute_gpt_prompt(prompt):
    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=prompt,
        temperature=0.7,
        max_tokens=256,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    return response

if __name__ == '__main__':
    config = load_config_or_exit()
    base_prompt = load_prompt_or_exit()
    cumulative_prompt = finish_initial_prompt(base_prompt)

    openai.api_key = config['openai_api_key']

    while True:
        user_query = read_user_query_or_exit()
        cumulative_prompt += "Me:\n\"" + user_query + "\"\nComputer:\n"
        print(cumulative_prompt)

        response = execute_gpt_prompt(cumulative_prompt)

        response_text = response['choices'][0]['text']
        cumulative_prompt += response_text + "\n"

        print('=' * 50)
        print('==== Raw response ====')
        print('=' * 50)
        print(response_text)

        response_json = json.loads(response_text)
        print('=' * 50)
        print('==== JSON response ====')
        print('=' * 50)
        print(response_json)

