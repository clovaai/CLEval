from cleval.utils import decode_utf8, load_zip_file


def validate_data(gt_file, submit_file, has_crlf):
    gt = load_zip_file(gt_file)
    subm = load_zip_file(submit_file)

    # Validate format of GroundTruth
    for k in gt:
        validate_lines_in_file(k, gt[k], has_crlf)

    # Validate format of results
    for k in subm:
        if k not in gt:
            raise ValueError("The sample %s not present in GT" % k)
        validate_lines_in_file(k, subm[k], has_crlf)


def validate_lines_in_file(file_name, file_contents, has_crlf=True):
    """This function validates that all lines of the file.
    Execute line validation function for each line.
    """
    utf8file = decode_utf8(file_contents)
    if utf8file is None:
        raise ValueError("The file %s is not UTF-8" % file_name)

    lines = utf8file.split("\r\n" if has_crlf else "\n")
    for line in lines:
        _ = line.replace("\r", "").replace("\n", "")


def validate_point_inside_bounds(x, y, img_width, img_height):
    if x < 0 or x > img_width:
        raise ValueError("X value (%s) not valid. Image dimensions: (%s,%s)" % (x, img_width, img_height))
    if y < 0 or y > img_height:
        raise ValueError("Y value (%s)  not valid. Image dimensions: (%s,%s)" % (y, img_width, img_height))


def validate_min_max_bounds(lower_val, upper_val):
    if lower_val > upper_val:
        raise ValueError(f"Value {lower_val} should be smaller than value {upper_val}.")


def validate_clockwise_points(points):
    """
    Validates that the points are in clockwise order.
    """

    if len(points) != 8:
        raise ValueError("Points list not valid." + str(len(points)))

    point = [
        [int(points[0]), int(points[1])],
        [int(points[2]), int(points[3])],
        [int(points[4]), int(points[5])],
        [int(points[6]), int(points[7])],
    ]
    edge = [
        (point[1][0] - point[0][0]) * (point[1][1] + point[0][1]),
        (point[2][0] - point[1][0]) * (point[2][1] + point[1][1]),
        (point[3][0] - point[2][0]) * (point[3][1] + point[2][1]),
        (point[0][0] - point[3][0]) * (point[0][1] + point[3][1]),
    ]

    summatory = edge[0] + edge[1] + edge[2] + edge[3]
    if summatory > 0:
        raise ValueError(
            "Points are not clockwise. " "The coordinates of bounding quads have to be given in clockwise order."
        )
