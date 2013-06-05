var config = {
    countdown: {
        year: 2013,
        month: 9,
        day: 10,
        hours: 9,
        minutes: 0,
        seconds: 0
    },

    subscription_form_tooltips: {

        /* On successful subscription */
        success: "You have been subscribed!",

        /* On some unknown error */
        default_error: "Error! Please, contact administration.",

        /* When email field is empty */
        empty_email: "Please, enter your email.",

        /* When email is invalid (for example, there is no @ character in it) */
        invalid_email: "Email is invalid. Please, enter valid email address.",

        /* When submitted email is already on the list */
        already_subscribed: "You are already subscribed."
    }
}

$(function() {

/*
    Countdown
=================================================================*/
    var date = new Date(config.countdown.year,
                        config.countdown.month - 1,
                        config.countdown.day,
                        config.countdown.hours,
                        config.countdown.minutes,
                        config.countdown.seconds),
        $body = $('body'),
        $countdown = $('#countdown');

    $countdown.countdown(date, function(event) {
        if(event.type == 'finished') {
            $countdown.fadeOut();
        } else {
            $('.countdown-' + event.type, $countdown).text(event.value);
        }
    });


/*
    Subscription form
=================================================================*/
    var messages = config.subscription_form_tooltips,
        error = false,
        $form = $('#subscribe-form'),
        $email = $('#subscribe-email'),
        $button = $('#subscribe-submit'),
        $tooltip;

    function renderTooltip(type, message) {
        if(!$tooltip) {
            $tooltip = $('<p id="subscribe-tooltip" class="subscribe-tooltip"></p>').appendTo($form).hide();
        }

        if(type == 'success') {
            $tooltip.removeClass('error').addClass('success');
        } else {
            $tooltip.removeClass('success').addClass('error');
        }

        $tooltip.text(message).fadeIn(200);
    }

    function hideTooltip() {
        if($tooltip) {
            $tooltip.fadeOut(200);
        }
    }

    function changeFormState(type, message) {
        $email.removeClass('success error');

        if(type == 'normal') {
            hideTooltip();
        } else {
            renderTooltip(type, message);
            $email.addClass(type);
        }
    }

    $form.submit(function(event) {
        event.preventDefault();

        var email = $email.val();

        if(email.length == 0) {
            changeFormState('error', messages['empty_email']);
        } else {
            $.post('/subscribe', {
                'email': email,
                'ajax': 1
            }, function(data) {
                if(data.status == 'success') {
                    changeFormState('success', messages['success']);
                } else {
                    switch(data.error) {
                        case 'empty_email':
                        case 'invalid_email':
                        case 'already_subscribed':
                            changeFormState('error', messages[data.error]);
                            break;

                        default:
                            changeFormState('error', messages['default_error'])
                            break;
                    }
                }
            }, 'json');
        }
    });

    // Remove tooltip on text change
    $email.on('change focus click keydown', function() {
        if($email.val().length > 0) {
            changeFormState('normal');
        }
    });
});