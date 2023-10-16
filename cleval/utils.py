import codecs
import re
import subprocess
import zipfile

import json
from numba import njit


def load_zip_file(file):
    """
    Returns an array with the contents (filtered by fileNameRegExp) of a ZIP file.
    all_entries validates that all entries in the ZIP file pass the fileNameRegExp
    """
    archive = zipfile.ZipFile(file, mode="r", allowZip64=True)

    pairs = dict()
    for name in archive.namelist():
        key_name = (
            name.replace("gt_", "").replace("res_", "").replace(".txt", "").replace(".json", "").replace(".jpg", "")
        )
        pairs[key_name] = archive.read(name)
    return pairs


def decode_utf8(raw):
    """
    Returns a Unicode object
    """
    raw = codecs.decode(raw, "utf-8", "replace")

    # extracts BOM if exists
    raw = raw.encode("utf8")
    if raw.startswith(codecs.BOM_UTF8):
        raw = raw.replace(codecs.BOM_UTF8, b"", 1)
    return raw.decode("utf-8")


def dump_json(json_file_path, json_data):
    with open(json_file_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f)


def read_json(json_file_path):
    with open(json_file_path, "r", encoding="utf-8") as f:
        json_data = json.load(f)
    return json_data


def convert_ltrb2quad(points):
    """Convert point format from LTRB to QUAD"""
    new_points = [
        points[0],
        points[1],
        points[2],
        points[1],
        points[2],
        points[3],
        points[0],
        points[3],
    ]
    return new_points


def ltrb_regex_match(line, with_transcription, with_confidence):
    if with_transcription and with_confidence:
        m = re.match(
            r"^\s*(-?[0-9]+)\s*"
            r",\s*(-?[0-9]+)\s*"
            r",\s*([0-9]+)\s*"
            r",\s*([0-9]+)\s*"
            r",\s*([0-1].?[0-9]*)\s*,(.*)$",
            line,
        )
        if m is None:
            raise ValueError("Format incorrect. " "Should be: xmin,ymin,xmax,ymax,confidence,transcription")
    elif with_confidence:
        m = re.match(
            r"^\s*(-?[0-9]+)\s*," r"\s*(-?[0-9]+)\s*," r"\s*([0-9]+)\s*," r"\s*([0-9]+)\s*," r"\s*([0-1].?[0-9]*)\s*$",
            line,
        )
        if m is None:
            raise ValueError("Format incorrect. Should be: xmin,ymin,xmax,ymax,confidence")
    elif with_transcription:
        m = re.match(
            r"^\s*(-?[0-9]+)\s*," r"\s*(-?[0-9]+)\s*," r"\s*([0-9]+)\s*," r"\s*([0-9]+)\s*,(.*)$",
            line,
        )
        if m is None:
            raise ValueError("Format incorrect. Should be: xmin,ymin,xmax,ymax,transcription")
    else:
        m = re.match(
            r"^\s*(-?[0-9]+)\s*," r"\s*(-?[0-9]+)\s*," r"\s*([0-9]+)\s*," r"\s*([0-9]+)\s*,?\s*$",
            line,
        )
        if m is None:
            raise ValueError("Format incorrect. Should be: xmin,ymin,xmax,ymax")
    return m


def quad_regex_match(line, with_transcription, with_confidence):
    if with_transcription and with_confidence:
        m = re.match(
            r"^\s*(-?[0-9]+)\s*,"
            r"\s*(-?[0-9]+)\s*,"
            r"\s*(-?[0-9]+)\s*,"
            r"\s*(-?[0-9]+)\s*,"
            r"\s*(-?[0-9]+)\s*,"
            r"\s*(-?[0-9]+)\s*,"
            r"\s*(-?[0-9]+)\s*,"
            r"\s*(-?[0-9]+)\s*,"
            r"\s*([0-1].?[0-9]*)\s*,(.*)$",
            line,
        )
        if m is None:
            raise ValueError("Format incorrect. " "Should be: x1,y1,x2,y2,x3,y3,x4,y4,confidence,transcription")
    elif with_confidence:
        m = re.match(
            r"^\s*(-?[0-9]+)\s*,"
            r"\s*(-?[0-9]+)\s*,"
            r"\s*(-?[0-9]+)\s*,"
            r"\s*(-?[0-9]+)\s*,"
            r"\s*(-?[0-9]+)\s*,"
            r"\s*(-?[0-9]+)\s*,"
            r"\s*(-?[0-9]+)\s*,"
            r"\s*(-?[0-9]+)\s*,"
            r"\s*([0-1].?[0-9]*)\s*$",
            line,
        )
        if m is None:
            raise ValueError("Format incorrect. Should be: x1,y1,x2,y2,x3,y3,x4,y4,confidence")
    elif with_transcription:
        m = re.match(
            r"^\s*(-?[0-9]+)\s*,"
            r"\s*(-?[0-9]+)\s*,"
            r"\s*(-?[0-9]+)\s*,"
            r"\s*(-?[0-9]+)\s*,"
            r"\s*(-?[0-9]+)\s*,"
            r"\s*(-?[0-9]+)\s*,"
            r"\s*(-?[0-9]+)\s*,"
            r"\s*(-?[0-9]+)\s*,(.*)$",
            line,
        )
        if m is None:
            raise ValueError("Format incorrect. Should be: x1,y1,x2,y2,x3,y3,x4,y4,transcription")
    else:
        if line[-1] == ",":
            line = line[:-1]
        m = re.match(
            r"^\s*(-?[0-9]+)\s*,"
            r"\s*(-?[0-9]+)\s*,"
            r"\s*(-?[0-9]+)\s*,"
            r"\s*(-?[0-9]+)\s*,"
            r"\s*(-?[0-9]+)\s*,"
            r"\s*(-?[0-9]+)\s*,"
            r"\s*(-?[0-9]+)\s*,"
            r"\s*(-?[0-9]+)\s*$",
            line,
        )
        if m is None:
            raise ValueError("Format incorrect. Should be: x1,y1,x2,y2,x3,y3,x4,y4")
    return m


@njit
def lcs(s1, s2):
    """Longeset Common Sequence between s1 & s2"""
    # https://stackoverflow.com/questions/48651891/longest-common-subsequence-in-python
    if len(s1) == 0 or len(s2) == 0:
        return 0, ""
    matrix = [["" for _ in range(len(s2))] for _ in range(len(s1))]
    for i in range(len(s1)):
        for j in range(len(s2)):
            if s1[i] == s2[j]:
                if i == 0 or j == 0:
                    matrix[i][j] = s1[i]
                else:
                    matrix[i][j] = matrix[i - 1][j - 1] + s1[i]
            else:
                if len(matrix[i - 1][j]) > len(matrix[i][j - 1]):
                    matrix[i][j] = matrix[i - 1][j]
                else:
                    matrix[i][j] = matrix[i][j - 1]
    cs = matrix[-1][-1]
    return len(cs), cs


@njit
def harmonic_mean(score1, score2):
    """get harmonic mean value"""
    if score1 + score2 == 0:
        return 0
    else:
        return (2 * score1 * score2) / (score1 + score2)


def cpu_count():
    """Get number of cpu
    os.cpu_count() has a problem with docker container.
    For example, we have 72 cpus. os.cpu_count() always return 72
    even if we allocate only 4 cpus for container.
    """
    return int(subprocess.check_output("nproc").decode().strip())
