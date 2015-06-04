
$(document).ready(function() {
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
		updater.showInfo("You are "+json.you + "<br>"+json.info);
		updater.updateBoard(json.html);
	    }
	    else if (json.type == "SUCCESS") {
		updater.you = json.you;
		updater.showInfo("You are "+json.you + "<br>It's " + json.turn + "'s turn!");
		
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
	$("#error").fadeOut(1500);
	console.log("ERROR:", message);
    },
    showInfo: function(message) {
	$("#info").html(message);
    },
    updateBoard: function(message) {
	$("#inbox").html(message);
    }
};
