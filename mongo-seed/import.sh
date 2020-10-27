#! /bin/bash

mongoimport --host database --db database_devC --collection comment --type json --file /mongo-seed/init-mongodb.json --jsonArray 