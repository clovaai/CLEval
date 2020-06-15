#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
sys.path.append('./')
import json
from io import BytesIO
import zipfile
import re
from datetime import datetime
import importlib
import sqlite3
import rrc_evaluation_funcs
from config.config import *

from validation import validate_data
from script import cleval_evaluation

from arg_parser import PARAMS

try:
    from bottle import route, run, request, static_file, url, template, TEMPLATE_PATH, HTTPResponse, redirect
except ImportError:
    print("""Required module not found: Bottle. Installation: pip install --user bottle""")
    sys.exit(-1)

try:
    from PIL import Image
except ImportError:
    print("""Required module not found: Pillow. Installation: pip install --user Pillow""")
    sys.exit(-1)

TEMPLATE_PATH.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "views")))


def image_name_to_id(name):
    id_ = name.replace('.jpg', '').replace('.png', '').replace('.gif', '').replace('.bmp', '')
    return id_


def get_sample_id_from_num(num):
    imagesFilePath = os.path.dirname(os.path.abspath(__file__)) + "/gt/images.zip"
    archive = zipfile.ZipFile(imagesFilePath,'r')
    current = 0
    for image in archive.namelist():
        if image_name_to_id(image) != False:
            current += 1
            if (current == num):
                return image_name_to_id(image)
            
    return False


def get_sample_from_num(num):
    imagesFilePath = os.path.dirname(os.path.abspath(__file__)) + "/gt/images.zip"
    archive = zipfile.ZipFile(imagesFilePath,'r')
    current = 0
    for image in archive.namelist():
        if image_name_to_id(image) != False:
            current += 1
            if (current == num):
                return image,archive.read(image)
            
    return False


def get_samples():
    imagesFilePath = os.path.dirname(os.path.abspath(__file__)) + "/gt/images.zip"
    archive = zipfile.ZipFile(imagesFilePath,'r')
    num_samples = 0
    samples_list = []
    for image in archive.namelist():
        if image_name_to_id(image) != False:
            num_samples += 1
            samples_list.append(image)
            
    return num_samples,samples_list

@route('/static/:path#.+#', name='static')
def static(path):
    return static_file(path, root=os.path.abspath(os.path.join(os.path.dirname(__file__), "static")))

@route('/static_custom/:path#.+#', name='static_custom')
def static_custom(path):
    return static_file(path, root=os.path.abspath(os.path.join(os.path.dirname(__file__), "static_custom")))

@route('/gt/:path#.+#', name='static_gt')
def static_gt(path):
    return static_file(path, root=os.path.abspath(os.path.join(os.path.dirname(__file__), "gt")))

@route('/favicon.ico')
def favicon():
    return static_file("Clova-ico.png", root=os.path.abspath(os.path.join(os.path.dirname(__file__), "static")))


@route('/')
def index():
    
    _, images_list = get_samples()

    page = 1
    if 'p' in request.query:
        page = int(request.query['p'])
        
    subm_data = get_all_submissions()

    vars = {
            'url': url,
            'acronym': acronym,
            'title': title,
            'images': images_list,
            'method_params': method_params,
            'page': page,
            'subm_data': subm_data,
            'submit_params': submit_params,
            'instructions': instructions,
            'extension': gt_ext
            }
    return template('index', vars)


@route('/exit')
def exit():
    sys.stderr.close()


@route('/method/', methods=['GET'])
def method():
    
    _, images_list = get_samples()
    
    results = None
    page = 1
    subm_data = {}
    
    if 'm' in request.query:
        id = request.query['m']
        submFilePath = os.path.dirname(os.path.abspath(__file__)) + "/output/results_" + id + ".zip"

        if os.path.isfile(submFilePath):
            results = zipfile.ZipFile(submFilePath,'r')
            
        if 'p' in request.query:
            page = int(request.query['p'])
        
        subm_data = get_submission(id)
        
        if results is None or subm_data is None:
            redirect('/')
    else:
        redirect('/')

    vars = {
        'url': url,
        'acronym': acronym,
        'title': title,
        'images': images_list,
        'method_params': method_params,
        'sample_params': sample_params,
        'results': results,
        'page': page,
        'subm_data': subm_data
    }
    return template('method', vars)


@route('/sample/')
def sample():
    
    num_samples, images_list = get_samples()

    sample = int(request.query['sample'])
    
    methodId = request.query['m']
    subm_data = get_submission(methodId)
    
    samplesValues = []
    
    id = get_sample_id_from_num(int(sample))
    sampleId = id + ".json"
    
    subms = get_all_submissions()
    for methodId, methodTitle, _, _ in subms:
        zipFolderPath = os.path.dirname(os.path.abspath(__file__)) + "/output/results_" + str(methodId)
        sampleFilePath = zipFolderPath + "/" + sampleId
        
        if os.path.isfile(sampleFilePath) == False:
            submFilePath = os.path.dirname(os.path.abspath(__file__)) + "/output/results_" + str(methodId) + ".zip"
            archive = zipfile.ZipFile(submFilePath,'r')
        
            if os.path.exists(zipFolderPath) == False:
                os.makedirs(zipFolderPath)
             
            archive.extract(sampleId, zipFolderPath)
            
        file = open(sampleFilePath,"r")
        results = json.loads(file.read())
        file.close()
        
        # results = json.loads(archive.read(id + ".json"))

        sampleResults = {"id": methodId, "title": methodTitle}
        for k, v in sample_params.items():
            if k not in results:
                continue
            sampleResults[k] = results[k]
            
        samplesValues.append(sampleResults)
    
    vars = {
                'url': url,
                'acronym': acronym,
                'title': title + ' - Sample ' + str(sample) + ' : ' + images_list[sample-1],
                'sample': sample,
                'num_samples': num_samples,
                'subm_data': subm_data,
                'samplesValues': samplesValues,
                'sample_params': sample_params,
                'customJS': customJS,
                'customCSS': customCSS
            }
    return template('sample',vars)



@route('/sampleInfo/', methods=['GET'])
def get_sample_info():
    
    methodId = request.query['m']    
    submFilePath = os.path.dirname(os.path.abspath(__file__)) + "/output/results_" + methodId + ".zip"
    archive = zipfile.ZipFile(submFilePath,'r')
    id = get_sample_id_from_num(int(request.query['sample']))
    results = json.loads(archive.read(id + ".json"))
    return json.dumps(results)

@route('/image_thumb/', methods=['GET'])
def image_thumb():

    sample = int(request.query['sample'])
    fileName,data = get_sample_from_num(sample)
    ext = fileName.split('.')[-1]
    
    f = BytesIO(data)	
    image = Image.open(f)

    maxsize = (205, 130)
    image.thumbnail(maxsize)
    output = BytesIO()

    if ext=="jpg":
            im_format = "JPEG"
            header = "image/jpeg"
            image.save(output,im_format, quality=80, optimize=True, progressive=True)
    elif ext == "gif":
            im_format = "GIF"
            header = "image/gif"
            image.save(output,im_format)
    elif ext == "png":
            im_format = "PNG"
            header = "image/png"
            image.save(output,im_format, optimize=True)
    
    contents = output.getvalue()
    output.close()
    
    body = contents
    headers = dict()
    headers['Content-Type'] = header
    if 'c' in request.query:
        headers['Cache-Control'] = "public, max-age=3600"
    
    return HTTPResponse(body, **headers)    


@route('/image/', methods=['GET'])
def image():
    sample = int(request.query['sample'])
    fileName,data = get_sample_from_num(sample)
    ext = fileName.split('.')[-1]
    if ext=="jpg":
        header = "image/jpeg"
    elif ext == "gif":
        header = "image/gif"    
    elif ext == "png":
        header = "image/png"            
    
    body = data
    headers = dict()
    headers['Content-Type'] = header
    if 'c' in request.query:
        headers['Cache-Control'] = "public, max-age=3600"
    return HTTPResponse(body, **headers)    


@route('/gt_image/', methods=['GET'])
def gt_image():
    imagesFilePath = os.path.dirname(os.path.abspath(__file__)) + "/gt/gt.zip"
    archive = zipfile.ZipFile(imagesFilePath,'r')
    fileName = request.query['sample']
    ext = fileName.split('.')[-1]
    if ext=="jpg":
        header = "image/jpeg"
    elif ext == "gif":
        header = "image/gif"    
    elif ext == "png":
        header = "image/png"            
    
    data = archive.read(fileName)
    body = data
    headers = dict()
    headers['Content-Type'] = header
    if 'c' in request.query:
        headers['Cache-Control'] = "public, max-age=3600"
    return HTTPResponse(body, **headers)   


@route('/gt_file/', methods=['GET'])
def gt_file():
    imagesFilePath = os.path.dirname(os.path.abspath(__file__)) + "/gt/gt.zip"
    archive = zipfile.ZipFile(imagesFilePath,'r')
    fileName = request.query['sample']
    ext = fileName.split('.')[-1]
    if ext=="xml":
        header = "text/xml"

    data = archive.read(fileName)
    body = data
    headers = dict()
    headers['Content-Type'] = header
    if 'c' in request.query:
        headers['Cache-Control'] = "public, max-age=3600"
    return HTTPResponse(body, **headers)   


@route('/subm_image/', methods=['GET'])
def subm_image():
    submFilePath = os.path.dirname(os.path.abspath(__file__)) + "/output/subm_" + str(request.query['m'])  + ".zip"
    archive = zipfile.ZipFile(submFilePath,'r')
    fileName = request.query['sample']
    ext = fileName.split('.')[-1]
    if ext=="jpg":
        header = "image/jpeg"
    elif ext == "gif":
        header = "image/gif"    
    elif ext == "png":
        header = "image/png"            
    
    data = archive.read(fileName)
    body = data
    headers = dict()
    headers['Content-Type'] = header
    if 'c' in request.query:
        headers['Cache-Control'] = "public, max-age=3600"
    return HTTPResponse(body, **headers)  


@route('/result_image/', methods=['GET'])
def result_image():
    submFilePath = os.path.dirname(os.path.abspath(__file__)) + "/output/results_" + str(request.query['m'])  + ".zip"
    archive = zipfile.ZipFile(submFilePath,'r')
    fileName = request.query['name']
    ext = fileName.split('.')[-1]
    if ext=="jpg":
        header = "image/jpeg"
    elif ext == "gif":
        header = "image/gif"    
    elif ext == "png":
        header = "image/png"            
    
    data = archive.read(fileName)
    body = data
    headers = dict()
    headers['Content-Type'] = header
    if 'c' in request.query:
        headers['Cache-Control'] = "public, max-age=3600"
    return HTTPResponse(body, **headers)  


@route('/evaluate', method=['POST','GET'])
def evaluate():
    
    id_ = 0
    submFile = request.files.get('submissionFile')
    
    if submFile is None:
        resDict = {"calculated":False,"Message":"No file selected"}
        if request.query['json']=="1":
            return json.dumps(resDict)
        else:        
            vars = {'url': url, 'title': 'Method Upload ' + title, 'resDict': resDict}
            return template('upload',vars)    
    else:
        
        name, ext = os.path.splitext(submFile.filename)
        if ext not in ('.' + gt_ext):
            resDict = {"calculated":False,"Message":"File not valid. A " + gt_ext.upper() + " file is required."}
            if request.query['json']=="1":
                return json.dumps(resDict)            
            else:
                vars = {'url':url, 'title':'Method Upload ' + title,'resDict':resDict}
                return template('upload', vars)
    
        p = {
            'g': os.path.dirname(os.path.abspath(__file__)) + "/gt/gt." + gt_ext, 
            's': os.path.dirname(os.path.abspath(__file__)) + "/output/subm." + gt_ext, 
            'o': os.path.dirname(os.path.abspath(__file__)) + "/output"
        }
        global PARAMS
        setattr(PARAMS, 'GT_PATH', os.path.dirname(os.path.abspath(__file__)) + "/gt/gt." + gt_ext)
        setattr(PARAMS, 'SUBMIT_PATH', os.path.dirname(os.path.abspath(__file__)) + "/output/subm." + gt_ext)
        setattr(PARAMS, 'OUTPUT_PATH', os.path.dirname(os.path.abspath(__file__)) + "/output")

        if os.path.isfile(PARAMS.SUBMIT_PATH):
            os.remove(PARAMS.SUBMIT_PATH)

        submFile.save(PARAMS.SUBMIT_PATH)

        
        # apply response to evaluation
        if request.forms.get('transcription') == 'on':
            setattr(PARAMS, 'TRANSCRIPTION', True)
        else:
            setattr(PARAMS, 'TRANSCRIPTION', False)
        
        if request.forms.get('confidence') == 'on':
            setattr(PARAMS, 'CONFIDENCES', True)
        else:
            setattr(PARAMS, 'CONFIDENCES', False)

        if request.forms.get('mode') == 'endtoend':
            setattr(PARAMS, 'E2E', True)
        else:
            setattr(PARAMS, 'E2E', False)

        resDict = rrc_evaluation_funcs.main_evaluation(validate_data, cleval_evaluation)

        if resDict['calculated'] == True:
            dbPath = os.path.dirname(os.path.abspath(__file__)) + "/output/submits"
            conn = sqlite3.connect(dbPath)
            cursor = conn.cursor()
            
            submTitle = request.forms.get('title')
            if submTitle=="":
                submTitle = "unnamed"
                
            cursor.execute('INSERT INTO submission(title,sumbit_date,results,is_end2end) VALUES(?,?,?,?)',(submTitle, datetime.now().strftime("%Y-%m-%d %H:%M"),json.dumps(resDict['method']), PARAMS.E2E))
            conn.commit()
            id_ = cursor.lastrowid

            os.rename(p['s'], p['s'].replace("subm." + gt_ext, "subm_" + str(id_) + "." + gt_ext))
            os.rename(p['o'] + "/results.zip", p['o'] + "/results_" + str(id_) + ".zip" )

            conn.close()
        if request.query['json']=="1":
            return json.dumps( {"calculated": resDict['calculated'],"Message": resDict['Message'],'id':id_})
        else:
            vars = {'url': url, 'title': 'Method Upload ' + title, 'resDict': resDict, 'id': id_}
            return template('upload', vars)

@route('/delete_all', method='POST')
def delete_all():
    output_folder = os.path.dirname(os.path.abspath(__file__)) + "/output"
    try:    
        for root, dirs, files in os.walk(output_folder, topdown=False):
            for f in files:
                os.remove(os.path.join(root, f))
            for d in dirs:
                os.rmdir(os.path.join(root, d))
    except:
        print("Unexpected error:", sys.exc_info()[0])
        
@route('/delete_method', method='POST')
def delete_method():
    id = request.forms.get('id')
    
    try:
        output_folder = os.path.dirname(os.path.abspath(__file__)) + "/output/results_" + id
        if os.path.isdir(output_folder):
            for root, dirs, files in os.walk(output_folder, topdown=False):
                for f in files:
                    os.remove(os.path.join(root, f))
                for d in dirs:
                    os.rmdir(os.path.join(root, d))
            os.rmdir(output_folder)
        subm_file = os.path.dirname(os.path.abspath(__file__)) + "/output/results_" + id + "." + gt_ext
        results_file = os.path.dirname(os.path.abspath(__file__)) + "/output/subm_" + id + ".zip"
        os.remove(subm_file)
        os.remove(results_file)
    except:
        print("Unexpected error:", sys.exc_info()[0])
        
    dbPath = os.path.dirname(os.path.abspath(__file__)) + "/output/submits"
    conn = sqlite3.connect(dbPath)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM submission WHERE id=:id and is_end2end=:e2e', {"id": id,
                                                                               "e2e": PARAMS.E2E})
    conn.commit()
    conn.close()
    
@route('/edit_method', method='POST')
def edit_method():
    id = request.forms.get('id')
    name = request.forms.get('name')
    
    dbPath = os.path.dirname(os.path.abspath(__file__)) + "/output/submits"
    conn = sqlite3.connect(dbPath)
    cursor = conn.cursor()
    cursor.execute('UPDATE submission SET title=? WHERE id=?', (name, id))
    conn.commit()
    conn.close()    
    
def get_all_submissions():
    dbPath = os.path.dirname(os.path.abspath(__file__)) + "/output/submits"
    conn = sqlite3.connect(dbPath)
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS submission(id integer primary key autoincrement, is_end2end varchar(20), title varchar(50), sumbit_date varchar(12),results TEXT)""")
    conn.commit()

    cursor.execute('SELECT id,title,sumbit_date,results FROM submission')
    data = cursor.fetchall()
    conn.close()
    return data


def get_submission(id_):
    dbPath = os.path.dirname(os.path.abspath(__file__)) + "/output/submits"
    conn = sqlite3.connect(dbPath)
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS submission(id integer primary key autoincrement, title varchar(50), sumbit_date varchar(12),results TEXT)""")
    conn.commit()

    cursor.execute('SELECT id,title,sumbit_date,results FROM submission WHERE id=:id', {"id": id_})
    
    # cursor.execute('SELECT id,title,sumbit_date,results FROM submission WHERE id=:id and is_end2end=:e2e', {"id": id_,
    #                                                                                                         "e2e": PARAMS.E2E})
    sumbData = cursor.fetchone()
    conn.close()
    
    return sumbData


if __name__=='__main__':
    print("***********************************************")
    print("RRC Standalone Task")
    print("-----------------------------------------------")
    print('Command line client:\ncurl -F "submissionFile=submit.zip" http://127.0.0.1:{}/evaluate'.format(PARAMS.PORT))
    print("\nGUI client:firefox http://127.0.0.1:{}".format(PARAMS.PORT))
    print("-----------------------------------------------")
    run(host='0.0.0.0', port=PARAMS.PORT, debug=True)
