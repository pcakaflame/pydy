#!/usr/bin/env python
import rollingdisc_lib as rd
from scipy.integrate import odeint
from numpy import array, arange, zeros, roots, sin, cos, tan, pi, complex
import matplotlib.pyplot as plt

# Dimensions of a quarter
m = 5.67/1000.  # A quarter has a mass of 5.67g
g = 9.81        # Gravitational acceleration
r = 0.02426/2.  # Radius of a quarter
params = [m, g, r]

#### Eigenvalue plot #####
u1 = arange(-30, 30.01, 0.01, dtype=complex)
n = len(u1)
eval = zeros((n,3), dtype=complex)
for i, u in enumerate(u1):
    eval[i] = rd.evals(u, (g, r))
mnmx = array([min([min(eval[:,1].imag), min(eval[:,1].real)]),
    max([max(eval[:,0].real), max(eval[:,0].imag)])])
cs = rd.critical_speed((g,r))
cs = array([cs, cs])
plt.figure()
plt.plot(u1, eval[:,0].real, 'r', label='Re($\lambda_0$)')
plt.plot(u1, eval[:,1].real, 'b', label='Re($\lambda_1$)')
plt.plot(u1, eval[:,0].imag, 'r:', label='Im($\lambda_0$)')
plt.plot(u1, eval[:,1].imag, 'b:', label='Im($\lambda_1$)')
plt.plot(cs, mnmx, 'g:', linewidth=2)
plt.plot(-cs, mnmx, 'g:', linewidth=2)
plt.title('Eigenvalues of linearized EOMS about upright steady configuration,\n'+
        'm=%.4f kg, r=%.4f m'%(m,r))
plt.xlabel('$u_1$ [rad / s] Spin rate')
plt.axis('tight')
plt.grid()
plt.legend(loc=0)
############################

# states = [q0, q1, q2, q3, q4, u0, u1, u2]
# q0, q1, q2 are Body Fixed (Euler) 3-1-2 angles
# q0:  Yaw / heading angle
# q1:  Lean angle
# q2:  Spin angle
# q3, q4 are N[1], N[2] Inertial positions of contact point
# u0, u1, u2 are the generalized speeds.
# Gravity is in the positive N[3] direction (into the ground)

# Specify the initial conditions of the coordinates
lean = 0.1
qi = [pi/4, lean, 0.0, .001, 0.001]
# Initial angular velocity measure numbers.  Will be used if
# animate_steady==False
# Critical speed is a speed below which the eigenvalues are purely real, a
# stable and an unstable pair.  Above this speed, the eigenvalues are a complex
# pair with no real part -- purely oscillitory.
# Initial condition below critical speed:
ui = [.1, cs[0]*1.1, 0.0]
# Initial condition above critical speed:
#ui = [.3, cs[0]*1.1, 0.0]
#ui = [.3, 15.5, 0.0]
animate_steady = False

# Steady turning conditions require:
# u0 = 0
# u2**2 - 6*u1/tan(q1)*u2 - 4*g*cos(q1)/r = 0
# Given lean angle q1 and gen. speed u1 (spin rate about normal to plane of disc),
# u2 must be a root of the above polynomial.  Note that for zero lean angles,
# the above polynomial is not valid.  Instead, there are three possible
# situations which can be considered steady turns:
# 1)  Rolling in a straight line  (steady turn of infinite radius)
# 2)  Spinning about contact point  (steady turn of zero radius)
# 3)  Static equilibrium   (disc remains upright)

u0i = 0.0  #  Must be 0.0 in a steady turn -- disc can't be falling over

if qi[1] == 0.0:    # If disc is upright, a steady turn is either:
    #  Case for spinning about contact point:
    u1i = 0.0
    u2i = 1.0
    #  Case for rolling in a straight line:
    u1i = 1.0
    u2i = 0.0
    #  Case for static equilibrium:
    u1i = 0.0
    u2i = 0.0
else:
    u1i = 5.0  #  Free to specify
    u2i = roots([1.0, -6.0*u1i/tan(qi[1]), -4*g*cos(qi[1])/r])[0]
ui_s = [u0i, u1i, u2i]

# Inital states
if animate_steady:
    xi = qi + ui_s
else:
    xi = qi + ui

# Integration time
ti = 0.0
ts = 0.01
tf = 30.0
t = arange(ti, tf+ts, ts)
n = len(t)
# Integrate the differential equations
x = odeint(rd.eoms, xi, t, args=(params,))

# Plot the kinetic energy, potential energy, and total energy
ke = zeros((n,1))
pe = zeros((n,1))
te = zeros((n,1))
for i in range(n):
    ke[i], pe[i] = rd.energy(x[i,:], params)
    te[i] = ke[i] + pe[i]

plt.figure()
plt.plot(t, ke, label='KE')
plt.plot(t, pe, label='PE')
plt.plot(t, te, label='TE')
plt.legend()
plt.title('Energy of rolling disc during numerical integration')
plt.xlabel('Time [s]')
plt.ylabel('Energy [kg * m ** 2 / s**2]')
plt.show()

# Animate using Visual-Python
CO = zeros((n, 3))
B2 = zeros((n, 3))
C1 = zeros((n, 3))
C3 = zeros((n, 3))
CN = zeros((n, 3))

# Animation playback speed multiplier (1 == realtime)
k = .1

for i, state in enumerate(x[:,:5]):
    CO[i], B2[i], C1[i], C3[i] = rd.anim(state, r)
    # Make the out of plane axis shorter since this is what control the height
    # of the cone
    B2[i] *= 0.001
    C1[i] *= r
    C3[i] *= r
    CN[i, 0] = state[3]
    CN[i, 1] = state[4]

from visual import display, rate, arrow, curve, cone, box
black = (0,0,0)
red = (1, 0, 0)
green = (0, 1, 0)
blue = (0, 0, 1)
white = (1, 1, 1)
NO = (0,0,0)
#scene = display(title='Rolling disc @ %0.2f realtime'%k, up=(0,0,-1),\
#        uniform=1, background=black, forward=(1,0,0), exit=0)

scene = display(title='Rigid body animation @ %0.2f realtime'%k, width=800,
        height=800, up=(0,0,-1), uniform=1, background=white, forward=(1,0,0))
# Inertial reference frame arrows
N = [arrow(pos=NO,axis=(.001,0,0),color=red),
     arrow(pos=NO,axis=(0,.001,0),color=green),
     arrow(pos=NO,axis=(0,0,.001),color=blue)]
# Two cones are used to look like a thin disc
body1 = cone(pos=CO[0], axis=B2[0], radius=r, color=blue)
body2 = cone(pos=CO[0], axis=-B2[0], radius=r, color=blue)
# Body fixed coordinates in plane of disc, can't really be seen through cones
c1c3 = [arrow(pos=CO[0],axis=C1[0],length=r,color=red),\
        arrow(pos=CO[0],axis=C3[0],length=r,color=green)]
trail = curve()
trail.append(pos=CN[0], color=black)

i = 1
while i<n:
    rate(k/ts)
    body1.pos = CO[i]
    body1.axis = B2[i]
    body2.pos = CO[i]
    body2.axis = -B2[i]
    c1c3[0].pos = body1.pos
    c1c3[1].pos = body1.pos
    c1c3[0].axis = C1[i]
    c1c3[1].axis = C3[i]
    trail.append(pos=CN[i])
    i += 1
