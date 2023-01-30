import requests
import json
import sys
import os
import openai
import wandb
from string import Template


simulated_queries = dict(
        sim1=('Turn on the hallway light',
              '[{"response":"Turning on the Hallway Light."},{"service":"light.turn_on","data":{},"target":{"entity_id":["light.hallway_light"]}}]'),
        sim2=('Turn off the hallway light',
              '[{"response":"Turning off the Hallway Light."},{"service":"light.turn_off","data":{},"target":{"entity_id":["light.hallway_light"]}}]'),
        )
simulated_query = None


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
    """Load the next line of user input from stdin."""
    global simulated_query

    try:
        line = input("HomeGPT > ")
    except EOFError:
        exit(0)

    if line == "exit":
        exit(0)
    elif line == "demo":
        return "Which lights are on?"
    elif line in simulated_queries:
        simulated_query = simulated_queries[line]
        return simulated_query[0]

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
    """Fill in the template variables in the prompt loaded from the file."""

    data = dict()
    return Template(base_prompt).substitute(data)


def execute_gpt_prompt(prompt):
    """Execute a finished prompt on GPT-3."""
    global simulated_query

    if simulated_query is not None:
        response_text = dict(choices=[dict(text=simulated_query[1])])
        simulated_query = None
        return response_text

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


def print_sep(title=""):
    total_len = 50
    title_len = len(title)
    pad_front = round((total_len - title_len) / 2)
    pad_back = total_len - title_len - pad_front
    print(('=' * pad_front) + title + ('=' * pad_back))


def tell_user(text, error=False):
    """Tell the user some arbitrary plain text in response to something."""

    file = sys.stderr if error else sys.stdout
    print("HomeGPT says: " + text, file=file)


def execute_service(service, data, target):
    """Call a Home Assistant service."""

    print("Calling Home Assistant service: " + str(dict(service=service,
                                                        data=data,
                                                        target=target)))
    # TODO: Call HA service


def handle_raw_gpt_response(raw_response):
    """Handle raw GPT API response object. Returns GPT's response to the prompt."""

    try:
        response_text = raw_response['choices'][0]['text']
    except Exception as e:
        tell_user("Failed to parse text from raw GPT response: %s\n\nFull response is: %s" % (str(e), str(raw_response)),
                  error=True)
        return "[]"

    print_sep(' Unparsed response text ')
    print(response_text)
    print_sep()
    print()

    try:
        response_json = json.loads(response_text)
    except Exception as e:
        tell_user("Failed to parse GPT response JSON: %s" % str(e),
              error=True)
        return "[]"

    if not isinstance(response_json, list):
        tell_user("GPT response was not an array: %s" % str(e),
              error=True)
        return "[]"

    for response_obj in response_json:
        handle_gpt_response_obj(response_obj)

    return response_text


def handle_gpt_response_obj(response):
    """Handle a GPT response"""

    if 'response' in response:
       tell_user(response['response'])
    if 'service' in response:
        try:
            service = response['service']
            data = response['data'] if 'data' in response else dict()
            target = response['target']
        except Exception as e:
            tell_user("Response contained a malformed service call: %s" % str(e),
                  error=True)
            return
        execute_service(service, data, target)


if __name__ == '__main__':
    config = load_config_or_exit()
    base_prompt = load_prompt_or_exit()
    cumulative_prompt = finish_initial_prompt(base_prompt)

    openai.api_key = config['openai_api_key']

    while True:
        user_query = read_user_query_or_exit()
        cumulative_prompt += "Me:\n\"" + user_query + "\"\nComputer:\n"
        #print(cumulative_prompt)
        raw_response = execute_gpt_prompt(cumulative_prompt)
        response_text = handle_raw_gpt_response(raw_response)
        cumulative_prompt += response_text + "\n"

