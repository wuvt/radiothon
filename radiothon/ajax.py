from models import *
from django.utils import simplejson
from django.http import HttpResponse
from django.core import serializers
from django.db.models.query_utils import Q

import operator

def ajax_get_premiums_at_amount(request, amount):
    premiums = Premium.objects.filter(donation__lte = amount)
    json = serializers.serialize(
             'json', premiums
             )
    return HttpResponse(json, content_type="application/json")

def ajax_get_premium_availability(request, premium, options):
    premium = Premium.objects.filter(pk = premium)
    options = [ int(option) for option in options.split('/') ]
    options = PremiumAttributeOption.objects.filter(pk__in = options)
    availabilities = PremiumAttributeRelationship.objects.filter(~Q(count = 0), 
                                                                 options__in = options,
                                                                 premium = premium,
                                                                 )
    
    json_list = []
    available_attrs = []
    for attr_rel in availabilities:
        for option in attr_rel.options.all():
            if (option.attribute not in available_attrs and
                    option.attribute not in [o.attribute for o in options]):
                available_attrs.append(option.attribute)
                form_object = {}
                form_object['attribute'] = option.attribute.name
                form_object['available_options'] = []    
                json_list.append(form_object)
                
            for fo in json_list:
                if (fo['attribute'] == option.attribute.name and
                    option.pk not in fo['available_options']):
                    fo['available_options'].append(option.pk)
    
    #json = serializers.serialize('json', availabilities)
    json = simplejson.dumps(json_list)
    return HttpResponse(json, content_type="application/json")
