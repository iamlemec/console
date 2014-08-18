Console is simple Python framework for real-time web plotting. The plots are served using Tornado, ZeroMQ, and WebSockets. Rendering is done with `d3.js`. Here's an example:

```
from iconsole import IConsole
ic = IConsole()
fig1 = ic.create_plot().title('Random Walk 1').data(np.cumsum(np.random.randn(1024)))
fig2 = ic.create_plot().title('Random Walk 2').data(np.cumsum(np.random.randn(1024)))
```

Run this and head to `http://localhost:8080` to see the results, which should look roughly like this

<img src="http://dohan.dyndns.org/images/console_random.png"/>

Currently there is support for `xrange` and `yrange` as well. All figure operations support chaining, can be changed on-the-fly, and only `data` is require for display. Mobile-scale output is supported through CSS media queries.
