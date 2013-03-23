from django import forms
from django.db.models import Q
from models import *
import re
from django.db.models.aggregates import Count

class AddressForm(forms.ModelForm):
    class Meta:
        model = Address

class DonorForm(forms.ModelForm):
    class Meta:
        model = Donor
        exclude = ('address', )        

class HokiePassportForm(forms.ModelForm):
    class Meta:
        model = HokiePassport

class CreditCardForm(forms.ModelForm):
    class Meta:
        model = CreditCard

class PledgeForm(forms.ModelForm):
    class Meta:
        model = Pledge 
        exclude = ('donor', 'creditcard', 'hokiepassport')

def premium_choice_form_factory(premium, form = forms.Form):
    """Creates a 'PremiumChoice' type form from a Premium"""
    attrs = {}
    attrs['premium'] = forms.ModelChoiceField(Premium.objects.filter(pk = premium.pk), initial = 1)
    for attribute in premium.attributes.all().order_by('cardinality'):
        attr_opts = PremiumAttributeOption.objects.filter(attribute__premium = premium, attribute = attribute)
        # If an option is set to 0 for all relationships in a Premium,
        # don't show that option in the attribute dropdown.
        for option in attr_opts:
            rels = option.premiumattributerelationship_set.filter(premium = premium)
            empty_rels = rels.filter(count = 0)
            if (empty_rels.count() == rels.count()):
                attr_opts = attr_opts.exclude(pk = option.pk)
        
        valid = validators.RegexValidator('.+')
        
        # Add the filtered list to the model choice field        
        attrs['%s' % attribute.name] = forms.ModelChoiceField(attr_opts, validators = [valid,])
        
    return type(premium.simple_name + 'OptionChoiceForm', (forms.Form,), attrs)
