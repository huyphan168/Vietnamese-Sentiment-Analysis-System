#! /bin/bash

mongoimport --host database --db database_devC --collection user --type json --file /mongo-seed/init-db1.json --jsonArray
mongoimport --host database --db database_devC -- collection cache --type json --file /mongo-seeed/init-db2.json --jsonArray