import json
import pprint
import sys;sys.path.append('./')
import zipfile
import re
import sys
import os
from io import StringIO

from validation import *
from file_utils import decode_utf8
from box_types import Box, QUAD, POLY

from arg_parser import PARAMS


def print_help():
    sys.stdout.write('Usage: python %s.py -g=<gt_path> -s=<submit_path> [-o=<outputFolder> -p=<jsonParams>]' % sys.argv[0])
    sys.exit(2)
    

def convert_LTRB2QUAD(points):
    """Convert point format from LTRB to QUAD"""
    new_points = [points[0], points[1], points[2], points[1], points[2], points[3], points[0], points[3]]
    return new_points
    
   
def parse_values_from_single_line(line, withTranscription=False, withConfidence=False, img_width=0, img_height=0) -> Box:
    """
    Validate the format of line. If the line is not valid, an exception will be raised.
    If max_width, and max_height are specified, all poi
    :param line:
    :param withTranscription:
    :param withConfidence:
    :param img_width:
    :param img_height:
    :return:
    """
    """
    Validate the format of the line. If the line is not valid an exception will be raised.
    If maxWidth and maxHeight are specified, all points must be inside the imgage bounds.
    Posible values are:
    LTRB=True: xmin,ymin,xmax,ymax[,confidence][,transcription] 
    LTRB=False: x1,y1,x2,y2,x3,y3,x4,y4[,confidence][,transcription]
    LTRB="POLY": x1,y1,x2,y2,x3,y3,x4,y4[,confidence][,transcription]

    box_type:
        - LTRB: add description
        - QUAD: add description
        - POLY: add description

    Returns values from a textline. Points , [Confidences], [Transcriptions]
    """
    confidence = 0.0
    transcription = ""
    points = []
    box_type = None
    
    numPoints = 4
    
    if PARAMS.BOX_TYPE == "LTRB":
        box_type = QUAD
        numPoints = 4
        
        if withTranscription and withConfidence:
            m = re.match(r'^\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*([0-9]+)\s*,\s*([0-9]+)\s*,\s*([0-1].?[0-9]*)\s*,(.*)$',line)
            if m == None :
                m = re.match(r'^\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*([0-9]+)\s*,\s*([0-9]+)\s*,\s*([0-1].?[0-9]*)\s*,(.*)$',line)
                raise Exception("Format incorrect. Should be: xmin,ymin,xmax,ymax,confidence,transcription")
        elif withConfidence:
            m = re.match(r'^\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*([0-9]+)\s*,\s*([0-9]+)\s*,\s*([0-1].?[0-9]*)\s*$',line)
            if m == None :
                raise Exception("Format incorrect. Should be: xmin,ymin,xmax,ymax,confidence")
        elif withTranscription:
            m = re.match(r'^\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*([0-9]+)\s*,\s*([0-9]+)\s*,(.*)$', line)
            if m == None :
                raise Exception("Format incorrect. Should be: xmin,ymin,xmax,ymax,transcription")
        else:
            m = re.match(r'^\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*([0-9]+)\s*,\s*([0-9]+)\s*,?\s*$', line)
            if m == None :
                raise Exception("Format incorrect. Should be: xmin,ymin,xmax,ymax")
            
        xmin = int(m.group(1))
        ymin = int(m.group(2))
        xmax = int(m.group(3))
        ymax = int(m.group(4))

        validate_min_max_bounds(lower_val=xmin, upper_val=xmax)
        validate_min_max_bounds(lower_val=ymin, upper_val=ymax)

        points = [float(m.group(i)) for i in range(1, (numPoints+1))]
        points = convert_LTRB2QUAD(points)

        if img_width > 0 and img_height > 0:
            validate_point_inside_bounds(xmin, ymin, img_width, img_height)
            validate_point_inside_bounds(xmax, ymax, img_width, img_height)

    elif PARAMS.BOX_TYPE == "QUAD":
        box_type = QUAD
        
        numPoints = 8

        if withTranscription and withConfidence:
            m = re.match(r'^\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*([0-1].?[0-9]*)\s*,(.*)$',line)
            if m == None :
                raise Exception("Format incorrect. Should be: x1,y1,x2,y2,x3,y3,x4,y4,confidence,transcription")
        elif withConfidence:
            m = re.match(r'^\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*([0-1].?[0-9]*)\s*$',line)
            if m == None :
                raise Exception("Format incorrect. Should be: x1,y1,x2,y2,x3,y3,x4,y4,confidence")
        elif withTranscription:
            m = re.match(r'^\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,(.*)$',line)
            if m == None :
                raise Exception("Format incorrect. Should be: x1,y1,x2,y2,x3,y3,x4,y4,transcription")
        else:
            if line[-1] == ',' : line = line[:-1]
            m = re.match(r'^\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)\s*$',line)
            if m == None :
                raise Exception("Format incorrect. Should be: x1,y1,x2,y2,x3,y3,x4,y4")
            
        points = [float(m.group(i)) for i in range(1, (numPoints+1))]
        
        validate_clockwise_points(points)
        
        if img_width > 0 and img_height > 0:
            validate_point_inside_bounds(points[0], points[1], img_width, img_height)
            validate_point_inside_bounds(points[2], points[3], img_width, img_height)
            validate_point_inside_bounds(points[4], points[5], img_width, img_height)
            validate_point_inside_bounds(points[6], points[7], img_width, img_height)

    elif PARAMS.BOX_TYPE == "POLY":
        box_type = POLY
        # TODO: TotalText GT보고 정하기
        # TODO: 이렇게 리턴하는 건 굉장히 위험
        splitted_line = line.split(',')
        tmp_transcription = list()

        if withTranscription:
            tmp_transcription.append(splitted_line.pop())
            while not len("".join(tmp_transcription)):
                tmp_transcription.append(splitted_line.pop())

        if withConfidence:
            if len(splitted_line) % 2 != 0:
                confidence = float(splitted_line.pop())
                points = [float(x) for x in splitted_line]
            else:
                backward_idx = len(splitted_line)-1
                while backward_idx > 0:
                    if splitted_line[backward_idx].isdigit() and len(splitted_line) % 2 != 0:
                        break
                    tmp_transcription.append(splitted_line.pop())
                    backward_idx -= 1
                confidence = float(splitted_line.pop())
                points = [float(x) for x in splitted_line]
        else:
            if len(splitted_line) % 2 == 0:
                points = [float(x) for x in splitted_line]
            else:
                backward_idx = len(splitted_line) - 1
                while backward_idx > 0:
                    if splitted_line[backward_idx].isdigit():
                        break
                    tmp_transcription.append(splitted_line.pop())
                    backward_idx -= 1
                points = [float(x) for x in splitted_line]

        transcription = ",".join(tmp_transcription)
        return POLY(points, confidence=confidence, transcription=transcription)

    # QUAD or LTRB format
    if withConfidence:
        try:
            confidence = float(m.group(numPoints+1))
        except ValueError:
            raise Exception("Confidence value must be a float")       
            
    if withTranscription:
        posTranscription = numPoints + (2 if withConfidence else 1)
        transcription = m.group(posTranscription)
        m2 = re.match(r'^\s*\"(.*)\"\s*$', transcription)
        if m2 != None :  # Transcription with double quotes, we extract the value and replace escaped characters
            transcription = m2.group(1).replace("\\\\", "\\").replace("\\\"", "\"")

    result_box = box_type(points, confidence=confidence, transcription=transcription)
    return result_box


# TODO: why not using this logic?
def validate_clockwise_points(points):
    """
    Validates that the points that the 4 points that dlimite a polygon are in clockwise order.
    """

    if len(points) != 8:
        raise Exception("Points list not valid." + str(len(points)))

    point = [
                [int(points[0]) , int(points[1])],
                [int(points[2]) , int(points[3])],
                [int(points[4]) , int(points[5])],
                [int(points[6]) , int(points[7])]
            ]
    edge = [
                ( point[1][0] - point[0][0])*( point[1][1] + point[0][1]),
                ( point[2][0] - point[1][0])*( point[2][1] + point[1][1]),
                ( point[3][0] - point[2][0])*( point[3][1] + point[2][1]),
                ( point[0][0] - point[3][0])*( point[0][1] + point[3][1])
    ]

    summatory = edge[0] + edge[1] + edge[2] + edge[3]
    if summatory > 0:
        raise Exception("Points are not clockwise. The coordinates of bounding quadrilaterals have to be given in clockwise order. Regarding the correct interpretation of 'clockwise' remember that the image coordinate system used is the standard one, with the image origin at the upper left, the X axis extending to the right and Y axis extending downwards.")


def parse_single_file(content, CRLF=True, LTRB=True, withTranscription=False, withConfidence=False, img_width=0, img_height=0, sort_by_confidences=True):
    """
    Returns all points, confindences and transcriptions of a file in lists. Valid line formats:
    xmin,ymin,xmax,ymax,[confidence],[transcription]
    x1,y1,x2,y2,x3,y3,x4,y4,[confidence],[transcription]
    """
    result_boxes = []

    lines = content.split("\r\n" if CRLF else "\n")
    for line in lines:
        line = line.replace("\r", "").replace("\n", "")
        if line != "":
            result_box = parse_values_from_single_line(line, withTranscription, withConfidence, img_width, img_height)
            result_boxes.append(result_box)

    if withConfidence and len(result_boxes) and sort_by_confidences:
        result_boxes.sort(key=lambda x: x.confidence, reverse=True)
        
    return result_boxes


def main_evaluation(validate_data_fn, evaluate_method_fn, show_result=True, per_sample=True):
    """
    This process validates a method, evaluates it and if it succed generates a ZIP file with a JSON entry for each sample.
    Params:
    p: Dictionary of parmeters with the GT/submission locations. If None is passed, the parameters send by the system are used.
    default_evaluation_params_fn: points to a function that returns a dictionary with the default parameters used for the evaluation
    validate_data_fn: points to a method that validates the corrct format of the submission
    evaluate_method_fn: points to a function that evaluated the submission and return a Dictionary with the results
    """

    resDict = {'calculated': True, 'Message': '', 'method': '{}', 'per_sample': '{}'}
    
    validate_data_fn(PARAMS.GT_PATH, PARAMS.SUBMIT_PATH)
    evalData = evaluate_method_fn(PARAMS.GT_PATH, PARAMS.SUBMIT_PATH)
    resDict.update(evalData)

    if PARAMS.OUTPUT_PATH:
        if not os.path.exists(PARAMS.OUTPUT_PATH):
            os.makedirs(PARAMS.OUTPUT_PATH)

        resultsOutputname = PARAMS.OUTPUT_PATH + '/results.zip'
        outZip = zipfile.ZipFile(resultsOutputname, mode='w', allowZip64=True)

        del resDict['per_sample']
        if 'output_items' in resDict.keys():
            del resDict['output_items']

        outZip.writestr('method.json', json.dumps(resDict))
        
    if not resDict['calculated']:
        if show_result:
            sys.stderr.write('Error!\n' + resDict['Message'])
        if PARAMS.OUTPUT_PATH:
            outZip.close()
        return resDict
    
    if PARAMS.OUTPUT_PATH:
        if per_sample:
            for k,v in evalData['per_sample'].items():
                outZip.writestr( k + '.json', json.dumps(v))

            if 'output_items' in evalData.keys():
                for k, v in evalData['output_items'].items():
                    outZip.writestr(k, v) 

        outZip.close()

    if show_result:
        pprint.pprint("Calculated!")
        pprint.pprint(resDict['method'])
    
    return resDict


def main_validation(validate_data_fn):
    """
    This process validates a method
    Params:
    default_evaluation_params_fn: points to a function that returns a dictionary with the default parameters used for the evaluation
    validate_data_fn: points to a method that validates the corrct format of the submission
    """    
    validate_data_fn(PARAMS.GT_PATH, PARAMS.SUBMIT_PATH)
    print('SUCCESS')
    sys.exit(0)
