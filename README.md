# Client/Server encrypted chat application ![Travis ci](https://travis-ci.org/Qinusty/Crypt-Chat.svg?branch=master)

~~**Example server running at qinusty.co.uk port 5000**~~

## Client command guide
`/register <username> <password>` is used to register an account with the server
`/login <username> <password>` is used to attempt to authenticate with the server

`/msg <username> <message>` is used to communicate with a user via username (end to end encryption is used)
`/gmsg <groupname> <message>` is used to communicate with a group via the server, all messages are end to end encrypted however user lists are stored.
`/exit` closes the client and logs out of the server

## Requirements
- Postgresql with database <dbname>
- Python 3.4.3 or above
- Virtualenv

## Setup basics
**Setup tested on Fedora 23 in Gnome terminal, Python 3.4.3 and virtualenv 15.0.1**


```
git clone git@github.com:Qinusty/Crypt-Chat.git
cd Crypt-Chat/
virtualenv -p python3.4 env
```
activate the virtual environment
- bash uses `. env/bin/activate`
- fish uses `. env/bin/activate.fish`

Double check python version with `python -V`
If you are still on python 2.7.x, run future python commands with `python3.4` instead of `python`

### Client
Modify config.json and add server details.

```
pip install -r client-requirements.txt
python Client.py
```

### Server
Install requirements with
`pip install -r server-requirements.txt`

#### Database configuration
Run commands and authenticate when required. You may need to configure postgres to use md5 authentication.
Take a look here [pg_hba](https://www.postgresql.org/docs/9.1/static/auth-pg-hba-conf.html)
```
psql -U <user> -c 'CREATE DATABASE <dbname>'
psql -U <user> <dbname> < DDL/schema.sql
```
Configure server and database connection settings via server_config.json
```
python Server.py
```

## Security disclaimer
I cannot guarantee completely secure communications due the self taught nature of my education on encryption. 
However the end to end encryption uses 4096 bit RSA keys and uses the PKCS1_OAEP standard for RSA encryption and
passwords are locally hashed using SHA512 and transmitted with end to end encryption before being
stored on the server's database as the unencrypted hash.
