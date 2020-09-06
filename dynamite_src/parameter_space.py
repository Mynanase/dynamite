# # some tricks to add the current path to sys.path (so the imports below work)

# import os.path
# import sys

# this_dir = os.path.dirname(__file__)
# if not this_dir in sys.path:
#     sys.path.append(this_dir)

import numpy as np
import copy
# import schwarzschild
from astropy import table
import parameter_space as parspace

class Parameter(object):

    attributes = []
    def __init__(self,
                 name=None,
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
        self.name = name
        self.desc = desc
        self.fixed = fixed
        self.LaTeX = LaTeX
        self.sformat = sformat
        self.value = value
        self.grid_parspace_settings = grid_parspace_settings
        self.gpe_parspace_settings = gpe_parspace_settings
        # self.lo = lo
        # self.hi = hi
        # self.step = step
        # self.minstep = minstep
        self.__class__.attributes = list(self.__dict__.keys())

    def update(self, **kwargs):
        for k, v in kwargs.items():
            if k not in self.__class__.attributes:
                raise ValueError(f'Invalid parameter key {k}. Allowed keys: {str(tuple(self.__class__.attributes))}')
            setattr(self, k, v)

    def validate(self):
        if sorted(self.__class__.attributes) != sorted(self.__dict__.keys()):
            raise ValueError(f'Parameter attributes can only be {str(tuple(self.__class__.attributes))} , not {str(tuple(self.__dict__.keys()))}')

    def __repr__(self):
        return (f'{self.__class__.__name__}({self.__dict__})')


class ParameterSpace(list):

    def __init__(self, system):
        for cmp in system.cmp_list:
            for par in cmp.parameters:
                self.append(par)
        for par in system.parameters:
            self.append(par)

        self.par_names = []
        for par in self:
            self.par_names.append(par.name)

        self.n_par = len(self)
        self.n_par_fixed = len([p for p in self if p.fixed])
        self.n_par_free = self.n_par - self.n_par_fixed

    def __repr__(self):
        return (f'{self.__class__.__name__}({[p for p in self]}, {self.__dict__})')


class ParameterGenerator(object):

    def __init__(self,
                 par_space=[],
                 name=None):
        self.par_space = par_space
        self.name = name
        self.status = {}

    def generate(self,
                 current_models=None,
                 kw_specific_generate_method={}):
        if current_models is None:
            raise ValueError('current_models needs to be a valid schwarzschild.AllModels instance')
        else:
            self.current_models = current_models
        self.check_stopping_critera()
        if not self.status['stop']: # check whether we need to do anything in the first place...
            self.specific_generate_method(**kw_specific_generate_method)
            newmodels = 0
            # Add new models to current_models.table
            for m in self.model_list:
                if self._is_newmodel(m, eps=1e-10):
                    row = [p.value for p in m]
                    for i in range(self.par_space.n_par, len(self.current_models.table.colnames)):
                        row.append([np.dtype(self.current_models.table.columns[i].dtype).type(0)])
                    self.current_models.table.add_row(row)
                    newmodels += 1
        print(f'{self.name} added {newmodels} new models')
        self.status['n_new_models'] = newmodels
        self.status['last_iter_added_no_new_models'] = True if newmodels == 0 else False
        if newmodels == 0:
            self.status['stop'] = True
        return self.status

    def check_stopping_critera(self):
        self.status['stop'] = False
        self.check_generic_stopping_critera()
        self.check_specific_stopping_critera()
        for key in [reasons for reasons in self.status if isinstance(reasons, bool) and reasons != 'stop']:
            if self.status[key]:
                self.status['stop'] = True
                break

    def check_generic_stopping_critera(self):
        self.status['n_max_mods_reached'] = \
            True if len(self.current_models.table) >= self.current_models.settings.parameter_space_settings['stopping_criteria']['n_max_mods'] \
                 else False
        # e.g. stop if:
        # i) number of models which have been run > max_n_mods => done
        # ii) number of iterations > max_n_iter => CODE ME: need iter_count in astropy table
        self.status['n_max_iter_reached'] = False
        # iii) ...

    def _is_newmodel(self, model, eps=1e-6):
        """
        Checks if model is a new model (i.e., its parameter set does not exist in
        self.current_models).

        Parameters
        ----------
        model : A self.model_list element (list of Parameter objects), must be given
        eps : Used for numerical comparison (relative difference w.r.t. model values), default is 1e-6

        Returns
        -------
        isnew : True if model is a new model, False otherwise.

        """
        if any(map(lambda t: not isinstance(t, parspace.Parameter), model)):
            raise ValueError('Model argument must be a list of Parameter objects')
        model_values = [p.value for p in model]
        if len(self.current_models.table) > 0:
            isnew = True
            for curmod in self.current_models.table[self.par_space.par_names]:
                if np.allclose(list(curmod), model_values, rtol=eps):
                    isnew = False
                    break
        else:
            isnew = True
        return isnew

    def model_compare(self, model1=None, model2=None, eps=1e-10): # might not need this method...
        """
        Compares the parameter sets of two models

        Parameters
        ----------
        model1, model2 : Model objects
        eps : accuracy for numerical comparison (default: 1e-10)

        Returns
        -------
        True if parameter sets have the same .value attributes and are in the
        same order, False otherwise
        """
        for paridx in range(len(model1.parset)):
            if abs(model1.parset[paridx].value-model2.parset[paridx].value) > eps:
                return False
        return True


class GridSearch(ParameterGenerator):

    def __init__(self,
                 par_space=[]):
        super().__init__(par_space=par_space,
                         name='GridWalk')

    def specific_generate_method(self, **kwargs):
        """
        Adds new models to current_models.table. The center is determined as the parameter set with
        the least chi2+kinchi2 value.

        Parameters
        ----------
        current_models : a schwarzschild.AllModels instance. Mandatory argument.
        n_new : not used. The default is 0.

        Raises
        ------
        ValueError if current_models is not provided

        Returns
        -------
        dict, self.status, self.status['stop'] == True if stopping criteria is met
        """
        if len(self.current_models.table) == 0: # The 'zeroth iteration' results in only one model (all parameters at their .value level)
            self.model_list = [[p for p in self.par_space]]
        else: # Subsequent iterations...
            # Center criterion: min(chi2+kinchi2)
            chi2_all = [m['chi2']+m['kinchi2'] for m in self.current_models.table]
            center_idx = np.argmin(chi2_all)
            center = list(self.current_models.table[center_idx])[:self.par_space.n_par]
            # print(f'center: {center}')
            # Build model_list by walking the grid
            self.model_list = []
            self.grid_walk(center=center)
            # for m in self.model_list:
            #     print(f'{[(p.name, p.value) for p in m]}')
        return

    def grid_walk(self, center=None, par=None, eps=1e-6):
        """
        Walks the grid defined by self.par_space.grid_parspace_settings attributes.
        Clips parameter values to lo/hi attributes. If clipping violates the minstep attribute,
        the resulting model(s) will not be created. If the minstep attribute is missing, the step
        attribute will be used instead. Use minstep=0 to eliminate minstep.

        Parameters
        ----------
        center : List of center coordinates. Must be in the same sequence as the parameters
                 in self.par_space. Mandatory argument.
        par : Internal use only. Gives the parameter to start with. Set automatically in the
              recursive process. The default is None.
        eps : Used for numerical comparison (relative tolerance), default is 1e-6

        Raises
        ------
        ValueError if center is not specified or fixed parameters differ from center.

        Returns
        -------
        None. Sets self.model_list to the resulting models.

        """
        if center == None:
            raise ValueError('Need center')
        if not par:
            par = self.par_space[0]
        paridx = self.par_space.index(par)
        # print(f'Call with paridx={paridx}, n_par={self.par_space.n_par}')

        if par.fixed:
            par_values = [par.value]
            if abs(center[paridx] - par.value) > eps:
                raise ValueError('Something is wrong: fixed parameter value not in center')
        else:
            lo = par.grid_parspace_settings['lo']
            hi = par.grid_parspace_settings['hi']
            # par_values will take up to 3 *distinct* clipped lo, mid, hi values
            par_values = []
            # use 'minstep' value if present, otherwise use 'step'
            minstep = par.grid_parspace_settings['minstep'] if 'minstep' in par.grid_parspace_settings else par.grid_parspace_settings['step']
            # start with lo...
            delta = center[paridx] - self.clip(center[paridx] - par.grid_parspace_settings['step'], lo, hi)
            if abs(delta) >= minstep:
                par_values.append(self.clip(center[paridx] - par.grid_parspace_settings['step'], lo, hi))
            # now mid... tol(erance) is necessary in case minstep < eps
            if len(par_values) > 0:
                tol = abs(self.clip(center[paridx], lo, hi) - par_values[0]) # check for values differing by more than eps...
                if abs(par_values[0]) > eps: # use relative tolerance if possible
                    tol /= abs(par_values[0])
                if tol > eps:
                    par_values.append(self.clip(center[paridx], lo, hi))
            else:
                par_values.append(self.clip(center[paridx], lo, hi))
            # and now hi...
            delta = self.clip(center[paridx] + par.grid_parspace_settings['step'], lo, hi) - center[paridx]
            if abs(delta) >= minstep:
                tol = abs(self.clip(center[paridx] + par.grid_parspace_settings['step'], lo, hi) - par_values[-1])
                if abs(par_values[-1]) > eps:
                    tol /= abs(par_values[-1])
                if tol > eps:
                    par_values.append(self.clip(center[paridx] + par.grid_parspace_settings['step'], lo, hi))

        for par.value in par_values:
            # par.value = value
            if not self.model_list: # add first entry if model_list is empty
                self.model_list = [[copy.deepcopy(par)]]
                models_prev = [[]]
                # print(f'new model list, starting with parameter {par.name}')
            elif par.name in [p.name for p in self.model_list[0]]: # in this case, create new (partial) model by copying last models and setting the new parameter value
                for m in models_prev:
                    new_model = m + [copy.deepcopy(par)]
                    self.model_list.append(new_model)
                # print(f'{par.name} is in {[p.name for p in self.model_list[0]]}, added {par.name}={par.value}')
            else: # new parameter - simply append the parameter to existing (partial) models
                models_prev = copy.deepcopy(self.model_list)
                for m in self.model_list:
                    m.append(copy.deepcopy(par))
                # print(f'new parameter {par.name}={par.value}')

        if paridx < self.par_space.n_par - 1: # call recursively until all paramaters are done...
            self.grid_walk(center=center, par=self.par_space[paridx+1])

    def clip(self, value, mini, maxi):
        """
        Clips value to the interval [mini, maxi]. Similar to the numpy.clip() method.
        If mini==maxi, that value is returned.

        Parameters
        ----------
        value : numeric value
        mini : numeric value
        maxi : numeric value

        Raises
        ------
        ValueError if mini > maxi

        Returns
        -------
        min(max(mini, value), maxi)

        """
        if mini <= maxi:
            return min(max(mini, value), maxi)
        else:
            raise ValueError('Clip error: minimum must be less than or equal to maximum')

    def check_specific_stopping_critera(self):
        stop = False
        # stop if...
        # (i) if iter>1, last iteration did not improve chi2 by min_delta_chi2
        # where we'll set min_delta_chi2 in config file => CODE ME: need iter_count in astropy table
        self.status['min_delta_chi2_reached'] = False
        # (ii) if step_size < min_step_size for all params => dealt with by grid_walk (doesn't create such models)
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
