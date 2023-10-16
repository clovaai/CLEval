import sys

import pytest


def test_output_score():
    sys.argv[1:] = [
        "-g=resources/test_data/gt/gt_eval_doc_v1_kr.zip",
        "-s=resources/test_data/pred/res_eval_doc_v1_kr.zip",
        "--E2E",
        "--DUMP_SAMPLE_RESULT",
        "--DEBUG",
    ]
    from cleval.arg_parser import get_params
    from cleval.main import cleval

    args = get_params()
    result = cleval(args)
    det_hmean = 0.977989360950786
    e2e_hmean = 0.9165773847119407
    pred_det_hmean = result["all"]["det"]["hmean"]
    pred_e2e_hmean = result["all"]["e2e"]["hmean"]
    assert pred_det_hmean == pytest.approx(det_hmean), pred_det_hmean
    assert pred_e2e_hmean == pytest.approx(e2e_hmean), pred_e2e_hmean


def test_output_score_torchmetric():
    sys.argv[1:] = [
        "-g=resources/test_data/gt/gt_eval_doc_v1_kr.zip",
        "-s=resources/test_data/pred/res_eval_doc_v1_kr.zip",
        "--E2E",
        "--DUMP_SAMPLE_RESULT",
        "--DEBUG",
    ]

    import numpy as np

    from cleval import CLEvalMetric
    from cleval.arg_parser import get_params
    from cleval.main import get_file_paths, parse_single_file

    args = get_params()
    gt_zipfile = args.GT_PATHS[0]
    submit_zipfile = args.SUBMIT_PATHS[0]
    gt_files, det_files, file_indices = get_file_paths(gt_zipfile, submit_zipfile)
    metric = CLEvalMetric()

    for gt_file, det_file, file_idx in zip(gt_files, det_files, file_indices):
        gt_boxes = parse_single_file(gt_file, args.CRLF, True, False, box_type=args.BOX_TYPE)
        det_boxes = parse_single_file(
            det_file,
            args.CRLF,
            args.TRANSCRIPTION,
            args.CONFIDENCES,
            box_type=args.BOX_TYPE,
        )
        gt_quads = np.array([gt_box.points for gt_box in gt_boxes])
        gt_letters = [gt_box.transcription for gt_box in gt_boxes]
        gt_is_dcs = [gt_box.is_dc for gt_box in gt_boxes]
        det_quads = np.array([det_box.points for det_box in det_boxes])
        det_letters = [det_box.transcription for det_box in det_boxes]
        _ = metric(det_quads, gt_quads, det_letters, gt_letters, gt_is_dcs)

    metric_out = metric.compute()
    metric.reset()

    det_hmean = 0.977989360950786
    e2e_hmean = 0.9165773847119407
    assert metric_out["det_h"].item() == pytest.approx(det_hmean), metric_out["det_h"]
    assert metric_out["e2e_h"].item() == pytest.approx(e2e_hmean), metric_out["e2e_h"]
