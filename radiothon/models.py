from django.db import models
from django.core import validators
from django.contrib.localflavor.us.models import *
from django.db.models import signals
import locale
import itertools
import re

class RadiothonSemester(models.Model):
    semester = models.CharField(max_length = 1, choices = (('F', 'Fall'),
                                                           ('S', "Spring")))
    year = models.IntegerField()
    
    def __unicode__(self):
        return self.semester + str(self.year)

class BusinessManager(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField()
    terms = models.ManyToManyField(RadiothonSemester)
    
    def __unicode__(self):
        return '%s: %s' % (self.name, self.email)

class Address(models.Model):
    _zip_validator = validators.RegexValidator('^[0-9]{5}$')
    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(max_length=255, blank = True)
    city = models.CharField(max_length=255)
    state = USStateField()
    zip = models.CharField(max_length=5, validators = [_zip_validator,])
    
    def as_email(self):
        return 'Address Line 1: %s\r\nAddress Line 2: %s\r\nCity: %s\r\nState: %s\r\nZip: %s\r\n' % \
                (self.address_line_1, self.address_line_2, self.city, self.state, self.zip)

class Donor(models.Model):
    #===========================================================================
    # TODO: Move the ForiegnKey to the Address model so a donor may have more than one address
    #===========================================================================
    name = models.CharField(max_length=255)
    address = models.ForeignKey(Address, null = True, blank = True)
    phone = PhoneNumberField(null = True, blank = True)
    email = models.EmailField()
    donation_list = models.BooleanField()
    
    def __unicode__(self):
        return '%s, %s' % (self.name, self.email)
    
    def as_email(self):
        return 'Name: %s\r\n%sPhone: %s\r\nEmail: %s\r\nAdded to donation list: %s\r\n' % \
                (self.name,
                 self.address.as_email() if self.address is not None else '',
                 self.phone,
                 self.email,
                 'Yes' if self.donation_list else 'No')

class HokiePassport(models.Model):
    _number_validator = validators.RegexValidator('^[0-9]*$', "Enter a valid number sequence.")
    number = models.CharField(max_length = 20, validators = [_number_validator,])
    
    def __unicode__(self):
        return self.number

class CreditCard(models.Model):
    _number_validator = validators.RegexValidator('^([0-9]{4}(\-| )?){4}$', "Enter a valid number sequence.")
    _expiry_validator = validators.RegexValidator('^[0-9]?[0-9]/[0-9]{2}([0-9]{2})?$', "Enter a valid month/year date string. i.e. 01/15")
    number = models.CharField(max_length = 30, validators = [_number_validator,])
    type = models.CharField(max_length = 1, choices = (('M', "Mastercard"),
                                                       ('V', "Visa"),
                                                       ('A', "American Express"),
                                                       ('D', "Discover")))
    expiration = models.CharField(max_length = 8, validators = [_expiry_validator,])
    code = models.IntegerField()
    
    def __unicode__(self):
        return '%s %s, %s' % (self.get_type_display(),
                              self.number,
                              [ pledge.donor.name for pledge in self.pledge_set.all() ])
    
    def as_email(self):
        return 'Card Number: ****%s\r\nType: %s\r\nExpires: %s\r\nCode: %s\r\n' % \
                (self.number[-4:], self.get_type_display(), self.expiration, self.code)
    
"""These are options, like Size or Color"""
class PremiumAttribute(models.Model):
    name = models.CharField(max_length = 255)
    cardinality = models.IntegerField()
    #=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=
    #TODO: When adding new option to an attribute, update the relationships
    #=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=
    def __unicode__(self):
        return '%s [%s]' % (self.name,
                            ''.join(['%s, ' % (attribute,)
                                     for attribute in self.premiumattributeoption_set.all()])[:-2])

"""Therese are the values for options, like Large, or Brown"""
class PremiumAttributeOption(models.Model):
    name = models.CharField(max_length = 255)
    attribute = models.ForeignKey(PremiumAttribute)
    
    def __unicode__(self):
        return self.name
        
"""This is information about premiums, like what attributes they have,
how much the donor must pledge, etc"""
class Premium(models.Model):
    donation = models.DecimalField(max_digits = 6, decimal_places = 2)
    name = models.CharField(max_length = 255)
    attributes = models.ManyToManyField(PremiumAttribute, null = True, blank = True)
    semesters_offered = models.ManyToManyField(RadiothonSemester)
    
    @property
    def simple_name(self):
        """Removes spaces from the name of """
        return re.compile('[\W_]+|[^A-z]+').sub('', str(self.name))
    
    # Turns a list of list of options into permutations of those lists
    def _option_combinations(self):
        option_combinations = [ attr.premiumattributeoption_set.all() for attr in self.attributes.all() ]
        return itertools.product(*option_combinations)
    
    def create_attr_rel(self):
        op_combos = self._option_combinations()
        combo_count = sum(1 for _ in op_combos)
        if combo_count != self.premiumattributerelationship_set.all().count():
            PremiumAttributeRelationship.objects.filter(premium = self).delete()
            for option_list in self._option_combinations():
                attr_rel = PremiumAttributeRelationship(premium = self)
                attr_rel.save()
                attr_rel.options.add(*option_list)
    
    def __unicode__(self):
        return '$%s %s [%s]' % (self.donation,
                              self.name,  
                              ''.join(['%s, ' % (attribute.name,)
                                       for attribute in self.attributes.all()])[:-2])

"""This class allows attributes to be related,
for example, if we have shirts in colors RGB and sizes SML,
we might not have the color Red in size Small, so we'd set
count to 0"""
class PremiumAttributeRelationship(models.Model):        
    count = models.IntegerField(default = -1) # -1: don't track, >=0: track
    options = models.ManyToManyField(PremiumAttributeOption)
    premium = models.ForeignKey(Premium)
 
    @property
    def attributes(self):
        """Gets the attributes matching the relationship's options"""
        return [option.attribute for option in self.options]
 
    def __unicode__(self):
        options_list_string = ''.join(['%s: %s, ' % (option.attribute.name, option.name)
                                       for option in self.options.all().order_by('attribute__cardinality')])
        return '%s [%s]' % (self.premium.name, options_list_string[:-2])

def update_premium_attr_rel_m2m(sender, instance, action, reverse, model, pk_set, **kwargs):
    # instance is a premiumattributerelationship
    if action == 'pre_add':
        pass
    elif action == 'post_add':
        instance.create_attr_rel()

def update_premium_attr_rel(sender, instance, created, raw, using, **kwargs):
    # instance is a premiumattributeoption
    attr_option = instance
    for premium in attr_option.attribute.premium_set.all():
        premium.create_attr_rel()

def update_premium_attr_rel_delete(sender, instance, using, **kwargs):
    # instance is a premiumattributeoption
    PremiumAttributeRelationship.objects.filter(options = instance).delete()

def update_premium(sender, instance, created, raw, using, **kwargs):
    instance.create_attr_rel()

# these update the attribute relationships when adding attributes to premiums
signals.m2m_changed.connect(receiver = update_premium_attr_rel_m2m, sender = Premium.attributes.through)
signals.post_save.connect(receiver = update_premium_attr_rel, sender = PremiumAttributeOption)

# not sure if these two are working
signals.post_save.connect(receiver = update_premium, sender = Premium)
signals.pre_delete.connect(receiver = update_premium_attr_rel_delete, sender = PremiumAttributeOption)
    
class Pledge(models.Model):
    created = models.DateTimeField(auto_now = True)
    amount = models.DecimalField(max_digits = 6, decimal_places = 2)
    donor = models.ForeignKey(Donor)
    show = models.CharField(max_length=255, blank = True) # Match this with Quicktrack?
    taker = models.CharField(max_length=255, blank = True)
    payment = models.CharField(max_length = 1, choices = (('R','Credit'),
                                                          ('H', 'Check'),
                                                          ('A', 'Cash'),
                                                          ('P', 'Hokie Passport')))
    credit = models.ForeignKey(CreditCard, null = True, blank = True)
    hokiepassport = models.ForeignKey(HokiePassport, null = True, blank = True)
    premium_delivery = models.CharField(max_length = 1,choices = (('M','Mail'),
                                                          ('P','Pick-Up'),
                                                          ('N','No Premium')))
    extra_info = models.CharField(max_length=512, blank = True)
        
    def __unicode__(self):
        return '%s: %s' % (self.created, self.donor.name)
    
    def as_email(self):
        #locale.setlocale(locale.LC_ALL, 'en_US')#not that important...
        email = '==============================================================\r\n'
        email += 'Pledge date: %s\r\nDonation: %s\r\n' % \
                    (self.created, self.amount)# locale.currency(self.amount))
        email += 'Premiums and Choices:\r\n'
        for choice in self.premiumchoice_set.all():
            email += choice.as_email()
        email += '\r\n'
        email += 'Donor Information:\n%s' % self.donor.as_email()
        email += 'Show: %s\r\nPledge Taker: %s\r\nPayment Method: %s\r\n' % \
                    (self.show, self.taker, self.get_payment_display())
        if self.credit:
            email += 'Credit Card Information:\r\n%s' % self.credit.as_email()
        if self.hokiepassport:
            email += 'Hokie Passport Information:\n%s' % self.hokiepassport.as_email()
        email += 'Extra Info: %s\r\n' % self.extra_info
        email += '==============================================================\r\n'
        return email
    
"""This associates donors with premiums, as well as any options that the
donor may choose, such as color, size, etc""" 
class PremiumChoice(models.Model):
    pledge = models.ForeignKey(Pledge)
    premium = models.ForeignKey(Premium)
    options = models.ManyToManyField(PremiumAttributeOption, null = True, blank = True)

    def __unicode__(self):
        return '%s: %s {%s}' % (self.pledge,
                                self.premium.name,
                                ''.join(['%s: %s, ' % (option.attribute.name, option)
                                         for option in self.options.all()])[:-2])
    def as_email(self):
        return '%s. %s\r\n' % (self.premium.name, 
                           ''.join(['%s: %s, ' % (option.attribute.name, option)
                                    for option in self.options.all()])[:-2])
