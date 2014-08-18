import numpy as np
from time import sleep
from iconsole import IConsole

# start server and create figures
ic = IConsole()
sleep(1.0)
fig1 = ic.create_plot().title('Random Walk').yrange(0.5,1.5)
fig2 = ic.create_plot().title('Sine Wave').yrange(-1.0,1.0)
fig3 = ic.create_plot().title('Cosine Wave').yrange(-1.0,1.0)

# constants
ar_var = 0.05
pval = 0.9
n_base = 128
randx = np.linspace(0.0,n_base,n_base)
randw = ar_var*np.random.randn(n_base)
randy = np.zeros(n_base)
randy[0] = randw[0]
for i in range(1,n_base):
  randy[i] = pval*randy[i-1] + randw[i]
upd_speed = 0.1
upd_iter = 1

theta0 = np.linspace(0.0,2.0*np.pi,n_base)
theta = np.linspace(0.0,2.0*np.pi,n_base)

# main loop
show_iter = 0
while True:
    sleep(upd_speed)

    randw = ar_var*np.random.randn(10)
    randy[:-10] = randy[10:]
    for i in range(10,0,-1):
      randy[n_base-i] = pval*randy[n_base-i-1] + randw[i-1]

    theta += 0.2

    show_iter += 1
    if show_iter == upd_iter:
        fig1.data(randx,np.exp(randy))
        fig2.data(theta0,np.sin(theta))
        fig3.data(theta0,np.cos(theta))
        show_iter = 0
