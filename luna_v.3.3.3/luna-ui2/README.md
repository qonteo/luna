# Luna GraphQL Server

## Requirements
This application uses python 3.6+

## Quickstart

Clone repository and install dependencies with pip.

```pip install -r requirements.txt```

Next, you need to generate key in order to provide secure sessions. Run `generate_secret_key.py` in `scripts/` and place output in COOKIE_SECRET variable in `config.ini`.

Specify value for `LUNA_API_URI` variable in `config.ini`.

This is it. Run server from root directory with 
```
python app/app.py
```

## Configuration
All of the server-related configuration can be found in `app/config.ini` file
`APP_PORT` - port that application listens to
`LUNA_API_URI` - self-descriptive
`COOKIE_SECRET` - secret cookie token for credentials encryption

All of the global constants can be found in `app/settings.py`

## Local static

In case of serving static from graphql server, additional steps are required:

* Run `git submodule init && git submodule update`
* Build `luna-ui` project, which can be found under `app/static` directory.

For building instructions refer to `luna-ui` README.md
