# ableton project organizer


## setup 

setup from sratch 
```conda create --name <env_name> --file requirements.txt```

install packages from requirements.txt
```conda install --yes --file requirements.txt```

## run project
run web app with autoimatic reload (https://stackoverflow.com/questions/16344756/auto-reloading-python-flask-app-upon-code-changes):
```flask --app app.py --debug run```