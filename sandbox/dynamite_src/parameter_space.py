import yaml

class Parameter(object):

    def __init__(self,
                 desc=None,
                 fixed=False,
                 LaTeX=None,
                 sformat="%g",
                 value=None,
                 grid_parspace_settings=None,
                 gpe_parspace_settings=None
                 # lo=None,
                 # hi=None,
                 # step=None,
                 # minstep=None,
                 ):
        self.valid = ('desc', 'fixed', 'LaTeX', 'sformat', 'value', 'grid_parspace_settings', 'gpe_parspace_settings')
        self.desc = desc
        self.fixed = fixed
        self.LaTeX = LaTeX
        self.sformat = sformat
        self.value = value
        self.grid_parspace_settings = None
        self.gpe_parspace_settings = None
        # self.lo = lo
        # self.hi = hi
        # self.step = step
        # self.minstep = minstep

    def update(self, **kwargs):
        for k, v in kwargs.items():
            if k not in self.valid:
                raise ValueError('Invalid parameter key', k, '. Allowed keys: ', self.valid)
            self.k = v


class BlackHoleParameters(object):
#    def __init__(self, *, name, **kwargs):
    def __init__(self, name=None, **kwargs):
        self.mass = None
        self.radius = None
        if name is not None:
            self.add(self, name, **kwargs)

#    def add(self, *, name, **kwargs):
    def add(self, name, **kwargs):
        if name == 'mass':
            self.mass = Parameter(**kwargs)
        elif name == 'radius':
            self.radius = Parameter(**kwargs)
        else:
            raise ValueError('Unknown black hole parameter', name, ', use mass or radius')

    def validate(self):
        if (self.mass is not None and self.radius is not None):
            return True
        else:
            return False


class StellarParameters(object):
#    def __init__(self, *, name, **kwargs):
    def __init__(self, name=None, **kwargs):
        self.q = None
        self.p = None
        self.u = None
        if name is not None:
            self.add(self, name, **kwargs)
        # if (name == 'q'):
        #     self.q = Parameter(**kwargs)
        # elif (name == 'p'):
        #     self.p = Parameter(**kwargs)
        # elif (name == 'u'):
        #     self.u = Parameter(**kwargs)
        # else:
        #     raise ValueError('Unknown stellar parameter ', name, ', use q, p, or u')

#    def add(self, *, name, **kwargs):
    def add(self, name, **kwargs):
        update = False
        if (name == 'q'):
            if (self.q is None):
                update = True
            self.q = Parameter(**kwargs)
        elif (name == 'p'):
            if (self.p is None):
                update = True
            self.p = Parameter(**kwargs)
        elif (name == 'u'):
            if (self.u is None):
                update = True
            self.u = Parameter(**kwargs)
        else:
            raise ValueError('Unknown stellar parameter ', name, ', use q, p, or u')
        return update

    def validate(self):
        if (self.q is not None and self.p is not None and self.u is not None):
            return True
        else:
            return False


class ParameterSpace(object):

    def __init__(self, system):

        self.n_par = system.n_par
        self.n_par_fixed = 0
        for cmp in system.cmp_list:
            for par in cmp.parameters:
                self.n_par_fixed += par.fixed
        self.n_par_free = self.n_par - self.n_par_fixed


class ParameterGenerator(object):

    def __init__(self,
                 param_list=[]):
        self.param_list = param_list

    def generate(self, current_models, n_new):
        # placeholder function to generate a list of "n_new" parameters
        # return new_parameter_list
        stop = self.check_stopping_critera()
        if stop:
            return []
        # else ...
        return []

    def check_stopping_critera(self, current_models):
        stop_generic = self.check_generic_stopping_critera()
        stop_specific = self.check_specific_stopping_critera()
        stop = stop_generic or stop_specific
        return stop

    def check_generic_stopping_critera(self, current_models):
        stop = True # or false
        return stop


class GridSearch(ParameterGenerator):

    def generate(self, current_models=None, n_new=0):
        # actual code to do grid search
        # return new_parameter_list of length n_new
        return []

    def check_specific_stopping_critera(self, current_models):
        stop = True # or false
        return stop


class GaussianProcessEmulator(ParameterGenerator):

    def generate(self, current_models=None, n_new=0):
        # actual code to do gaussian process emulation
        # return new_parameter_list of length n_new
        return []

    def check_specific_stopping_critera(self, current_models):
        stop = True # or false
        return stop


# end
