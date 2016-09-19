# Client/Server encrypted chat application

## Requirements
- Postgresql with database 'enchat'
- Python 3.4.3 or above
- Virtualenv

## Setup basics
**Setup tested on Fedora 23 in Gnome terminal, Python 3.4.3 and virtualenv 15.0.1**

use `python -V` to ensure python is running version 3.4.3 or above.
if not, consider changing this via the `update-alternatives --config` command
or check `python3 -V`

```
git clone git@github.com:Qinusty/Crypt-Chat.git
cd Crypt-Chat/
virtualenv env
```
activate the virtual environment
- bash uses `source env/bin/activate`
- fish uses `. env/bin/activate.fish`

Double check python version with `python -V`
If you are still on python 2.7.x, run future python commands with `python3` instead of `python`

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
psql -U <user> <dbname> < schema.sql
```
Configure server and database connection settings via server_config.json
```
python Server.py
```