import os
import subprocess

from zipfile import ZipFile

from tornado import gen

from analytics.classes.img_downloader import getPath, ImgDownloader
from errors.error import Result, Error
from common.tasks import TaskType

filesToRemove = ['.tex', '.log', '.aux']

resultFolder = os.path.abspath(os.path.join('storage', 'reports'))
if not os.path.exists(resultFolder):
    os.mkdir(resultFolder)

TEX_DOC_START = (
    "\\documentclass[14pt,DIV14]{scrartcl}\n"
    "\\usepackage[utf8x]{inputenc}\n"
    "\\usepackage[russian]{babel}\n"
    "\\usepackage{lscape}\n"
    "\\usepackage{graphicx}% http://ctan.org/pkg/graphicx\n"
    "\\usepackage{array}% http://ctan.org/pkg/array\n"
    "\\usepackage[table]{xcolor}\n"
    "\\evensidemargin=-1cm\n"
    "\\oddsidemargin=-1cm\n"
    "%\\textwidth=20cm\n"
    "\\topmargin=-2.0cm \\textheight=26cm\n"
    "\\begin{document}\n"
    "%\\begin{landscape}\n"
    "\\newcommand\\columnWidth{2.5cm}\n"
    "\\newcommand\\scaleFactor{0.15}\n"
    "\\begin{table}[h!]\n"
    "\\tiny\n"
    "\\centering\n"
    "\\begin{tabular}{| m{0.5cm} | m{\columnWidth} | m{\columnWidth} | m{\columnWidth} |  m{\columnWidth} "
    "| m{\columnWidth} | m{\columnWidth} | }\n"
    "\\hline\n"
)
TEX_DOC_CELL_SEP = "&\n"
TEX_DOC_ROW_END = "\\\\ \n\\hline\n"
TEX_DOC_PAGE_SEP = (
    "\\end{tabular}\n"
    "\\end{table}\n"
    "\\clearpage\n"
    "\\begin{table}[h!]\n"
    "\\tiny\n"
    "\\centering\n"
    "\\begin{tabular}{| m{0.5cm} | m{\columnWidth} | m{\columnWidth} | m{\columnWidth} | "
    "m{\columnWidth} | m{\columnWidth} | m{\columnWidth} | }\n" 
    "\\hline\n"
)
TEX_DOC_END = (
    "\\end{tabular}\n"
    "\\end{table}\n"
    "%\\end{landscape}\n"
    "\\end{document}\n"
)
TEX_COUNT_COLUMNS = 7


def TEXDescriptorIdToImg(reference, color=""):
    """
    Make tex image with color bounds.

    :param reference: image path
    :param color: any supported color
    :return: tex cell content
    """
    defaultReference = os.path.join('storage', 'no_face.jpg')
    path = getPath(reference)
    if not os.path.exists(path):
        path = defaultReference
    path = os.path.abspath(path)
    if color:
        color = "\\cellcolor{%s}\n" % color
    return color + "\\begin{minipage}{\\scaleFactor\\textwidth}\n" \
                   "\\includegraphics[width=\\linewidth]{" + \
                   path + \
                   "}\n" \
                   "\\end{minipage}\n"


def TEXLineGenerator(preparedData, resource_type):
    """
    Generate lines (one line consists of three rows: ids, images, comments).

    :param preparedData: input data, reporterObject list list
    :param resource_type: input task type
    :return: None
    """
    for i in range(len(preparedData)):
        result = [[str(i + 1)], [""], [""]]
        for cell in preparedData[i]:
            result[0].append(cell.object_id)
            result[1].append(TEXDescriptorIdToImg(cell.portrait_id, cell.color))
            result[2].append(cell.comment)

        # for clusterization stub must be [" "]
        if resource_type == TaskType.CROSS_MATCHER:
            stub = [" ", " "]
        elif resource_type == TaskType.CLUSTERIZATION:
            stub = [" "]
        else:
            raise TypeError('Cannot make csv on "{}" type'.format(resource_type))
        while len(result[-1]) > TEX_COUNT_COLUMNS:
            result += [
                stub + result[-3][TEX_COUNT_COLUMNS:],
                stub + result[-2][TEX_COUNT_COLUMNS:],
                stub + result[-1][TEX_COUNT_COLUMNS:]
            ]
            result[-6], result[-5], result[-4] = result[-6][:TEX_COUNT_COLUMNS], result[-5][:TEX_COUNT_COLUMNS], \
                                                 result[-4][:TEX_COUNT_COLUMNS]

        for j in range(1, 4):
            result[-j] += [" "] * (TEX_COUNT_COLUMNS - len(result[-j]))

        for lineNum in range(len(result) // 3):
            text = ""
            for line in (TEX_DOC_CELL_SEP.join(line) for line in result[lineNum * 3:(lineNum + 1) * 3]):
                text += line + TEX_DOC_ROW_END
            yield text


def TEXCreate(preparedData, resource_type):
    """
    Create result tex-file text content.

    :param preparedData: input data, reporterObject list list
    :param resource_type: input task type
    :return: text of tex file
    """
    count = 0
    text = TEX_DOC_START
    for line in TEXLineGenerator(preparedData, resource_type):
        count += 1
        text += line
        if not count % 6:
            text += TEX_DOC_PAGE_SEP
    text += TEX_DOC_END
    return text


def CSVCreateCrossMatch(crossMatch, referenceType, candidateType, savePortraits):
    """
    Create csv from cross_match results.

    :param crossMatch: list of match results
    :param referenceType: one of "descriptors", "persons", "events" or "groups"
    :param candidateType: one of "descriptors", "persons", "events" or "groups"
    :return: text of csv file
    """
    headers = ['Num', referenceType[:-1].capitalize()] + \
              ['Reference ' + k for k in crossMatch[0][0].fields585(savePortraits).keys()] + \
              [candidateType[:-1].capitalize()] +\
              ['Candidate ' + k for k in crossMatch[0][1].fields585(savePortraits).keys()]

    data = [headers]
    for match in crossMatch:
        ref = match[0]
        for cand in match[1:]:
            data += [[str(len(data)), ref.object_id, *ref.fields585(savePortraits).values(),
                      cand.object_id, *cand.fields585(savePortraits).values()]]
    text = '\n'.join(','.join(str(cell) for cell in row) for row in data)
    return text


def CSVCreateClusterization(clusterization, objectType, savePortraits):
    """
    Create csv from cross_match results.

    :param clusterization: list of results clusters
    :param objectType: one of "descriptors", "persons", "events" or "groups"
    :return: text of csv file
    """
    headers = ['Num', 'Cluster', objectType[:-1].capitalize(), *clusterization[0][0].fields585(savePortraits).keys()]

    data = [headers]
    for clusterNum in range(len(clusterization)):
        for obj in clusterization[clusterNum]:
            data += [[str(len(data)), str(clusterNum + 1), obj.object_id, *obj.fields585(savePortraits).values()]]
    text = '\n'.join(','.join(str(cell) for cell in row) for row in data)
    return text


def makezip(resultFolder, taskId, SCVText, portraits=None):
    """
    Zip file generator from input files.

    :param resultFolder: a folder to save zip file in
    :param taskId: the current task id to name the archive
    :param SCVText: text of a csv file
    :param portraits: portraits to save if needed
    :return: None
    """
    zipfileName = os.path.join(resultFolder, '{}.zip'.format(taskId))
    with ZipFile(zipfileName, 'w') as zipfile:
        zipfile.writestr('{}.csv'.format(taskId), SCVText)
        if portraits is not None:
            portraitsDir = 'portraits'
            for portrait in portraits:
                target_file = getPath(portrait)
                result_file = os.path.join(portraitsDir, '{}.jpg'.format(portrait))
                if os.path.exists(target_file):
                    zipfile.write(target_file, result_file)


class ReporterObject:
    """
    Object (represent any of: descriptor, person, event or group) reporter to work with.

    Attributes:
        object_id (UUID4): object id
        portrait_id (UUID4): object portrait
        color (str): color to color image boundaries in a pdf report
        additional_fields (dict): dictionary with additional object data
    """
    def __init__(
            self,
            object_id: str,
            portrait_id: str,
            color: str,
            additional_fields: dict,
    ):
        """
        Reporter object
        :param object_id: object id
        :param portrait_id: object portrait id
        :param color: color to wrap image in pdf in, smth like "green", "orange", etc
        :param additional_fields: dict    # any of them could not exist
            {
                'user_data': '<str>',       # is set if object is person
                'create_time': '<str>',     # is set if object is event or group
                'source': '<str>',          # is set if object is event or group
                'tags': '<str>',            # is set if object is event or group
            }
        """
        self.object_id = object_id
        self.portrait_id = portrait_id
        self.color = color
        self.additional_fields = additional_fields
        self.round_data()

    def round_data(self):
        """
        Round additional fields' data.

        :return: None
        """
        for attr in ('age', 'gender'):
            if attr in self.additional_fields:
                try:
                    self.additional_fields[attr] = round(float(self.additional_fields[attr]))
                except ValueError:
                    pass
        if 'create_time' in self.additional_fields:
            datetime_field = 'create_time'
        elif 'last_update' in self.additional_fields:
            datetime_field = 'last_update'
        else:
            datetime_field = None
        if datetime_field is not None and self.additional_fields[datetime_field]:
            datetime = self.additional_fields[datetime_field]
            self.additional_fields['date'] = '.'.join(reversed(datetime.split('T')[0].split('-')))
            self.additional_fields['time'] = datetime.split('T')[1][:-1]
            if '.' in self.additional_fields['time']:
                self.additional_fields['time'] = self.additional_fields['time'].split('.')[0]
            self.additional_fields.pop(datetime_field)

    @property
    def comment(self):
        """
        Makes comment in csv in appropriate order. Only first four found fields are included.
        Field is truncated if it's length is more than 17 symbols.

        :rtype: str
        :return: comment text
        """
        fields_to_add = ('Similarity', 'Date', 'Time', 'Source', 'User_Data', 'Age', 'Tags', 'Gender')
        comment = {
            k: self.fields585(0)[k]
            for k in fields_to_add
            if k in self.fields585(0) and self.fields585(0)[k] not in ("", None)
        }

        for text_field in ('User_Data', 'Source', 'Tags'):
            if text_field in comment and len(comment[text_field]) > 17:
                comment[text_field] = comment[text_field][:14] + '...'

        comment_pairs = sorted(list(comment.items()), key=lambda x: fields_to_add.index(x[0]))[:4]

        return '\n\n'.join(
            '{}: {}'.format(k, v).replace('_', '\\_') for k, v in comment_pairs
        )

    def fields585(self, savePortraits=True):
        """
        Get necessary fields or None if not exist.

        :param savePortraits: column 'Photo Name' is not used if no photos provided
        :return: data dictionary
        """
        newData = {
            # 2018-02-05T18:07:59Z -> 2018-02-05
            'Date': self.additional_fields.get('date', None),
            # 2018-02-05T18:07:59Z -> 18:07:59
            'Time': self.additional_fields.get('time', None),
            # Camera Name is event source
            'Source': self.additional_fields.get('source', None),
            # Tags
            'Tags': self.additional_fields.get('tags', None),
            # Detection is descriptor_id
            'Detection': self.portrait_id,
            # Age - just another name
            'Age': self.additional_fields.get('age', None),
            # Gender - just another name
            'Gender': self.additional_fields.get('gender', None),
            # User data for person
            'User_Data': self.additional_fields.get('user_data', None)
        }
        if savePortraits:
            # Photo Name is <descriptor_id>.jpg
            newData['Photo Name'] = (self.portrait_id + '.jpg') if os.path.exists(getPath(self.portrait_id)) else None
        if 'similarity' in self.additional_fields:
            newData['Similarity'] = self.additional_fields['similarity']
        return newData


class Reporter:
    """
    Report creator worker

    Attributes:
        input (list): input ReporterObject matrix
        task (Task): task
        weight (float): number is equal to time(report)/time(task)
        format (str): report format, one of "csv" or "pdf"
        types (object): object type(s)
    """

    def __init__(self, inputData, task, weightOfReporterStep, types=(None, None)):
        """
        Init and prepare reporter object

        :param inputData:
            for cross-match: [[ref, cand, cand, ...]], both ref and cand are ReporterObject
            for clusterization: [[obj, obj, obj, ...]], obj is ReporterObject
        :param task: task to increase progress in
        :param weightOfReporterStep: number is equal to time(report)/time(task)
        :param types:
            for cross-match: tuple of two types - reference and candidate
            for clusterization: object type
        """
        self.input = inputData
        self.task = task
        self.weight = weightOfReporterStep
        self.format = task.task['format']
        self.types = types

    @gen.coroutine
    def report(self, resource_type=TaskType.CROSS_MATCHER):
        """
        Reporter function.

        :param resource_type:
        :return: result
            Success if succeed
            Fail if an error occurred
        """
        portraits = {obj.portrait_id for l in self.input for obj in l}

        downloader = ImgDownloader(portraits, self.task, 0.7 * self.weight)

        if self.format == 'pdf':
            yield downloader.download()

            texFile = os.path.join(resultFolder, '{}.tex'.format(self.task.id))
            if resource_type == TaskType.CROSS_MATCHER:
                text = TEXCreate(self.input, resource_type)
            elif resource_type == TaskType.CLUSTERIZATION:
                text = TEXCreate(self.input, resource_type)
            else:
                return Result(Error.NotImplementedError,
                              'Wrong resource task type for Reporter: "{}"'.format(resource_type))
            with open(texFile, 'w', encoding='UTF-8') as _:
                _.write(text)
            r = subprocess.call([
                'pdflatex',
                '-interaction=nonstopmode',
                '-output-directory={}'.format(resultFolder),
                texFile,
            ], stdout=subprocess.DEVNULL)
            almostFile = texFile[:-4]
            subprocess.call(['rm'] + [almostFile + suffix for suffix in filesToRemove])
            self.task.progress += 0.3 * self.weight
            if not r:
                return Result(Error.Success, 0)
            return Result(Error.UnknownError, 0)
        elif self.format == 'csv':
            savePortraits = 'parameters' in self.task.task and self.task.task['parameters'].get('save_portraits', 0)
            if savePortraits:
                yield downloader.download()

            if resource_type == TaskType.CROSS_MATCHER:
                text = CSVCreateCrossMatch(self.input, *self.types, savePortraits)
            elif resource_type == TaskType.CLUSTERIZATION:
                text = CSVCreateClusterization(self.input, self.types, savePortraits)
            else:
                return Result(Error.NotImplementedError,
                              'Wrong resource task type for Reporter: "{}"'.format(resource_type))

            makezip(resultFolder, self.task.id, text, portraits if savePortraits else None)
            return Result(Error.Success, 0)
        return Result(Error.NotImplementedError, 'Wrong Reporter format: "{}"'.format(self.format))
