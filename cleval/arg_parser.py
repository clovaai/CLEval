import argparse
import os

from cleval.utils import cpu_count


def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ("yes", "true", "t", "y", "1"):
        return True
    elif v.lower() in ("no", "false", "f", "n", "0"):
        return False
    else:
        raise argparse.ArgumentTypeError("Boolean value expected.")


def get_params():
    parser = argparse.ArgumentParser(description="test global argument parser")

    # script parameters
    parser.add_argument("-g", "--GT_PATHS", nargs="+", help="Path of the Ground Truth files.")
    parser.add_argument("-s", "--SUBMIT_PATHS", nargs="+", help="Path of your method's results file.")

    # webserver parameters
    parser.add_argument(
        "-o",
        "--OUTPUT_PATH",
        default="output/",
        help="Path to a directory where to copy the file that" " contains per-sample results.",
    )
    parser.add_argument("--DUMP_SAMPLE_RESULT", action="store_true")
    parser.add_argument("-p", "--PORT", default=8080, help="port number to show")

    # result format related parameters
    parser.add_argument("--BOX_TYPE", default="QUAD", choices=["LTRB", "QUAD", "POLY"])
    parser.add_argument("--TRANSCRIPTION", action="store_true")
    parser.add_argument("--CONFIDENCES", action="store_true")
    parser.add_argument("--CRLF", action="store_true")

    # end-to-end related parameters
    parser.add_argument("--E2E", action="store_true")
    parser.add_argument("--CASE_SENSITIVE", default=True, type=str2bool)
    parser.add_argument("--RECOG_SCORE", default=True, type=str2bool)

    # evaluation related parameters
    parser.add_argument("--AREA_PRECISION_CONSTRAINT", type=float, default=0.3)
    parser.add_argument("--RECALL_GRANULARITY_PENALTY_WEIGHT", type=float, default=1.0)
    parser.add_argument("--PRECISION_GRANULARITY_PENALTY_WEIGHT", type=float, default=1.0)
    parser.add_argument("--VERTICAL_ASPECT_RATIO_THRESH", default=0.5)

    # orientation evaluation
    parser.add_argument("--ORIENTATION", action="store_true")

    # sub-set evaluation  (
    parser.add_argument("--SCALE_WISE", action="store_true")  # scale-wise evaluation
    parser.add_argument("--SCALE_BINS", default=(0.0, 0.005, 0.01, 0.015, 0.02, 0.025, 0.1, 0.5, 1.0))

    # other parameters
    parser.add_argument("-t", "--NUM_WORKERS", default=-1, type=int, help="number of threads to use")
    parser.add_argument(
        "-v",
        "--VERBOSE",
        default=False,
        action="store_true",
        help="print evaluation progress or not",
    )
    parser.add_argument("--DEBUG", action="store_true")
    parser.add_argument("--PROFILE", action="store_true")

    args = parser.parse_args()
    assert len(args.GT_PATHS) == len(args.SUBMIT_PATHS) == 1

    if args.NUM_WORKERS == -1:
        args.NUM_WORKERS = cpu_count()

    # We suppose there always exist transcription information on end-to-end evaluation
    if args.E2E:
        args.TRANSCRIPTION = True

    os.makedirs(args.OUTPUT_PATH, exist_ok=True)
    return args


if __name__ == "__main__":
    from pprint import pprint

    args = get_params()
    pprint(args)
