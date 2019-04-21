# cosicasbot

Online store bot written in Python 3

## Install

1. Clone this repository
2. Install MySQL
3. Install Python 3
4. Install dependencies:

```pip install -r requirements.txt```

5. Edit `config.json` to match your environment
6. Generate helper config files:

```./generate_config.py config/config.json```

7. Generate the tables:

```alembic upgrade head```

## Run

Run bot with:

```./cosicasbot.py config/config.json```

In development you can use nodemon:

```nodemon ./cosicasbot.py config/config.json```
