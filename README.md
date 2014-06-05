# Proxyvor
## Target (Server Side)

### Informations
Proxyvor is a solution for testing proxys.

It works with a client and a server(target). You launch the target in a remote place
and the client will try to reach it using a proxy and then reach it directly.
The target will record the headers (plus some additional ip informations) and will return them to the client when requested.
The client will then compare the results and give you some informations about the quality and the anonymity of the proxy

For the moment, the criteria for anonymity are:
*   If your ip address appears on the server ==> Bad anonymity
*   If your ip address doesn't appear, but the server knows there is a proxy ==> Neutral Anonymity
*   Else ==> Good anonymity

The criterias for the quality are:
*   If the User-Agent is changed ==> Bad quality
*   If the proxy ip doesn't appear on the server ==> Warning!

### Dependencies
You will need to have bottle, python-openssl and python-cherrypy3 installed:
```bash
sudo easy_install -U bottle
sudo apt-get install python-cherrypy3
sudo apt-get install python-openssl
```

### Usage
The server can be launched using the command:
`python main.py`

The configuration of the server is done via the file `config.json`

#### Path
**(mandatory)**
```json
"paths" : {
        "proxy_check" : "store/"
    }
```
This will configure the path in which the server will save the results when it is stopped. Obviously, they are read on startup in this path too.

#### HTTPS
**(optional)**
```json
"https": {
        "enabled": false,
        "certfile": "server.pem",
        "keyfile": "server.pem"
    }
```
This will allow you to use the server in https mode.
If you enable it, you have to provide a key and a certificate (in PEM format).
This is *disabled* by default

#### Logger
**(mandatory)**
```json
"logger": {
        "_comment": "See https://docs.python.org/2/library/logging.config.html#dictionary-schema-details for details on how to configure loggers",
        "version": 1,
        "formatters": {
            "simple": {
                "format": "'%(asctime)s - %(levelname)s - %(message)s'"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "DEBUG",
                "formatter": "simple",
                "stream": "ext://sys.stdout"
            },
            "file": {
                "class": "logging.FileHandler",
                "level": "INFO",
                "formatter": "simple",
                "filename": "logfile.log"
            }
        },
        "root": {
            "level": "DEBUG",
            "handlers": ["console", "file"]
        }
    }
```
This is the configuration of the logger, you can go to `https://docs.python.org/2/library/logging.config.html#dictionary-schema-details for details on how to configure loggers` if you want to have more details on how it works.
The default configuration provided will log everything on the *console*, and less information (**Warnings** essentially) in the file logfile.log

#### Port
**(optional)**
```json
"port": 8080
```
The port on which the server listens, if not provided, 8080 is used

### REST API of the server
(for all the routes, a token is supposed to be an uuid4 string)
#### `'/'`
Basic index page of the server

#### `'/<token>', 'GET'`
This the route used to record a result.
If you use this route directly, the first time will be considered as the proxy one, the second time will be considered as the real one.
You can use the routes:
*   `'/r/<token>', 'GET'` to record the real connection
*   `'/p/<token>', 'GET'` to record the proxy connection

#### `'/proxy_checks', 'GET'`
This is the route for listing all the existing tokens
It is also accessed via `'/proxy_checks/', 'GET'`

#### `'/proxy_checks/<token>', 'GET'`
This is the route for getting the results of a token

#### `'/proxy_checks/<token>', 'DELETE'`
This is the route for deleting the results of a token

#### `'/proxy_checks/create', 'PUT'`
This is the first route you need to call, it will create a token and return it to you in a json way


### Example of use
If you have the server running, you use curl to test it:
```bash
$ curl -X PUT http://192.168.10.93:8080/proxy_checks/create 
{"token": "153d5acd-45ce-41b9-a0d6-06a22a233a42", "success": true}

$ curl -X GET http://192.168.10.93:8080/153d5acd-45ce-41b9-a0d6-06a22a233a42
<pre>{
    "headers": {
        "client_ip": "192.168.10.93",
        "client_remote_route": [
            "192.168.10.93"
        ],
        "http_headers": {
            "Accept": "*/*",
            "Host": "192.168.10.93:8080",
            "User-Agent": "curl/7.26.0"
        },
        "remote_addr": "192.168.10.93"
    },
    "method": "GET"
}</pre>

$ curl -X DELETE 192.168.10.93:8080/proxy_checks/153d5acd-45ce-41b9-a0d6-06a22a233a42
{"success": true}

$ curl -X GET http://192.168.10.93:8080/153d5acd-45ce-41b9-a0d6-06a22a233a42
Nothing here, sorry
```