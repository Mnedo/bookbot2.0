import os

import git


repo = git.Repo(os.getcwd())

files = repo.git.diff(None, name_only=True)
for f in files.split('\n'):
    repo.git.add(f)
print(files)
repo.git.commit('-m', 'test commit', author='Mnedo <Basecam@gmail.com>')
origin = repo.remote(name='origin')
origin.push()