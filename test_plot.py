import iconsole as ic
import numpy as np
from time import sleep

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

theta0 = np.linspace(0.0,2.0*np.pi,n_base)
theta = np.linspace(0.0,2.0*np.pi,n_base)

# main loop
while True:
    sleep(upd_speed)

    randw = ar_var*np.random.randn(10)
    randy[:-10] = randy[10:]
    for i in range(10,0,-1):
      randy[n_base-i] = pval*randy[n_base-i-1] + randw[i-1]

    theta += 0.2

    #print randw
    ic.update_plot('random_walk',randx,np.exp(randy),yaxis={'min':0.5,'max':1.5})
    ic.update_plot('sine_wave',theta0,np.sin(theta),yaxis={'min':-1.0,'max':1.0})

