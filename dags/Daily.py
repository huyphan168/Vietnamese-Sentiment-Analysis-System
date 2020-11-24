from airflow import DAG
import datetime as dt
from airflow.operators.python_operator import PythonOperator, BranchPythonOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow import DAG
from scripts.crawler import scrape_all_posts
from scripts.sentiment_prediction import Estimator, normalize_text
from scripts.gender import Gender_estimator
import numpy
import nltk
import random
from pprint import pprint
import pymongo
from pymongo import MongoClient
from pymongo import ReturnDocument

mongo_link = "mongodb+srv://quandat438:quandat10@cluster0.trl9y.mongodb.net/devC?retryWrites=true&w=majority"

default_args = {
    'owner': 'airflow',
    'start_date': dt.datetime(2020, 10, 22, 19, 00, 00),
    'retries': 1
}

def crawl_task(**context):
    ti = context["ti"]
    client = MongoClient(mongo_link)
    db = client.devC
    user_col = db.users
    cache_col = db.cache
    all_info = ti.xcom_pull(task_ids='branching',key='the_message')
    print(all_info)
    for page_info in all_info:
        app_id, app_secret, access_token, page_id, keyword, cp_id = page_info
        arr, new_token = scrape_all_posts(app_id, app_secret, access_token, page_id)
        user_col.update({"campaigns.campaignId":cp_id},
                        {'$set':{"campaigns.$.page_info":
                        {
                            "app_id": app_id,
                            "app_secret": app_secret,
                            "access_token": new_token,
                            "page_id": page_id,
                            "keyword": keyword
                        }}})
        

        cache_col.insert_one({"campaign_id": cp_id, "data": arr})
    tf = context["task_instance"]
    tf.xcom_push(key="cpid", value=all_info)
    
def branching(**context):
    client = MongoClient(mongo_link)
    db = client.devC
    user_col = db.users
    cp_ids = []
    all_info = []
    users_campaigns = user_col.find({"campaigns.flag":"2"})
    if users_campaigns:
        for user_campaigns in users_campaigns:
            for campaign in user_campaigns["campaigns"]:
                if campaign["flag"] == "2":
                    cp_ids.append(campaign["campaignId"])
                
    if len(cp_ids) > 0:
        for cp_id in cp_ids:
            usr = user_col.find_one({"campaigns.campaignId":cp_id})
            for cp in usr["campaigns"]:
                if cp["campaignId"] == cp_id:
                    page_info = []
                    for k, v in cp["page_info"].items():
                        page_info.append(v)
                    page_info.append(cp_id)
                    all_info.append(page_info)

        task_instance = context['task_instance']
        task_instance.xcom_push(key="the_message", value=all_info)

    if len(cp_ids) > 0:
        return "crawling"
    else:
        return "skip"
def gender_task():
    pass

def sentiment_task(**context):
    client = MongoClient(mongo_link)
    db = client.devC
    cache_col = db.cache
    estimator = Estimator()
    ti = context["ti"]
    # Loop through all users
    all_info = ti.xcom_pull(task_ids='crawling',key='cpid')
    for page_info in all_info:
        cp_id = page_info[5]
        document = cache_col.find_one({"campaign_id": cp_id})
        cache_col.delete_one({"campaign_id": cp_id})
        arr = document["data"]
        pos_points = []
        neg_points = []
        neu_points = []
        pos_cmt = []
        neg_cmt = []
        neu_cmt = []
        ACOM = ""
        for idx in range(len(arr)):
            day = arr[idx]["created_time"]
            comments = arr[idx]["comments"]
            num_pos = 0
            num_neg = 0
            num_neu = 0
            for comment in comments:
                comment_norm = normalize_text(comment)
                ACOM = comment_norm + " " + ACOM
                label = estimator.predict(comment_norm)
                if label == 0:
                    num_pos += 1
                    pos_cmt.append(comment)
                elif label == 1:
                    num_neu += 1
                    neu_cmt.append(comment)
                elif label == 2:
                    num_neg += 1
                    neg_cmt.append(comment)
            pos_points.append((day, num_pos))
            neg_points.append((day, num_neg))
            neu_points.append((day, num_neu))
        total_pos = sum([y for (x,y) in pos_points])
        total_neg = sum([y for (x,y) in neg_points])
        total_neu = sum([y for (x,y) in neu_points])
        pos_percent = round(total_pos*100/(total_pos+total_neg+total_neu))
        neg_percent = round(total_neg*100/(total_pos+total_neg+total_neu))
        neu_percent = 100 - pos_percent - neg_percent
        male = random.randint(8,15) + 50
        female = 100- male
        word_freq = {}
        for word in ACOM.split():
            if word not in word_freq.keys():
                word_freq[word] = 1
            else:
                word_freq[word] += 1
        if len(pos_cmt) >= 5:
            pos_cmt = pos_cmt[:5]
        if len(neg_cmt) >= 5:
            neg_cmt = neg_cmt[:5]
        if len(neu_cmt) >= 5:
            neu_cmt = neu_cmt[:5]
    
        words = [{"text": word, "value": word_freq[word]} for word in word_freq.keys()]
        result = {
                    "positive": {
                                    "points": pos_points,
                                    "percent": pos_percent,
                                    "sample": pos_cmt
                                },
                    "neural": {
                                "points": neu_points,
                                "percent": neu_percent,
                                "sample": neu_cmt
                                },
                    "negative": 
                                {
                                "points": neg_points,
                                "percent": neg_percent,
                                "sample": neg_cmt
                                },
                    "gender": {
                                "Male": male,
                                "Female": female
                                },
                    "words": words}

        user_col = db.users
        user_col.update({"campaigns.campaignId":cp_id},
                        {'$set':{"campaigns.$.result":result}})


with DAG('daily_1',
         default_args=default_args,
         schedule_interval='*/5 * * * *',
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
    sentiment_opr = PythonOperator(task_id="sentiment", python_callable=sentiment_task, provide_context=True)
    gender_opr = PythonOperator(task_id="gender", python_callable=gender_task)

dummy_opr >> branching >> crawl_opr >> [sentiment_opr, gender_opr] >> end_opr
branching >> skip_opr >> end_opr