from django.shortcuts import render_to_response, redirect
from django.views.generic.detail import DetailView
from django.views.generic import TemplateView
from django.template.context import RequestContext
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import F, Count
from django.db.models.query_utils import Q

from datetime import datetime, timedelta
import re
import smtplib

from radiothon.forms import (PledgeForm, DonorForm, AddressForm,
                             CreditCardForm, HokiePassportForm)
from radiothon.models import (Pledge, Premium, BusinessManager,
                              CreditCard, HokiePassport, Donor,
                              Address, PremiumChoice, PremiumAttributeOption,
                              PremiumAttributeRelationship)
from radiothon.forms import premium_choice_form_factory
from radiothon.settings_local import EMAIL_HOST_USER, EMAIL_HOST_PASSWORD, EMAIL_HOST, EMAIL_PORT


class MainView(TemplateView):
    template_name = "index.html"


class PledgeDetail(DetailView):
    queryset = Pledge.objects.all()
    template_name = 'pledge_detail.html'

@login_required(login_url='/radiothon/accounts/login')
def rthon_pledge(request):
    pledge_form = PledgeForm(request.POST or None, prefix="pledge_form")
    donor_form = DonorForm(request.POST or None, prefix="donor_form")
    address_form = AddressForm(request.POST or None, prefix="address_form")
    credit_form = CreditCardForm(request.POST or None, prefix="creditcard_form")
    hokiepassport_form = HokiePassportForm(request.POST or None, prefix="hokiepassport_form")

    errors = []
    premium_choice_forms = []

    if (request.POST):
        pledge = None
        if (pledge_form.is_valid()):
            pledge = pledge_form.save(commit=False)

            premiums_allowed = Premium.objects.filter(donation__lte=pledge_form.cleaned_data['amount'])
            premium_choice_forms = create_premium_formsets(request, premiums_allowed)

            if pledge_form.cleaned_data['payment'] == 'R':
                # You can have a Credit card OR a Hokiepassport or Neither but NOT both
                if credit_form.is_valid():
                    credit = CreditCard.objects.filter(number=credit_form.cleaned_data['number'])
                    credit = credit.filter(expiration=credit_form.cleaned_data['expiration'])
                    credit = credit.filter(type=credit_form.cleaned_data['type'])

                    if credit:
                        credit = credit[0]
                    else:
                        credit = credit_form.save()

                    pledge.credit = credit
                else:
                    errors.append(credit_form.errors)
            elif pledge_form.cleaned_data['payment'] == 'P':
                if hokiepassport_form.is_valid():
                    hokiepassport = HokiePassport.objects.filter(number=hokiepassport_form.cleaned_data['number'])
                    if hokiepassport:
                        hokiepassport = hokiepassport[0]
                    else:
                        hokiepassport = hokiepassport_form.save()
                    pledge.hokiepassport = hokiepassport
                else:
                    errors.append(hokiepassport_form.errors)

            if (pledge.payment == 'R' or pledge.premium_delivery == 'M'):
                if (address_form.is_valid()):
                    address = Address.objects.filter(address_line_1=address_form.cleaned_data['address_line_1'])
                    address = address.filter(address_line_2=address_form.cleaned_data['address_line_2'])
                    address = address.filter(city=address_form.cleaned_data['city'])
                    address = address.filter(state=address_form.cleaned_data['state'])
                    address = address.filter(zip=address_form.cleaned_data['zip'])
                    if address:
                        address = address[0]
                    else:
                        address = address_form.save()
                    donor_address = address
                else:
                    errors.append(address_form.errors)

            if (donor_form.is_valid()):
                donor = Donor.objects.filter(name=donor_form.cleaned_data['name'])
                donor = donor.filter(phone=donor_form.cleaned_data['phone'])
                donor = donor.filter(email=donor_form.cleaned_data['email'])
                donor = donor.filter(donation_list=donor_form.cleaned_data['donation_list'])

                if ('donor_address' in locals()):
                    donor = donor.filter(address=donor_address)

                if donor:
                    donor = donor[0]
                else:
                    donor = donor_form.save(commit=False)

                if ('donor_address' in locals()):
                    donor.address = donor_address

                if not donor.phone and not donor.email:
                    errors.append('You must ask the donor for their email or their phone number')
                else:
                    donor.save()
                    pledge.donor = donor
            else:
                errors.append(donor_form.errors)

            if len(errors) == 0:
                pledge.save()
                if pledge.premium_delivery != 'N':
                    for form in premium_choice_forms:
                        # TODO: For some reason, even if fields are left blank,
                        # the premium form's is_valid remains true.
                        # GAH killin' me Django
                        if (form.is_valid() and 'premium' in form.cleaned_data.keys()):  # form.fields['premium'].queryset[0]
                            if (form.cleaned_data['want'] is False):
                                continue

                            premium = form.cleaned_data['premium']
                            instance = PremiumChoice(premium=premium,
                                                     pledge=pledge)
                            #try:
                            instance.save()
                            #except IntegrityError:
                                #break
                            for value in form.cleaned_data.values():
                                if (type(value) is PremiumAttributeOption):
                                    instance.options.add(value)
                            
                            # Subtract one from the inventory of this object.
                            # When the count on the relationship is 0, donors will no longer
                            # be able to request an item with these attributes
                            # i.e. You run out of small red shirts. (they're dead, Jim)

                            # Retrieve the relationship object for this premiumchoice
                            #relationshipQuery = PremiumAttributeRelationship.objects.filter(premium=premium) 
                            #for option in instance.options.all():
                            #relationshipQuery.filter(options=option)
                            # If the count is greater than 0, subtract one      
                            #relationshipQuery.filter(count__gt=0).update(count=F('count')-1)

                            target_options = instance.options.all()
                            candidate_relationships = PremiumAttributeRelationship.objects.filter(premium=premium) 
                            candidate_relationships = candidate_relationships.annotate(c=Count('options')).filter(c=len(target_options))

                            for option in target_options:
                                candidate_relationships = candidate_relationships.filter(options=option)

                            final_relationships = candidate_relationships
                            final_relationships.filter(count__gt=0).update(count=F('count')-1)

                        else:
                            if (len(form.errors) > 0):
                                errors.append(form.errors)
                    if len(errors) > 0:
                        PremiumChoice.objects.filter(pledge=pledge).delete()
                        if pledge.id is not None:
                            pledge.delete()

            # If we've successfully parsed all the data
            # email it to the business manager
            if len(errors) == 0:
                email_to_business_manager(pledge)
        else:
            errors.extend(['%s: %s' % (key, value) for key, value in dict(pledge_form.errors).items()])

        if len(errors) == 0:
            return redirect('/radiothon/pledge/%s' % str(pledge.pk))
    else:
        premium_choice_forms = create_premium_formsets(request)

    return render_to_response('pledge_form.html', {
        'errors': errors,
        'pledge': pledge_form,
        'donor': donor_form,
        'address': address_form,
        'credit': credit_form,
        'hokiepassport': hokiepassport_form,
        'premium_formsets': premium_choice_forms,
        'sending_to': BusinessManager.objects.order_by('-terms__year', 'terms__semester')[0].email,
    }, context_instance=RequestContext(request))


def create_premium_formsets(request, queryset=None):
    premium_forms = []
    post_data = request.POST if request is not None else None
    if queryset is None:
        queryset = Premium.objects.all()

    # make sure there are some premium choice formsets in post
    if (post_data is not None):
        premium_choice_formset_post = [k for k in post_data.keys()
                                       if 'premium_choice_formset' in k]
        if (len(premium_choice_formset_post) == 0):
            return []

    for premium in list(queryset):
        PremiumChoiceForm = premium_choice_form_factory(premium)
        #FormsetClass = formset_factory(PremiumChoiceForm)
        #premium_forms.append(FormsetClass(post_data, prefix='%s_premium_choice_formset' % premium.simple_name ))
        premium_forms.append(PremiumChoiceForm(post_data, prefix='%s_premium_choice_formset' % premium.simple_name))
    return premium_forms


def simple_send_email(sender, recipient, subject, message, server=EMAIL_HOST, port=EMAIL_PORT):
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

    simple_send_email(sender, current_bm.email, subject, message)


def rthon_plain_logs(request, timespan):
    ip = get_client_ip(request)

    #if (ip != '192.168.0.59'): # should probably de-hardcode this
    #    return HttpResponse('Error, not authorized.', content_type="text/plain")

    response = HttpResponse(content_type="text/plain")

    pledges = Pledge.objects.all()
    datefilter = Q()
    if (timespan == 'hourly'):
        time_threshold = datetime.now() - timedelta(hours=1)
        datefilter = Q(created__gt=time_threshold)
    elif (timespan == 'daily'):
        time_threshold = datetime.now() - timedelta(days=1)
        datefilter = Q(created__gt=time_threshold)
    else:
        matches = re.search('^(\d{4})\-(\d{2})\-(\d{2})\s?(?:(\d{2}):(\d{2}))?$', timespan).groups()
        matches = [int(match) for match in matches if match is not None]
        if len(matches) == 3 or len(matches) == 5:
            response.write(matches)
            try:
                matchdate = datetime(*matches)
            except ValueError:
                #response.write('Error in request')
                return response
            response.write(matchdate)
            delta = timedelta(days=1) if len(matches) is 3 else timedelta(hours=1)
            #response.write(matchdate + delta)
            #response.write('\n')
            datefilter = Q(created__gte=matchdate, created__lte=matchdate + delta)
        else:
            #response.write('Error in request.')
            return response

    pledges = pledges.filter(datefilter)

    for pledge in pledges:
        response.write(pledge.as_email())

    return response


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_object_or_none(model, **kwargs):
    try:
        return model.objects.get(**kwargs)
    except model.DoesNotExist:
        return None
