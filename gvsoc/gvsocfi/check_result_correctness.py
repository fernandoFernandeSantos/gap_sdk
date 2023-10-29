#!/usr/bin/python3


# import required module
import os

# assign directory
directory = 'logs/MatrixAdd/injection-logs/'

# iterate over files in
# that directory
for root, dirs, files in os.walk(directory):
    for filename in files:
        print(os.path.join(root, filename))
