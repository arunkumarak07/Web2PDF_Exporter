from django.shortcuts import render, redirect
from django.core.mail import EmailMessage
from django.conf import settings
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from xhtml2pdf import pisa
import requests
import os



def home_page(request):
    if request.method == 'POST':
        url = request.POST['url']
        receiver_email = request.POST['email']
        content = scrape_web_content(url)
        file_name = extract_domain_without_tld(url)
        file_path = convert_html_to_pdf(content, file_name)
        send_email_with_pdf(receiver_email, file_name, file_path)
        return redirect('success')
    return render(request, 'homepage.html')

def confirm(request):
    return render(request, 'confirm.html')


def scrape_web_content(url):
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        body_content = soup.find('body')

        # Clean the extracted text by stripping leading/trailing spaces and collapsing multiple spaces
        clean_content = body_content.get_text(separator='\n').strip()
        clean_content = '\n'.join([line for line in clean_content.splitlines() if line.strip()])

        # Wrap the cleaned content in basic HTML structure for better formatting
        clean_content.replace('\n','<div>')
        html_content = f"<html><body><div>{clean_content}</div></body></html>"
        
        print('Scraping and cleaning are done.')
        return html_content
    else:
        return "Unable to retrieve content"




def convert_html_to_pdf(html_content, file_name):
    # Ensure MEDIA_ROOT exists
    if not os.path.exists(settings.MEDIA_ROOT):
        os.makedirs(settings.MEDIA_ROOT)

    file_path = os.path.join(settings.MEDIA_ROOT, f"{file_name}.pdf")
    
    with open(file_path, "w+b") as pdf_file:
        pisa_status = pisa.CreatePDF(html_content, dest=pdf_file)
        if pisa_status.err:
            print('Error in PDF conversion.')
            return None
        print('File conversion is done.')
    return file_path


def send_email_with_pdf(receiver_email, domain, file_path):
    subject = f'Content extract from {domain}'
    body = f'This email contains a PDF attachment. \n Thank you.'
    email_sender = settings.EMAIL_HOST_USER
    email_receiver = [receiver_email]
    
    email = EmailMessage(subject, body, email_sender, email_receiver)

    # Attach the PDF
    try:
        with open(file_path, 'rb') as pdf_file:
            email.attach(f'{os.path.basename(file_path)}', pdf_file.read(), 'application/pdf')

        email.send()
        print('Email with PDF sent successfully!')
    except Exception as e:
        print(f'Failed to send email: {e}')


def extract_domain_without_tld(url):
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.replace('www.', '')
    # Split domain by '.' and take the second-to-last part (the SLD)
    domain_parts = domain.split('.')
    if len(domain_parts) > 1:
        return domain_parts[-2]
    return domain
