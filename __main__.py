import requests

url = "http://httpstat.us/200"

if __name__ == '__main__':
    """Test request"""
    response = requests.get(url)
    print(response.text)

