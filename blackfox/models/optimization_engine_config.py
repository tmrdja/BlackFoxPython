# coding: utf-8

"""
    BlackFox

    No description provided (generated by Swagger Codegen https://github.com/swagger-api/swagger-codegen)  # noqa: E501

    OpenAPI spec version: v1
    
    Generated by: https://github.com/swagger-api/swagger-codegen.git
"""


import pprint
import re  # noqa: F401

import six

from blackfox.models.convergency_criterion import ConvergencyCriterion  # noqa: F401,E501


class OptimizationEngineConfig(object):
    """NOTE: This class is auto generated by the swagger code generator program.

    Do not edit the class manually.
    """

    """
    Attributes:
      swagger_types (dict): The key is attribute name
                            and the value is attribute type.
      attribute_map (dict): The key is attribute name
                            and the value is json key in definition.
    """
    swagger_types = {
        'optimization_algorithm': 'str',
        'crossover_distribution_index': 'int',
        'crossover_probability': 'float',
        'mutation_distribution_index': 'int',
        'mutation_probability': 'float',
        'proc_timeout_miliseconds': 'int',
        'max_num_of_generations': 'int',
        'population_size': 'int',
        'hyper_volume': 'ConvergencyCriterion'
    }

    attribute_map = {
        'optimization_algorithm': 'optimizationAlgorithm',
        'crossover_distribution_index': 'crossoverDistributionIndex',
        'crossover_probability': 'crossoverProbability',
        'mutation_distribution_index': 'mutationDistributionIndex',
        'mutation_probability': 'mutationProbability',
        'proc_timeout_miliseconds': 'procTimeoutMiliseconds',
        'max_num_of_generations': 'maxNumOfGenerations',
        'population_size': 'populationSize',
        'hyper_volume': 'hyperVolume'
    }

    def __init__(self, optimization_algorithm=None, crossover_distribution_index=None, crossover_probability=None, mutation_distribution_index=None, mutation_probability=None, proc_timeout_miliseconds=None, max_num_of_generations=None, population_size=None, hyper_volume=None):  # noqa: E501
        """OptimizationEngineConfig - a model defined in Swagger"""  # noqa: E501

        self._optimization_algorithm = "SimpleGA"
        self._crossover_distribution_index = 20
        self._crossover_probability = 0.9
        self._mutation_distribution_index = 20
        self._mutation_probability = 0.01
        self._proc_timeout_miliseconds = 2000000
        self._max_num_of_generations = 10
        self._population_size = 20
        self._hyper_volume = ConvergencyCriterion()
        self.discriminator = None

        if optimization_algorithm is not None:
            self.optimization_algorithm = optimization_algorithm
        if crossover_distribution_index is not None:
            self.crossover_distribution_index = crossover_distribution_index
        if crossover_probability is not None:
            self.crossover_probability = crossover_probability
        if mutation_distribution_index is not None:
            self.mutation_distribution_index = mutation_distribution_index
        if mutation_probability is not None:
            self.mutation_probability = mutation_probability
        if proc_timeout_miliseconds is not None:
            self.proc_timeout_miliseconds = proc_timeout_miliseconds
        if max_num_of_generations is not None:
            self.max_num_of_generations = max_num_of_generations
        if population_size is not None:
            self.population_size = population_size
        if hyper_volume is not None:
            self.hyper_volume = hyper_volume

    @property
    def optimization_algorithm(self):
        """Gets the optimization_algorithm of this OptimizationEngineConfig.  # noqa: E501


        :return: The optimization_algorithm of this OptimizationEngineConfig.  # noqa: E501
        :rtype: str
        """
        return self._optimization_algorithm

    @optimization_algorithm.setter
    def optimization_algorithm(self, optimization_algorithm):
        """Sets the optimization_algorithm of this OptimizationEngineConfig.


        :param optimization_algorithm: The optimization_algorithm of this OptimizationEngineConfig.  # noqa: E501
        :type: str
        """
        allowed_values = ["SimpleGA", "VidnerovaNeruda"]  # noqa: E501
        if optimization_algorithm not in allowed_values:
            raise ValueError(
                "Invalid value for `optimization_algorithm` ({0}), must be one of {1}"  # noqa: E501
                .format(optimization_algorithm, allowed_values)
            )

        self._optimization_algorithm = optimization_algorithm

    @property
    def crossover_distribution_index(self):
        """Gets the crossover_distribution_index of this OptimizationEngineConfig.  # noqa: E501


        :return: The crossover_distribution_index of this OptimizationEngineConfig.  # noqa: E501
        :rtype: int
        """
        return self._crossover_distribution_index

    @crossover_distribution_index.setter
    def crossover_distribution_index(self, crossover_distribution_index):
        """Sets the crossover_distribution_index of this OptimizationEngineConfig.


        :param crossover_distribution_index: The crossover_distribution_index of this OptimizationEngineConfig.  # noqa: E501
        :type: int
        """

        self._crossover_distribution_index = crossover_distribution_index

    @property
    def crossover_probability(self):
        """Gets the crossover_probability of this OptimizationEngineConfig.  # noqa: E501


        :return: The crossover_probability of this OptimizationEngineConfig.  # noqa: E501
        :rtype: float
        """
        return self._crossover_probability

    @crossover_probability.setter
    def crossover_probability(self, crossover_probability):
        """Sets the crossover_probability of this OptimizationEngineConfig.


        :param crossover_probability: The crossover_probability of this OptimizationEngineConfig.  # noqa: E501
        :type: float
        """

        self._crossover_probability = crossover_probability

    @property
    def mutation_distribution_index(self):
        """Gets the mutation_distribution_index of this OptimizationEngineConfig.  # noqa: E501


        :return: The mutation_distribution_index of this OptimizationEngineConfig.  # noqa: E501
        :rtype: int
        """
        return self._mutation_distribution_index

    @mutation_distribution_index.setter
    def mutation_distribution_index(self, mutation_distribution_index):
        """Sets the mutation_distribution_index of this OptimizationEngineConfig.


        :param mutation_distribution_index: The mutation_distribution_index of this OptimizationEngineConfig.  # noqa: E501
        :type: int
        """

        self._mutation_distribution_index = mutation_distribution_index

    @property
    def mutation_probability(self):
        """Gets the mutation_probability of this OptimizationEngineConfig.  # noqa: E501


        :return: The mutation_probability of this OptimizationEngineConfig.  # noqa: E501
        :rtype: float
        """
        return self._mutation_probability

    @mutation_probability.setter
    def mutation_probability(self, mutation_probability):
        """Sets the mutation_probability of this OptimizationEngineConfig.


        :param mutation_probability: The mutation_probability of this OptimizationEngineConfig.  # noqa: E501
        :type: float
        """

        self._mutation_probability = mutation_probability

    @property
    def proc_timeout_miliseconds(self):
        """Gets the proc_timeout_miliseconds of this OptimizationEngineConfig.  # noqa: E501


        :return: The proc_timeout_miliseconds of this OptimizationEngineConfig.  # noqa: E501
        :rtype: int
        """
        return self._proc_timeout_miliseconds

    @proc_timeout_miliseconds.setter
    def proc_timeout_miliseconds(self, proc_timeout_miliseconds):
        """Sets the proc_timeout_miliseconds of this OptimizationEngineConfig.


        :param proc_timeout_miliseconds: The proc_timeout_miliseconds of this OptimizationEngineConfig.  # noqa: E501
        :type: int
        """
        if proc_timeout_miliseconds is None:
            raise ValueError("Invalid value for `proc_timeout_miliseconds`, must not be `None`")  # noqa: E501
        if proc_timeout_miliseconds is not None and proc_timeout_miliseconds > 2147483647:  # noqa: E501
            raise ValueError("Invalid value for `proc_timeout_miliseconds`, must be a value less than or equal to `2147483647`")  # noqa: E501
        if proc_timeout_miliseconds is not None and proc_timeout_miliseconds < 0:  # noqa: E501
            raise ValueError("Invalid value for `proc_timeout_miliseconds`, must be a value greater than or equal to `0`")  # noqa: E501

        self._proc_timeout_miliseconds = proc_timeout_miliseconds

    @property
    def max_num_of_generations(self):
        """Gets the max_num_of_generations of this OptimizationEngineConfig.  # noqa: E501


        :return: The max_num_of_generations of this OptimizationEngineConfig.  # noqa: E501
        :rtype: int
        """
        return self._max_num_of_generations

    @max_num_of_generations.setter
    def max_num_of_generations(self, max_num_of_generations):
        """Sets the max_num_of_generations of this OptimizationEngineConfig.


        :param max_num_of_generations: The max_num_of_generations of this OptimizationEngineConfig.  # noqa: E501
        :type: int
        """

        self._max_num_of_generations = max_num_of_generations

    @property
    def population_size(self):
        """Gets the population_size of this OptimizationEngineConfig.  # noqa: E501


        :return: The population_size of this OptimizationEngineConfig.  # noqa: E501
        :rtype: int
        """
        return self._population_size

    @population_size.setter
    def population_size(self, population_size):
        """Sets the population_size of this OptimizationEngineConfig.


        :param population_size: The population_size of this OptimizationEngineConfig.  # noqa: E501
        :type: int
        """

        self._population_size = population_size

    @property
    def hyper_volume(self):
        """Gets the hyper_volume of this OptimizationEngineConfig.  # noqa: E501


        :return: The hyper_volume of this OptimizationEngineConfig.  # noqa: E501
        :rtype: ConvergencyCriterion
        """
        return self._hyper_volume

    @hyper_volume.setter
    def hyper_volume(self, hyper_volume):
        """Sets the hyper_volume of this OptimizationEngineConfig.


        :param hyper_volume: The hyper_volume of this OptimizationEngineConfig.  # noqa: E501
        :type: ConvergencyCriterion
        """

        self._hyper_volume = hyper_volume

    def to_dict(self):
        """Returns the model properties as a dict"""
        result = {}

        for attr, _ in six.iteritems(self.swagger_types):
            value = getattr(self, attr)
            if isinstance(value, list):
                result[attr] = list(map(
                    lambda x: x.to_dict() if hasattr(x, "to_dict") else x,
                    value
                ))
            elif hasattr(value, "to_dict"):
                result[attr] = value.to_dict()
            elif isinstance(value, dict):
                result[attr] = dict(map(
                    lambda item: (item[0], item[1].to_dict())
                    if hasattr(item[1], "to_dict") else item,
                    value.items()
                ))
            else:
                result[attr] = value

        return result

    def to_str(self):
        """Returns the string representation of the model"""
        return pprint.pformat(self.to_dict())

    def __repr__(self):
        """For `print` and `pprint`"""
        return self.to_str()

    def __eq__(self, other):
        """Returns true if both objects are equal"""
        if not isinstance(other, OptimizationEngineConfig):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other
