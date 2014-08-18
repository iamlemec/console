Console is simple Python framework for real-time web plotting. The plots are served using Tornado and ZeroMQ. Here's an example:

```
from iconsole import IConsole
ic = IConsole()
v = np.random.rand(10)
fig = ic.create_plot()
fig.title('Random Data')
fig.data(v)
```

Then head to `http://localhost:8080` to see the results, which should look roughly like this

<img src="http://dohan.dyndns.org/images/console.png"/>

Currently there is support for `xrange` and `yrange` as well. All figure operations support chaining, can be changed on-the-fly, and only `data` is require for display.
