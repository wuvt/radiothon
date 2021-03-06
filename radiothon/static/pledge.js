(function () {
    if (!String.prototype.format) {
        String.prototype.format = function() {
        var args = arguments;
        return this.replace(/{(\d+)}/g, function(match, number) {
            return typeof args[number] != 'undefined' ? args[number] : match;
        });
      };
    }

    /**
     * Hides an option by placing it in a <span>
     * tag and hiding the span.
     */
    $.fn.hideOption = function () {
        // this ought to be an option
        if ($(this).attr('carlos_hidden') != '1') {
            $(this).wrap('<span>').hide();
            $(this).attr('carlos_hidden','1');
        }
    };
    /**
     * Unhides a tag wrapped in a hidden span
     */
    $.fn.showOption = function () {
        // this ought to be an <option>
        if ($(this).attr('carlos_hidden') == '1') {
            $(this).attr('carlos_hidden', '0');
            $(this).parent().replaceWith($(this));
            $(this).show();
        }
    };

    /**
     * After the document has fully loaded, apply event handlers to
     * form controls and initalize the empty form state
     */
    $(document).ready(function () {
        donation_update();
        payment_update();

        // Add the event handler for changes in the premium forms
        // Unhide/Create premium forms
        $('#id_pledge_form-amount').change(function () {
            donation_update();
        });

        // Add the event handler for changes in the payment method dropdown
        $('#id_pledge_form-payment').change(function () {
            payment_update();
        });

        // Add the event handler for changes in the Premium Delivery dropdown
        $('#id_pledge_form-premium_delivery').change(function () {
            var delivery = $(this).val();
            var address_subform = $('#address_subform');
	    var mail_subform = $('#mail_subform');
            var premium_formarea = $('#premiums_subform_formarea');
            if (delivery !== 'N' && delivery !== '') {
                premium_formarea.show('slow');
            } else {
                premium_formarea.hide('slow');
            }

            if (delivery === 'M') {
                address_subform.show('slow');
		mail_subform.show('slow');
            } else {
		mail_subform.hide('slow');
                var payment = $('#id_pledge_form-payment').val();
                if(payment === 'R') { // Credit
                    address_subform.show('slow');
                } else {
                    address_subform.hide('slow');
                }
            }
        });
    });

    /**
     * Add an event handler to the 'Amount' textbox
     * that will request the correct premium forms from
     * the server.
     */
    var donation_update = function () {
        var donation = $('#id_pledge_form-amount').val();
        var formarea = $('#premiums_subform_formarea');
        formarea.hide('fast');
        formarea.html('');

        if (donation !== '') {
            $('#premiums_subform').show('slow');
            var url = '/radiothon/premium/{0}/'.format(donation);
            $.getJSON(url, function (data) {
                var formhtml = '';
                for(var i = 0; i < data.length; i++) {
                    formhtml += '<h4 class="subform_title">{0}</h2>'.format(data[i].name);
                    formhtml += data[i].form;
                    /* Create/Unhide the premium forms */
                }
                formarea.html(formhtml);
                add_premium_eventhandlers();

                var delivery = $('#id_pledge_form-premium_delivery').val();
                if (delivery !== 'N' && delivery !== '') {
                    formarea.show('slow');
                }
            });
        } else {
            $('#premiums_subform').hide('fast');
        }
    };


    /** 
     * Add an event handler to the 'Payment' dropdown that will
     * show/hide the appropriate sub-forms. 
     * If Credit: Show the Credit and Address forms
     * If HokiePassport: Show the Hokiepassport forms
     */
    var payment_update = function () {
        var payment_method = $('#id_pledge_form-payment').val();
        if(payment_method === 'R') {
            $('#address_subform').show('slow');
            $('#credit_subform').show('slow');
            $('#hokiepassport_subform').hide('slow');
        } else if(payment_method === 'P') {
            $('#credit_subform').hide('slow');
            $('#hokiepassport_subform').show('slow');
        } else {
            $('#credit_subform').hide('slow');
            $('#hokiepassport_subform').hide('slow');
        }

        if (payment_method === 'H') {
            $('#check_subform').show('slow');
        } else {
            $('#check_subform').hide('slow');
        }

        // If it's not Credit, and the Delivery 
        // isn't Mail, hide the Address
        if(payment_method !== 'R') {
            var delivery = $('#id_pledge_form-premium_delivery').val();
            if(delivery !== 'M') {
                $('#address_subform').hide('slow');
            }
        }
    };

    /**
     * Add event handlers to each of the attribute dropdowns.
     * These event handlers make AJAX requests that determine
     * what attributes are available based on the option choices
     * selected in the dropdowns.
     */
    var add_premium_eventhandlers = function () {
        /* Hide unavailable options based on attribute choices */
        var avail_url = '/radiothon/premium/availability/{0}/';

        // Attempt to disable submitting the form with 'enter'
        $('form').bind("keyup", function (e) {
            var code = e.keyCode || e.which;
            if (code === 13) {
                e.preventDefault();
                return false;
            }
        });

        $('select[id*="premium_choice_formset"]').each(function () {
            var attribute = '';
            var premium = '';

            var regexp = 'premium_choice_formset\\-(\\w+)';
            var re = new RegExp(regexp,'i');
            attribute = $(this).attr('id').match(re)[1];

            regexp = 'id_(\\w+)_premium_choice_formset';
            re = new RegExp(regexp,'i');
            premium_name = $(this).attr('id').match(re)[1];

            if (attribute !== 'premium' && attribute !== '') {
                // Get the attribute options' premium's id
                var option_id = '';
                var premium_id = '';
                var selector = 'select[id="id_{0}_premium_choice_formset-premium"]';
                selector = selector.format(premium_name);

                premium_id = $('option:selected', selector).val();

                // Add the event handler that will send the AJAX query,
                // containing the premium and option primary keys
                $(this).change(function () {
                    var regexp = 'id_(\\w+)_premium_choice_formset';
                    var re = new RegExp(regexp,'i');
                    premium_name = $(this).attr('id').match(re)[1];

                    // Reset all attribute-option selectors for this premium
                    // TODO: Don't show all of your own attribute's option when selecting '-------'
                    if ($('option:selected:first',this).val() === '') {
                        var unselected_attribute = $(this);
                        $('option','select[id*="{0}_premium_choice_formset-"]'.format(premium_name)).each(function () {
                            if ($(this).parents('select')[0] !== unselected_attribute[0]) {
                                $(this).showOption();
                            }
                        });
                        return;
                    }

                    // Executes the AJAX query and shows available options
                    // and hides unavailable ones.
                    var selected_option = $('option:selected:first', this);
                    var option_id = selected_option.val();
                    if (option_id !== '') {
                        var url = '/radiothon/premium/availability/{0}/{1}/'.format(premium_id, option_id);

                        // Perform the AJAX query
                        $.getJSON(url, function (data) {
                            // Data is an array containing relationship objects
                            // I need to organize it by attributes, 
                            for(var i = 0; i < data.length; i++) {
                                var attribute = data[i];
                                // For each element matching this (which should just be one)
                                $('option','select[id="id_{0}_premium_choice_formset-{1}"]'.format(premium_name, attribute.attribute)).each(function () {
                                    var val = parseInt(this.value, 10);
                                    if (!isNaN(val)) {
                                        if($.inArray(val, attribute.available_options) === -1) {
                                            $(this).hideOption();
                                        }else{
                                            $(this).showOption();
                                        }
                                    }
                                });
                            }
                        });
                    }
                });
            }
        });
    };
}());
