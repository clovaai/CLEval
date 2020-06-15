import re
import codecs
import zipfile


def load_zip_file_keys(file, file_name_reg_exp=''):
    try:
        archive = zipfile.ZipFile(file, mode='r', allowZip64=True)
    except:
        raise Exception('Error loading the ZIP archive.')

    pairs = []

    for name in archive.namelist():
        addFile = True
        keyName = name
        if file_name_reg_exp != "":
            m = re.match(file_name_reg_exp, name)
            if m == None:
                addFile = False
            else:
                if len(m.groups()) > 0:
                    keyName = m.group(1)

        if addFile:
            pairs.append(keyName)

    return pairs


def load_zip_file(file, file_name_reg_exp='', allEntries=False):
    """
    Returns an array with the contents (filtered by fileNameRegExp) of a ZIP file.
    The key's are the names or the file or the capturing group definied in the fileNameRegExp
    allEntries validates that all entries in the ZIP file pass the fileNameRegExp
    """
    try:
        archive = zipfile.ZipFile(file, mode='r', allowZip64=True)
    except:
        raise Exception('Error loading the ZIP archive')

    pairs = dict()
    for name in archive.namelist():
        addFile = True
        keyName = name.replace('gt_', '').replace('res_', '').replace('.txt', '')

        if addFile:
            pairs[keyName] = archive.read(name)
        else:
            if allEntries:
                raise Exception('ZIP entry not valid: %s' % name)
    return pairs


def decode_utf8(raw):
    """
    Returns a Unicode object on success, or None on failure
    """
    try:
        raw = codecs.decode(raw, 'utf-8', 'replace')
        # extracts BOM if exists
        raw = raw.encode('utf8')
        if raw.startswith(codecs.BOM_UTF8):
            raw = raw.replace(codecs.BOM_UTF8, '', 1)
        return raw.decode('utf-8')
    except Exception:
        return None
