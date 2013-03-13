import iconsole as ic
import numpy as np
from time import sleep

# constants
ar_var = 0.05
pval = 0.9
pname1 = 'random_walk1'
pname2 = 'random_walk2'
pname3 = 'random_walk3'
pname4 = 'random_walk4'
n_base = 128
randx = np.linspace(0.0,n_base,n_base)
randw = ar_var*np.random.randn(n_base)
randy = np.zeros(n_base)
randy[0] = randw[0]
for i in range(1,n_base):
  randy[i] = pval*randy[i-1] + randw[i]
upd_speed = 0.1

# main loop
while True:
    sleep(upd_speed)

    randw = ar_var*np.random.randn(10)
    randy[:-10] = randy[10:]
    for i in range(10,0,-1):
      randy[n_base-i] = pval*randy[n_base-i-1] + randw[i-1]

    #print randw
    ic.update_plot(pname1,randx,np.exp(randy),yaxis={'min':0.5,'max':1.5})
    ic.update_plot(pname2,randx,np.sin(randy)+1.0,yaxis={'min':0.5,'max':1.5})
    ic.update_plot(pname3,randx,np.exp(-randy),yaxis={'min':0.5,'max':1.5})
    ic.update_plot(pname4,randx,np.exp(1.5*randy),yaxis={'min':0.5,'max':1.5})

