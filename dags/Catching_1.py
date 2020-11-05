from airflow import DAG
import datetime as dt
from airflow.operators.python_operator import PythonOperator, BranchPythonOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow import DAG
from scripts.crawler import scrape_all_posts
from scripts.sentiment_prediction import Estimator
from scripts.gender import Gender_estimator
import numpy
import nltk
from pprint import pprint
import pymongo
from pymongo import MongoClient
from pymongo import ReturnDocument

default_args = {
    'owner': 'airflow',
    'start_date': dt.datetime(2020, 10, 22, 19, 00, 00),
    'retries': 1
}

def crawl_task(**kwargs):
    ti = kwargs["ti"]
    page_info = ti.xcom_pull(task_ids='branching',key='the_message')
    print(page_info)
    pass
    
def branching(**context):
    client = MongoClient('mongodb://database:27017')
    db = client.database_devC
    user_col = db.user
    cp_id = None
    page_info = []
    user_campaigns = user_col.find_one({"Campaigns.First_attempt":0})
    for campaign in user_campaigns["Campaigns"]:
        if campaign["First_attempt"] == 0:
            cp_id = campaign["campaignID"]
            break
    user_col.update({"Campaigns.campaignID":cp_id},
                    {'$set':{"Campaigns.$.First_attempt":1}})
    if cp_id is not None:
        usr = user_col.find_one({"Campaigns.campaignID":cp_id})
        for cp in usr["Campaigns"]:
            if cp["campaignID"] == cp_id:
                for k, v in cp["page_info"].items():
                    page_info.append(v)
        task_instance = context['task_instance']
        task_instance.xcom_push(key="the_message", value=page_info)

    if cp_id is not None:
        return "crawling"
    else:
        return "skip"

def sentiment_task():
    vocab_path = "/opt/airflow/weight_vocab/vocab_ver1.pkl"
    weight_path = "/opt/airflow/weight_vocab/BiLSTM_Classification_16.pth"
    estimator = Estimator(weight_path, vocab_path)
    label = 0
    for i in range(5):
        label = estimator.predict("Chiếc máy này sinh ra để dành cho đối tượng nhân viên công sở nhưng muốn giải trí sau những giờ làm việc căng thẳng, hoặc với dân multimedia muốn một chiếc máy gọn nhẹ nhất có thể")
    print("Label is",label) 


def gender_task():
    pass

with DAG('Catching_1_dag_2',
         default_args=default_args,
         schedule_interval='*/1 * * * *',
         max_active_runs=1
         ) as dag:
    branching = BranchPythonOperator(
        task_id='branching',
        python_callable=branching,
        provide_context=True)  
    skip_opr = DummyOperator(task_id='skip', retries=3)
    dummy_opr = DummyOperator(task_id='dummy', retries=3)
    end_opr = DummyOperator(task_id='dummy_end', retries=3)
    crawl_opr = PythonOperator(task_id="crawling", python_callable=crawl_task,provide_context=True)
    sentiment_opr = PythonOperator(task_id="sentiment", python_callable=sentiment_task)
    gender_opr = PythonOperator(task_id="gender", python_callable=gender_task)

dummy_opr >> branching >> crawl_opr >> [sentiment_opr, gender_opr] >> end_opr
branching >> skip_opr >> end_opr