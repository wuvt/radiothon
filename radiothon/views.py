from django.shortcuts import render_to_response
from radiothon.forms import *
from django.utils.functional import curry
from django.forms.formsets import formset_factory

from django.views.generic import TemplateView
from django.views.generic.edit import FormMixin
from django.template.context import RequestContext
from django.forms.models import inlineformset_factory
import datetime

class RadiothonView(FormMixin, TemplateView):
    template_name = "main.html"
    form_class = PledgeForm

    def get_context_data(self, **kwargs):
        context = super(RadiothonView, self).get_context_data(**kwargs)
        context['form'] = PledgeForm()
        return context

    def form_valid(self, form):
        return render_to_response({'form':form, 'valid': True})

    def form_invalid(self, form):
        return render_to_response({'form':form, 'valid': False})
    
def rthon_pledge(request):
    pledge_form = PledgeForm(request.POST or None, prefix = "pledge_form")
    donor_form = DonorForm(request.POST or None, prefix = "donor_form")
    address_form = AddressForm(request.POST or None, prefix = "address_form")
    credit_form = CreditCardForm(request.POST or None, prefix = "creditcard_form")
    hokiepassport_form = HokiePassportForm(request.POST or None, prefix = "hokiepassport_form")
    
    premium_formsets = create_premium_formsets(request)
    
    #===========================================================================
    # TODO: AJAX validation of attribute relationships!
    #===========================================================================
    
    return render_to_response('main.html', {
        'pledge': pledge_form,
        'donor': donor_form,
        'address': address_form,
        'credit': credit_form,
        'hokiepassport': hokiepassport_form,
        'premium_formsets': premium_formsets,
        }, context_instance=RequestContext(request))

def create_premium_formsets(request):
    premium_forms = []
    for premium in list(Premium.objects.all()):
        PremiumChoiceForm = premium_choice_form_factory(premium)
        FormsetClass = formset_factory(PremiumChoiceForm)
        premium_forms.append(FormsetClass(request.POST or None, prefix = '%s_premium_choice_formset' % premium.simple_name ))
    return premium_forms

def rthon_review(request):
    pledge_form = PledgeForm(request.POST or None, prefix = "pledge_form")
    donor_form = DonorForm(request.POST or None, prefix = "donor_form")
    address_form = AddressForm(request.POST or None, prefix = "address_form")
    credit_form = CreditCardForm(request.POST or None, prefix = "creditcard_form")
    hokiepassport_form = HokiePassportForm(request.POST or None, prefix = "hokiepassport_form")
    premium_choice_formsets = create_premium_formsets(request)
    
    pledge = None
    
    # attempt to get from existing records.
    if (request.POST):
        pledge = pledge_form.save(commit = False)
    
        # You can have a Credit card OR a Hokiepassport or Neither but NOT both
        if (credit_form.is_valid()):
            credit = CreditCard.objects.filter(number = credit_form.cleaned_data['number'])
            credit = credit.filter(expiration = credit_form.cleaned_data['expiration'])
            credit = credit.filter(type = credit_form.cleaned_data['type'])
            
            if credit:
                credit = credit[0]
            else:
                credit = credit_form.save()
                
            pledge.credit = credit
            pledge.payment = "R"
            
        if (hokiepassport_form.is_valid()):
            hokiepassport = HokiePassport.objects.filter(number = hokiepassport_form.cleaned_data['number'])
            if hokiepassport:
                hokiepassport = hokiepassport[0]
            else:
                hokiepassport = hokiepassport_form.save()
                
            pledge.hokiepassport = hokiepassport
            pledge.payment = "P"
            
        if (not credit_form.is_valid() and not hokiepassport_form.is_valid()):
            pledge.payment = "A"
        
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
                    
        if (donor_form.is_valid()):
            donor = Donor.objects.filter(name = donor_form.cleaned_data['name'])
            donor = donor.filter(phone = donor_form.cleaned_data['phone'])
            donor = donor.filter(email = donor_form.cleaned_data['email'])
            donor = donor.filter(donation_list = donor_form.cleaned_data['donation_list'])
            
            if (address_form.is_valid()):
                donor = donor.filter(address = donor_address)
                
            if donor:
                donor = donor[0]
            else:
                donor = donor_form.save(commit = False)
                
            if (address_form.is_valid()):
                donor.address = donor_address
                
            donor.save()
            pledge.donor = donor
        
        pledge.save()
        
        for formset in premium_choice_formsets:
            for form in formset:
                if (form.is_valid()):
                    premium = form.cleaned_data['premium']
                    instance = PremiumChoice(premium = premium,
                                             pledge = pledge)
                    instance.save()
                    for key, value in form.cleaned_data.iteritems():
                        if (key != 'premium'):
                            instance.options.add(value)
                
    return render_to_response('reviewpledge.html', {
            'pledge': pledge,
            }, context_instance=RequestContext(request))

def get_object_or_none(model, **kwargs):
    try:
        return model.objects.get(**kwargs)
    except model.DoesNotExist:
        return None