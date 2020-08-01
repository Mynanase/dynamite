#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 16 15:14:17 2020

@author: maindl
"""

import yaml
#import dynamite_src.physical_system as physys
from dynamite_src.physical_system import *
import dynamite_src.parameter_space as parspace
import dynamite_src.kinematics as kinem
import dynamite_src.populations as popul

class Configuration(object):
    """
    Class that collect misc configuration settings
    """
    def __init__(self):
        self.orblib_settings = {}
        self.parameter_space_settings = {}

    def add(self, kind, values):
        if kind == 'orblib_settings':
            self.orblib_settings = values
        elif kind == 'parameter_space_settings':
            self.parameter_space_settings = values
        else:
            raise ValueError('Config only takes orblib_settings and parameter_space_settings')

    def validate(self):
        if not(self.orblib_settings and self.parameter_space_settings):
            raise ValueError('Config needs orblib_settings and parameter_space_settings')

    def __repr__(self):
        return (f'{self.__class__.__name__}({self.__dict__})')


class ConfigurationReaderYaml(object):
    """
    Reads the configuration file and instantiates the objects
    self.system, ...
    """
    def __init__(self, filename=None, silent=False): # instantiate the objects here. instead of the dict, self.system will be a System object, etc.
        """
        Reads onfiguration file and instantiates objects. Does some rudimentary
        checks for consistency.

        Parameters
        ----------
        filename : string, needs to refer to an existing file including path
        silent : True suppresses output, default=False

        Raises
        ------
        FileNotFoundError
            DESCRIPTION. If file does not exist or filename is None or not given.

        Returns
        -------
        None.

        """

        if filename is not None:
            with open(filename, 'r') as f:
                self.params = yaml.safe_load(f)
        else:
            raise FileNotFoundError('Please specify filename')

        self.system = System() # instantiate System object
        self.config = Configuration() # instantiate Configuration object
#        self.__dict__ = par

        for key, value in self.params.items(): # walk through the file contents...

            # add components to system

            if key == 'model_components':
                if not silent:
                    print('model_components:')
                for comp, data_comp in value.items():
                    if not data_comp['include']:
                            if not silent:
                                print('', comp, '  ...ignored')
                            continue

                    # instantiate the component

                    if not silent:
                        print(f" {comp}... instantiating {data_comp['type']} object")
                    if 'contributes_to_potential' not in data_comp:
                        raise ValueError(f'Component {comp} needs contributes_to_potential attribute')
                    c = globals()[data_comp['type']](contributes_to_potential = data_comp['contributes_to_potential'])

                    # initialize the componnt's paramaters, kinematics, and populations

                    par_list, kin_list, pop_list = [], [], []

                    # read parameters

                    if 'parameters' not in data_comp:
                        raise ValueError('Component ' + comp + ' needs parameters')
                    if not silent:
                        print(f" Has parameters {tuple(data_comp['parameters'].keys())}")
                    for par, data_par in data_comp['parameters'].items():
                        the_parameter = parspace.Parameter(name=par, **data_par)
                        par_list.append(the_parameter)
                    c.parameters = par_list

                    # read kinematics

                    if 'kinematics' in data_comp:   # shall we include a check here (e.g., only VisibleComponent can have kinematics?)
                        if not silent:
                            print(f" Has kinematics {tuple(data_comp['kinematics'].keys())}")
                        for kin, data_kin in data_comp['kinematics'].items():
                            kinematics_set = kinem.Kinematics(**data_kin)
                            kin_list.append(kinematics_set)
                        c.kinematic_data = kin_list

                    # read populations

                    if 'populations' in data_comp:   # shall we include a check here (e.g., only VisibleComponent can have populations?)
                        if not silent:
                            print(f" Has populations {tuple(data_comp['populations'].keys())}")
                        for pop, data_pop in data_comp['populations'].items():
                            populations_set = popul.Populations(**data_pop)
                            pop_list.append(populations_set)
                        c.population_data = pop_list

                    # add component to system
    
                    self.system.add_component(c)
    
            # add other parameters to system

            elif key == 'other_parameters':
                if not silent:
                    print('other_parameters...')
                    print(f' {tuple(value.keys())}')
                for other, data in value.items():
                    if other == 'ml':
                        self.system.ml = parspace.Parameter(**data)
                    else:
                        setattr(self.system, other, data)

            # add orbit library settings to config object

            elif key == 'orblib_settings':
                if not silent:
                    print('orblib_settings...')
                    print(f' {tuple(value.keys())}')
                self.config.add('orblib_settings', value)

            # add parameter space settings to config object

            elif key == 'parameter_space_settings':
                if not silent:
                    print('parameter_space_settings...')
                    print(f' {tuple(value.keys())}')
                self.config.add('parameter_space_settings', value)

            else:
                raise ValueError(f'Unknown configuration key: {key}')

        #self.system.validate()
        #self.config.validate()

        if not silent:
            print(f'**** System assembled:\n{self.system}')
            print(f'**** Configuration data:\n{self.config}')



    # def read_parameters(self, par=None, items=None):
    #     """
    #     Will add each key-value pair in items to parameters object par by calling
    #     par.add(...) and subsequently calls the par.validate() method.

    #     Parameters
    #     ----------
    #     par : ...parameters object, optional
    #         The default is None.
    #     items : dictionary, optional
    #         The default is None.

    #     Returns
    #     -------
    #     None.

    #     """
        
    #     for p, v in items:
    #         par.add(name=p, **v)
    #     par.validate()
