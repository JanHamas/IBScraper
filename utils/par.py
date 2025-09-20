import requests
requests.get(
    "https://ipv4.webshare.io/",
    proxies={
        "http": "http://vziwbgul:4yywedjc29ib@45.56.161.182:9058/",
        "https": "http://vziwbgul:4yywedjc29ib@45.56.161.182:9058/"
    }
).text
