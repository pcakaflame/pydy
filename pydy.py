from sympy import Symbol, Basic, Mul, Pow, Matrix, sin, cos, S, eye, Add, \
        trigsimp

e1 = Matrix([1, 0, 0])
e2 = Matrix([0, 1, 0])
e3 = Matrix([0, 0, 1])
e1n = Matrix([-1, 0, 0])
e2n = Matrix([0, -1, 0])
e3n = Matrix([0, 0, -1])
zero = Matrix([0, 0, 0])
t = Symbol("t")

class UnitVector(Basic):
    """A standard unit vector  with a symbolic and a numeric representation"""

    # XXX: UnitVector should be noncommutative in Mul, but currently it is
    # probably commutative. However, we haven't found any case, where this
    # actually fails, so until we find some, let's leave it as is and keep this
    # in mind.
    def __init__(self, frame, i=0): #=-1,num=None):
        self.frame = frame    # Parent reference frame
        self.i = i
        self.v = {}
        s = frame.name
        if i == 1:
            self.v['sym'] = Symbol(s.lower()+str(i))
            self.v['num'] = e1
        elif i == 2:
            self.v['sym'] = Symbol(s.lower()+str(i))
            self.v['num'] = e2
        elif i == 3:
            self.v['sym'] = Symbol(s.lower()+str(i))
            self.v['num'] = e3
        elif i == -1:
            self.v['sym'] = Symbol('-'+s.lower()+str(abs(i)))
            self.v['num'] = e1n
        elif i == -2:
            self.v['sym'] = Symbol('-'+s.lower()+str(abs(i)))
            self.v['num'] = e2n
        elif i == -3:
            self.v['sym'] = Symbol('-'+s.lower()+str(abs(i)))
            self.v['num'] = e3n
        elif i == 0:
            self.v['sym'] = Symbol(s.lower()+str(0))
            self.v['num'] = zero

    def _sympystr_(self):
        return str(self.v['sym']) + ">"


class Vector(Basic):
    """
    General vector expression.  Internally represented as a dictionary whose
    keys are UnitVectors and whose key values are the corresponding coefficient
    of that UnitVector.  For example:
    N = ReferenceFrame("N")
    x, y, z = symbols('x y z')
    v = Vector(x*N[1]+y*N[2] + z*N[3])
    then v would be represented internally as:
    {N[1]: x, N[2]: y, N[3]: z}
    """

    def __init__(self, v):
        if isinstance(v, dict):
            self.dict = v
        else:
            self.dict = self.parse_terms(v)

    def parse_terms(self,v):
        #    """
        #Given a Sympy expression with UnitVector terms, return a dictionary whose
        #keys are the UnitVectors and whose values are the coeefficients of the
        #UnitVectors
        #"""

        if v == 0:
            return {}
        elif isinstance(v, UnitVector):
            v.expand()
            return {v : S(1)}
        elif isinstance(v, Mul):
            v.expand()
            for b in v.args:
                if isinstance(b, UnitVector):
                    return {b: v.coeff(b)}
        elif isinstance(v, Pow):
            v.expand()
            #  I don't think this will ever be entered into.
            #  You would have to have something like A[1]*A[2],
            #  which isn't a valid vector expression.
            #  Or q1*q2, which is a scalar expression.
            for b in v.args:
                if isinstance(b, UnitVector):
                    return {b: v.coeff(b)}
        elif isinstance(v, Add):
            v.expand()
            terms = {}
            for b in v.args:
                #print "b = ", b, "type(b): ", type(b)
                #print "b parsed = ", parse_terms(b)
                bp = self.parse_terms(b)
                #print "bp.keys(): ", bp.keys()[0]
                if terms.has_key(bp.keys()[0]):
                    terms[bp.keys()[0]] += bp[bp.keys()[0]]
                else:
                    terms.update(self.parse_terms(b))
            return terms
        else:
            return NotImplemented

    def __add__(self, other):
        list1 = self.dict.keys()
        list2 = other.dict.keys()
        intersection = filter(lambda x:x in list1, list2)
        difference = filter(lambda x:x not in list2, list1)
        union=list1+filter(lambda x:x not in list1,list2)
        sum = {}
        '''
        for k in intersection:
            sum.update({k: self.dict[k] + other.dict[k]})
        for k in difference:
            if self.dict.has_key(k):
                sum.update({k: self.dict[k]})
            elif other.dict.has_key(k):
                sum.update({k: other.dict[k]})
        return Vector(sum)
        '''
        for k in union:
            if k in list1 and k in list2:
                sum.update({k: (self.dict[k] + other.dict[k])})
            elif (k in list1) and not (k in list2):
                sum.update({k: self.dict[k]})
            elif not (k in list1) and (k in list2):
                sum.update({k: other.dict[k]})
            else:
                print "shouldn't have gotten here"
        return Vector(sum)

    def __eq__(self, other):
        if self.dict == other.dict:
            return True
        else:
            return False

class Particle:
    def __init__(self, s, m):
        self.mass = m
        self.name = s


class ReferenceFrame:
    """A standard reference frame with 3 dextral orthonormal vectors"""

    def __init__(self, s, matrix=None, frame=None, omega=None):
        """
        ReferenceFrame('B', matrix, A)
        The matrix represents A_B, e.g. how to transform a vector from B to A.
        """


        if frame == None:
            self.ref_frame_list = [self]
        else:
            #print "inside __init__: ", frame.ref_frame_list
            self.ref_frame_list = frame.ref_frame_list[:]
            self.ref_frame_list.insert(0,self)

        self.name = s
        self.triad = [UnitVector(self, i) for i in (1,2,3)]
        self.transforms = {}
        self.parent = frame
        self.W = {}
        if omega != None:
            self.set_omega(omega, self.parent)
            self.parent.set_omega(-omega, self, force=True)

        if frame is not None:
            self.append_transform(frame, matrix)
            frame.append_transform(self, matrix.T)

    def __getitem__(self, i):
        return self.triad[i-1]

    def append_transform(self, frame, matrix):
        """
        Gives us a transform to the frame "frame".
        """
        # We just append it to our "transforms" dict.
        self.transforms[frame] = matrix

    def rotate(self, name, axis, angle):
        if axis == 1:
            matrix = Matrix([
                [1, 0, 0],
                [0, cos(angle), -sin(angle)],
                [0, sin(angle), cos(angle)],
                ])
            omega = angle.diff(t)*self[axis]
            #print "omega = ", omega
        elif axis == 2:
            matrix = Matrix([
                [cos(angle), 0, sin(angle)],
                [0, 1, 0],
                [-sin(angle), 0, cos(angle)],
                ])
            omega = angle.diff(t)*self[axis]
            #print "omega = ", omega
        elif axis == 3:
            matrix = Matrix([
                [cos(angle), -sin(angle), 0],
                [sin(angle), cos(angle), 0],
                [0, 0, 1],
                ])
            omega = angle.diff(t)*self[axis]
            #print "omega = ", omega
        else:
            raise ValueError("wrong axis")
        return ReferenceFrame(name, matrix, self, omega)

    def __repr__(self):
        return "<Frame %s>" % self.name

    def get_frames_list(self, frame):
        """
        Returns a list of frames from "self" to "frame", including both.

        Example:

        N - A - D - E - F
            |
            B
            |
            C

        Then:

        C.get_frames_list(F) == [C, B, A, D, E, F]
        F.get_frames_list(C) == [F, E, D, A, B, C]
        """
        if self == frame:
            return [self]
        else:
            r2t = [f for f in reversed(frame.ref_frame_list)]

            if len(self.ref_frame_list) == 1:
                return r2t
            elif len(r2t) == 1:
                return self.ref_frame_list

            r1t = [f for f in reversed(self.ref_frame_list)]
            i = 1
            while r1t[i] == r2t[i]:
                del r1t[i-1]
                del r2t[i-1]
                if len(r1t)<=2 or len(r2t)<=2:
                    break

            r1t.reverse()
            return r1t[:-1] + r2t

    def get_rot_matrices(self, frame):
        """
        Returns a list of matrices to get from self to frame.
        """
        frames = self.get_frames_list(frame)
        if frames == [self]:
            return [eye(3)]
        result = []
        for i, f in enumerate(frames[:-1]):
            result.append(f.transforms[frames[i+1]])
        result.reverse()
        return result

    def set_omega(self, W, frame, force=False):
        """
        Sets the angular velocity Omega with respect to the frame "frame".
        """
        if self.W == {} or force:
            self.W[frame] = W
        else:
            raise ValueError("set_omaga has already been called.")

    def get_omega(self, frame):
        """
        Returns the angular velocity Omega with respect to the frame "frame".

        E.g. it returns W_A_N, where A=self, N=frame
        """

        if self.W.has_key(frame):
            return self.W[frame]
        else:
            #print self.W
            return sum(self.get_omega_list(frame))
            raise NotImplementedError()

    def get_omega_list(self, frame):
        """
        Returns a list of simple angular velocities from self to frame.
        """
        frames = self.get_frames_list(frame)
        if frames == [self]:
            return [S(0)]
        result = []
        for i, f in enumerate(frames[:-1]):
            result.append(f.W[frames[i+1]])
        return result


class RigidBody(ReferenceFrame, Particle):
    def __init__(self, s, matrix=None, frame=None, omega=None, m=0, I=0):
        ReferenceFrame.__init__(self, s, Matrix=None, frame=None, omega=None)
        Particle.__init__(self,s+'O', m)
        self.inertia = I


def dot(v1,v2):
    if isinstance(v1, UnitVector) and isinstance(v2, UnitVector):
        B = v2.frame
        u = express(v1, B)
        u1, u2, u3 = expression2vector(u, B)
        # second vector:
        v = Matrix(v2.v['num'])
        return dot_vectors((u1, u2, u3), v)
    else:
        v1v2 = (v1*v2).expand()
        #print "DOT:", v1v2
        if isinstance(v1v2, Add):
            #print v1v2.args
            e = 0
            for a in v1v2.args:
                c, v1, v2 = identify(a)
                #print "IDENTIFY", c, v1, v2, a
                if v1 is None or v2 is None:
                    raise Exception("!")
                else:
                    #print "c", c
                    #print "dot", dot(v1, v2)
                    e += c*dot(v1, v2)
            return e
        elif isinstance(v1v2, Mul):
            c, v1, v2 = identify(v1v2)
            if v1 is None or v2 is None:
                raise NotImplementedError()
            else:
                e = c*dot(v1, v2)
            return e
        elif v1v2 == 0:
            return v1v2
        else:
            raise NotImplementedError()


def dot2(v1,v2):
    """
    Alternative implementation of dot product
    """

    v1.expand()
    v2.expand()
    v1_dict = parse_terms(v1)
    v2_dict = parse_terms(v2)
    return v1_dict,v2_dict


'''
def parse_terms(v):
    #"""
    #Given a Sympy expression with UnitVector terms, return a dictionary whose
    #keys are the UnitVectors and whose values are the coeefficients of the
    #UnitVectors
    #"""
    v.expand()
    if v == 0:
        return {}
    elif isinstance(v, UnitVector):
        return {v : S(1)}
    elif isinstance(v, Mul):
        for b in v.args:
            if isinstance(b, UnitVector):
                return {b: v.coeff(b)}
        return NotImplemented
    elif isinstance(v, Pow):
        #  I don't think this will ever be entered into.
        #  You would have to have something like A[1]*A[2],
        #  which isn't a valid vector expression.
        #  Or q1*q2, which is a scalar expression.
        for b in v.args:
            if isinstance(b, UnitVector):
                return {b: v.coeff(b)}
    elif isinstance(v, Add):
        terms = {}
        for b in v.args:
            #print "b = ", b, "type(b): ", type(b)
            #print "b parsed = ", parse_terms(b)
            bp = parse_terms(b)
            #print "bp.keys(): ", bp.keys()[0]
            if terms.has_key(bp.keys()[0]):
                terms[bp.keys()[0]] += bp[bp.keys()[0]]
            else:
                terms.update(parse_terms(b))
        return terms
    else:
        return NotImplemented
'''


def identify(a):
    """
    Takes a Mul instance and parses it as

    a = c * UnitVector() * UnitVector()

    and returns c, v1, v2, where v1 and v2 are the UnitVectors.
    """
    if isinstance(a, Mul):
        unit_vectors = []
        for b in a.args:
            if isinstance(b, UnitVector):
                unit_vectors.append(b)
            if isinstance(b, Pow):
                if isinstance(b.args[0], UnitVector):
                    unit_vectors.append(b.args[0])
                    unit_vectors.append(b.args[0])
        if len(unit_vectors) == 2:
            v1 = unit_vectors[0]
            v2 = unit_vectors[1]
            c = coeff(a, v1*v2)
            #XXX here is a bug, if a=B[1]*Derivative()*B[1] and we do coeff for
            #B[1]**2
            #print "identify, coeff", a, v1*v2, c
            return c, v1, v2

    return a, None, None

def identify_v1(a):
    """
    Takes a Mul instance and parses it as

    a = c * UnitVector()

    and returns c, v1 where v1 is the UnitVector.
    """
    if isinstance(a, UnitVector):
        return S(1), a
    elif isinstance(a, Mul):
        unit_vectors = []
        for b in a.args:
            if isinstance(b, UnitVector):
                unit_vectors.append(b)
            if isinstance(b, Pow):
                if isinstance(b.args[0], UnitVector):
                    unit_vectors.append(b.args[0])
                    unit_vectors.append(b.args[0])
        if len(unit_vectors) == 1:
            v1 = unit_vectors[0]
            c = a.coeff(v1)
            return c, v1

    return a, None

def express(v, frame):
    """
    Express "v" in the reference frame "frame".
    """
    if isinstance(v, UnitVector):
        matrices = v.frame.get_rot_matrices(frame)
        #print matrices
        u = Matrix(v.v['num'])
        #XXX: Not sure why reversed is necessary
        for m in reversed(matrices):
            u = m*u
        return vector2expression(u, frame)
    elif isinstance(v, Add):
        e = 0
        for a in v.args:
            c, v1 = identify_v1(a)
            #print c, v1
            if v1 is None:
                pass
            else:
                e += c*express(v1, frame)
        e = e.expand()
        u = expression2vector(e, frame)
        u = [trigsimp(x) for x in u]
        return vector2expression(u, frame)
    elif isinstance(v, Mul):
        c, v1 = identify_v1(v)
        return (c*express(v1, frame)).expand()
    elif v == 0:
        return v
    else:
        #print "XXX", v
        raise NotImplementedError()

def cross_vectors(u, v):
    c1 = u[1]*v[2] - u[2]*v[1]
    c2 = -(u[0]*v[2] - u[2]*v[0])
    c3 = u[0]*v[1] - u[1]*v[0]
    return c1, c2, c3

def dot_vectors(u, v):
    return u[0]*v[0]+u[1]*v[1]+u[2]*v[2]

def coeff(e, x):
    """
    Workaround the bug in sympy.
    """
    if isinstance(x, list):
        r = []
        for xi in x:
            ri = e.coeff(xi)
            if ri is None:
                r.append(S(0))
            else:
                r.append(ri)
        return r
    else:
        r = e.coeff(x)
        if r is None:
            return S(0)
        else:
            return r

def cross(v1, v2):
    if isinstance(v1, UnitVector) and isinstance(v2, UnitVector):
        B = v2.frame
        u = express(v1, B)
        u1, u2, u3 = expression2vector(u, B)
        # second vector:
        v = Matrix(v2.v['num'])
        c1, c2, c3 = cross_vectors((u1, u2, u3), v)
        return c1*B[1] + c2*B[2] + c3*B[3]
    else:
        v1v2 = (v1*v2).expand()
        if isinstance(v1v2, Add):
            e = 0
            for a in v1v2.args:
                c, v1, v2 = identify(a)
                if v1 is None or v2 is None:
                    pass
                else:
                    e += c*cross(v1, v2)
            return e
        elif isinstance(v1v2, Mul):
            c, v1, v2 = identify(v1v2)
            if v1 is None or v2 is None:
                raise NotImplementedError()
            else:
                e = c*cross(v1, v2)
            return e
        raise NotImplementedError()

def expression2vector(e, frame):
    """
    Converts a sympy expression "e" to a coefficients vector in the frame "frame".
    """
    u1 = coeff(e, frame[1])
    u2 = coeff(e, frame[2])
    u3 = coeff(e, frame[3])
    return u1, u2, u3

def vector2expression(u, frame):
    """
    Converts a coefficients vector to a sympy expression in the frame "frame".
    """
    return u[0]*frame[1] + u[1]*frame[2] + u[2]*frame[3]

def dt(u, frame, t):
    if isinstance(u, Add):
        r = 0
        for a in u.args:
            c, v = identify_v1(a)
            #print "c = ", c, "type(c)", type(c), "v = ",v, "type(v)", type(v)
            dc_dt = c.diff(t)
            W = v.frame.get_omega(frame)
            #print "W = ", W, "type(W):", type(W)
            if W == 0:
                print "W = 0"
                print "r = ", r, "dc_dt = ", dc_dt, "v = ", v
                r += dc_dt * v
                continue
            #print "dc_dt*v + W x v", dc_dt, v, W, v, cross(W, v)
            r += dc_dt * v + c*cross(W, v)
        r = r.expand()
        return r

    elif isinstance(u, Mul):
        c, v = identify_v1(u)
        #print "c = ", c, "v = ", v
        dc_dt = c.diff(t)
        W = v.frame.get_omega(frame)
        #print "W = ", W
        #print "W x v = ", cross(W,v)
        r = dc_dt * v + c*cross(W, v)
        return r
    else:
        raise NotImplementedError()

from sympy.printing.pretty.pretty import PrettyPrinter, xsym
# here is how to get a nice symbol for multiplication:
# print xsym("*")
from sympy.printing.str import StrPrinter

class PyDyPrinter(StrPrinter):
    printmethod = "_pydystr_"

    #def _print_Symbol(self, e):
    #    return "|%s|" % str(e)

    def _print_UnitVector(self, e):
        one = "\xe2\x82\x81"
        two = "\xe2\x82\x82"
        three = "\xe2\x82\x83"
        bold = "\033[1m"
        reset = "\033[0;0m"
        s = str(e.v['sym'])
        name = s[:-1]
        index = s[-1]
        r = "%s%s%s" % (bold, name, reset)
        if index == "1":
            r += one
        elif index == "2":
            r += two
        elif index == "3":
            r += three
        return r

    def _print_sin(self, e):
        name = str(e.args[0])
        if name[0] == "q":
            index = name[1]
            return "s_%s" % index
        else:
            return str(e)


def print_pydy(e):
    pp = PyDyPrinter()
    print pp.doprint(e)
