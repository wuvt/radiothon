//first, checks if it isn't implemented yet
if (!String.prototype.format) {
  String.prototype.format = function() {
    var args = arguments;
    return this.replace(/{(\d+)}/g, function(match, number) { 
      return typeof args[number] != 'undefined'
        ? args[number]
        : match
      ;
    });
  };
}

/* Hides an option by placing it in a <span>
 * tag and hiding the span.
 */
$.fn.hideOption = function() {
	// this ought to be an option
	if ($(this).attr('carlos_hidden') != '1'){
		$(this).wrap('<span>').hide();
		$(this).attr('carlos_hidden','1');
	}
}

/* Unhides a tag wrapped in a hidden span */
$.fn.showOption = function() {
	// this ought to be an <option>
	if ($(this).attr('carlos_hidden') == '1'){
		$(this).attr('carlos_hidden', '0');
		$(this).parent().replaceWith($(this));
		$(this).show();
	}
}

$(document).ready(function(){
	/* Adds the event handler for changes in the payment method dropdown */
	$('#id_pledge_form-payment').change(function(){
		/* Handle what happens when changing the payment method 
		 * If Credit: Show the Credit and Address forms
		 * If HokiePassport: Show the Hokiepassport forms */
		$('option:selected', this).each(function () {
			if($(this).text() == 'Credit'){
				$('#address_subform').show('slow');
				
				$('#credit_subform').show('slow');
				$('#hokiepassport_subform').hide('slow');
			}else if($(this).text() == 'Hokie Passport'){
				$('#credit_subform').hide('slow');
				$('#hokiepassport_subform').show('slow');
			}else{
				$('#credit_subform').hide('slow');
				$('#hokiepassport_subform').hide('slow');
			}
			
			/* If it's not credit, and the Delivery 
			 * isn't Mail, hide the Address */
			if($(this).text() != 'Credit'){
				$('#id_pledge_form-premium_delivery option:selected').each(function(){
					if($(this).text() != 'Mail'){
						$('#address_subform').hide('slow');
					}
				});
			}
		});
	})
  
	/* Add the event handler for changes in the Premium Delivery dropdown */
	$('#id_pledge_form-premium_delivery').change(function(){
		$('option:selected', this).each(function(){
			if($(this).text() == 'Mail'){
				$('#address_subform').show('slow');
			}else{
				$('#id_pledge_form-payment option:selected').each(function(){
					if($(this).text() == 'Credit'){
						$('#address_subform').show('slow');
					}else{
						$('#address_subform').hide('slow');
					}
				});
			}
		});
	})
	
	/* Add the event handler for changes in the premium forms */
	/* Unhide/Create premium forms */
	$('#id_pledge_form-amount').change(function(){
		var donation = $('#id_pledge_form-amount').val()
		var args = {url:'/radiothon/premium/' + donation + '/'};
		$.getJSON(args, function(data){
			/* Create/Unhide the premium forms */
		});
	});
	
	/* Hide unavailable options based on attribute choices */
	var avail_url = '/radiothon/premium/availability/{0}/'
	
	/* On document load,
	 * Add event handlers to each of the attribute dropdowns.
	 * These event handlers make AJAX requests that determine
	 * what attributes are available based on the option choices
	 * selected in the dropdowns.
	 */
	$('select[id*="premium_choice_formset"]').each(function(){
		var attribute = '';
		var premium = '';
		
		var regexp = 'premium_choice_formset\\-\\d+\\-(\\w+)';
		var re = new RegExp(regexp,'i');
		attribute = $(this).attr('id').match(re)[1];
		
		regexp = 'id_(\\w+)_premium_choice_formset';
		re = new RegExp(regexp,'i');
		premium_name = $(this).attr('id').match(re)[1];
		
		if (attribute != 'premium' && attribute != ''){
			/* Get the attribute options' premium's id */
			var option_id = ''
			var premium_id = ''
			var selector = 'select[id="id_{0}_premium_choice_formset-0-premium"]'.format(premium_name)
			premium_id = $('option:selected', selector).val();
			
			/* Add the event handler that will send the AJAX query,
			 * containing the premium and option primary keys */
			$(this).change(function(){
				var regexp = 'id_(\\w+)_premium_choice_formset';
				var re = new RegExp(regexp,'i');
				premium_name = $(this).attr('id').match(re)[1];
				
				/* Reset all attribute-option selectors for this premium */
				// TODO: Don't show all of your own attribute's option when selecting '-------'
				if ($('option:selected:first',this).val() == ''){
					var unselected_attribute = $(this)
					$('option','select[id*="{0}_premium_choice_formset-0-"]'.format(premium_name)).each(function(){
						if (!($(this).parents('select')[0] === unselected_attribute[0])){
							$(this).showOption();
						}
					});
					return;
				}
				
				/* Executes the AJAX query and shows available options
				 * and hides unavailable ones. */
				var selected_option = $('option:selected:first', this)
				var option_id = selected_option.val();
				if (option_id != ''){
					var url = '/radiothon/premium/availability/{0}/{1}/'.format(premium_id, option_id);
					/* Perform the AJAX query */
					$.getJSON(url, function(data){
						// Data is an array containing relationship objects
						// I need to organize it by attributes, 
						for(var i = 0; i < data.length; i++){
							var attribute = data[i];
							// For each element matching this (which should just be one)
							$('option','select[id="id_{0}_premium_choice_formset-0-{1}"]'.format(premium_name, attribute.attribute)).each(function(){
								if (!isNaN(parseInt(this.value))){
									if($.inArray(parseInt(this.value),attribute.available_options) == -1){
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
});