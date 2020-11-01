#! /bin/bash

mongoimport --host database --db database_devC --collection results --type json --file /mongo-seed/init-results.json --jsonArray 