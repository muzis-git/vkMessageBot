#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import tools
import sys
import time
import requests
import logging
import uuid
import shutil, os
import socket
import json
import glob
import traceback

logging.getLogger('requests').setLevel(logging.CRITICAL)


from tools import audio
from tools import mongo

import template

from colorama import *
init(autoreset=True)

from api import telegram as bot
from api import vk 

from app import common


table='jobs_flashmob'



#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Хелперы


def allParamInit(job_id,data):
    # генерируем переменные 

    appName='vkMessageApp'

    jobFormat=640
    bitrate="800"
    w,h = (640,360)
    qp=20


    if data:

        local_input = "/tmp/up/"+job_id +'/'     # локально скачиваем
        local_output= "/tmp/conv/"+job_id +'/'      # путь для конвертации   

        local_input_full = local_input 
        local_output_full = local_output   
        local_output_video = local_output_full + 'video'    

        local_film = local_output_full + 'film'      
        # urlfilm = str(data['userId'])+"_"+str(data['_id']) +'.mp4'
        urlfilm = str(job_id) +'.mp4'
        pathFinal = local_film +'/'+urlfilm

        if int(data['sound'])==1:
            sound = True
        else:
            sound = False


        allParam={
            'jobFormat':jobFormat
            ,'job_id':job_id
            ,'local_input':local_input
            ,'local_input_full':local_input_full
            ,'local_output_full':local_output_full
            ,'local_output_video':local_output_video
            ,'local_output':local_output
            ,'local_film':local_film
            ,'pathFinal':pathFinal
            ,'urlfilm':urlfilm
            ,'bitrate':bitrate
            ,'width':w
            ,'height':h
            ,'qp':qp
            ,'appName':appName
            ,'speed':1
            ,'sound':sound
            }

        print (json.dumps(allParam, indent=4, sort_keys=True))

        allParam.update(data)

    return allParam


def stepDownloadVideo(videos,allParam):

    print (Fore.GREEN +'---------- Start VK Download%s -------------------' %allParam['local_output'] )

    videos = vk.downloadVideos(videos,allParam)

    return videos

def stepMusic(data,allParam):

    #период аудио
    print (Fore.GREEN +'---------- Audio %s -------------------' %allParam['local_output'] )

    music={}

    audioParam = {
            'musicType':'noMusic',
            'audio_period':2
        }

    if 'music' in data:

        if data['music'][0]:

            music=vk.downloadMusic(data['music'],allParam)   
            # если пользователь выбрал свою музыку

            #определяем ритм 
            audioParam = audio.userMusic(allParam, music)



        


    print (json.dumps(audioParam, indent=4, sort_keys=True))

    allParam.update(audioParam)

    return music


def createDescription(allParam):
    if allParam:
        description = """
Фильм создан в видеоредакторе LIFE2FILM. 
Это просто! Попробуй создать и ты https://vk.com/life2film
        
Автор ролика: https://vk.com/%s
""" % (allParam['userId'])

        # description.format(allParam['userId'])

        if 'musicType' in allParam:
            if not allParam['musicType']=='noMusic':
                description+= """Музыка: %s""" % (allParam['audio_name'])
        

        description+= """
#life2film"""

        print description
        return description



def stepUpload(allParam,group_id='77765978'):

    print (Fore.GREEN +'---------- Start UPLOAD %s -------------------' %allParam['local_output'] )

    if not allParam['name']: allParam['name']='Мой @LIFE2FILM'

    description=createDescription(allParam)

    post={
        'name':allParam['name'],
        'description':description,
        # 'is_private':0,
        # 'wallpost':0,
        # 'link': link
        'group_id':group_id,
        'album_id':1,
        # 'privacy_view':0,
        # 'privacy_comment':xxxxx,
        # 'no_comments':0,
        # 'repeat':0
    
    }

    respDict=vk.saveVideo(post,allParam['pathFinal'])

    if respDict:
        allParam.update(respDict)
        mongo.updateJob(allParam['job_id'],respDict,table)
        mongo.updateFilm(allParam['job_id'],respDict)



def saveFilmsInfo(allParam,group_id='77765978'):

    #записываем длину фильма, можно и другие параметры

    if group_id:
        link='video-'+str(group_id)+'_'+str(allParam['video_id'])
    else:
        if 'video_id' in allParam:
            link='video'+str(allParam['userId'])+'_'+str(allParam['video_id'])
        else:
            return

    postFilm = {
        'urlfilm': str(allParam['urlfilm'])
        ,'link': str(link)
        ,'duration': str(allParam['duration'])
        ,'status': '10'
    }

    # print (Fore.YELLOW +json.dumps(postFilm, indent=4, sort_keys=True))


    allParam.update(postFilm)

    mongo.updateJob(allParam['job_id'],postFilm,table)
    mongo.updateFilm(allParam['job_id'],postFilm)

    fulllink='vk.com/'+link
    print (fulllink)

    vk.sendNotification(allParam['userId'],
        'Ваш фильм готов: '+fulllink);



def stepConvert(videos,allParam):

    print (Fore.GREEN +'---------- Start Converting %s -------------------' %allParam['local_input_full'] )

    #параметры для нарезки сегмнетов через ГОП
    if 'audio_period' in allParam:
        keyint = str(int(360*allParam['audio_period'])) #максимальная длина GOP в кадрах
        min_keyint = str(int(30*allParam['audio_period']*1.1)) # минимальная длина сегмента, кратно fps
        # scenecut = str(int(90-10*allParam['speed'])) # чувствительность, чем выше тем чаще режет (дефолт 40)
    else:
        keyint = 80
        min_keyint = 30

        
    jSegm={    
        'keyint':keyint
        ,'min_keyint':min_keyint
        ,'scenecut':80
        }

    print (json.dumps(jSegm, indent=4, sort_keys=True))
    allParam.update(jSegm)

    vid = []

    for index,file in enumerate(videos):

        print (json.dumps(file, indent=4, sort_keys=True))

        fconv=0

        # быстрый конвертер с GOP
        if 'tmp_url' in file:
            fconv = tools.newconvert.fast_convert(file, allParam)     

        if fconv:
            file['status']=-1
            print 'Статус -1'
        else:
          #если проблема исключить исходник
          print 'Удаляем исходник из задания'



    if not videos:
        return common.returnError(allParam['job_id'],'-300',message='Ошибка конвертации')

    return videos


def stepSegmnets(videos,allParam):

    print (Fore.GREEN +'---------- Start Salect Segments %s -------------------' %allParam['local_input_full'] )

    segments=[]

    for index,file in enumerate(videos):

        print (json.dumps(file, indent=4, sort_keys=True))

        #сохраняем анализ данных в базу, данные по сегментам
        if 'tmp_url' in file:
            segm = tools.segments.segments(file, allParam)
        else:
            continue

        print (str(index)+'/'+str(len(videos)-1)+' -> '+ str(round((index+1)*100/len(videos)))+'%')

        if segm:
            for subsegm in segm:
                segments.append(subsegm)

        
    if not segments:
        return common.returnError(allParam['job_id'],'-300',message='Ошибка  сегментации')

    return segments



#######################################################################

#######################################################################

def renderJob(job_id, test=False):
#основной модуль создания фильма, все собрано тут

    status = False

    local_input = "/tmp/up/"+job_id +'/'     # локально скачиваем
    local_output= "/tmp/conv/"+job_id +'/'      # путь для конвертации   
    videos=[]



    try:

        if not job_id: return False
        # if test: mongo.setQueue(job_id,1)

        #параметры задания в базе
        data = mongo.selectJob(job_id,table) 

        if not data: return False        
        if data is None : return False        

        data['chat_id']=121250082 #мой чат


        # bot.notify('Рендеринг VKlife: '+str(data['userId'])+', job_id: '+str(data['_id']))

        # #занимаем очередь
        # Queue=mongo.setQueue(job_id) 
        # # print ("Очередь: " + str(Queue))

        # if Queue:                
        #     # if int(data['status'])<=0:
        #     status=mongo.setStatus(job_id, '2')
        # else:
        #     status = False
        #     return False    

# Шаг 1 Инициализация ########################################################      

        print (Fore.GREEN + '---------- Start job: %s -------------------' %job_id )

        status=mongo.setStatus(job_id, '2',table)

        # jobFormat = int(data['format'])
        chat_id = str(data['chat_id'])
        # input_path  =  str(data['path_up'])

        #формируем все параметры
        allParam=allParamInit(job_id,data)

        #загружаем список видео
        videos = data['videos']
        if not videos:            
            return status

        # подсчитываем общую длину видео
        fDur = common.sumKeyDict(videos, 'duration')
        print (Fore.GREEN + 'all fDur: '+str(fDur))
        # fSize = sumKeyDict(videos, 'duration')
        allParam.update({'fDur':fDur})

        # если видео короткое, то просто склеиваем
        if (data['sound']=='1' and fDur<140) or (data['sound']=='0' and fDur<70):
            print (Fore.GREEN + 'Не нарезаем, видео короткое, просто склеиваем')
            allParam['renderType']='merge'

        print allParam['renderType']


        # создаем локальные временные папки с префиксом local_ 
        common.mkLocalDir(allParam)


# Шаг 2 Скачиваем Видео ######################################################## 

        videos=stepDownloadVideo(videos,allParam)
        if not videos:            
            return status

        status=  mongo.setStatus(job_id, '3',table)

# Шаг 3 Музыка ######################################################## 
   
        music = stepMusic(data,allParam)
        # if not music:            
        #     return returnError(job_id,'-300',message='Ошибка скачки музыки')

        # проверям визуально что скачалось
        command = 'ls -lah '+allParam['local_input_full']
        tools.bash.runCMD(command)

        status = mongo.setStatus(job_id, '4',table)

# Шаг 4 Конвертируем и сегментируем ##################################################

        if allParam['renderType']=='clip':
            # конвертируем
            videos = stepConvert(videos,allParam)
            # записываем сегменты
            segments = stepSegmnets(videos,allParam)
        else:
            segments = videos

        print (json.dumps(segments, indent=4, sort_keys=True))

        status = mongo.setStatus(job_id, '5',table)
   
        
# Шаг 5 Признаки #######################################################################

        # #выбираем сегменты
        # (segments, segDur) = mongo.selectSegments(data['group'])

        # if len(segments)==0 and len(videos)>1:
        #     status=mongo.setStatus(job_id, '-300')
        #     mongo.saveError({'job_id':job_id,'status':status,'error':'No Segments'})    
        #     return status        
        # if len(segments)==0:
        #     status=mongo.setStatus(job_id, '-400')
        #     return status


        # if len(segments)<3 and cutGop:
        #     status=mongo.setStatus(job_id, '-400')
        #     return status

        ##ищем признаки
        # tools.recognition.googlenet(segments, allParam)

        status=mongo.setStatus(job_id, '6',table)

# Шаг 6 Нарезка и склейка ########################################################


        # if len(segments)>1:
        #     concatPath=allParam['local_output']+'/cut/concat.mp4'

        #     #смотрим, делать ли клип или полностью клеить если короткий исходник
        #     cutRes=tools.cutter.cutSegments(segments, segDur, allParam, concatPath, cutGop)

        #     print cutRes
        #     concatDur=tools.ffprobe.getDuration(concatPath)
        #     print(Fore.YELLOW + 'Concat duration: '+ str(concatDur)+' sec')

        #     compression=100-int(concatDur*100/allParam['fDur'])

        #     if cutRes==0:
        #         concatDur=tools.ffprobe.getDuration(concatPath)
        #         print(Fore.YELLOW + 'Concat duration: '+ str(concatDur)+' sec')
        #     else:
        #         print(Fore.RED + 'Problem Concat')
        #         status=mongo.setStatus(job_id, '-300')
        #         mongo.saveError({'job_id':job_id,'status':status,'error':'Problem Concat'})    
        #         return status
        # else:
        #     print(Fore.YELLOW + 'No concat, 1 segment only')
        #     concatPath=allParam['local_output']+'/'+segments[0]['path']
        #     compression=0

        # #записываем отношение исходное/итоговая длина
        # print(Fore.YELLOW + 'K:'+str(compression)+'% compression')
        # d = {'compression': compression}
        # mongo.updateJob(job_id,d)

        status=mongo.setStatus(job_id, '7',table)


# Шаг 7 Рендеринг финала ########################################################
        
        print (Fore.GREEN +'---------- Start Rendering %s -------------------' %allParam['local_input_full'] )

        # if not test: bot.notifyRendering(data['chat_id'],50)

        # print (segments)

        if allParam['renderType']=='clip':
            print ('Clip type rendering')
            # рендерим клип
            duration = template.clip.render(allParam, segments)

        else:
            print ('Merge type rendering')
            #Рендерим сразу в быстром режиме
            duration = template.merge.render(allParam, segments)


        #Отпрвляем результат клиенту 
        if duration!=0:

            status=mongo.setStatus(job_id, '9',table)
    
            allParam.update({'duration': round(duration)})

            if test==False:

                stepUpload(allParam)
                status=mongo.setStatus(job_id, '10',table)
                saveFilmsInfo(allParam)
            else:
                status=10

                
        else:

            return common.returnError(job_id, '-400', 'Final render duration 0')

                    
        return status

#   Ошибки отлавливаем ##############################################################################

    except ValueError as err:
        error=traceback.format_exc()
        print('----------')
        print(err)
        print('----------')
        print(error)
        print('----------')

        mongo.saveError(job_id,status,'except',err) 

#   Выполнять всегда по завершению ################################################################


    finally:
        
        # если не закончили, значит ошибка
        if not int(status)==10:

            error=traceback.format_exc()
            common.returnError(job_id, '-300', 'Прервался со статусом '+str(status),str(error))
            # if not test: bot.notify('Error rendering...')

        # очистка 
        if os.path.exists(local_input) and local_input and not test and status:
            time.sleep(1)
            print (Fore.GREEN +'Удаляем мусор ...')
            try:
                shutil.rmtree(local_input)
                shutil.rmtree(local_output)
                for fl in glob.glob("*.log"):
                    os.remove(fl)
            except Exception,e:
                print('no delete...')
                print(e)
        
        time.sleep(2)




###################################################################################################
if __name__ == '__main__':

    test=False

    if len(sys.argv)>1: 
    #получили айди напрямую
        print sys.argv
        job_id=str(sys.argv[1])

    if len(sys.argv)>2: 
    #получили айди напрямую
        if sys.argv[2]=='test':
            test=True



    ######################################################################
    print test

    if job_id:
        print(job_id)

        #отправляем в обработку
        status = renderJob(job_id, test)
        print status

