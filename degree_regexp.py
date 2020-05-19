import sys
import traceback
import csv
import re
from enum import IntEnum
from operator import itemgetter


if len(sys.argv) < 2:
    print('Usage: python degree_regexp.py csv_path')
    exit()

"""
功能：将数据中的学位信息转换成统一标准
机制：
    1. 分隔原始学历数据。分隔标准，是否含有简称标记符号。分为firstA(是)和firstB(否)。
    2. 识别firstA。firstA先识别简称，后识别其中普通文本，如果识别出来，更新_map，添加新元素。
    3. firstA未识别出来的信息，暂存到_temporary_after_find表。
    4. 识别firstB。firstB识别其中普通文本。
    5. firstB未识别出来的信息，暂存到_temporary_after_find表。
    6. 识别剩余未识别信息，_temporary_after_find表
备注：
    1. 简称标记符号'(简称)',' - 简称'。
    2. 识别简称_recognize_short
    2. 识别普通文本_recognize_text
    2. 识别剩余未识别信息_recognize_other
环境：Python3.5.6
"""


class Degree(IntEnum):
    POSTDOC = 7
    PHD = 6
    MD = 5
    JD = 4
    MBA = 3
    MASTER = 2
    BACHELOR = 1
    INVALID = 0


DEGREE_NAME = {
    Degree.POSTDOC: 'POSTDOC',
    Degree.PHD: 'PHD',
    Degree.MD: 'MD',
    Degree.JD: 'JD',
    Degree.MBA: 'MBA',
    Degree.MASTER: 'MASTER',
    Degree.BACHELOR: 'BACHELOR',
    Degree.INVALID: '',
}


class DRBase:
    def __init__(self, csv_file=None):
        """
        _map: dict, 学历对照表。key为简称(小写无标点无空格)，value为对应学历。初始值为基本学历简称，正则过程中，键值会逐渐增多。
        _map_pattern: str。简称匹配模式，可变。由_map表的key值组成，随_map键值的增多同步增加。
        _pattern_base: str。基础匹配模式，不可变。由基本学历简称组成，按学历高低顺序匹配。
        _original_degrees: list。学历信息的原始数据。['a', 'b', 'c']
        _temporary_noshort: list。暂存数据，firstB部分。
        _temporary_after_find: list。暂存数据。firstA和firstB两部分在第一次识别后，其中部分数据未识别出来，在这里暂存。
        _degrees: list。正则化后的新学历数据，可导出csv。[{'original': original_str, 'regexp': regexp_str}]
        """
        self._map = {'postdoc': Degree.POSTDOC, 'phd': Degree.PHD, 'md': Degree.MD, 'jd': Degree.JD, 'mba': Degree.MBA,
                     'master': Degree.MASTER, 'bachelor': Degree.BACHELOR}
        self._pattern_base = '|'.join([data[0] for data in sorted(self._map.items(), key=itemgetter(1), reverse=True)])
        self._map_pattern = self._pattern_base
        self._degrees = []
        self._temporary_noshort = []
        self._temporary_after_find = []
        self._original_degrees = DRBase.import_csv_file(csv_file)

    def get_degrees(self):
        # 获取正则化后的数据
        return self._degrees[:]

    def _manage_unrecognized_text_with_noshort(self, degree_str):
        # 暂存没有标记简称的文本
        self._temporary_noshort.append(degree_str)

    def _manage_unrecognized_text_after_find(self, degree_str):
        # 暂存经过一次find，未识别出来的
        self._temporary_after_find.append(degree_str)

    def _recognize_short(self, s_short):
        """
        识别简称
        :param s_short:
        :return: Degree Obj
        """
        return self._map.get(s_short)

    def _recognize_text(self, d_text):
        """
        识别文本
        :param d_text:
        :return: Degree Obj
        """
        d_text = d_text.lower()
        result = re.findall(self._pattern_base, d_text)

        return '' if not result else self._map.get(result[0], '')

    def _recognize_other(self, d_other):
        """
        识别剩余的
        :param d_other:
        :return: Degree Obj
        """
        d_other = d_other.lower().replace('.', '')
        # 简称识别
        enum_degree = self._recognize_short(d_other)
        if enum_degree:
            return enum_degree
        # 去除空格再识别一次简称
        d_nospace = d_other.replace(' ', '')
        enum_degree = self._recognize_short(d_nospace)
        if enum_degree:
            return enum_degree
        # map模糊识别
        enum_degree = self._map_recognize_fuzzy(d_other)
        if enum_degree:
            return enum_degree
        # 识别不出来
        return ''

    def _map_recognize_fuzzy(self, d_str):
        """
        map的键模糊匹配
        判断字符串中是否含有map任意一个键
        :param d_str:
        :return:
        """
        _ret_list = re.findall(self._map_pattern, d_str)
        if _ret_list:
            enum_degree = self._map[_ret_list[0]]
            for m_key in _ret_list:
                enum_degree = max(enum_degree, self._map[m_key])
            return enum_degree
        return None

    def _new_degree(self, original_str, regexp_str):
        # 正则化后学历元素
        return self.__create_degree(original_str, regexp_str)

    def __create_degree(self, original_str, regexp_str):
        return {'original': original_str, 'regexp': regexp_str}

    def _get_str_degree_short(self, d_str):
        """
        获取文本中标记的学历简称。简称标记符号'()',' - '。
        """
        s_index = d_str.rfind(' - ')
        if s_index >= 0:
            return d_str[s_index+3:].strip()
        s_list = re.findall(r'[(](.*?)[)]', d_str)
        if s_list:
            return s_list[0]
        return ''

    @classmethod
    def import_csv_file(cls, csv_path):
        """
        导入csv文件
        :param csv_path:
        :return: list
        """
        csv_data = []
        with open(csv_path, newline='') as csvfile:
            spamreader = csv.reader(csvfile)
            for row in spamreader:
                csv_data += row
        return csv_data

    @classmethod
    def export_csv_file(cls, csv_path='degree_regexp.csv', new_csv_data=[]):
        """
        导出csv文件
        :param csv_path:
        :param new_csv_data: [{'original': original_str, 'regexp': regexp_str}]
        """
        with open(csv_path, 'w', newline='') as csvfile:
            spamwriter = csv.writer(csvfile)
            spamwriter.writerow(['original_str', 'regexp_str'])
            for c_data in new_csv_data:
                spamwriter.writerow([c_data.get('original', ''), c_data.get('regexp', '')])


class DRegexp(DRBase):
    def __init__(self, csv_file=None):
        super(DRegexp, self).__init__(csv_file=csv_file)

    def regexp_run(self):
        """
        学历信息正则化
        :return: {}
        """
        # 识别标记简称的
        for _degree_str in self._original_degrees:
            _degree_data = self.degree_recognize_with_short(_degree_str)
            if _degree_data:
                self._degrees.append(_degree_data)
        # 识别普通文本的
        for _degree_str in self._temporary_noshort:
            _degree_data = self.degree_recognize_with_text(_degree_str)
            if _degree_data:
                self._degrees.append(_degree_data)
        # 识别前两步没识别出来的
        for _degree_str in self._temporary_after_find:
            _degree_data = self.degree_recognize_with_second(_degree_str)
            self._degrees.append(_degree_data)
        return self.get_degrees()

    def degree_recognize_with_short(self, degree_str):
        # 识别那些标记为简称的
        d_short = self._get_str_degree_short(degree_str)
        if d_short:
            enum_degree = self.parse_has_short(degree_str, d_short)
            if enum_degree:
                return self._new_degree(degree_str, DEGREE_NAME[enum_degree])
            else:
                self._manage_unrecognized_text_after_find(degree_str)
        # 没标记为简称的，和标记了简称依然没识别出来的，都暂存起来
        self._manage_unrecognized_text_with_noshort(degree_str)
        return None

    def degree_recognize_with_text(self, degree_str):
        # 识别普通文本
        enum_degree = self._recognize_text(degree_str)

        if enum_degree:
            return self._new_degree(degree_str, DEGREE_NAME[enum_degree])
        # 没标记为简称的，和标记了简称依然没识别出来的，都暂存起来
        self._manage_unrecognized_text_after_find(degree_str)
        return None

    def degree_recognize_with_second(self, degree_str):
        # 识别前一次没识别出来的, 最后没识别出来的按无学位算
        enum_degree = self._recognize_other(degree_str)
        if enum_degree:
            return self._new_degree(degree_str, DEGREE_NAME[enum_degree])
        return self._new_degree(degree_str, DEGREE_NAME[Degree.INVALID])

    def parse_has_short(self, degree_str, d_short):
        # 处理简称文本，先把可能的.去掉
        ds_short = d_short.lower().replace('.', '')
        # 识别简称
        enum_degree = self._recognize_short(ds_short)
        if enum_degree:
            return enum_degree
        # 识别全文
        enum_degree = self._recognize_text(degree_str)
        if enum_degree:
            # 简称可以用了
            self.map_update(ds_short, enum_degree)
        return enum_degree

    def map_update(self, _short, _degree):
        """
        对照表更新
        :param _short: 学士简称
        :param _degree: Degree Obj
        :return:
        """
        if self._map.get(_short) is not None:
            return
        self._map[_short] = _degree
        self._map_pattern += '|{}'.format(_short)


def degree_regexp(csv_path):
    """
    学历数据正则化为：POSTDOC，PHD，MD，JD，MBA，MASTER，BACHELOR，没有找到学位
    :param csv_path:
    :return:
    """
    # 获取学历信息
    obj = DRegexp(csv_path)
    degree_list = obj.regexp_run()
    # 数据导出
    DRegexp.export_csv_file(new_csv_data=degree_list)


if __name__ == '__main__':
    file_path = sys.argv[1]
    try:
        degree_regexp(file_path)
    except Exception as e:
        print('Error', e)
        print(traceback.format_exc())
    else:
        print('Success')
    finally:
        print('Over')

