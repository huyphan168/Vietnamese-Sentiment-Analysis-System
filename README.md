# Sentiment Analysis System
This web application includes 2 main parts
Front-end is written in ReactJS
Back-end is a docker-compose combining airflow scheduler and airflow webserver
The airflow scheduler will manage and schedule how Support Vector Machine module run predictions on the data collected from Facebook Graph API

# How to run
1. Install the docker and docker-compose
2. Install npm module
3. Create a terminal window, cd in main dictionary then run sudo docker-compose up
4. Create a second terminal window, cd in client dictionary then run npm install and npm start to start client-side
5. Create a 3rd terminal window, cd in server dictionary then run npm install and npm start to start API-side
