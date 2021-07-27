import os

print(os.environ.keys())
os.system('heroku ps:restart worker.1')