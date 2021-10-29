import numpy as np
import pandas as pd

from .BillExtraction import BillExtraction
import re
from .predict_table import detect_tables
from django.conf import settings
import os
from PyPDF2 import PdfFileWriter, PdfFileReader
import csv
from cdqa.utils.converters import pdf_converter
from cdqa.pipeline import QAPipeline
import sys
# from transformers.models.bert.modeling_bert import BertModel,BertForMaskedLM


def extract(_file_name):
    df, df1 = None, None
    single_coloumn = False
    BE = BillExtraction(file_name=_file_name)

    CLIENT_DETAIL = ["Client's Name", 'Sex', 'Smoker',
                     'Premium Mode', 'Age', 'Occupation Class',
                     'Basic Sum Assured', 'Occupational Class', 'Gender',
                     'Date of birth','Name']

    _pages = BE.pages()
    details_found = []
    if BE.pages() != 0:
        for _ in range(_pages):
            _text = BE.extract_all_text(_)
            _is_bill = BE.is_bill(_text)
            print('page ' + str(_ + 1) + ' --> ' + str(_is_bill))
            _is_details = BE.is_client_details(_text)
            client_pn = 0
            invoice_pn = 0

            if df is None and _is_details >= 4:
                client_pn = _
                print('Page Number ' + str(_ + 1) + ' is clients details in ' + _file_name + ' ' + str(_pages))
                with open('invoice.csv', 'w') as invoice:
                    writer = csv.writer(invoice)
                    writer.writerow([_text])
                added = []
                temp_1 = []
                temp_2 = []
                # BE.extract_all_tables(page_number=_ + 1)
                _text = BE.extract_all_text(page_number=_)
                for d in CLIENT_DETAIL:
                    if d in _text:
                        details_found.append(d)
                for cd in CLIENT_DETAIL:
                    _find = re.findall(cd + '.*', _text)
                    if _find:
                        # details_found.append(cd)
                        ins = True
                        for _cd in CLIENT_DETAIL:
                            if _cd != cd:
                                temp = re.findall(_cd + '.*', _find[0])

                                if temp:
                                    ins = False
                                    __find = _find[0].split(temp[0])
                                    # print("__find", __find)
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
                if len(temp_1) != len(temp_2):
                    df = pd.DataFrame()
                    # df['Testing '] = ['No Client details found']

                    print("Entered Bert Model")
                    cdqa_pipeline = QAPipeline(reader=(os.path.join(settings.MEDIA_ROOT, 'model', 'bert_qa.joblib')),
                                               max_df=1.0)

                    # df_bert = pd.DataFrame({'title': _file_name, 'paragraphs': [_text]})
                    input_pdf = PdfFileReader(os.path.join(settings.MEDIA_ROOT, _file_name))
                    output = PdfFileWriter()
                    output.addPage(input_pdf.getPage(_))

                    split_pdf_page_name = "page.pdf"
                    split_page_dir = os.path.join(settings.MEDIA_ROOT, 'invoice_pdf')
                    split_pdf_page_path = os.path.join(split_page_dir, split_pdf_page_name)
                    with open(split_pdf_page_path, "wb") as output_stream:
                        output.write(output_stream)
                    df_bert = pdf_converter(directory_path=split_page_dir)
                    cdqa_pipeline.fit_retriever(df=df_bert)

                    client_attributes = []
                    client_details = []
                    print(details_found)
                    if 'Name' in details_found:
                        client_attributes.append('Name')
                        prediction = cdqa_pipeline.predict('What is the name of the client or person?')
                        print('Name', prediction[0])
                        client_details.append(prediction[0])
                    if 'Age' in details_found:
                        client_attributes.append('Age')
                        prediction = cdqa_pipeline.predict('What is the Age of person/client?')
                        print('Age', prediction[0])
                        client_details.append(prediction[0])
                    if 'Gender' in details_found:
                        client_attributes.append('Gender')
                        prediction = cdqa_pipeline.predict('What is the Gender?')
                        print('Gender', prediction[0])
                        if 'Male' in prediction[0]:
                            client_details.append('Male')
                        else:
                            client_details.append('Female')
                        # client_details.append(prediction[0])
                    if 'Smoker' in details_found:
                        client_attributes.append('Smoker')
                        prediction = cdqa_pipeline.predict('Is the client Smoker?')
                        print('Smoker', prediction[0].lower())
                        if 'yes' in prediction[0].lower():
                            client_details.append('Yes')
                        elif 'smoker' in prediction[0].lower():
                            client_details.append('Smoker')
                        elif 'non Smoker' in prediction[0].lower():
                            client_details.append('Non Smoker')
                        elif 'no' in prediction[0].lower():
                            client_details.append('No')
                        # client_details.append(prediction[0])

                    client_attributes.append('Organization')
                    prediction = cdqa_pipeline.predict('what is the name of the organization?')
                    print('Organization', prediction[0])
                    client_details.append(prediction[0])

                    df = pd.DataFrame({'Client': client_attributes, 'Details': client_details})
                elif single_coloumn:
                    df = pd.DataFrame({'Client': temp_1})
                else:
                    df = pd.DataFrame({'Client': temp_1, 'Details': temp_2})

                # BE.extract_all_tables(_ + 1)
                # df1 = BE.extract_all_tables(_ + 1)

            if df1 is None and _is_bill >= 5:
                invoice_pn = _
                try:
                    invoice_output_dir = os.path.join(settings.MEDIA_ROOT, 'invoice_output')
                    csv_name = 'invoice.csv'
                    print('Page Number ' + str(_ + 1) + ' is an invoice in ' + _file_name + ' ' + str(_pages))
                    df1 = detect_tables(_file_name, _ + 1, client_pn, invoice_pn)
                    # print("DF1", df1)
                    df1.to_csv(os.path.join(invoice_output_dir, csv_name))
                    # print(BE.extract_all_text(_))
                except:
                    df1 = BE.extract_all_tables(_ + 1)

            if (df is not None) and (df1 is not None):
                plan_df1 = pd.DataFrame()
                yearly_df = pd.DataFrame()
                half_yearly_df = pd.DataFrame()
                quarterly_df = pd.DataFrame()
                monthly_df = pd.DataFrame()
                year, half_year, quarter, month, plan = 0, 0, 0, 0, 0

                # print("=================")
                # print(plan_df1)
                # print(yearly_df)
                # print(half_yearly_df)
                # print(quarterly_df)
                # print(monthly_df)
                # print("===================")
                # print(year, half_year, quarter, month, plan)

                try:
                    print("try")
                    plan_df = pd.DataFrame()
                    # print("--", df1.head())
                    for i in df1.columns:
                        plan_df1 = df1.loc[df1[i].str.match('Basic|Basic/Riders|Riders|Plan', case=False)]
                        if not plan_df1.empty:
                            plan = i
                            break

                    for i in df1.columns:
                        yearly_df = df1.loc[df1[i].str.match('Annually|Yearly|Annual', case=False)]
                        if not yearly_df.empty:
                            year = i
                            break

                    for i in df1.columns:
                        half_yearly_df = df1.loc[df1[i].str.match('Half Yearly|Half-Yearly|Semi '
                                                                  'Annually|Semi-Annually|Semi-Annual|semi annual',
                                                                  case=False)]
                        if not half_yearly_df.empty:
                            half_year = i
                            break

                    for i in df1.columns:
                        quarterly_df = df1.loc[df1[i].str.match('Quarterly', case=False)]
                        if not quarterly_df.empty:
                            quarter = i
                            break

                    for i in df1.columns:
                        monthly_df = df1.loc[df1[i].str.match('Monthly', case=False)]
                        if not monthly_df.empty:
                            month = i
                            break

                    if len(plan_df1) > 0:
                        plan_df['Plan'] = df1[plan]
                        plan_df['Plan'].replace('', np.nan, inplace=True)
                        plan_df.dropna(subset=['Plan'], inplace=True)

                    if len(yearly_df) != 0:
                        plan_df['Yearly'] = df1[year]
                        plan_df['Yearly'].replace('', np.nan, inplace=True)
                        plan_df.dropna(subset=['Yearly'], inplace=True)

                    if len(half_yearly_df) != 0:
                        plan_df['Half Yearly'] = df1[half_year]
                        plan_df['Half Yearly'].replace('', np.nan, inplace=True)
                        plan_df.dropna(subset=['Half Yearly'], inplace=True)

                    if len(quarterly_df) != 0:
                        plan_df['Quarterly'] = df1[quarter]
                        plan_df['Quarterly'].replace('', np.nan, inplace=True)
                        plan_df.dropna(subset=['Quarterly'], inplace=True)

                    if len(monthly_df) != 0:
                        plan_df['Monthly'] = df1[month]
                        plan_df['Monthly'].replace('', np.nan, inplace=True)
                        plan_df.dropna(subset=['Monthly'], inplace=True)


                        # total_df = df1.loc[df1[0].str.contains('Total', case=False)]
                        # if not total_df.empty:
                        #     print(total_df[year])
                        #     print(total_df[half_year])
                        #     print(total_df[quarter])
                        #     print(total_df[month])

                        # plan_df[0] = total_df[0]
                        # plan_df = pd.DataFrame()
                        #
                        # plan_df['Yearly'] = df1[year]
                        #
                        # plan_df['Quarterly'] = df1[quarter]

                        # print("===========================================================")

                        # plan_df = plan_df.dropna(inplace=True)d
                        # f['Tenant'].replace('', np.nan, inplace=True)
                        # df.dropna(subset=['Tenant'], inplace=True)
                        # for i in range(plan_df.shape[1]):

                        # plan_df['Yearly'].replace('', np.nan, inplace=True)


                        # plan_df.dropna(subset=['Yearly'], inplace=True)


                        plan_df.to_csv("plandf.csv")
                        print("---------------------------")
                        # print(df1[plan])
                        # print(df1[year])
                        # print(df1[month])
                        # print(df1[quarter])
                        # print(df1[half_year])
                        df_list = []
                        for i in range(len(plan_df)):
                            print(plan_df.iloc[i, ])
                            temp = plan_df.iloc[i, ].to_frame()
                            df_list.append(temp)
                        print("---------------------------")
                        print(df_list)
                        return df, df_list
                except:
                    print("EXCEPT")
                    return df, [df1]

                # for i in range(df1.shape[1]):
                #     df1[i].replace('', np.nan, inplace=True)
                # for i in range(df1.shape[1]):
                #     df1.dropna(subset=[i], inplace=True)

                return df, [df1]

        # df = pd.DataFrame()
        print("nothing found")
        df1 = pd.DataFrame()
        df = pd.DataFrame()
        df1['Invoice'] = ['No Invoice Details Found']
        df['Client'] = ['No Client Details Found']
        return df, [df1]
