// Copyright 2009 FriendFeed
//
// Licensed under the Apache License, Version 2.0 (the "License"); you may
// not use this file except in compliance with the License. You may obtain
// a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
// WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
// License for the specific language governing permissions and limitations
// under the License.

$(document).ready(function() {
    if (!window.console) window.console = {};
    if (!window.console.log) window.console.log = function() {};

    $(".inputbutton").click(function() {
	newMove($(this));
    });
    updater.poll();
});

function newMove(button) {
    var form = $("#moveform");
    var json = {};
    json["_xsrf"] = $("input[name=_xsrf]").val();
    json["button"] = button.val();

    $.postJSON("/a/move/new", json, function(response) {
        updater.updateBoard(response);
    });
}

function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

jQuery.postJSON = function(url, args, callback) {
    args._xsrf = getCookie("_xsrf");
    $.ajax({url: url, data: $.param(args), dataType: "text", type: "POST",
            success: function(response) {
        if (callback) callback( response );
    }, error: function(response) {
	$("#error").fadeIn(0).html(response.response);
	$("#error").fadeOut(2000);
        console.log("ERROR:", response.response);
    }});
};

var updater = {
    errorSleepTime: 500,

    poll: function() {
        var args = {"_xsrf": getCookie("_xsrf")};
        $.ajax({url: "/a/move/updates", type: "POST", dataType: "text",
                data: $.param(args), success: updater.onSuccess,
                error: updater.onError});
    },

    onSuccess: function(response) {
        try {
            updater.updateBoard( response );
        } catch (e) {
            updater.onError();
            return;
        }
        updater.errorSleepTime = 500;
        window.setTimeout(updater.poll, 0);
    },

    onError: function(response) {
        updater.errorSleepTime *= 2;
        console.log("Poll error; sleeping for", updater.errorSleepTime, "ms");
        window.setTimeout(updater.poll, updater.errorSleepTime);
    },

    updateBoard: function(message) {
	$("#inbox").html(message);
    }
};
