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
    updater.start();
});

function enableButtons() {
    $(".inputbutton").removeAttr("disabled");
}
function disableButtons() {
    $(".inputbutton").attr("disabled", "disabled");
}

function newMove(button) {
    var form = $("#moveform");
    var json = {};
    json["_xsrf"] = $("input[name=_xsrf]").val();
    json["type"] = "MOVE";
    json["body"] = button.val();
    updater.socket.send(JSON.stringify(json));
}

var updater = {
    socket: null,
    you: null,

    start: function() {
	var url = "ws://" + location.host + "/socket";
	updater.socket = new WebSocket(url);
	updater.socket.onmessage = function(event) {
	    var json = JSON.parse(event.data);
	    if (json.type == "ERROR")
		updater.showError(json.html);
	    else if (json.type == "GAMEOVER") {
		updater.showInfo(json.info);
		updater.updateBoard(json.html);
	    }
	    else if (json.type == "SUCCESS") {
		updater.you = json.you;
		$("#info").html("You are "+json.you + "<br>It's " + json.turn + "'s turn!");
		
		if (updater.you == json.turn)
		    enableButtons();
		else
		    disableButtons();
		updater.updateBoard(json.html);
	    }
	}
    },

    showError: function(message) {
	$("#error").fadeIn(0).html(message);
	$("#error").fadeOut(2000);
	console.log("ERROR:", message);
    },
    showInfo: function(message) {
	$("#info").html(message);
    },
    updateBoard: function(message) {
	$("#inbox").html(message);
    }
};
