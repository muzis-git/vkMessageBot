#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

# https://habrahabr.ru/post/247987/
from __future__ import division

import os
import logging
import requests
import json

from api import youtubedl as dl

from colorama import *
init(autoreset=True)

logging.getLogger('requests').setLevel(logging.CRITICAL)

# токен от моего приложения
# token_audio = getToken()
token =''


vk_method="https://api.vkontakte.ru/method/"



# **********************************************************************************
# Muzis


def getPosts(access_token,tag="life2film",count=1):

	# ищем посты по всему контакту, с нашим тегом

	if not access_token: return

	posts= {}

	# Адрес запроса
	resp = requests.get(vk_method+'newsfeed.search',
	                'q={}&extended=1&count={}&access_token={}&v=5.53'.format(tag, count, access_token))
	
	posts = resp.json()['response']

	if posts:

		print (Fore.YELLOW + '********** Find posts: '+str(posts[0]))

		if int(posts[0])>0:

			print (json.dumps(posts, indent=4, sort_keys=True, ensure_ascii=False))
			del posts[0]			
		
	else:
		print (Fore.RED + 'Error, NO: '+tag)
	
	return posts


def getGroupPosts(count=30,tag="life2film",group_id='-77765978'):

	# ищем посты по нашей группе, с нашим тегом

	posts= {}

	# Адрес запроса
	resp = requests.get(vk_method+'wall.search',
	                'query={}&owner_id={}&extended=1&count={}&access_token={}&v=5.53'.format(tag, group_id, count, token))
	
	
	posts = resp.json()['response']

	if posts:

		# print (Fore.YELLOW + '********** Find posts: '+str(posts[0]))

		# print (json.dumps(posts, indent=4, sort_keys=True, ensure_ascii=False))
		pass
		
	else:
		print (Fore.RED + 'Error, NO: '+tag)
		return {}
	
	return posts


def getGroupPostById(post_id,count=30,tag="life2film",group_id='-77765978'):

	# ищем посты по нашей группе, с нашим тегом

	posts= {}

	wall_id = group_id+'_'+post_id

	# Адрес запроса
	resp = requests.get(vk_method+'wall.getById',
	                'posts={}&extended=1&access_token={}'.format(wall_id,token))
	
	
	posts = resp.json()['response']

	if posts:

		print (json.dumps(posts, indent=4, sort_keys=True, ensure_ascii=False))
		
	else:
		print (Fore.RED + 'Error, NO: '+tag)
		return {}
	
	return posts



def getPostComments(post_id,count=100,group_id='-77765978'):

	# ищем комменты к посту в группе

	if not post_id: return

	comments= {}

	# Адрес запроса
	resp = requests.get(vk_method+'wall.getComments',
	                'owner_id={}&post_id={}&count={}&extended=1&access_token={}&v=5.53'.format(group_id,post_id,count,token))
	
	

	if not 'error' in resp.json():
		if resp.json():
		
			comments = resp.json()['response']

			# print (Fore.YELLOW + '********** Find comments: '+str(posts[0]))

			print (json.dumps(comments, indent=4, sort_keys=True, ensure_ascii=False))
		
	else:
		print (Fore.RED + 'Error, No PostComments: '+post_id)
		print (json.dumps(resp.json(), indent=4, sort_keys=True, ensure_ascii=False))
	
	return comments

		

# **********************************************************************************

if __name__ == "__main__":


	owner_id='-77765978'


	# posts=getGroupPosts(token)

	# del posts['wall'][0]

	# for row in posts['wall']:
	#     # owner_id=str(row['owner_id'])
	#     post_id=str(row['id'])
	#     print post_id

	#     if int(row['comments']['count']) >0:
	#     	getPostComments(post_id, token)


	getGroupPostById('935')
	getPostComments('935')




			