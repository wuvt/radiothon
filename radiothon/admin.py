from django.contrib import admin
from django import forms
from radiothon.models import *

class AttrRelInlineFormset(forms.models.BaseInlineFormSet):
    def clean(self):
        # get forms that actually have valid data
        count = 0
        for form in self.forms:
            try:
                if form.cleaned_data:
                    count += 1
            except AttributeError:
                # annoyingly, if a subform is invalid Django explicity raises
                # an AttributeError for cleaned_data
                pass
        #if count < 1:
        #    raise forms.ValidationError('You must have at least one order')

class AttrRelInline(admin.TabularInline):
    formset = AttrRelInlineFormset
    extra = 0
    model = PremiumAttributeRelationship
    exclude = ('options',)
    
class PremiumAdmin(admin.ModelAdmin):
    inlines = [ AttrRelInline, ]

class AttrOptInline(admin.TabularInline):
    model = PremiumAttributeOption
class PremiumAttributeAdmin(admin.ModelAdmin):
    inlines = [AttrOptInline]


admin.site.register(Premium, PremiumAdmin)    
admin.site.register(PremiumAttribute, PremiumAttributeAdmin)
admin.site.register(BusinessManager)
admin.site.register(PremiumChoice)