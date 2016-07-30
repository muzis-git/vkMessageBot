#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import sys
import shutil, os
os.chdir(os.path.abspath(os.path.expanduser('/opt/vkliferender')))
import json

from tools import mongo
from tools import bash

from colorama import *
init(autoreset=True)

from api import vk 
from api import vkMessageApi as vkMessage


owner_id='-77765978'
post_id='935'

table='jobs_flashmob'


# while True:

    # data = mongo.newJob()  

    # posts=getGroupPosts(token)

    # del posts['wall'][0]

    # for row in posts['wall']:
    #     # owner_id=str(row['owner_id'])
    #     post_id=str(row['id'])
    #     print post_id

    #     if int(row['comments']['count']) >0:
    #       getPostComments(post_id, token)





job_id=str(owner_id+'_'+post_id)
print (job_id)

# берем данные о посте и записываем в базу
post = vkMessage.getGroupPostById(post_id)

if post:

    post["_id"]=str(job_id)

    try:
        mongo.insert(table,post)

    except Exception, e:
        mongo.update(table,post)


# ищем комменты
comments = vkMessage.getPostComments(post_id)

video= []
videoidlist= []
musicidlist= []

if comments:   

    print (Fore.YELLOW + '******** Comment find')
    
    post_comments={}
    post_comments['_id']=str(job_id)

    
    if comments['items']:
        for row in comments['items']:


            if 'attachments' in row:

                for items in row['attachments']:

                    if items['type']=='video':
                    
                        print(json.dumps(items, indent=4, sort_keys=True, ensure_ascii=False))

                        video.append(items['video'])

                        videoId=str(items['video']['owner_id'])+'_'+str(items['video']['id'])

                        videoidlist.append(videoId)

                    elif items['type']=='audio':

                        if str(row['from_id']) == owner_id:

                            print (Fore.YELLOW + '**** Music set')

                            print(json.dumps(items, indent=4, sort_keys=True, ensure_ascii=False))

                            musicId=str(items['audio']['owner_id'])+'_'+str(items['audio']['id'])

                            musicidlist.append(musicId)




                # запрос в апи, на список файлов по списку айди
                videoidStr=', '.join(videoidlist)
    
                videoFiles=vk.getVideoFiles(videoidStr)

                videoFiles.pop(0) # удаляем счетчик вначале листа

                post_comments['video']=videoFiles


                

                # запрос в апи, на список музыки по списку айди
                musicidStr=', '.join(musicidlist)
    
                musicFiles=vk.getAudio(musicidStr)

                post_comments['music']=musicFiles

                post_comments['status']=1

                mongo.update(table,post_comments)






    #отправляем в обработку
    
    # runTime = bash.runCMD('./app/vkMessageApp.py '+str(job_id), False, True)

    # #записываем длину фильма, можно и другие параметры
    # d = {'rendertime': round(runTime)}
    # mongo.updateJob(job_id,d)



    # time.sleep(10)


