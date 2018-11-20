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

// remove all plots
function clear_plots() {
  box.empty();
}

function set_title(plabel,title) {
  box.find(".figure_box#"+plabel+" > .figure_title").html(title);
}

function set_vega(plabel,spec) {
  var targ = "#" + plabel + " > .plot_box";
  spec["$schema"] = "https://vega.github.io/schema/vega-lite/v3.json";
  spec["width"] = 400;
  spec["height"] = 300;
  vegaEmbed(targ,spec);
}

function set_svg(plabel,svg,css) {
  var targ = "#" + plabel + " > .plot_box";
  var vtarg = $(targ);
  vtarg.html(svg);
  var vcss = $("<style>", {figure: plabel, html: css});
  $("head > style[figure=\"" + plabel + "\"]").remove();
  $("head").append(vcss);
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
      console.log(receivedMsg);

      var json_data = JSON.parse(receivedMsg);
      if (json_data)
      {
        var cmd = json_data["cmd"];
        var plabel = json_data["label"];
        if (cmd == "create_plot") {
          ensure_plot(plabel);
        } else if (cmd == "remove_plot") {
          remove_plot(plabel);
        } else if (cmd == "clear_plots") {
          clear_plots();
        } else if (cmd == "set_title") {
          title = json_data["title"];
          set_title(plabel,title);
        } else if (cmd == "set_vega") {
          var spec = json_data["spec"];
          set_vega(plabel,spec);
        } else if (cmd == "set_svg") {
          var svg = json_data["svg"];
          var css = json_data["css"]
          set_svg(plabel,svg,css);
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
