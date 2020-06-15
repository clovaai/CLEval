from file_utils import load_zip_file, decode_utf8
from arg_parser import PARAMS

def validate_data(gt_file, submit_file):
    """
    Method validate_data: validates that all files in the results folder are correct (have the correct name contents).
                            Validates also that there are no missing files in the folder.
                            If some error detected, the method raises the error
    """
    gt = load_zip_file(gt_file, PARAMS.GT_SAMPLE_NAME_2_ID)
    subm = load_zip_file(submit_file, PARAMS.DET_SAMPLE_NAME_2_ID, True)

    # Validate format of GroundTruth
    for k in gt:
        validate_lines_in_file(k, gt[k], PARAMS.CRLF, PARAMS.BOX_TYPE, True)

    # Validate format of results
    for k in subm:
        if k not in gt:
            raise Exception("The sample %s not present in GT" % k)

        validate_lines_in_file(k, subm[k], PARAMS.CRLF, PARAMS.BOX_TYPE,
                               PARAMS.TRANSCRIPTION, PARAMS.CONFIDENCES)


def validate_lines_in_file(fileName, file_contents, CRLF=True, LTRB=True, withTranscription=False, withConfidence=False, imWidth=0, imHeight=0):
    """
    This function validates that all lines of the file calling the Line validation function for each line
    """
    utf8File = decode_utf8(file_contents)
    if utf8File is None:
        raise Exception("The file %s is not UTF-8" % fileName)

    lines = utf8File.split("\r\n" if CRLF else "\n" )
    for line in lines:
        line = line.replace("\r","").replace("\n","")
        # if(line != ""):
        #     try:
        #         validate_tl_line(line,LTRB,withTranscription,withConfidence,imWidth,imHeight)
        #     except Exception as e:
        #         raise Exception(("Line in sample not valid. Sample: %s Line: %s Error: %s" %(fileName,line,str(e))).encode('utf-8', 'replace'))


def validate_point_inside_bounds(x, y, img_width, img_height):
    if x < 0 or x > img_width:
        raise Exception("X value (%s) not valid. Image dimensions: (%s,%s)" % (x, img_width, img_height))
    if y < 0 or y > img_height:
        raise Exception("Y value (%s)  not valid. Image dimensions: (%s,%s)" % (y, img_width, img_height))


def validate_min_max_bounds(lower_val, upper_val):
    if lower_val > upper_val:
        raise Exception("Value {} should be smaller than value {}.".format(lower_val, upper_val))


def validate_text_line_format(box_type=None, with_confidence=False, with_transcription=False):
    if box_type == "LTRB":
        pass
    elif box_type == "QUAD":
        pass
    elif box_type == "POLY":
        pass
    return False


def validate_clockwise_points(points):
    """
    Validates that the points that the 4 points that dlimite a polygon are in clockwise order.
    """

    if len(points) != 8:
        raise Exception("Points list not valid." + str(len(points)))

    point = [
                [int(points[0]), int(points[1])],
                [int(points[2]), int(points[3])],
                [int(points[4]), int(points[5])],
                [int(points[6]), int(points[7])]
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