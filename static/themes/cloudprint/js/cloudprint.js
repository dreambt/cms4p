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
        success: "恭喜您，订阅成功!",
        default_error: "抱歉，请稍后重试.",
        empty_email: "请输入您的 Email 邮箱地址.",
        invalid_email: "Email 邮箱地址格式貌似有点奇葩.",
        already_subscribed: "您貌似已经订阅过了, 感谢您的关注."
    }
}
// 图片渐现
$('#container').imagesLoaded().always( function( instance ) {
    console.log('all images loaded');
  })
  .done( function( instance ) {
    console.log('all images successfully loaded');
  })
  .fail( function() {
    console.log('all images loaded, at least one is broken');
  }).progress( function( instance, image ) {
  var result = image.isLoaded ? 'loaded' : 'broken';
  console.log( 'image is ' + result + ' for ' + image.img.src);
  image.fadeIn("slow");
});
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
                if(data.status == 200) {
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