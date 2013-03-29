from radiothon.forms import (PledgeForm, DonorForm, AddressForm,
                              CreditCardForm, HokiePassportForm)
from radiothon.models import (Pledge, Premium, BusinessManager,
                               CreditCard, HokiePassport, Donor,
                                Address, PremiumChoice, PremiumAttributeOption)
from radiothon.forms import premium_choice_form_factory
from radiothon.settings_local import EMAIL_HOST_USER, EMAIL_HOST_PASSWORD, EMAIL_HOST, EMAIL_PORT
from django.forms.formsets import formset_factory
from django.shortcuts import render_to_response, redirect
from django.views.generic.detail import DetailView
from django.views.generic import TemplateView
from django.template.context import RequestContext
import smtplib, itertools
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.core.context_processors import request


class MainView(TemplateView):
    template_name = "index.html"

@login_required(login_url = '/radiothon/accounts/login')
def rthon_pledge(request):
    pledge_form = PledgeForm(request.POST or None, prefix = "pledge_form")
    donor_form = DonorForm(request.POST or None, prefix = "donor_form")
    address_form = AddressForm(request.POST or None, prefix = "address_form")
    credit_form = CreditCardForm(request.POST or None, prefix = "creditcard_form")
    hokiepassport_form = HokiePassportForm(request.POST or None, prefix = "hokiepassport_form")
    
    errors = []
    premium_choice_forms = []
    
    if (request.POST):
        pledge = None
        if (pledge_form.is_valid()):
            pledge = pledge_form.save(commit = False)
            
            premiums_allowed = Premium.objects.filter(donation__lte = pledge_form.cleaned_data['amount'])
            premium_choice_forms = create_premium_formsets(request, premiums_allowed)
            
            if pledge_form.cleaned_data['payment'] == 'R':
                # You can have a Credit card OR a Hokiepassport or Neither but NOT both
                if credit_form.is_valid():
                    credit = CreditCard.objects.filter(number = credit_form.cleaned_data['number'])
                    credit = credit.filter(expiration = credit_form.cleaned_data['expiration'])
                    credit = credit.filter(type = credit_form.cleaned_data['type'])
                    
                    if credit:
                        credit = credit[0]
                    else:
                        credit = credit_form.save()
                        
                    pledge.credit = credit
                else:
                    errors.append(credit_form.errors)
            elif pledge_form.cleaned_data['payment'] == 'P':
                if hokiepassport_form.is_valid():
                    hokiepassport = HokiePassport.objects.filter(number = hokiepassport_form.cleaned_data['number'])
                    if hokiepassport:
                        hokiepassport = hokiepassport[0]
                    else:
                        hokiepassport = hokiepassport_form.save()
                    pledge.hokiepassport = hokiepassport
                else:
                    errors.append(hokiepassport_form.errors)
            
            if (pledge.payment == 'R' or pledge.premium_delivery == 'M'):
                if (address_form.is_valid()):
                    address = Address.objects.filter(address_line_1 = address_form.cleaned_data['address_line_1'])
                    address = address.filter(address_line_2 = address_form.cleaned_data['address_line_2'])
                    address = address.filter(city = address_form.cleaned_data['city'])
                    address = address.filter(state = address_form.cleaned_data['state'])
                    address = address.filter(zip = address_form.cleaned_data['zip'])
                    if address:
                        address = address[0]
                    else:
                        address = address_form.save()
                    donor_address = address
                else:
                    errors.append(address_form.errors)
                    
            if (donor_form.is_valid()):
                donor = Donor.objects.filter(name = donor_form.cleaned_data['name'])
                donor = donor.filter(phone = donor_form.cleaned_data['phone'])
                donor = donor.filter(email = donor_form.cleaned_data['email'])
                donor = donor.filter(donation_list = donor_form.cleaned_data['donation_list'])
                
                if ('donor_address' in locals()):
                    donor = donor.filter(address = donor_address)
                    
                if donor:
                    donor = donor[0]
                else:
                    donor = donor_form.save(commit = False)
                    
                if ('donor_address' in locals()):
                    donor.address = donor_address
                    
                donor.save()
                pledge.donor = donor
            else:
                errors.append(donor_form.errors)
            
            if len(errors) == 0:
                pledge.save()
                for form in premium_choice_forms:
                    # For some reason, even if fields are left blank,
                    # the premium form's is_valid remains true.
                    # GAH killin' me Django
                    if (form.is_valid() and 'premium' in form.cleaned_data.keys()): #form.fields['premium'].queryset[0]
                        if (form.cleaned_data['want'] is False):
                            continue
                        
                        premium = form.cleaned_data['premium']
                        instance = PremiumChoice(premium = premium,
                                                 pledge = pledge)
                        #try:
                        instance.save()
                        #except IntegrityError:
                            #break
                        for value in form.cleaned_data.values():
                            if (type(value) is PremiumAttributeOption):
                                instance.options.add(value)
                    else:
                        if (len(form.errors) > 0):
                            errors.append(form.errors)
                if len(errors) > 0:
                    PremiumChoice.objects.filter(pledge = pledge).delete()
                    if pledge.id != None:
                        pledge.delete()
                        
            # If we've successfully parsed all the data
            # email it to the business manager
            if len(errors) == 0:
                email_to_business_manager(pledge)                    
        else:
            errors.extend([ '%s: %s' % (key, value) for key, value in dict(pledge_form.errors).items() ])
        
        if len(errors) == 0:
            return redirect('/radiothon/pledge/%s' % str(pledge.pk))
    else:
        premium_choice_forms = create_premium_formsets(request)
    
    return render_to_response('pledge_form.html', {
        'pledge': pledge_form,
        'donor': donor_form,
        'address': address_form,
        'credit': credit_form,
        'hokiepassport': hokiepassport_form,
        'premium_formsets': premium_choice_forms,
        'sending_to': BusinessManager.objects.order_by('-terms__year', 'terms__semester')[0].email,
        }, context_instance=RequestContext(request))

def create_premium_formsets(request, queryset = None):
    premium_forms = []
    post_data = request.POST if request is not None else None
    if queryset is None:
        queryset = Premium.objects.all();
        
    # make sure there are some premium choice formsets in post
    if (post_data is not None):
        premium_choice_formset_post = [ k for k in post_data.keys() 
                                       if 'premium_choice_formset' in k]
        if (len(premium_choice_formset_post) == 0):
            return []
    
    for premium in list(queryset):
        PremiumChoiceForm = premium_choice_form_factory(premium)
        #FormsetClass = formset_factory(PremiumChoiceForm)
        #premium_forms.append(FormsetClass(post_data, prefix = '%s_premium_choice_formset' % premium.simple_name ))
        premium_forms.append(PremiumChoiceForm(post_data, prefix = '%s_premium_choice_formset' % premium.simple_name))
    return premium_forms

def simple_send_email(sender, recipient, subject, message, server = EMAIL_HOST, port = EMAIL_PORT):
    """Sends an e-mail to the specified recipient."""
    headers = ["From: " + sender,
               "Subject: " + subject,
               "To: " + recipient,
               "MIME-Version: 1.0",
               "Content-Type: text/plain"]
    headers = "\r\n".join(headers)

    session = smtplib.SMTP(server, port)
    
    session.ehlo()
    session.starttls()
    session.ehlo()
    session.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
     
    session.sendmail(sender, recipient, headers + "\r\n\r\n" + message)
    session.close()

def email_to_business_manager(pledge):
    subject = 'Radiothon Pledge System: %s' % pledge.donor.name
    message = pledge.as_email()
    sender = 'WUVT.IT@gmail.com'
    current_bm = BusinessManager.objects.order_by('-terms__year', 'terms__semester')[0]

    simple_send_email(sender,current_bm.email, subject, message)

class PledgeDetail(DetailView):
    queryset = Pledge.objects.all()
    template_name = 'pledge_detail.html'    
    
def get_object_or_none(model, **kwargs):
    try:
        return model.objects.get(**kwargs)
    except model.DoesNotExist:
        return None