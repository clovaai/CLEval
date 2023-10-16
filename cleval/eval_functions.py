from dataclasses import dataclass
from typing import List

import numpy as np
from numpy.typing import NDArray
from numba import njit

from cleval.data import (
    DetBoxResult,
    GTBoxResult,
    MatchReleation,
    MatchResult,
    Point,
    SampleResult,
)
from cleval.utils import harmonic_mean, lcs


@dataclass
class EvalMaterial:
    """EvalMaterial Dataclass
    These are used for calculating eval results.
    """

    gt_pcc_points: List[List]  # [gt_idx][pcc_idx] nested list which has variable length
    pcc_mat_list: List[NDArray]  # list of pcc_mat which has (len_det, len_pcc) shape.
    pcc_mat_sum: NDArray[np.int16]  # (len_gt, len_det)
    ap_mat: NDArray[np.float32]  # (len_gt, len_det)
    ap_mat_binary: NDArray[bool]  # (len_gt, len_det)
    ap_constraint: float
    gt_valid_indices: set
    det_valid_indices: set
    len_gt: int
    len_det: int


def evaluation(args, gt_boxes, det_boxes, scale_range=(0.0, 1.0)):
    """main evaluation function

    Notes:
        Abbreviations for variable names.
         - ap: area precision (not average precision)
         - thresh: threshold
         - pcc: pseudo char center
         - mat: matrix
         - res: result
         - dc: don't care
         - fp: false positive
         - tran: transcription
    """
    # prepare gt, det
    gt_dc_indices, gt_pcc_points = prepare_gt(
        gt_boxes, args.CASE_SENSITIVE, args.VERTICAL_ASPECT_RATIO_THRESH, scale_range
    )
    prepare_det(det_boxes, args.CASE_SENSITIVE)
    len_gt = len(gt_boxes)
    len_det = len(det_boxes)

    # calc area_precision
    ap_constraint = args.AREA_PRECISION_CONSTRAINT
    ap_mat, ap_mat_binary = calc_area_precision(gt_boxes, det_boxes, ap_constraint)

    # calc pcc inclusion
    pcc_mat_list, pcc_mat_sum = calc_pcc_inclusion(det_boxes, gt_pcc_points)

    # prepare valid indices
    det_dc_indices = get_det_dc_indices(gt_dc_indices, pcc_mat_sum, ap_mat, ap_mat_binary, ap_constraint, len_det)
    gt_valid_indices = set(range(len_gt)) - gt_dc_indices
    det_valid_indices = set(range(len_det)) - det_dc_indices

    # construct eval material
    eval_material = EvalMaterial(
        gt_pcc_points,
        pcc_mat_list,
        pcc_mat_sum,
        ap_mat,
        ap_mat_binary,
        ap_constraint,
        gt_valid_indices,
        det_valid_indices,
        len_gt,
        len_det,
    )

    # Matching process
    match_mat, match_results = calc_match_matrix(eval_material)

    # Prepare sample_result
    gt_results, det_results = get_box_results(gt_boxes, gt_pcc_points, det_boxes)
    sample_res = SampleResult(match_results, gt_results, det_results)

    # Evaluation Process
    eval_det(args, sample_res, gt_boxes, det_boxes, eval_material, match_mat)

    if args.E2E:
        eval_e2e(args, sample_res, gt_boxes, det_boxes, eval_material, match_mat)

    if args.ORIENTATION:
        eval_orientation(sample_res, gt_boxes, det_boxes, gt_valid_indices, match_mat)

    return sample_res


def prepare_gt(gt_boxes, is_case_sensitive, vertical_aspect_ratio_thresh, scale_range):
    """prepare ground-truth boxes in evaluation format."""
    gt_dc_indices = set()  # fast check via using set (hash-table)
    gt_pcc_points = []
    for gt_idx, gt_box in enumerate(gt_boxes):
        if not is_case_sensitive:
            gt_box.transcription = gt_box.transcription.upper()

        if gt_box.is_dc or (gt_box.scale is not None and not scale_range[0] <= gt_box.scale <= scale_range[1]):
            gt_dc_indices.add(gt_idx)
        gt_pcc_point = gt_box.pseudo_character_center(vertical_aspect_ratio_thresh)
        gt_pcc_points.append(gt_pcc_point)

    # subtract overlapping gt area from don't care boxes
    # Area(Don't care) - Area(Ground Truth):
    for dc_idx in gt_dc_indices:
        for idx in range(len(gt_boxes)):
            if idx in gt_dc_indices:
                continue
            if gt_boxes[idx] & gt_boxes[dc_idx] > 0:
                # TODO: Consider PCC exclusion for area overlapped with don't care.
                gt_boxes[dc_idx].subtract(gt_boxes[idx])
    return gt_dc_indices, gt_pcc_points


def prepare_det(det_boxes, is_case_sensitive):
    """prepare detection results in evaluation format."""
    for det_idx, det_box in enumerate(det_boxes):
        if not is_case_sensitive:
            det_box.transcription = det_box.transcription.upper()


def calc_area_precision(gt_boxes, det_boxes, ap_constraint):
    """calculate area precision between each GTbox and DETbox
    Args:
        gt_boxes(List[Box]): list of gt boxes
        det_boxes(List[Box]): list of det boxes
        ap_constraint(float): area precision contstraint

    Returns:
        ap_mat(NDArray[float32]): area precision matrix
        ap_mat_binary(NDArray[bool]): boolean mat that area precision >= ap_constraint

    """
    ap_mat = np.zeros([len(gt_boxes), len(det_boxes)], dtype=np.float32)

    for gt_idx, gt_box in enumerate(gt_boxes):
        for det_idx, det_box in enumerate(det_boxes):
            intersected_area = gt_box & det_box
            det_area = det_box.area()
            if det_area > 0.0:
                ap_mat[gt_idx, det_idx] = intersected_area / det_area
    ap_mat_binary = ap_mat >= ap_constraint
    return ap_mat, ap_mat_binary


def calc_pcc_inclusion(det_boxes, gt_pcc_points):
    """fill PCC counting matrix by iterating each GTbox and DETbox"""
    len_gt = len(gt_pcc_points)
    len_det = len(det_boxes)
    pcc_mat_list = []
    pcc_mat_sum = np.zeros((len_gt, len_det), dtype=np.int16)

    for gt_idx, gt_word_pccs in enumerate(gt_pcc_points):
        len_pcc = len(gt_word_pccs)
        pcc_mat = np.zeros((len_det, len_pcc), dtype=bool)

        for det_idx, det_box in enumerate(det_boxes):
            for pcc_idx, pcc_point in enumerate(gt_word_pccs):
                if det_box.is_inside(pcc_point[0], pcc_point[1]):
                    pcc_mat[det_idx, pcc_idx] = True
                    pcc_mat_sum[gt_idx, det_idx] += 1

        pcc_mat_list.append(pcc_mat)
    return pcc_mat_list, pcc_mat_sum


def get_det_dc_indices(gt_dc_indices, pcc_mat_sum, ap_mat, ap_mat_binary, ap_constraint, len_det):
    """Filter detection Don't care boxes"""
    det_dc_indices = set()
    if len(gt_dc_indices) > 0:
        for det_idx in range(len_det):
            ap_sum = 0
            for gt_idx in gt_dc_indices:
                if ap_mat_binary[gt_idx, det_idx]:
                    det_dc_indices.add(det_idx)
                    break
                if pcc_mat_sum[gt_idx, det_idx] > 0:
                    ap_sum += ap_mat[gt_idx, det_idx]
            if ap_sum >= ap_constraint:
                det_dc_indices.add(det_idx)
    return det_dc_indices


def calc_match_matrix(eval_material):
    """Calculate match matrix with PCC counting matrix information."""
    em = eval_material
    match_results = []
    match_mat = np.zeros([em.len_gt, em.len_det], dtype=bool)

    # one-to-one match
    for gt_idx in em.gt_valid_indices:
        for det_idx in em.det_valid_indices:
            is_matched = one_to_one_match(em.pcc_mat_sum, gt_idx, det_idx, em.ap_mat_binary, em.len_gt, em.len_det)
            if is_matched:
                match_result = MatchResult(
                    gt_ids=[gt_idx],
                    det_ids=[det_idx],
                    match_relation=MatchReleation.ONE_TO_ONE,
                )
                match_results.append(match_result)

    # one-to-many match
    for gt_idx in em.gt_valid_indices:
        det_valid_indices_np = np.array(list(em.det_valid_indices), dtype=np.int16)
        is_matched, matched_det_indices = one_to_many_match(
            em.pcc_mat_sum, gt_idx, em.ap_mat_binary, det_valid_indices_np
        )
        if is_matched:
            match_result = MatchResult(
                gt_ids=[gt_idx],
                det_ids=matched_det_indices,
                match_relation=MatchReleation.ONE_TO_MANY,
            )
            match_results.append(match_result)

    # many-to-one match
    for det_idx in em.det_valid_indices:
        gt_valid_indices_np = np.array(list(em.gt_valid_indices), dtype=np.int16)
        is_matched, matched_gt_indices = many_to_one_match(
            em.pcc_mat_sum, det_idx, em.ap_mat, em.ap_constraint, gt_valid_indices_np
        )
        if is_matched:
            match_result = MatchResult(
                gt_ids=matched_gt_indices,
                det_ids=[det_idx],
                match_relation=MatchReleation.MANY_TO_ONE,
            )
            match_results.append(match_result)

    for match_result in match_results:
        match_mat[match_result.gt_ids, match_result.det_ids] = True

    # clear pcc count flag for not matched pairs
    for gt_idx in range(em.len_gt):
        for det_idx in range(em.len_det):
            if match_mat[gt_idx, det_idx]:
                continue
            for pcc_idx in range(len(em.gt_pcc_points[gt_idx])):
                em.pcc_mat_sum[gt_idx, det_idx] -= em.pcc_mat_list[gt_idx][det_idx, pcc_idx]
                em.pcc_mat_list[gt_idx][det_idx, pcc_idx] = 0
    return match_mat, match_results


@njit
def one_to_one_match(pcc_mat_sum, gt_idx, det_idx, ap_mat_binary, len_gt, len_det):
    """One-to-One match condition"""
    match_counter = 0
    for i in range(len_det):
        if ap_mat_binary[gt_idx, i] and pcc_mat_sum[gt_idx, i] > 0:
            match_counter += 1
            if match_counter >= 2:
                break
    if match_counter != 1:
        return False

    match_counter = 0
    for i in range(len_gt):
        if ap_mat_binary[i, det_idx] and pcc_mat_sum[i, det_idx] > 0:
            match_counter += 1
            if match_counter >= 2:
                break
    if match_counter != 1:
        return False

    if ap_mat_binary[gt_idx, det_idx] and pcc_mat_sum[gt_idx, det_idx] > 0:
        return True
    return False


@njit
def one_to_many_match(pcc_mat_sum, gt_idx, ap_mat_binary, det_valid_indices):
    """One-to-Many match condition"""
    many_sum = 0
    matched_det_indices = []
    for det_idx in det_valid_indices:
        if ap_mat_binary[gt_idx, det_idx] and pcc_mat_sum[gt_idx, det_idx] > 0:
            many_sum += pcc_mat_sum[gt_idx, det_idx]
            matched_det_indices.append(det_idx)

    if many_sum > 0 and len(matched_det_indices) >= 2:
        return True, matched_det_indices
    else:
        return False, matched_det_indices


@njit
def many_to_one_match(pcc_mat_sum, det_idx, ap_mat, ap_constraint, gt_valid_indices):
    """Many-to-One match condition"""
    many_sum = 0
    matched_gt_indices = []
    for gt_idx in gt_valid_indices:
        if pcc_mat_sum[gt_idx, det_idx] > 0:
            many_sum += ap_mat[gt_idx, det_idx]
            matched_gt_indices.append(gt_idx)
    if many_sum >= ap_constraint and len(matched_gt_indices) >= 2:
        return True, matched_gt_indices
    else:
        return False, matched_gt_indices


def get_box_results(gt_boxes, gt_pcc_points, det_boxes):
    gt_results = []
    for gt_idx, gt_box in enumerate(gt_boxes):
        gt = GTBoxResult(
            id=gt_idx,
            points=__points_to_result(gt_box.points),
            pccs=__pccs_to_result(gt_pcc_points[gt_idx]),
            orientation=gt_box.orientation,
            letters=gt_box.transcription,
            is_dc=gt_box.is_dc,
        )
        gt_results.append(gt)

    det_results = []
    for det_idx, det_box in enumerate(det_boxes):
        det = DetBoxResult(
            id=det_idx,
            points=__points_to_result(det_box.points),
            orientation=det_box.orientation,
            letters=det_box.transcription,
        )
        det_results.append(det)

    return gt_results, det_results


def __points_to_result(points):
    points = np.array(points, dtype=np.int16).reshape(-1, 2)
    new_points = [Point(int(round(pt[0])), int(round(pt[1]))) for pt in points]
    return new_points


def __pccs_to_result(pcc_points):
    return [Point(int(round(pt[0])), int(round(pt[1]))) for pt in pcc_points]


def eval_det(args, sample_res, gt_boxes, det_boxes, eval_material, match_mat):
    stats = sample_res.stats
    em = eval_material

    # res_mat has +2 size for granuarity penalty and summation of matrix
    res_mat = np.zeros([em.len_gt + 2, em.len_det + 2], dtype=np.float32)

    match_mat_gts_sum = match_mat.sum(axis=0)
    match_mat_dets_sum = match_mat.sum(axis=1)
    pcc_checked = [np.zeros(len(pccs), dtype=bool) for pccs in em.gt_pcc_points]

    # Precision score
    for det_idx in em.det_valid_indices:
        if match_mat_gts_sum[det_idx] > 0:
            matched_gt_indices = np.where(match_mat[:, det_idx])[0]
            if len(matched_gt_indices) > 1:
                stats.num_merged += 1

            for gt_idx in matched_gt_indices:
                pcc_indices = np.where(em.pcc_mat_list[gt_idx][det_idx])[0]
                for pcc_idx in pcc_indices:
                    if not pcc_checked[gt_idx][pcc_idx]:
                        pcc_checked[gt_idx][pcc_idx] = True
                        res_mat[-2, det_idx] += 1  # for total score
                        res_mat[gt_idx, det_idx] += 1
                    else:
                        stats.num_char_overlapped += 1
            gran_weight = args.PRECISION_GRANULARITY_PENALTY_WEIGHT
            res_mat[-1, det_idx] = get_gran_score(len(matched_gt_indices), gran_weight)

    # Recall score
    for gt_idx in em.gt_valid_indices:
        found_gt_chars = 0
        if match_mat_dets_sum[gt_idx] > 0:
            matched_det_indices = np.where(match_mat[gt_idx] > 0)[0]
            if len(matched_det_indices) > 1:
                stats.num_splitted += 1

            found_gt_chars = np.sum(pcc_checked[gt_idx])
            gran_weight = args.RECALL_GRANULARITY_PENALTY_WEIGHT
            res_mat[gt_idx, -1] = get_gran_score(len(matched_det_indices), gran_weight)
        res_mat[gt_idx, -2] = found_gt_chars

    # Calculate precision / recall
    num_char_gt, num_char_det = get_num_total_char(gt_boxes, em.pcc_mat_sum, em.gt_valid_indices, em.det_valid_indices)
    num_char_fp = get_num_fp_char(det_boxes, em.det_valid_indices, match_mat_gts_sum)
    num_char_det += num_char_fp
    extract_stats(sample_res.stats.det, num_char_fp, num_char_gt, num_char_det, res_mat)

    # Calculate match-wise eval out
    if args.DUMP_SAMPLE_RESULT:
        for match_res in sample_res.matches:
            gt_ids = match_res.gt_ids
            det_ids = match_res.det_ids
            num_char_gt, num_char_det = get_num_total_char(gt_boxes, em.pcc_mat_sum, gt_ids, det_ids)
            num_char_fp = get_num_fp_char(det_boxes, det_ids, match_mat_gts_sum)
            num_char_det += num_char_fp
            extract_stats(match_res.det, num_char_fp, num_char_gt, num_char_det, res_mat)


def get_num_total_char(gt_boxes, pcc_mat_sum, gt_valid_indices, det_valid_indices):
    """get TotalNum for detection evaluation."""
    num_char_gt = 0
    num_char_det = 0
    for gt_idx, gt_box in enumerate(gt_boxes):
        if gt_idx in gt_valid_indices:
            num_char_gt += len(gt_box.transcription)
        num_char_det += np.sum(pcc_mat_sum[gt_idx][list(det_valid_indices)])
    return num_char_gt, num_char_det


def get_num_fp_char(det_boxes, det_valid_indices, match_mat_gts_sum):
    """get FalsePositive for detection evaluation."""
    fp_char_counts = 0
    for det_idx in det_valid_indices:
        # no match with any GTs && not matched with don't care
        if match_mat_gts_sum[det_idx] == 0:
            fp_char_count = round(0.5 + 1 / (1e-5 + det_boxes[det_idx].aspect_ratio()))
            fp_char_counts += min(fp_char_count, 10)
    return fp_char_counts


def eval_e2e(args, sample_res, gt_boxes, det_boxes, eval_material, match_mat):
    gt_trans = [box.transcription for box in gt_boxes]
    det_trans = [box.transcription for box in det_boxes]
    gt_trans_not_found = [box.transcription for box in gt_boxes]
    det_trans_not_found = [box.transcription for box in det_boxes]

    em = eval_material
    stats = sample_res.stats

    # +2 size for granuarity penalty and summation of matrix
    res_mat = np.zeros([em.len_gt + 2, em.len_det + 2], dtype=np.float32)

    match_mat_gts_sum = match_mat.sum(axis=0)
    match_mat_dets_sum = match_mat.sum(axis=1)

    # Recall score
    for gt_idx in em.gt_valid_indices:
        if match_mat_dets_sum[gt_idx] > 0:
            matched_det_indices = np.where(match_mat[gt_idx])[0]
            sorted_det_indices = sort_detbox_order_by_pcc(
                gt_idx, matched_det_indices, em.gt_pcc_points, em.pcc_mat_list
            )
            corrected_num_chars = lcs_elimination(
                gt_trans,
                gt_trans_not_found,
                det_trans_not_found,
                gt_idx,
                sorted_det_indices,
            )
            res_mat[gt_idx, -2] = corrected_num_chars
            gran_weight = args.RECALL_GRANULARITY_PENALTY_WEIGHT
            res_mat[gt_idx, -1] = get_gran_score(len(matched_det_indices), gran_weight)

    # Precision score
    for det_idx in em.det_valid_indices:
        if match_mat_gts_sum[det_idx] > 0:
            matched_gt_indices = np.where(match_mat[:, det_idx])[0]
            gran_weight = args.PRECISION_GRANULARITY_PENALTY_WEIGHT
            res_mat[-1, det_idx] = get_gran_score(len(matched_gt_indices), gran_weight)
        res_mat[-2, det_idx] = len(det_trans[det_idx]) - len(det_trans_not_found[det_idx])

    num_char_det = sum([len(det_trans[i]) for i in em.det_valid_indices])
    num_char_fp = num_char_det - np.sum(res_mat[-2])
    extract_stats(stats.e2e, num_char_fp, stats.det.num_char_gt, num_char_det, res_mat)

    if args.DUMP_SAMPLE_RESULT:
        for match_res in sample_res.matches:
            det_ids = match_res.det_ids
            num_char_det = sum([len(det_trans[i]) for i in det_ids])
            num_char_fp = num_char_det - np.sum(res_mat[-2][det_ids])
            num_char_gt = match_res.det.num_char_gt
            extract_stats(match_res.e2e, num_char_fp, num_char_gt, num_char_det, res_mat)


def sort_detbox_order_by_pcc(gt_idx, matched_det_indices, gt_pcc_points, pcc_mat_list):
    """sort detected box order by pcc information."""
    unordered = matched_det_indices.tolist()  # deepcopy
    ordered_indices = []

    char_len = len(gt_pcc_points[gt_idx])
    for pcc_idx in range(char_len):
        if len(unordered) == 1:
            break

        for det_idx in unordered:
            if pcc_mat_list[gt_idx][det_idx, pcc_idx]:
                ordered_indices.append(det_idx)
                unordered.remove(det_idx)
                break

    ordered_indices.append(unordered[0])
    return ordered_indices


def lcs_elimination(gt_trans, gt_trans_not_found, det_trans_not_found, gt_idx, sorted_det_indices):
    """longest common sequence elimination by sorted detection boxes"""
    target_string = "".join(det_trans_not_found[i] for i in sorted_det_indices)
    lcs_length, lcs_string = lcs(gt_trans[gt_idx], target_string)

    for char in lcs_string:
        gt_trans_not_found[gt_idx] = gt_trans_not_found[gt_idx].replace(char, "", 1)

        for det_idx in sorted_det_indices:
            det_tran = det_trans_not_found[det_idx]
            if not det_tran.find(char) < 0:
                det_trans_not_found[det_idx] = det_tran.replace(char, "", 1)
                break
    return lcs_length


def eval_orientation(sample_res, gt_boxes, det_boxes, gt_valid_indices, match_mat):
    gt_query = [box.orientation for box in gt_boxes]
    det_query = [box.orientation for box in det_boxes]

    match_mat_dets_sum = match_mat.sum(axis=1)
    counter = 0
    num_ori_correct = 0
    stats = sample_res.stats

    for gt_idx in gt_valid_indices:
        if match_mat_dets_sum[gt_idx] > 0:
            matched_det_indices = np.where(match_mat[gt_idx])[0]
            counter += 1
            count_size = 0 if len(matched_det_indices) else 1 / len(matched_det_indices)
            for det_idx in matched_det_indices:
                if gt_query[gt_idx] == det_query[det_idx]:
                    num_ori_correct += count_size
    if counter != 0:
        stats.num_ori_total = counter
        stats.num_ori_correct = num_ori_correct
        stats.ori_acc = num_ori_correct / counter


def extract_stats(core_stats, num_char_fp, num_char_gt, num_char_det, res_mat):
    core_stats.num_char_fp = int(num_char_fp)
    core_stats.num_char_gt = total_gt = int(num_char_gt)
    core_stats.num_char_det = total_det = int(num_char_det)
    core_stats.num_char_tp_recall = tp_gt = int(np.sum(res_mat[-2]))
    core_stats.gran_score_recall = gran_gt = float(np.sum(res_mat[:, -1]))
    core_stats.num_char_tp_precision = tp_det = int(np.sum(res_mat[-2]))
    core_stats.gran_score_precision = gran_det = float(np.sum(res_mat[-1]))

    # Sample Score : Character correct length - Granularity Penalty
    recall = 0.0 if total_gt == 0 else max(0.0, tp_gt - gran_gt) / total_gt
    precision = 0.0 if total_det == 0 else max(0.0, tp_det - gran_det) / total_det
    hmean = harmonic_mean(recall, precision)
    core_stats.recall = recall
    core_stats.precision = precision
    core_stats.hmean = hmean


@njit
def get_gran_score(num_splitted, penalty_weight):
    """get granularity penalty given number of how many splitted"""
    return max(num_splitted - 1, 0) * penalty_weight
