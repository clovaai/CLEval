from itertools import permutations
import rrc_evaluation_funcs
import math

import numpy as np
import Polygon as polygon3
from shapely.geometry import Point

from file_utils import load_zip_file, decode_utf8
from validation import validate_data
from arg_parser import PARAMS

import concurrent.futures
from tqdm import tqdm


def granularity_score(num_splitted):
    """get granularity penalty given number of how many splitted"""
    return max(num_splitted-1, 0) * PARAMS.GRANULARITY_PENALTY_WEIGHT

def get_element_total_length(l):
    return sum([len(x) for x in l])

def harmonic_mean(score1, score2):
    """get harmonic mean value"""
    if score1+score2 == 0:
        return 0
    else:
        return (2*score1*score2) / (score1+score2)

def lcs(s1, s2):
    """Longeset Common Sequence between s1 & s2"""
    # source: https://stackoverflow.com/questions/48651891/longest-common-subsequence-in-python
    if len(s1) == 0 or len(s2) == 0:
        return 0, ''
    matrix = [["" for x in range(len(s2))] for x in range(len(s1))]
    for i in range(len(s1)):
        for j in range(len(s2)):
            if s1[i] == s2[j]:
                if i == 0 or j == 0:
                    matrix[i][j] = s1[i]
                else:
                    matrix[i][j] = matrix[i-1][j-1] + s1[i]
            else:
                matrix[i][j] = max(matrix[i-1][j], matrix[i][j-1], key=len)
    cs = matrix[-1][-1]
    return len(cs), cs


class GlobalResult(object):
    """Object that holds each record of all samples."""

    def __init__(self, with_e2e=False):
        self.with_e2e = with_e2e           # flags for calculate end-to-end or not

        # recording stats for detection evaluation
        self.det_correct_num_recall = 0    # CorrectNum for Recall
        self.det_correct_num_precision = 0 # CorrectNum for Precision
        self.chars_gt = 0                  # TotalNum for Recall (Both detection ,end-to-end)
        self.chars_det = 0                # TotalNum for Precisiion

        # recording stats for end-to-end evaluation
        self.e2e_correct_num_recall = 0    # CorrectNum for Recall
        self.e2e_correct_num_precision = 0 # CorrectNum for Precision
        self.chars_recog = 0               # TotalNum for Precision

        # metadata information
        self.num_splitted = 0
        self.num_merged = 0
        self.num_false_positive = 0
        self.char_missed = 0
        self.char_overlapped = 0
        self.char_false_positive = 0

        # # recording stats for end-to-end evaluation
        self.e2e_correct_num_recall = 0    # CorrectNum for Recall
        self.e2e_correct_num_precision = 0 # CorrectNum for Precision
        self.chars_recog = 0               # TotalNum for Precision

        self.e2e_char_missed = 0
        self.e2e_char_false_positive = 0
        self.e2e_recog_score_chars = 0
        self.e2e_recog_score_correct_num = 0
        



    def accumulate_stats(self, sample_dict):

        """accumulate single sample statistics in this object."""
        self.det_correct_num_recall += sample_dict['det_correct_num_recall']
        self.det_correct_num_precision += sample_dict['det_correct_num_precision']
        self.chars_gt += sample_dict['chars_gt']
        self.chars_det += sample_dict['chars_det']

        self.num_splitted += sample_dict['num_splitted']
        self.num_merged += sample_dict['num_merged']
        self.num_false_positive += sample_dict['num_false_positive']
        self.char_missed += sample_dict['char_missed']
        self.char_overlapped += sample_dict['char_overlapped']
        self.char_false_positive += sample_dict['char_false_positive']

        if self.with_e2e:
            self.e2e_correct_num_recall += sample_dict['e2e_correct_num_recall']
            self.e2e_correct_num_precision += sample_dict['e2e_correct_num_precision']
            self.chars_recog += sample_dict['chars_recog']

            self.e2e_char_missed += sample_dict['e2e_char_missed']
            self.e2e_char_false_positive = sample_dict['e2e_char_false_positive']
            self.e2e_recog_score_chars = sample_dict['e2e_recog_score_chars']
            self.e2e_recog_score_correct_num = sample_dict['e2e_recog_score_correct_num']


    def to_dict(self):
        """make stats to dictionary."""
        det_recall = 0 if self.chars_gt == 0 else self.det_correct_num_recall / self.chars_gt
        det_precision = 0 if self.chars_det == 0 else self.det_correct_num_precision / self.chars_det
        det_hmean = harmonic_mean(det_recall, det_precision)

        result_dict = {
            'Detection': {
                'recall': det_recall,
                'precision': det_precision,
                'hmean': det_hmean
            },
            'Detection_Metadata': {
                'num_merge': self.num_merged,
                'num_split': self.num_splitted,
                'num_false_pos': self.num_false_positive,
                'char_miss': self.char_missed,
                'char_overlap': self.char_overlapped,
                'char_false_pos': self.char_false_positive
            }
            
        }

        e2e_recall = 0 if self.chars_gt == 0 else self.e2e_correct_num_recall / self.chars_gt
        e2e_precision = 0 if self.chars_recog == 0 else self.e2e_correct_num_precision / self.chars_recog
        e2e_hmean = harmonic_mean(e2e_recall, e2e_precision)
        e2e_recog_score = 0 if self.e2e_recog_score_chars == 0 else self.e2e_recog_score_correct_num / self.e2e_recog_score_chars
        result_dict.update({
            'EndtoEnd': {
                'recall': e2e_recall,
                'precision': e2e_precision,
                'hmean': e2e_hmean,
                'recognition_score': e2e_recog_score,
            },
            'EndtoEnd_Metadata': {
                    'num_merge': self.num_merged,
                    'num_split': self.num_splitted,
                    'num_false_pos': self.num_false_positive,
                    'char_miss': self.e2e_char_missed,
                    'char_false_pos': self.e2e_char_false_positive
            }
        })
        return result_dict


class SampleResult(object):
    """Object that holds result of single sample."""
    def __init__(self, with_e2e=False, with_recog_score=False):
        self.with_e2e = with_e2e
        self.with_recog_score = with_recog_score
        self.det_recall = 0                # Detection Recall score
        self.det_precision = 0             # Detection Precision score
        self.det_hmean = 0                 # Detection H-Mean score

        self.chars_gt = 0                  # TotalNum for Recall (Both detection ,end-to-end)
        self.chars_det = 0                # TotalNum for Precisiion

        self.det_correct_num_recall = 0    # CorrectNum for recall
        self.det_correct_num_precision = 0 # CorrectNum for precision

        # detection metadata information
        self.num_splitted = 0
        self.num_merged = 0
        self.num_false_pos = 0
        self.char_missed = 0
        self.char_overlapped = 0
        self.char_false_pos = 0

        if self.with_e2e:
            # create variables for end-to-end evaluation
            self.e2e_recall = 0            # End-to-End Recall score
            self.e2e_precision = 0         # End-to-End Precision score
            self.e2e_hmean = 0             # End-to-End H-Mean score
            self.e2e_recog_score = 0       # Recognition Score 
            self.chars_recog = 0
            self.e2e_correct_num_precision = 0
            self.e2e_correct_num_recall = 0

            self.e2e_result_matrix = np.zeros([1,1])
            self.e2e_char_missed = 0
            self.e2e_char_false_pos = 0
            self.e2e_recog_score_chars = 0
            self.e2e_recog_score_correct_num = 0
        
        # Array of GT keys marked as don't Care
        self.gt_dont_care_indices = []

        # Array of Detected keys matched with a don't Care GT
        self.det_dont_care_indices = []

        # matrix for storing matching information (M_ij)
        self.match_matrix = np.zeros([1,1])

        # pseudo character centers (gt_pcc_points[i][k] == (c_i)^k )
        self.gt_pcc_points = []
        self.gt_char_counts = []

        # for counting how may PCC points included
        self.pcc_count_matrix = [] # ( (m_ij)^k )
        self.gt_pcc_checked = []
        self.gt_pcc_count = []

        # for storing area precision / sample scoring
        self.area_precision_matrix = np.zeros([1,1])
        self.det_result_matrix = np.zeros([1,1])

        # for storing pairs to visualize on Web
        # (just to give different color for case OO, OM, MO, not used for evaluation)
        self.pairs = []

        # Below variables are for web visualization
        # evaluation logs
        self.eval_log = ""

        # character count matrix
        self.character_counts = np.zeros(([1,1]))

    def prepare_gt(self, gt_boxes):
        """prepare ground-truth boxes in evaluation format."""
        self.gt_boxes = gt_boxes
        for gt_idx, gt_box in enumerate(self.gt_boxes):
            if not PARAMS.CASE_SENSITIVE:
                gt_box.transcription = gt_box.transcription.upper()

            if gt_box.is_dc:
                self.gt_dont_care_indices.append(gt_idx)
            self.gt_pcc_points.append(gt_box.pseudo_character_center())
        self.eval_log += "GT polygons: " + str(len(self.gt_boxes)) + (" (" + str(len(self.gt_dont_care_indices)) + " don't care) \n")

        # subtract overlapping gt area from don't care boxes
        # Area(Don't care) - Area(Ground Truth):
        for dc in self.gt_dont_care_indices:
            for idx in list(set(range(len(self.gt_boxes))) - set(self.gt_dont_care_indices)):
                if self.gt_boxes[idx] & self.gt_boxes[dc] > 0:
                    # TODO: currently, PCC exclusion for area overlapped with don't care is not considered.
                    self.gt_boxes[dc].subtract(self.gt_boxes[idx])


    def prepare_det(self, det_boxes):
        """prepare detection results in evaluation format."""
        self.det_boxes = det_boxes
        for det_idx, det_box in enumerate(self.det_boxes):
            if not PARAMS.CASE_SENSITIVE:
                det_box.transcription = det_box.transcription.upper()

        self.eval_log += "DET polygons: {}\n".format(str(len(self.det_boxes)))


    def total_character_counts(self):
        """get TotalNum for detection evaluation."""
        total_num_recall = 0
        total_num_precision = 0
        for gt_idx in range(len(self.gt_boxes)):
            if gt_idx not in self.gt_dont_care_indices:
                total_num_recall += len(self.gt_boxes[gt_idx].transcription)

            for det_idx in range(len(self.det_boxes)):
                if det_idx not in self.det_dont_care_indices:
                    total_num_precision += sum(self.pcc_count_matrix[gt_idx][det_idx])
        return total_num_recall, total_num_precision

    def get_false_positive_char_counts(self):
        """get FalsePositive for detection evaluation."""
        fp_char_counts = 0
        for det_idx in range(len(self.det_boxes)):
            # no match with any GTs && not matched with don't care
            if self.match_matrix.sum(axis=0)[det_idx] == 0 and det_idx not in self.det_dont_care_indices:
                fp_char_counts += min(round(0.5+(1 / (1e-5 + self.det_boxes[det_idx].aspect_ratio()))), 10)
        return fp_char_counts

    def sort_detbox_order_by_pcc(self, gt_idx, det_indices):
        """sort detected box order by pcc information."""
        char_len = len(self.gt_pcc_points[gt_idx])

        not_ordered_yet = det_indices
        ordered_indices = list()

        for c in range(char_len):
            if len(not_ordered_yet) == 1:
                break

            for det_id in not_ordered_yet:
                if self.pcc_count_matrix[gt_idx][det_id][c] == 1:
                    ordered_indices.append(det_id)
                    not_ordered_yet.remove(det_id)
                    break

        ordered_indices.append(not_ordered_yet[0])
        return ordered_indices

    def lcs_elimination(self, gt_idx, sorted_det_indices):
        """longest common sequence elimination by sorted detection boxes"""
        standard_script = self.gtQuery[gt_idx]
        lcs_length, lcs_string = lcs(standard_script, "".join(self.det_trans_not_found[idx] for idx in sorted_det_indices))
        for c in lcs_string:
            self.gt_trans_not_found[gt_idx] = self.gt_trans_not_found[gt_idx].replace(c, '', 1)

            for det_idx in sorted_det_indices:
                if not self.det_trans_not_found[det_idx].find(c) < 0:
                    self.det_trans_not_found[det_idx] = self.det_trans_not_found[det_idx].replace(c, '', 1)
                    break
        return lcs_length

    def calc_area_precision(self):
        """calculate area precision between each GTbox and DETbox"""
        for gt_idx, gt_box in enumerate(self.gt_boxes):
            det_char_counts = []
            self.gt_pcc_checked.append(np.zeros(len(self.gt_pcc_points[gt_idx])))
            for det_idx, det_box in enumerate(self.det_boxes):
                intersected_area = gt_box & det_box
                if det_box.area() > 0.0:
                    self.area_precision_matrix[gt_idx, det_idx] = intersected_area / det_box.area()
                det_char_counts.append(np.zeros(len(self.gt_pcc_points[gt_idx])))
            self.gt_char_counts.append(det_char_counts)
            self.pcc_count_matrix.append(det_char_counts)

    def calc_pcc_inclusion(self):
        """fill PCC counting matrix by iterating each GTbox and DETbox"""
        for gt_id, gt_box in enumerate(self.gt_boxes):
            pcc_points = gt_box.pseudo_character_center()
            for det_id, det_box in enumerate(self.det_boxes):
                for pcc_id, pcc_point in enumerate(pcc_points):
                    if det_box.is_inside(pcc_point[0], pcc_point[1]):
                        self.pcc_count_matrix[gt_id][det_id][pcc_id] = 1

    def filter_det_dont_care(self):
        """Filter detection Don't care boxes"""
        if len(self.gt_dont_care_indices) > 0:
            for det_id in range(len(self.det_boxes)):
                area_precision_sum = 0
                for gt_id in self.gt_dont_care_indices:
                    if sum(self.pcc_count_matrix[gt_id][det_id]) > 0:
                        area_precision_sum += self.area_precision_matrix[gt_id][det_id]
                if area_precision_sum > PARAMS.AREA_PRECISION_CONSTRAINT:
                    self.det_dont_care_indices.append(det_id)
                else:
                    for gt_id in self.gt_dont_care_indices:
                        if self.area_precision_matrix[gt_id, det_id] > PARAMS.AREA_PRECISION_CONSTRAINT:
                            self.det_dont_care_indices.append(det_id)
                            break

        self.eval_log += " (" + str(len(self.det_dont_care_indices)) + " don't care)\n" if len(self.det_dont_care_indices) > 0 else "\n"

    def one_to_one_match(self, row, col):
        """One-to-One match condition"""
        cont = 0
        for j in range(len(self.area_precision_matrix[0])):
            if sum(self.pcc_count_matrix[row][j]) > 0 and self.area_precision_matrix[row, j] >= PARAMS.AREA_PRECISION_CONSTRAINT:
                cont = cont + 1
        if cont != 1:
            return False
        cont = 0
        for i in range(len(self.area_precision_matrix)):
            if sum(self.pcc_count_matrix[i][col]) > 0 and self.area_precision_matrix[i, col] >= PARAMS.AREA_PRECISION_CONSTRAINT:
                cont = cont + 1
        if cont != 1:
            return False

        if sum(self.pcc_count_matrix[row][col]) > 0 and self.area_precision_matrix[row, col] >= PARAMS.AREA_PRECISION_CONSTRAINT:
            return True
        return False


    def one_to_many_match(self, gt_id):
        """One-to-Many match condition"""
        many_sum = 0
        detRects = []
        for det_idx in range(len(self.area_precision_matrix[0])):
            if det_idx not in self.det_dont_care_indices:
                if self.area_precision_matrix[gt_id, det_idx] >= PARAMS.AREA_PRECISION_CONSTRAINT and \
                sum(self.pcc_count_matrix[gt_id][det_idx]) > 0:
                    many_sum += sum(self.pcc_count_matrix[gt_id][det_idx])
                    detRects.append(det_idx)

        if many_sum > 0 and len(detRects) >= 2:
            return True, detRects
        else:
            return False, []

    def many_to_one_match(self, det_id):
        """Many-to-One match condition"""
        many_sum = 0
        gtRects = []
        for gt_idx in range(len(self.area_precision_matrix)):
            if gt_idx not in self.gt_dont_care_indices:
                if sum(self.pcc_count_matrix[gt_idx][det_id]) > 0:
                    many_sum += self.area_precision_matrix[gt_idx][det_id]
                    gtRects.append(gt_idx)
        if many_sum >= PARAMS.AREA_PRECISION_CONSTRAINT and len(gtRects) >= 2:
            return True, gtRects
        else:
            return False, []


    def calc_match_matrix(self):
        """Calculate match matrix with PCC counting matrix information."""
        self.eval_log += "Find one-to-one matches\n"
        for gt_id in range(len(self.gt_boxes)):
            for det_id in range(len(self.det_boxes)):
                if gt_id not in self.gt_dont_care_indices and det_id not in self.det_dont_care_indices:
                    match = self.one_to_one_match(gt_id, det_id)
                    if match:
                        self.pairs.append({'gt': [gt_id], 'det': [det_id], 'type': 'OO'})
                        self.eval_log += "Match GT #{} with Det #{}\n".format(gt_id, det_id)

        # one-to-many match
        self.eval_log += "Find one-to-many matches\n"
        for gt_id in range(len(self.gt_boxes)):
            if gt_id not in self.gt_dont_care_indices:
                match, matched_det = self.one_to_many_match(gt_id)
                if match:
                    self.pairs.append({'gt': [gt_id], 'det': matched_det, 'type': 'OM'})
                    self.eval_log += "Match GT #{} with Det #{}\n".format(gt_id, matched_det)

        # many-to-one match
        self.eval_log += "Find many-to-one matches\n"
        for det_id in range(len(self.det_boxes)):
            if det_id not in self.det_dont_care_indices:
                match, matched_gt = self.many_to_one_match(det_id)
                if match:
                    self.pairs.append({'gt': matched_gt, 'det': [det_id], 'type': 'MO'})
                    self.eval_log += "Match GT #{} with Det #{}\n".format(matched_gt, det_id)

        for pair in self.pairs:
            self.match_matrix[pair['gt'], pair['det']] = 1

        # clear pcc count flag for not matched pairs
        for gt_idx in range(len(self.gt_boxes)):
            for det_idx in range(len(self.det_boxes)):
                if not self.match_matrix[gt_idx][det_idx]:
                    for pcc in range(len(self.gt_pcc_points[gt_idx])):
                        self.pcc_count_matrix[gt_idx][det_idx][pcc] = 0

    def eval_det(self):
        self.eval_log += "<b>Detection | PRECISION\n</b>"
        for detNum in range(len(self.det_boxes)):
            box_precision = 0
            if detNum in self.det_dont_care_indices:
                continue

            if self.match_matrix.sum(axis=0)[detNum] > 0:
                matched_gt_indices = np.where(self.match_matrix[:, detNum] == 1)[0]
                if len(matched_gt_indices) > 1:
                    self.num_merged += 1

                for gt_idx in matched_gt_indices:
                    intermediate_precision = 0
                    found_char_pos = np.where(self.pcc_count_matrix[gt_idx][detNum] == 1)[0]
                    for x in found_char_pos:
                        if self.gt_pcc_checked[gt_idx][x] == 0:
                            self.gt_pcc_checked[gt_idx][x] = 1
                            box_precision += 1
                            intermediate_precision += 1
                        elif self.gt_pcc_checked[gt_idx][x] >= 1:
                            self.char_overlapped += 1
                    self.det_result_matrix[gt_idx][detNum] = intermediate_precision

                self.det_result_matrix[len(self.gt_boxes)][detNum] = box_precision
                self.det_result_matrix[len(self.gt_boxes)+1][detNum] = granularity_score(len(matched_gt_indices))
            else:
                self.num_false_pos += 1

        # Recall score
        self.eval_log += "<b>Detection | RECALL\n</b>"
        for gtNum in range(len(self.gt_boxes)):
            if gtNum in self.gt_dont_care_indices:
                continue
            found_gt_chars = 0
            num_gt_characters = len(self.gt_pcc_points[gtNum])
            box_char_recall_list = np.ones(num_gt_characters)
            if self.match_matrix.sum(axis=1)[gtNum] > 0:
                matched_det_indices = np.where(self.match_matrix[gtNum] > 0)[0]
                if len(matched_det_indices) > 1:
                    self.num_splitted += 1

                found_gt_chars = np.sum(self.gt_pcc_checked[gtNum])
                self.char_missed += int(np.sum(box_char_recall_list) - found_gt_chars)
                self.det_result_matrix[gtNum][len(self.det_boxes)+1] = granularity_score(len(matched_det_indices))
            else:
                self.char_missed += int(np.sum(box_char_recall_list))

            self.det_result_matrix[gtNum][len(self.det_boxes)] = found_gt_chars


        # Pseudo Character Center Visualization
        self.character_counts = np.zeros((len(self.gt_boxes), len(self.det_boxes)))
        for gtNum in range(len(self.gt_boxes)):
            for detNum in range(len(self.det_boxes)):
                self.character_counts[gtNum][detNum] = sum(self.gt_char_counts[gtNum][detNum])

        # calculate precision / recall
        self.chars_gt, self.chars_det = self.total_character_counts()
        self.char_false_pos += self.get_false_positive_char_counts()
        self.chars_det += self.char_false_pos

        self.eval_log += "<b># of false positive chars\n</b>"
        self.eval_log += "{}\n".format(self.char_false_pos)

        # Sample Score : Character correct length - Granularity Penalty
        self.det_correct_num_recall = max(np.sum(self.det_result_matrix[:, len(self.det_boxes)]) - np.sum(self.det_result_matrix[:, len(self.det_boxes)+1]), 0)
        self.det_correct_num_precision = max(np.sum(self.det_result_matrix[len(self.gt_boxes)]) - np.sum(self.det_result_matrix[len(self.gt_boxes)+1]), 0)

        self.det_recall = float(0) if self.chars_gt == 0 else float(self.det_correct_num_recall) / self.chars_gt
        self.det_precision = float(0) if self.chars_det == 0 else float(self.det_correct_num_precision) / self.chars_det
        self.det_hmean = harmonic_mean(self.det_recall, self.det_precision)


    def eval_e2e(self):
        self.gtQuery = [box.transcription for box in self.gt_boxes]
        self.detQuery = [box.transcription for box in self.det_boxes]
        self.gt_trans_not_found = [box.transcription for box in self.gt_boxes]
        self.det_trans_not_found = [box.transcription for box in self.det_boxes]

        self.eval_log += "=================================\n"
        self.eval_log += "<b>End-to-End | Recall\n</b>"
        for gtNum in range(len(self.gt_boxes)):
            if gtNum in self.gt_dont_care_indices:
                continue

            if self.match_matrix.sum(axis=1)[gtNum] > 0:
                matched_det_indices = np.where(self.match_matrix[gtNum] > 0)[0]

                sorted_det_indices = self.sort_detbox_order_by_pcc(gtNum, matched_det_indices.tolist())
                corrected_num_chars = self.lcs_elimination(gtNum, sorted_det_indices)

                self.e2e_result_matrix[gtNum][len(self.det_boxes)] = corrected_num_chars
                self.e2e_result_matrix[gtNum][len(self.det_boxes)+1] = granularity_score(len(matched_det_indices))

        self.eval_log += "<b>End-to-End | Precision\n</b>"
        for detNum in range(len(self.det_boxes)):
            if detNum in self.det_dont_care_indices:
                continue

            if self.match_matrix.sum(axis=0)[detNum] > 0:
                matched_gt_indices = np.where(self.match_matrix[:, detNum] == 1)[0]
                self.e2e_result_matrix[len(self.gt_boxes)+1][detNum] = granularity_score(len(matched_gt_indices))
            self.e2e_result_matrix[len(self.gt_boxes)][detNum] = len(self.detQuery[detNum]) - len(self.det_trans_not_found[detNum])


        self.chars_recog = get_element_total_length([x for k, x in enumerate(self.detQuery) if k not in self.det_dont_care_indices])

        # Sample Score : Character correct length - Granularity Penalty
        self.e2e_correct_num_recall = max(np.sum(self.e2e_result_matrix[:, len(self.det_boxes)]) - np.sum(self.e2e_result_matrix[:, len(self.det_boxes)+1]), 0)
        self.e2e_correct_num_precision = max(np.sum(self.e2e_result_matrix[len(self.gt_boxes)]) - np.sum(self.e2e_result_matrix[len(self.gt_boxes)+1]), 0)

        self.e2e_char_missed = self.chars_gt - self.e2e_correct_num_recall
        self.e2e_char_false_pos = self.chars_recog - np.sum(self.e2e_result_matrix[len(self.gt_boxes)])


        self.e2e_recall = float(0) if self.chars_gt == 0 else float(self.e2e_correct_num_recall) / self.chars_gt
        self.e2e_precision = float(0) if self.chars_recog == 0 else float(self.e2e_correct_num_precision) / self.chars_recog
        self.e2e_hmean = harmonic_mean(self.e2e_recall, self.e2e_precision)

        # Additional recognition score calculation. Notated as RS in paper.
        for det in np.where(np.sum(self.match_matrix, axis=0) > 0)[0]:
            self.e2e_recog_score_chars += len(self.detQuery[det])
        self.e2e_recog_score_correct_num = np.sum(self.e2e_result_matrix[len(self.gt_boxes)])
        self.e2e_recog_score = float(0) if self.e2e_recog_score_chars == 0 else  float(self.e2e_recog_score_correct_num) / self.e2e_recog_score_chars


    def evaluation(self):
        self.area_precision_matrix = np.zeros([len(self.gt_boxes), len(self.det_boxes)])
        self.det_result_matrix = np.zeros([len(self.gt_boxes)+2, len(self.det_boxes)+2])
        self.match_matrix = np.zeros([len(self.gt_boxes), len(self.det_boxes)])

        self.calc_area_precision()
        self.calc_pcc_inclusion()
        self.filter_det_dont_care()
        self.calc_match_matrix()

        # Matching Process
        self.eval_det()

        # Evaluation Process
        if self.with_e2e:
            self.e2e_result_matrix = np.zeros([len(self.gt_boxes)+2, len(self.det_boxes)+2])
            self.eval_e2e()

    def to_dict(self):
        # print(self.pcc_count_matrix[0], type(self.pcc_count_matrix[0]))
        # print(self.pcc_count_matrix[0][0], type(self.pcc_count_matrix[0][0]))

        sample_metric_dict = {
            'Rawdata': {
                'det_correct_num_recall': self.det_correct_num_recall,
                'det_correct_num_precision': self.det_correct_num_precision,
                'chars_gt': self.chars_gt,
                'chars_det': self.chars_det,
                'num_splitted': self.num_splitted,
                'num_merged': self.num_merged,
                'num_false_positive': self.num_false_pos,
                'char_missed': self.char_missed,
                'char_overlapped': self.char_overlapped,
                'char_false_positive': self.char_false_pos
            },
            'Detection': {
                'precision': self.det_precision,
                'recall': self.det_recall,
                'hmean': self.det_hmean,
            },
            'pairs': self.pairs,
            'detectionMat': [] if len(self.gt_boxes) > 100 else self.det_result_matrix.tolist(),
            'precisionMat': [] if len(self.det_boxes) > 100 else self.area_precision_matrix.tolist(),
            'gtPolPoints': [box.points for box in self.gt_boxes],
            'detPolPoints': [box.points for box in self.det_boxes],
            'gtCharPoints': self.gt_pcc_points,
            'gtCharCounts': [np.sum(x, axis=0).tolist() for x in self.pcc_count_matrix],
            'gtDontCare': self.gt_dont_care_indices,
            'detDontCare': self.det_dont_care_indices,
            'evaluationParams': vars(PARAMS),
            'evaluationLog': self.eval_log
        }

        if self.with_e2e:
            sample_metric_dict['Rawdata'].update({
                'e2e_correct_num_recall': self.e2e_correct_num_recall,
                'e2e_correct_num_precision': self.e2e_correct_num_precision,
                'chars_recog': self.chars_recog,
                'e2e_char_missed': self.e2e_char_missed,
                'e2e_char_false_positive': self.e2e_char_false_pos,
                'e2e_recog_score_chars': self.e2e_recog_score_chars,
                'e2e_recog_score_correct_num': self.e2e_recog_score_correct_num
            })
            sample_metric_dict.update({
                'EndtoEnd': {
                    'precision': self.e2e_precision,
                    'recall': self.e2e_recall,
                    'hmean': self.e2e_hmean,
                    'recognition_score': self.e2e_recog_score
                },
                'end2endMat': [] if len(self.gt_boxes) > 100 else self.e2e_result_matrix.tolist(),
                'gtTrans': [box.transcription for box in self.gt_boxes],
                'detTrans': [box.transcription for box in self.det_boxes],
                'gtQuery': self.gtQuery,
                'detQuery': self.detQuery
            })

        return sample_metric_dict


def eval_single_result(gt_file, det_file):
    sample_result = SampleResult(PARAMS.E2E, PARAMS.RS)
    # We suppose there always exist transcription information on end-to-end evaluation
    if PARAMS.E2E:
        PARAMS.TRANSCRIPTION = True
    gt_boxes = rrc_evaluation_funcs.parse_single_file(gt_file, PARAMS.CRLF, PARAMS.BOX_TYPE, True, False)
    sample_result.prepare_gt(gt_boxes)
    det_boxes = rrc_evaluation_funcs.parse_single_file(det_file, PARAMS.CRLF, PARAMS.BOX_TYPE,
                                                       PARAMS.TRANSCRIPTION, PARAMS.CONFIDENCES)
    sample_result.prepare_det(det_boxes)
    sample_result.evaluation()
    return sample_result.to_dict()

def cleval_evaluation(gt_file, submit_file):
    """
    evaluate and returns the results
    Returns with the following values:
        - method (required)  Global method metrics. Ex: { 'Precision':0.8,'Recall':0.9 }
        - per_sample (optional) Per sample metrics. Ex: {'sample1' : { 'Precision':0.8,'Recall':0.9 },
                                                         'sample2' : { 'Precision':0.8,'Recall':0.9 }
    """

    # storing overall result
    overall_result = GlobalResult(PARAMS.E2E)

    # to store per sample evaluation results
    per_sample_metrics = {}

    gt_files = load_zip_file(gt_file, PARAMS.GT_SAMPLE_NAME_2_ID)
    submission_files = load_zip_file(submit_file, PARAMS.DET_SAMPLE_NAME_2_ID, True)

    # prepare ThreadPool for multi-process
    executor = concurrent.futures.ProcessPoolExecutor(max_workers=PARAMS.NUM_WORKERS)
    futures = {}
    bar_len = len(gt_files)

    for file_idx in gt_files:
        gt_file = rrc_evaluation_funcs.decode_utf8(gt_files[file_idx])
        if file_idx in submission_files:
            det_file = decode_utf8(submission_files[file_idx])
            if det_file is None:
                det_file = ""
        else:
            det_file = ""

        future = executor.submit(eval_single_result, gt_file, det_file)
        futures[future] = file_idx

    with tqdm(total=bar_len) as pbar:
        pbar.set_description("Integrating results...")
        for future in concurrent.futures.as_completed(futures):
            file_idx = futures[future]
            result = future.result()
            per_sample_metrics[file_idx] = result
            overall_result.accumulate_stats(result['Rawdata'])
            pbar.update(1)

    executor.shutdown()

    resDict = {'calculated': True, 'Message': '', 'method': overall_result.to_dict(), 'per_sample': per_sample_metrics}
    return resDict


if __name__ == '__main__':
    rrc_evaluation_funcs.main_evaluation(validate_data, cleval_evaluation)
