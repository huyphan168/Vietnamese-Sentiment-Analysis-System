from airflow import DAG
import datetime as dt
from airflow.operators.python_operator import PythonOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow import DAG
import flask
import inspect
from scripts.crawler import Crawler
from scripts.sentiment_prediction import LSTM_VSA
from scripts.other_statistics import common_stats
import numpy
import nltk
import pymongo


default_args = {
    'owner': 'airflow',
    'start_date': dt.datetime(2020, 10, 22, 19, 00, 00),
    'retries': 1
}

def crawl_task():
    crawler = Crawler()
    input = "huy"
    output = crawler.crawling(input)
    print(output)


def sentiment_task():
    predictor = LSTM_VSA()
    input = "San pham nay tot the nhi"
    output = predictor.predict(input)
    print(output) 


def statistical_task():
    insight_looker = common_stats()
    input = "id1"
    output = insight_looker.getting_insight(input)
    print(output) 

with DAG('VSA10_dag',
         default_args=default_args,
         schedule_interval='*/5 * * * *',
         max_active_runs=1
         ) as dag:

    dummy_opr = DummyOperator(task_id='dummy', retries=3)
    end_opr = DummyOperator(task_id='dummy_end', retries=3)
    crawl_opr = PythonOperator(task_id="crawling", python_callable=crawl_task)
    sentiment_opr = PythonOperator(task_id="sentiment", python_callable=sentiment_task)
    stats_opr = PythonOperator(task_id="stats", python_callable=statistical_task)

dummy_opr >> [crawl_opr, sentiment_opr, stats_opr] >> end_opr