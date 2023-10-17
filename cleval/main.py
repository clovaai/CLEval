import os
import re
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict
from pprint import pprint

from tqdm import tqdm

from cleval.arg_parser import get_params
from cleval.box_types import POLY, QUAD, Box
from cleval.data import GlobalResult, accumulate_result, calculate_global_rph
from cleval.eval_functions import evaluation
from cleval.utils import (
    convert_ltrb2quad,
    decode_utf8,
    dump_json,
    load_zip_file,
    ltrb_regex_match,
    quad_regex_match,
)
from cleval.validation import (
    validate_data,
    validate_min_max_bounds,
    validate_point_inside_bounds,
)


def main():
    """Also used by cli"""
    start_t = time.perf_counter()
    args = get_params()

    if args.PROFILE:
        assert args.DEBUG, "DEBUG mode should be turned on for PPROFILE."
        import pprofile

        prof = pprofile.Profile()
        with prof():
            res_dict = cleval(args)
        prof.print_stats()
    else:
        res_dict = cleval(args)
    end_t = time.perf_counter()
    print(f"CLEval total duration...{end_t - start_t}s")
    pprint(res_dict)


def cleval(args):
    """This process validates a method, evaluates it.
    If it succeeds, generates a ZIP file with a JSON entry for each sample.
    """
    validate_data(args.GT_PATHS[0], args.SUBMIT_PATHS[0], args.CRLF)

    global_res = GlobalResult()
    gt_zipfile = args.GT_PATHS[0]
    submit_zipfile = args.SUBMIT_PATHS[0]
    gt_files, det_files, file_indices = get_file_paths(gt_zipfile, submit_zipfile)

    with tqdm(total=len(gt_files), disable=not args.VERBOSE) as pbar:
        pbar.set_description("Integrating results...")
        if args.DEBUG or args.NUM_WORKERS <= 1:
            for gt_file, det_file, file_idx in zip(gt_files, det_files, file_indices):
                sample_res = eval_single(args, gt_file, det_file, file_idx)
                accumulate_result(global_res, sample_res, args.E2E, args.DUMP_SAMPLE_RESULT)
                pbar.update(1)
        else:
            futures = []
            executor = ProcessPoolExecutor(max_workers=args.NUM_WORKERS)
            for gt_file, det_file, file_idx in zip(gt_files, det_files, file_indices):
                future = executor.submit(eval_single, args, gt_file, det_file, file_idx)
                futures.append(future)

            for future in as_completed(futures):
                sample_res = future.result()
                accumulate_result(global_res, sample_res, args.E2E, args.DUMP_SAMPLE_RESULT)
                pbar.update(1)

            executor.shutdown()

    # Calculate global recall, precision, hmean after accumulate all sample-results.
    calculate_global_rph(global_res, args.E2E)

    res_dict = {"all": asdict(global_res.stats)}
    dump_path = os.path.join(args.OUTPUT_PATH, "results.json")
    dump_json(dump_path, res_dict)

    if args.DUMP_SAMPLE_RESULT:
        dump_path = os.path.join(args.OUTPUT_PATH, f"sample_wise.json")
        dump_json(dump_path, asdict(global_res))

    if args.VERBOSE:
        pprint("Calculated!")
        pprint(res_dict)

    return res_dict


def get_file_paths(gt_zipfile, submit_zipfile):
    gt_zipfile_loaded = load_zip_file(gt_zipfile)
    submission_zipfile_loaded = load_zip_file(submit_zipfile)
    gt_files, det_files, file_indices = [], [], []

    for file_idx in gt_zipfile_loaded:
        gt_file = decode_utf8(gt_zipfile_loaded[file_idx])

        if file_idx in submission_zipfile_loaded:
            det_file = decode_utf8(submission_zipfile_loaded[file_idx])
            if det_file is None:
                det_file = ""
        else:
            det_file = ""

        gt_files.append(gt_file)
        det_files.append(det_file)
        file_indices.append(file_idx)
    return gt_files, det_files, file_indices


def eval_single(args, gt_file, det_file, file_id):
    gt_boxes = parse_single_file(gt_file, args.CRLF, True, False, box_type=args.BOX_TYPE)
    det_boxes = parse_single_file(
        det_file,
        args.CRLF,
        args.TRANSCRIPTION,
        args.CONFIDENCES,
        box_type=args.BOX_TYPE,
    )
    sample_res = evaluation(args, gt_boxes, det_boxes)
    sample_res.img_id = file_id
    return sample_res


def parse_single_file(
    content,
    has_crlf=True,
    with_transcription=False,
    with_confidence=False,
    img_width=0,
    img_height=0,
    sort_by_confidences=True,
    box_type="QUAD",
):
    """Returns all points, confindences and transcriptions of a file in lists.

    valid line formats:
        xmin,ymin,xmax,ymax,[confidence],[transcription]
        x1,y1,x2,y2,x3,y3,x4,y4,[confidence],[transcription]
    """
    result_boxes = []
    lines = content.split("\r\n" if has_crlf else "\n")
    for line in lines:
        line = line.replace("\r", "").replace("\n", "")
        if line != "":
            result_box = parse_values_from_single_line(
                line,
                with_transcription,
                with_confidence,
                img_width,
                img_height,
                box_type=box_type,
            )
            result_boxes.append(result_box)

    if with_confidence and len(result_boxes) and sort_by_confidences:
        result_boxes.sort(key=lambda x: x.confidence, reverse=True)

    return result_boxes


def parse_values_from_single_line(
    line,
    with_transcription=False,
    with_confidence=False,
    img_width=0,
    img_height=0,
    box_type="QUAD",
) -> Box:
    """
    Validate the format of the line.
    If the line is not valid an ValueError will be raised.
    If maxWidth and maxHeight are specified, all points must be inside the image bounds.
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

    if box_type == "LTRB":
        box_type = QUAD
        num_points = 4
        m = ltrb_regex_match(line, with_transcription, with_confidence)
        xmin = int(m.group(1))
        ymin = int(m.group(2))
        xmax = int(m.group(3))
        ymax = int(m.group(4))

        validate_min_max_bounds(lower_val=xmin, upper_val=xmax)
        validate_min_max_bounds(lower_val=ymin, upper_val=ymax)

        points = [float(m.group(i)) for i in range(1, (num_points + 1))]
        points = convert_ltrb2quad(points)

        if img_width > 0 and img_height > 0:
            validate_point_inside_bounds(xmin, ymin, img_width, img_height)
            validate_point_inside_bounds(xmax, ymax, img_width, img_height)

    elif box_type == "QUAD":
        box_type = QUAD

        num_points = 8
        m = quad_regex_match(line, with_transcription, with_confidence)
        points = [float(m.group(i)) for i in range(1, (num_points + 1))]

        # validate_clockwise_points(points)
        if img_width > 0 and img_height > 0:
            validate_point_inside_bounds(points[0], points[1], img_width, img_height)
            validate_point_inside_bounds(points[2], points[3], img_width, img_height)
            validate_point_inside_bounds(points[4], points[5], img_width, img_height)
            validate_point_inside_bounds(points[6], points[7], img_width, img_height)

    elif box_type == "POLY":
        # TODO: TotalText GT보고 정하기
        # TODO: 이렇게 리턴하는 건 굉장히 위험
        splitted_line = line.split(",")
        tmp_transcription = list()

        if with_transcription:
            tmp_transcription.append(splitted_line.pop())
            while not len("".join(tmp_transcription)):
                tmp_transcription.append(splitted_line.pop())

        if with_confidence:
            if len(splitted_line) % 2 != 0:
                confidence = float(splitted_line.pop())
                points = [float(x) for x in splitted_line]
            else:
                backward_idx = len(splitted_line) - 1
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
    else:
        raise RuntimeError(f"Something is wrong with configuration. Box Type: [{box_type}]")

    # QUAD or LTRB format
    if with_confidence:
        try:
            confidence = float(m.group(num_points + 1))
        except ValueError:
            raise ValueError("Confidence value must be a float")

    if with_transcription:
        pos_transcription = num_points + (2 if with_confidence else 1)
        transcription = m.group(pos_transcription)
        m2 = re.match(r"^\s*\"(.*)\"\s*$", transcription)

        # Transcription with double quotes
        # We extract the value and replace escaped characters
        if m2 is not None:
            transcription = m2.group(1).replace("\\\\", "\\").replace('\\"', '"')

    result_box = box_type(points, confidence=confidence, transcription=transcription)
    return result_box


def parse_jylee_annot(quad, transcription, box_type):
    assert box_type == "QUAD"
    points = [
        quad["x1"],
        quad["y1"],
        quad["x2"],
        quad["y2"],
        quad["x3"],
        quad["y3"],
        quad["x4"],
        quad["y4"],
    ]
    result_box = QUAD(points, confidence=0.0, transcription=transcription)
    return result_box


def parse_clova_ocr(quad, transcription, box_type):
    assert box_type == "QUAD"
    result_box = QUAD(quad, confidence=0.0, transcription=transcription)
    return result_box


if __name__ == "__main__":
    main()
