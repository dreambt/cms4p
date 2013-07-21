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

        elem.addClass("alert-"+type).find("span").html(text);
        elem.fadeIn();
        hideHandler = setTimeout(function() {
            that.hide();
            elem.removeClass("alert-"+type).find("span").html();
        }, 5000);
    };

    that.hide = function() {
        elem.fadeOut();
    };

    return that;
}());
$(function () {
    SiQiTip.init({
        "selector": ".bb-alert"
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
                    SiQiTip.show("error", "操作已取消!");
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
                    SiQiTip.show("error", "操作已取消!");
                }
        });
    });
});