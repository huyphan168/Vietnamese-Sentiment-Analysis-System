#! /bin/bash

mongoimport --host database --db database_devC --collection user --type json --file /mongo-seed/init-db.json --jsonArray 