import json
import datetime
import csv
import time
import datetime
import pprint
import sys
import os
import requests
import functools
import operator
# set since 3000 recursions, for post with >= 25000 comments
sys.setrecursionlimit(3000)

try:
    from urllib.request import urlopen, Request
except ImportError:
    from urllib2 import urlopen, Request

num_post = 0
num_comments = 0
num_comm_per_page = 25

def add_num_post(value):
    global num_post
    num_post = num_post + value


def add_num_comments(value):
    global num_comments
    num_comments = num_comments + value


def request_until_succeed(url):
    req = Request(url)
    success = False
    while success is False:
        try:
            response = urlopen(req)
            if response.getcode() == 200:
                success = True
        except Exception as e:
            print(e)
            time.sleep(5)

            print("Error for URL {}: {}".format(url, datetime.datetime.now()))
            print("Retrying.")

    return response.read()
def get_my_key(obj):
  return obj.get("created_time")[0: 10] 

# def writeFile(path, name, text):
#     write_file = open(path + name, "w+")
#     write_file.write(text)
#     write_file.close()

# The function for taking comments is recursive. Comments are taken 25 at a time.
# There is a maximum number of recursion for the python interpreter (= 1000).
# If the post has a number of comments > 25000 (25000/25 = 1000), our interpreter crash.
# This function is useful for dynamically increase the maximum number of recursions possible by the Python interpreter


def set_recursion_limit(total_comments):
    for key, value in total_comments.iteritems():
        if key == "total_count":
            sys.setrecursionlimit(value/num_comm_per_page)

####################################################################
#                       SCRAPING POSTs                             #
####################################################################

# first request will be of the type:
# https://graph.facebook.com/v7.0/v2.11/page_id/posts?access_token=....
# then, will be gather all the values next in the json file in order to do at the next request


def scrape_first_posts_in_page(page_id, access_token):
    base = "https://graph.facebook.com/v8.0/"
    parameters = "&access_token={}".format(access_token)
    fields = "?fields=posts"
    num_page = 1

    url = base + page_id + fields + parameters
    # print(url)
    print("\n scraping posts in page: " + str(num_page))
    json_downloaded = request_until_succeed(url)
    # Json(casted in list) data from our request
    data = json.loads(json_downloaded)['posts']['data']
    # this are used for take 'next' element in the dictionary
    next_post = json.loads(json_downloaded)['posts']['paging']
    for key, value in next_post:
        if key == "next":
            next_value = value

    writeFile("./posts/", str(num_page) + ".next_value.txt", next_value)
    print("\n writing " + str(num_page) + " next_value")

    loops_for_scraping_comments(num_page, data, post_array, access_token)

    scrape_all_posts_in_page(next_value, num_page + 1)


def scrape_all_posts_in_page(url, num_page, post_array, access_token):
    if url == "":
      return
    else: 
      json_downloaded = request_until_succeed(url)
      # Json(casted in dictionary) data from our request
      data = json.loads(json_downloaded)['data']
      # this are used for take 'next' element in the dictionary
      next_post = json.loads(json_downloaded)['paging']

      #pp = pprint.PrettyPrinter(indent=2)
      # pp.pprint(next_post)
      key = "next"
      if key in next_post:
          next_value = next_post.get("next")
      else: next_value = ""
        
      print("\n scraping posts in page: " + str(num_page))

      loops_for_scraping_comments(num_page, data, post_array, access_token)

      scrape_all_posts_in_page(next_value, num_page + 1, post_array, access_token)

####################################################################
#                       SCRAPE POST'S COMMENTS                     #
####################################################################

# function for scrape single post's comments


def loops_for_scraping_comments(num_page, data, post_array, access_token):
    # retrieve data, message and id (useful for querying the comments)
    extension = ".json"
    i = 0
    # print(len(data))
    # count num_post
    add_num_post(len(data))

    while (i < len(data)):
        print("\n   scraping post " + str(i + 1) + " in page: " + str(num_page))

        created_time = data[i]['created_time']

        # use get method over the dictionary because the comment couldn't exist and Facebook doesn't generate the corresponding item in the Json file

        id_post = data[i]['id']
        # shares_count_json = requests.get("https://graph.facebook.com/v8.0/"+ id_post + "?fields=shares" + "&access_token={}".format(access_token))
        # if shares_count_json.json().get("shares") is None:
        #   shares_count = 0
        # else:  
        #   shares_count = shares_count_json.json().get("shares").get("count")   // shares count (important)
        scrape_starttime = datetime.datetime.now()
        comments = scrape_first_comments_from_post_id(id_post, access_token)
        print("   Done! Comment Processed in {}".format(
            datetime.datetime.now() - scrape_starttime))
        # for items in comments:
        #   comment_id = items["id"]
        #   comment_url = "https://graph.facebook.com/v8.0/"+ comment_id + 
        #   requests.get()

        # name_file = str(created_time).replace(':', '.') + \
        #     "page_" + str(num_page) + "_posts" + str(i + 1)
        
        # dict_data = {
        #     "created_time" : str(created_time), 
        #     "post_id" : str(id_post),
        #     "comments": comments,
        #     "shares_count" : shares_count
        # }                                                                           // json dump (important)
        
        post_array.append(comments)
        # with open("./posts/" + name_file + extension, 'w', encoding='utf-8') as f:
        #   json.dump(dict_data, f, ensure_ascii=False, indent=4)
        i = i + 1


def scrape_first_comments_from_post_id(post_id, access_token):
    # with filter=stream should also gather the aswers to comments, but it seems doesn't work
    # https://graph.facebook.com/v7.0/v2.11/post_id/comments?filter=stream&summary=true&access_token=2081983152047773|cUqdwRV6VnEZBTwAwmv5wdBQEBw
    base = "https://graph.facebook.com/v8.0/"
    parameters = "&access_token={}".format(access_token)
    fields = "/comments?filter=stream&summary=true"

    scr_data = []
    url = base + post_id + fields + parameters
    json_downloaded = request_until_succeed(url)

    data = json.loads(json_downloaded)['data']

    if json.loads(json_downloaded).get('paging') is None:
        next_post = {}
    else:
        next_post = json.loads(json_downloaded).get('paging')

    total_comments = json.loads(json_downloaded)['summary']

    # set_recursion_limit(total_comments)

     # search next post url
    for key in next_post:
        if key == "next":
            scr_data = scrape_all_comments_from_post_id(next_post.get("next"))

    return data + scr_data


def scrape_all_comments_from_post_id(url):
    scr_data = []
    json_downloaded = request_until_succeed(url)

    # Json(casted in dictionary) data from our request
    data = json.loads(json_downloaded)['data']
    # this are used for take 'next' element in the dictionary
    next_post = json.loads(json_downloaded)['paging']

    comment_count = 0
    for count in data:
        comment_count += 1

    # count comments
    add_num_comments(comment_count)

    for key in next_post:
        if key == "next":
            scr_data = scrape_all_comments_from_post_id(next_post.get("next"))

    return data + scr_data


# if __name__ == '__main__':

#     filename_n_v = []

#     for filename in os.listdir('./posts/'):
#         if filename.endswith(".next_value"):
#             filename_n_v.append(filename)
def filter_function(item):
    if item.get("message") == "":
      return False
    return True
def main_modify(arr):
  obj_arr = []
  for x in range(len(arr)):
    if x == 0:
      temp_dict = {"created_time": arr[x].get("created_time")[0 : 10], "comments": [arr[x].get("message")]}
      obj_arr.append(temp_dict)
    else: 
      if not arr[x].get("created_time")[0: 10] == arr[x-1].get("created_time")[0 : 10]:
        temp_dict = {"created_time": arr[x].get("created_time")[0 : 10], "comments": [arr[x].get("message")]}
        obj_arr.append(temp_dict)
      else:
        temp_pointer = len(obj_arr) - 1
        print(temp_pointer)
        obj_arr[temp_pointer]["comments"].append(arr[x].get("message"))
  return obj_arr
def scrape_all_posts(app_id, app_secret, access_short_token, page_id):
    # app_id = "392288491810886"
    # app_secret = "1b3342f87bb28ffaef76f80ec1685cbd"
    # access_token = "EAAFkyMg0MEYBAIBZAE1XSg6CDMtZBBztsAslSfnQ31vIofASVROjYOijYaqNdoTkVzXk7ZB2167f6CcqtttBxB37fzQasZC8UYOywPP8ZCxWNJrvPndsNVvOvBTZCU1Nl1T5AFftGorqedxHzgfXD8OddFGfR9J5nX2In8MFLZBPA4ZBhWoJEeHJn5QkRkWoQQFW0kfHUeJXUgZDZD"
    # page_id = "meibook2018" 
    long_request_token = "https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=" + app_id + "&client_secret=" + app_secret + "&fb_exchange_token=" + access_short_token
    print(long_request_token)
    response_long = requests.get(long_request_token)
    res_long_token = response_long.json()
    access_token = res_long_token.get("access_token")
    print(access_token)
    post_array = []
    # final_comments = []
    num_page = 1
    url = "https://graph.facebook.com/v8.0/" + page_id + "/posts?access_token=" + access_token + "&limit=25"

    scrape_starttime = datetime.datetime.now()
    scrape_all_posts_in_page(url, num_page, post_array, access_token)
    # for item in post_array:
    #   for key, value in item:
    #     if key = "comments":
    flatted_cmt_array = functools.reduce(operator.iconcat, post_array, [])
    flatted_cmt_array.sort(key = get_my_key)
    arr = list(filter(filter_function, flatted_cmt_array))
    result_arr = main_modify(arr)
    return result_arr