# Github Analytics Tool
A Program made in Python, that uses requests module to fetches and analysis publically available information of Github account

## Requirements
Language Used = Python3<br />
Modules/Packages used:
* requests
* os
* pathlib
* subprocess
* datetime
* bs4
* optparse
* pickle
* colorama
* time
<!-- -->
Install the dependencies:
```bash
pip install -r requirements.txt
```

### main.py
It takes the arguments from the command that is used to run the Python Program.<br />
It takes in the following arguments:
* '-u', "--users" : ID of the Users to get Details. (seperated by ',')
* '-l', "--load" : File from which to load the Users
* '-w', "--write" : Name of the file to dump extracted data
* '-r', "--read" : Read a dump file
* '-c', "--clone-repositories" : Clone All Repositories of a User (True/False)

### Files
It makes **data** and **users** folders.
* data: It stores the dumped data of the users. (Dumped using *pickle*)
* users: It stores the cloned repositories of the Users. (with User's name as the Parent Folder of the Cloned Repositories)

### Note
Reason of using *requests* instead of *github API* is that, by using this method of approach, it gives a proof that scrapping other Website that don't have API would be easy. Because the documentation of API is given online and can be easily used to get all required data.