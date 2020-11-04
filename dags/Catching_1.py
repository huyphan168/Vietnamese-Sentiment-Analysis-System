from airflow import DAG
import datetime as dt
from airflow.operators.python_operator import PythonOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow import DAG
from scripts.crawler import crawl
from scripts.sentiment_prediction import Estimator
from scripts.other_statistics import common_stats
import numpy
import nltk
import pymongo
from pymongo import MongoClient

default_args = {
    'owner': 'airflow',
    'start_date': dt.datetime(2020, 10, 22, 19, 00, 00),
    'retries': 1
}

def crawl_task():
    app_id = "392288491810886"
    app_secret = "1b3342f87bb28ffaef76f80ec1685cbd"  
    page_id = "meimath"
    pass
    
def branching():
    client = MongoClient('mongodb://database:27017')
    db = client.database_devC
    user_col = db.user
    if True:
        return "crawling"
    else:
        return "skip"

def sentiment_task():
    vocab_path = "/opt/airflow/weight_vocab/vocab_ver1.pkl"
    weight_path = "/opt/airflow/weight_vocab/BiLSTM_Classification_16.pth"
    estimator = Estimator(weight_path, vocab_path)
    label = 0
    for i in range(1000):
        label = estimator.predict("Chiếc máy này sinh ra để dành cho đối tượng nhân viên công sở nhưng muốn giải trí sau những giờ làm việc căng thẳng, hoặc với dân multimedia muốn một chiếc máy gọn nhẹ nhất có thể")
    print("Label is",label) 


def gender_task():
    pass

with DAG('Catching_1_dag',
         default_args=default_args,
         schedule_interval='*/1 * * * *',
         max_active_runs=1
         ) as dag:
    branching = BranchPythonOperator(
        task_id='branching',
        python_callable=return_branch,
        provide_context=True)  
    skip_opr = DummyOperator(task_id='skip', retries=3)
    dummy_opr = DummyOperator(task_id='dummy', retries=3)
    end_opr = DummyOperator(task_id='dummy_end', retries=3)
    crawl_opr = PythonOperator(task_id="crawling", python_callable=crawl_task)
    sentiment_opr = PythonOperator(task_id="sentiment", python_callable=sentiment_task)
    stats_opr = PythonOperator(task_id="stats", python_callable=statistical_task)

dummy_opr >> branching >> crawl_opr >> [sentiment_opr, gender_opr] >> end_opr
branching >> skip >> end_opr