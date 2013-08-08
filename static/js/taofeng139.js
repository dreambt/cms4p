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
// 提示消息
var SiQiTip = (function() {
    "use strict";

    var elem,
        hideHandler,
        that = {};

    that.init = function(options) {
        elem = $(options.selector);
    };

    that.show = function(type, text) {
        clearTimeout(hideHandler);

        var title = "成功";
        switch (type) {
            case "info":
                title = "信息";
                break;
            case "error":
                title = "错误";
                break;
            case "warning":
                title = "警告";
                break;
        }
        elem.addClass("message-"+type).find("h3").html(title);
        elem.find("p").html(text);
        elem.fadeIn(500);
        elem.animate({top:"0"}, 500);
        hideHandler = setTimeout(function() {
            that.hide(type);
            //elem.removeClass("message-"+type).find("p").html("");
        }, 4000);
    };

    that.hide = function(type) {
        elem.fadeOut(10);
        elem.animate({top:"-97px"}, 500);
        elem.removeClass("message-"+type);
    };

    return that;
}());
$(function () {
    SiQiTip.init({
        "selector": ".message"
    });
    $('.message').click(function(){
	    $(this).animate({top: -$(this).outerHeight()}, 500);
    });
    $("#flushcache").click(function () {
            bootbox.confirm("确认清空缓存?", function(result) {
                if(result) {
                    $.ajax({
                        url: "/admin/flushdata?act=flushcache",
                        method: "POST"
                    }).success(function () {
                        SiQiTip.show("info", "缓存已清空!");
                    });
                }
                else {
                    SiQiTip.show("warning", "操作已取消!");
                }
            });
        });
    $("#flush").click(function () {
            bootbox.confirm("确认清空数据? 这将删除所有文章、留言等数据！！！", function(result) {
                if(result) {
                    $.ajax({
                        url: "/admin/flushdata?act=flush",
                        method: "POST"
                    }).success(function () {
                        SiQiTip.show("info", "数据已清空!");
                    });
                }
                else {
                    SiQiTip.show("warning", "操作已取消!");
                }
        });
    });
});