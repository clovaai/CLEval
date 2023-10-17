from dataclasses import dataclass, field
from typing import Dict, List, Union

from cleval.utils import harmonic_mean


class MatchReleation:
    ONE_TO_ONE = "one-to-one"
    MANY_TO_ONE = "many-to-one"
    ONE_TO_MANY = "one-to-many"


@dataclass
class CoreStats:
    recall: float = 0.0
    precision: float = 0.0
    hmean: float = 0.0

    num_char_gt: int = 0  # TotalNum for Recall
    num_char_det: int = 0  # TotalNum for Precisiion
    gran_score_recall: float = 0.0
    num_char_tp_recall: int = 0
    gran_score_precision: float = 0.0
    num_char_tp_precision: int = 0

    num_char_fp: int = 0  # false positive


@dataclass
class MatchResult:
    gt_ids: List[int]
    det_ids: List[int]
    match_relation: str  # from MatchRelation

    det: CoreStats = field(default_factory=CoreStats)
    e2e: CoreStats = field(default_factory=CoreStats)


@dataclass
class Point:
    x: int
    y: int


@dataclass
class GTBoxResult:
    id: int
    points: List[Point]
    pccs: List[Point]
    orientation: Union[None, str]
    letters: str
    is_dc: bool


@dataclass
class DetBoxResult:
    id: int
    points: List[Point]
    orientation: Union[None, str]
    letters: str


@dataclass
class Stats:
    det: CoreStats = field(default_factory=CoreStats)
    e2e: CoreStats = field(default_factory=CoreStats)

    # split-merge cases
    num_splitted: int = 0
    num_merged: int = 0
    num_char_overlapped: int = 0

    # orientation evaluation
    ori_acc: float = 0.0
    num_ori_total: int = 0
    num_ori_correct: int = 0


@dataclass
class SampleResult:
    matches: List[MatchResult]
    gts: List[GTBoxResult]
    preds: List[DetBoxResult]
    stats: Stats = field(default_factory=Stats)
    image_id: Union[int, None] = None


@dataclass
class GlobalResult:
    """Object that holds each record of all samples."""

    dataset_inform: Dict = field(default_factory=dict)
    sample_results: List[SampleResult] = field(default_factory=list)
    stats: Stats = field(default_factory=Stats)


def accumulate_result(
    global_res: GlobalResult,
    sample_res: SampleResult,
    is_e2e: bool,
    dump_sample_res: bool = False,
):
    if dump_sample_res:
        global_res.sample_results.append(sample_res)
    accumulate_stats(global_res.stats, sample_res.stats, is_e2e)


def accumulate_stats(stats1: Stats, stats2: Stats, is_e2e: bool):
    """Accumulate core stats exclude ori_acc."""
    stats1.num_splitted += stats2.num_splitted
    stats1.num_merged += stats2.num_merged
    stats1.num_char_overlapped += stats2.num_char_overlapped
    stats1.num_ori_total += stats2.num_ori_total
    stats1.num_ori_correct += stats2.num_ori_correct

    accumulate_core_stats(stats1.det, stats2.det)
    if is_e2e:
        accumulate_core_stats(stats1.e2e, stats2.e2e)


def accumulate_core_stats(stats1: CoreStats, stats2: CoreStats):
    """Accumulate core stats exclude recall, precision, and hmean."""
    stats1.num_char_gt += stats2.num_char_gt
    stats1.num_char_det += stats2.num_char_det
    stats1.gran_score_recall += stats2.gran_score_recall
    stats1.num_char_tp_recall += stats2.num_char_tp_recall
    stats1.gran_score_precision += stats2.gran_score_precision
    stats1.num_char_tp_precision += stats2.num_char_tp_precision
    stats1.num_char_fp += stats2.num_char_fp


def calculate_global_rph(res: GlobalResult, is_e2e: bool):
    calculate_rph(res.stats.det)
    if is_e2e:
        calculate_rph(res.stats.e2e)


def calculate_rph(stats: CoreStats):
    total_gt = stats.num_char_gt
    total_det = stats.num_char_det
    tp_gt = stats.num_char_tp_recall
    gran_gt = stats.gran_score_recall
    tp_det = stats.num_char_tp_precision
    gran_det = stats.gran_score_precision

    # Sample Score : Character correct length - Granularity Penalty
    recall = 0.0 if total_gt == 0 else max(0.0, tp_gt - gran_gt) / total_gt
    precision = 0.0 if total_det == 0 else max(0.0, tp_det - gran_det) / total_det
    hmean = harmonic_mean(recall, precision)
    stats.recall = recall
    stats.precision = precision
    stats.hmean = hmean
