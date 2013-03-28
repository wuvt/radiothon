from django import forms
from models import (Address, Donor, HokiePassport,
                    CreditCard, Pledge, Premium,
                    PremiumAttributeOption)

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

class PremiumChoiceFormBase(forms.BaseForm):
    def clean(self):
        cleaned_data = super(PremiumChoiceFormBase, self).clean()
        error = 'Please select an option for attribute %s, ' + \
                'or check that the donor doesn\'t want a %s'
        want = cleaned_data['want']
        premium = cleaned_data['premium']
        attrs = [ field for key, field in cleaned_data.iteritems() 
                 if key is not 'premium' and key is not 'want' ]
        if not want: # do want
            for attr in attrs:
                if not attr:
                    raise forms.ValidationError(error % (attr, premium))
        return cleaned_data

def premium_choice_form_factory(premium, form = PremiumChoiceFormBase):
    """Creates a 'PremiumChoice' type form from a Premium"""
    attrs = {}
    attrs['premium'] = forms.ModelChoiceField(Premium.objects.filter(pk = premium.pk), initial = 1)
    attrs['want'] = forms.BooleanField(label = "Donor wants this premium.", initial = True, required = False)
    for attribute in premium.attributes.all().order_by('cardinality'):
        attr_opts = PremiumAttributeOption.objects.filter(attribute__premium = premium, attribute = attribute)
        # If an option is set to 0 for all relationships in a Premium,
        # don't show that option in the attribute dropdown.
        for option in attr_opts:
            rels = option.premiumattributerelationship_set.filter(premium = premium)
            empty_rels = rels.filter(count = 0)
            if (empty_rels.count() == rels.count()):
                attr_opts = attr_opts.exclude(pk = option.pk)
        
        # Add the filtered list to the model choice field    
        attrs['%s' % attribute.name] = forms.ModelChoiceField(attr_opts, required = False) # could add validator to force required
        
    return type(premium.simple_name + 'OptionChoiceForm', (forms.Form,), attrs)
