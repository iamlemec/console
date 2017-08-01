// main content area
var box = $("#outer_box");

// if a figure is not present, create it
function ensure_plot(plabel,options)
{
  if (box.children("#"+plabel).length == 0) {
    var fig = $("<div>").addClass("figure_box").attr("id",plabel);
    var title = $("<div>").addClass("figure_title");
    var plot = $("<div>").addClass("plot_box");
    fig.append(title);
    fig.append(plot);
    box.append(fig);
  }
}

// remove a figure
function remove_plot(plabel) {
  var plot = box.children("#"+plabel);
  if (plot.length > 0) {
    plot.remove();
  }
}

function set_title(plabel,title) {
  box.find(".figure_box#"+plabel+" > .figure_title").html(title);
}

function set_vega(plabel,spec) {
  var targ = "#" + plabel + " > .plot_box";
  var vtarg = $(targ);
  var twidth = vtarg.width();
  var size = {'width': 400, 'height': 300};
  if ('config' in spec) {
    var conf = spec['config'];
    conf['cell'] = size;
  } else {
    spec['config'] = {'cell': size};
  }
  var embedSpec = {
    mode: "vega-lite",
    spec: spec
  };
  vg.embed(targ,embedSpec,function(error,result) {
    vtarg.children('.vega-actions').hide();
  });
}

function connect()
{
  if ('MozWebSocket' in window) {
    WebSocket = MozWebSocket;
  }
  if ('WebSocket' in window) {
    var ws_con = "ws://" + window.location.host + "/mec";
    console.log(ws_con);

    ws = new WebSocket(ws_con);

    ws.onopen = function() {
      console.log('websocket connected!');
      var msg = JSON.stringify({"cmd": "init", "content": ""});
      ws.send(msg);
    };

    ws.onmessage = function (evt) {
      var receivedMsg = evt.data;
      // console.log(receivedMsg);

      var json_data = JSON.parse(receivedMsg);
      if (json_data)
      {
        var cmd = json_data["cmd"];
        var plabel = json_data["label"];
        if (cmd == "create_plot") {
          ensure_plot(plabel);
        } else if (cmd == "remove_plot") {
          remove_plot(plabel);
        } else if (cmd == "set_title") {
          title = json_data["title"];
          set_title(plabel,title);
        } else if (cmd == "set_vega") {
          var spec = JSON.parse(json_data["spec"]);
          set_vega(plabel,spec);
        }
      }
    };

    ws.onclose = function() {
      console.log('websocket closed');
    };
  } else {
    console.log('Sorry, your browser does not support websockets.');
  }
}

function disconnect()
{
  if (ws) {
    ws.close();
  }
}

connect();
