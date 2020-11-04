from airflow import DAG
import datetime as dt
from airflow.operators.python_operator import PythonOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow import DAG
import flask
import inspect
from scripts.crawler import crawl
from scripts.sentiment_prediction import Estimator
from scripts.other_statistics import common_stats
import numpy
import nltk
from pymongo import MongoClient


default_args = {
    'owner': 'airflow',
    'start_date': dt.datetime(2020, 10, 22, 19, 00, 00),
    'retries': 1
}

def crawl_task():
    pass
    

def sentiment_task():
    pass    


def gender_task():
    pass

with DAG('Daily_dag',
         default_args=default_args,
         schedule_interval='*/10 * * * *',
         max_active_runs=1
         ) as dag:
    
    dummy_opr = DummyOperator(task_id='dummy', retries=3)
    end_opr = DummyOperator(task_id='dummy_end', retries=3)
    crawl_opr = PythonOperator(task_id="crawling", python_callable=crawl_task)
    sentiment_opr = PythonOperator(task_id="sentiment", python_callable=sentiment_task)
    gender_opr = PythonOperator(task_id="gender", python_callable=gender_task)

dummy_opr >> crawl_opr >> [sentiment_opr, gender_opr] >> end_opr