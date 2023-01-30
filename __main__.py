import requests
import json

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
        print("Copy config.example.json to config.json and complete it.")
        exit(1)
    except Exception as e:
        print("Invalid config.json: %s" % str(e))
        exit(1)

if __name__ == '__main__':
    config = load_config_or_exit()
    print(config)

