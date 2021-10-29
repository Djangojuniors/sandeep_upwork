import pandas as pd

from .BillExtraction import BillExtraction
import re
from prettytable import PrettyTable
from .predict_table import detect_tables
from django.core.files.storage import default_storage
from django.conf import settings
import os

from cdqa.utils.converters import pdf_converter
from cdqa.pipeline import QAPipeline


# _file_name = r'input/Allianz Powerlink.pdf'
# _file_name = r'input/Allianz Premierlink.pdf'
# _file_name = r'input/GEWLNP01.01 (1).pdf'
# _file_name = r'input/HLILTA01.pdf'
# _file_name = r'input/IKHLAS BERSAMA_Illustration_v.1.1.9 pdf.pdf' #2, 9, 10
# # _file_name = r'input/IKHLAS Dariku_Illustration_v.1.1.9 pdf.pdf' #2, 9
# _file_name = r'input/PAMB_PRUWealth_Plus.pdf' #
# _file_name = r'input/PAMB_PruWith You.pdf'
# _file_name = r'input/TITANP02.pdf'
# _file_name = r'input/Zurich Takaful Family Hero.pdf'
# _file_name = r'input/Zurich Takaful ProEssential.pdf'


def extract(_file_name):
    single_coloumn = False
    BE = BillExtraction(file_name=_file_name)
    # print(BE.extract_all_text(32))

    CLIENT_DETAIL = ['Name', 'Sex', 'Smoker',
                     'Premium Mode', 'Age', 'Occupation Class',
                     'Basic Sum Assured', 'Occupational Class', 'Gender',
                     'Date of birth']

    _pages = BE.pages()
    details_found = []
    if BE.pages() != 0:
        for _ in range(_pages):
            _text = BE.extract_all_text(_)
            _is_bill = BE.is_bill(_text)
            # print('page ' + str(_ + 1) + ' --> ' + str(_is_bill))

            if _is_bill >= 5:
                added = []
                table = PrettyTable(['1', '2'])
                temp_1 = []
                temp_2 = []
                print('Page Number ' + str(_ + 1) + ' is an invoice in ' + _file_name + ' ' + str(_pages))
                # BE.extract_all_tables(page_number=_ + 1)
                _text = BE.extract_all_text(page_number=_)
                for d in CLIENT_DETAIL:
                    if d in _text:
                        details_found.append(d)
                # print("CLIENT_DETAIL", CLIENT_DETAIL)
                for cd in CLIENT_DETAIL:
                    _find = re.findall(cd + '.*', _text)
                    # print("_find", _find)
                    if _find:
                        # details_found.append(cd)
                        ins = True
                        for _cd in CLIENT_DETAIL:
                            if _cd != cd:
                                # print("_cd and cd", _cd, cd)
                                # print('_find[0]', _find[0])
                                temp = re.findall(_cd + '.*', _find[0])

                                if temp:
                                    print("temp", temp)
                                    ins = False
                                    __find = _find[0].split(temp[0])
                                    print("__find", __find)
                                    # print('inside', __find[0].split(':'))
                                    # table.add_row(__find[0].split(':'))
                                    # table.add_row([_cd, _find[0].split(':')[-1]])
                                    try:
                                        temp_1.append(__find[0].split(':')[0])
                                        temp_1.append(_cd)
                                        # print(__find)
                                        # print(__find[0])
                                        # print(_find)
                                        temp_2.append(__find[0].split(':')[1])
                                        temp_2.append(_find[0].split(':')[-1])
                                    except:
                                        temp_1.append(__find[0])
                                        temp_1.append(_find[0])
                                        single_coloumn = True
                                        # temp_2.append(__find[0])
                                        # temp_2.append(_find[0])
                                    added.append(cd)
                                    added.append(_cd)
                                    break
                        if ins and cd not in added:
                            try:
                                # table.add_row(_find[0].split(':'))
                                temp_1.append(_find[0].split(':')[0])
                                temp_2.append(_find[0].split(':')[1])
                            except:
                                # print(_find)
                                temp_list = re.findall(r'\w+', _find[0])
                                # print(cd, temp_list)

                                for i in range(len(temp_list)):
                                    if temp_list[i] == cd:
                                        _str = ''
                                        for x in range(len(temp_list)):
                                            if temp_list[x] != cd:
                                                _str += ' ' + temp_list[x]
                                                # print(_str)
                                        # table.add_row([cd, _str])
                                        temp_1.append(cd)
                                        temp_2.append(_str)
                                        # table.add_row([cd, temp_list[i + 1]])

                                # temp_list = re.findall(cd + '.*', _find[0])
                                # print(cd, temp_list)
                                # # temp_list = list(set(temp_list))
                                # # print(cd, temp_list)
                                # for i in range(len(temp_list)):
                                #     if temp_list[i] == cd:
                                #         print(cd, temp_list[i + 1])
                                #         table.add_row([cd, temp_list[i + 1]])
                # print(temp_1)
                # print(temp_2)
                # print(table)
                # print(len(temp_1))
                # print(len(temp_2))
                if len(temp_1) != len(temp_2):
                    print("Entered Bert Model")
                    print(details_found)
                    cdqa_pipeline = QAPipeline(reader=(os.path.join(settings.MEDIA_ROOT, 'model', 'bert_qa.joblib')),
                                               max_df=1.0)
                    df_bert = pd.DataFrame({'title': _file_name, 'paragraphs': [_text]})
                    cdqa_pipeline.fit_retriever(df=df_bert)

                    df = pd.DataFrame({'Client': ['Not Found'], 'Details': ['Not Found']})
                elif single_coloumn:
                    df = pd.DataFrame({'Client': temp_1})
                else:
                    df = pd.DataFrame({'Client': temp_1, 'Details': temp_2})

                # BE.extract_all_tables(_ + 1)
                # df1 = BE.extract_all_tables(_ + 1)
                df1 = detect_tables(_file_name, _ + 1)
                # print(BE.extract_all_text(_))
                return df, df1
                break

