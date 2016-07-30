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
	                'q={}&extended=1&count={}&access_token={}'.format(tag, count, access_token))
	
	posts = resp.json()['response']

	if posts:

		print (Fore.YELLOW + '********** Find posts: '+str(posts[0]))

		if int(posts[0])>0:

			print (json.dumps(posts, indent=4, sort_keys=True, ensure_ascii=False))
			del posts[0]			
		
	else:
		print (Fore.RED + 'Error, NO: '+tag)
	
	return posts


def getGroupPosts(access_token,count=2,tag="life2film",group_id='-77765978'):

	# ищем посты по нашей группе, с нашим тегом

	if not access_token: return

	posts= {}

	# Адрес запроса
	resp = requests.get(vk_method+'wall.search',
	                'query={}&owner_id={}&extended=1&count={}&access_token={}'.format(tag, group_id, count, access_token))
	
	
	posts = resp.json()['response']

	if posts:

		# print (Fore.YELLOW + '********** Find posts: '+str(posts[0]))

		print (json.dumps(posts, indent=4, sort_keys=True, ensure_ascii=False))
		
	else:
		print (Fore.RED + 'Error, NO: '+tag)
		return {}
	
	return posts


		

# **********************************************************************************

if __name__ == "__main__":


	path = "/tmp/downloads"

	if not os.path.exists(path):
	    os.makedirs(path)

	# getToken()

	getGroupPosts(token)


	