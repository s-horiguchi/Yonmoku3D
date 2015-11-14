
$(document).ready(function() {
    $(".inputbutton").click(function() {
	newMove_button($(this));
    });
    $("#resetbutton").click(function() {
	resetBoard();
    });
    updater.start();
});

function enableButtons() {
    $(".inputbutton").removeAttr("disabled");
}
function disableButtons() {
    $(".inputbutton").attr("disabled", "disabled");
}
function newMove(name) {
    var json = {};
    json["type"] = "MOVE";
    json["body"] = String.fromCharCode(0x41 + parseInt(name[10]), //y
				       name[8].charCodeAt(0)+1); //x
    updater.socket.send(JSON.stringify(json));
}
    
function newMove_button(button) {
    var form = $("#moveform");
    var json = {};
    json["type"] = "MOVE";
    json["body"] = button.val();
    updater.socket.send(JSON.stringify(json));
}
function resetBoard() {
    var form = $("#moveform");
    var json = {};
    json["type"] = "RESET";
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
	    updater.updateConnection(json.connection);
	    if (json.type == "ERROR")
		updater.showError(json.html);
	    else if (json.type == "GAMEOVER") {
		updater.showInfo("You are <b>"+json.you + "</b><br><span id='result'>"+json.info+"</span>");
		updater.updateBoardHTML(json.html);
		updater.updateBoardGraphics(json.scene);
		var paragraph = document.getElementById('result');
		textEffect(paragraph, 'fly-in-out');
	    }
	    else if (json.type == "SUCCESS") {
		updater.you = json.you;
		if(json.you === json.turn)
		    updater.showInfo("You are <b>"+json.you + "</b><br>It's YOUR turn!");
		else
		    updater.showInfo("You are <b>"+json.you + "</b><br>It's " + json.turn + "'s turn!");
		
		if (updater.you == json.turn)
		    enableButtons();
		else
		    disableButtons();
		updater.updateBoardHTML(json.html);
		updater.updateBoardGraphics(json.scene);
	    }
	}
    },

    updateConnection: function(message) {
	$("#connection").html(message);
    },
    showError: function(message) {
	$("#error").fadeIn(0).html(message);
	$("#error").fadeOut(1500);
	console.log("ERROR:", message);
    },
    showInfo: function(message) {
	$("#info").html(message);
    },
    updateBoardHTML: function(message) {
	$("#inbox").html(message);
    },
    updateBoardGraphics: function(scene) {
	for(var x=0; x< 4; x++) {
	    for(var y=0; y < 4; y++) {
		for(var z = 0; z < 4; z++) {
		    switch(scene[x][y][z]){
		    case "|":
			spheres[16*x+4*y+z].visible = false;
			break;
		    case "W":
			spheres[16*x+4*y+z].visible = true;
			spheres[16*x+4*y+z].material.color.setHex(0xffffff);
			break;
		    case "B":
			spheres[16*x+4*y+z].visible = true;
			spheres[16*x+4*y+z].material.color.setHex(0x000000);
			break;
		    }
		}
	    }
	}
    }
};

function textEffect(paragraph, animationName) {
    var text = paragraph.innerHTML,
    chars = text.length,
    newText = '',
    animation = animationName,
    char,
    i;
    
    for (i = 0; i < chars; i += 1) {
	newText += '<i>' + text.charAt(i) + '</i>';
    }
    
    paragraph.innerHTML = newText;
    
    var wrappedChars = document.getElementsByTagName('i'),
    wrappedCharsLen = wrappedChars.length,
    j = 0;
    
    function addEffect () {
	setTimeout(function () {
	    wrappedChars[j].className = animation;
	    j += 1;
	    if (j < wrappedCharsLen) {
		addEffect();
	    }
	}, 100)
    }
    
    addEffect();
};
