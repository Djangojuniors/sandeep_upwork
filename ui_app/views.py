from django.shortcuts import render, HttpResponse, redirect, get_object_or_404
from django.core.files.storage import FileSystemStorage
from django.utils.text import get_valid_filename
import os
from django.conf import settings
from django.contrib import messages
from .testing import extract

uploaded_file_url = None

# Create your views here.
def upload(request):
    global uploaded_file_url
    if request.method == 'POST':
        myFile = request.FILES.get('myFile')
        if os.path.splitext(myFile.name)[-1] == ".pdf":
            # fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'documents/user_' + user),
            #                        base_url='documents/')
            fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'documents/'), base_url='documents/')
            myFile.name = get_valid_filename(myFile.name)
            filename = fs.save(myFile.name, myFile)
            uploaded_file_url = fs.url(filename)
            # print("---------------------------------------------------")
            # print(uploaded_file_url)
            # print("---------------------------------------------------")
            messages.success(request, 'File Uploaded')
            context = {
                'file': uploaded_file_url
            }
            return redirect('/display_data/')
        else:
            messages.error(request, 'Please select valid file with extension .pdf')
            return redirect('/upload/')

    return render(request, 'upload.html')

def display_data(request):
    global uploaded_file_url
    if uploaded_file_url:
        # print(os.path.join(settings.MEDIA_ROOT, str(uploaded_file_url)))
        file_name = os.path.join(settings.MEDIA_ROOT, str(uploaded_file_url))
        client_df, invoice_df = extract(uploaded_file_url)
        # print(client_df.head())
        client_df = client_df.to_html(classes="table table-striped table-hover")
        # invoice_df = invoice_df[0]
        # invoice_df.fillna(" ", inplace=True)
        # print(invoice_df.head())
        # invoice_df = invoice_df.to_html(classes="table table-striped table-hover")
        temp_data = []
        for i in invoice_df:
            i.fillna(" ", inplace=True)
            i = i.transpose()
            i = i.to_html(classes="table table-striped table-hover")
            temp_data.append(i)

        data = {'client_details': client_df, 'invoice_data': temp_data}
        # print(data)
        return render(request, 'display_data.html', data)
