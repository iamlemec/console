// Why!?!
Array.prototype.contains = function(obj) {
    var i = this.length;
    while (i--) {
        if (this[i] === obj) {
            return true;
        }
    }
    return false;
}

// main content area
var box = d3.select("div.outer_box");

// figure geometry
var base_width = Math.min(screen.width,500);
var base_height = 0.6*base_width;
var margin = {top: 10, right: 10, bottom: 20, left: 30};
var width = base_width - margin.left - margin.right;
var height = base_height - margin.top - margin.bottom;

// plot state information
var nplots = 0;
var fig_xscale = new Array();
var fig_yscale = new Array();
var fig_data = new Array();

// if a figure is not present, create it
function ensure_plot(plabel,options)
{
  if (box.select("div#"+plabel)[0][0]==null) {
    nplots++;

    var fig = box.append("div").attr("id",plabel).attr("class","figure_box");
    var title = fig.append("div").attr("class","figure_title").attr("id",plabel);
    var plot = fig.append("div").attr("class","plot_box");

    // Add the SVG element
    var svg = plot.append("svg")
                 .attr("width",base_width)
                 .attr("height",base_height)
                 .append("g")
                 .attr("transform","translate("+margin.left+","+margin.top+")")
                 .attr("class","box")
                 .attr("id",plabel);

    // Add the x-axis
    var xaxis_svg = svg.append("g")
        .attr("class", "x axis")
        .attr("transform", "translate(0," + height + ")")
        .attr("id",plabel);

    // Add the y-axis
    var yaxis_svg = svg.append("g")
        .attr("class", "y axis")
        .attr("id",plabel);

    // Add the line
    var path = svg.append("g")
                  .append("path")
                  .attr("class", "line")
                  .attr("id",plabel);
  }
}

// remove a figure
function remove_plot(plabel) {
  if (box.select("div#"+plabel)[0][0]!=null) {
    box.select("div#"+plabel).remove();
  }
  fig_xscale.splice(plabel,1);
  fig_yscale.splice(plabel,1);
  fig_data.splice(plabel,1);
}

function set_title(plabel,title) {
  box.select("div.figure_title#"+plabel).html(title);
}

function set_xrange(plabel,xmin,xmax) {
  var xScale = d3.scale.linear().domain([xmin,xmax]).range([0,width]);
  var xAxis = d3.svg.axis().scale(xScale).ticks(10);
  comps = ['xaxis'];
  if (plabel in fig_data) {
    comps.push('data');
  }
  fig_xscale[plabel] = xScale;
  redraw(plabel,comps);
}

function set_yrange(plabel,ymin,ymax) {
  var yScale = d3.scale.linear().domain([ymin,ymax]).range([height,0]);
  var yAxis = d3.svg.axis().scale(yScale).ticks(10);
  comps = ['yaxis'];
  if (plabel in fig_data) {
    comps.push('data');
  }
  fig_yscale[plabel] = yScale;
  redraw(plabel,comps);
}

function set_data(plabel,x_data,y_data) {
  var comps = ['data'];
  if (!(plabel in fig_xscale) || !(plabel in fig_data)) {
    comps.push('xaxis');
  }
  if (!(plabel in fig_yscale) || !(plabel in fig_data)) {
    comps.push('yaxis');
  }
  fig_data[plabel] = [x_data,y_data];
  redraw(plabel,comps);
}

function redraw(plabel,comps) {
  //console.log(comps);

  // fetch data
  if (plabel in fig_data) {
    var x_data = fig_data[plabel][0];
    var y_data = fig_data[plabel][1];
    var data = new Array();
    for (i in x_data) {
      data[i] = [x_data[i],y_data[i]];
    }
  }

  // draw elements
  if (comps.contains('xaxis') || comps.contains('data')) {
    if (plabel in fig_xscale) {
      var x = fig_xscale[plabel];
    } else {
      var x = d3.scale.linear().domain([d3.min(x_data),d3.max(x_data)]).range([0,width]);
    }
  }
  if (comps.contains('yaxis') || comps.contains('data')) {
    if (plabel in fig_yscale) {
      var y = fig_yscale[plabel];
    } else {
      var y = d3.scale.linear().domain([d3.min(y_data),d3.max(y_data)]).range([height,0]);
    }
  }

  // generate transition
  var t = d3.transition().duration(0);
  if (comps.contains('xaxis')) {
    var xAxis = d3.svg.axis().scale(x).ticks(10);
    t.select("g.x.axis#"+plabel).call(xAxis);
  }
  if (comps.contains('yaxis')) {
    var yAxis = d3.svg.axis().scale(y).ticks(10).orient("left");
    t.select("g.y.axis#"+plabel).call(yAxis);
  }
  if (comps.contains('data')) {
    var line = d3.svg.line().x(function(d, i) { return x(d[0]); }).y(function(d, i) { return y(d[1]); }).interpolate('monotone');
    box.select("path#"+plabel).data([data]);
    t.select("path#"+plabel).attr("d",line);
  }
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
    };

    ws.onmessage = function (evt) {
      var receivedMsg = evt.data;
      //console.log(receivedMsg);

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
        } else if (cmd == "set_xrange") {
          xmin = json_data["xmin"];
          xmax = json_data["xmax"];
          set_xrange(plabel,xmin,xmax);
        } else if (cmd == "set_yrange") {
          ymin = json_data["ymin"];
          ymax = json_data["ymax"];
          set_yrange(plabel,ymin,ymax);
        } else if (cmd == "set_options") {
          // yep
        } else if (cmd == "set_data") {
          var x_values = json_data["x_values"];
          var y_values = json_data["y_values"];
          set_data(plabel,x_values,y_values);
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
