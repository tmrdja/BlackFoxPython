from tempfile import NamedTemporaryFile
from io import BytesIO
import os
import sys
import signal
import time
import shutil
import hashlib
# import ApiClient
from blackfox_restapi.api_client import ApiClient
from blackfox_restapi.configuration import Configuration
# import apis into sdk package
from blackfox_restapi.api.info_api import InfoApi
from blackfox_restapi.api.data_set_api import DataSetApi
from blackfox_restapi.api.ann_model_api import AnnModelApi
from blackfox_restapi.api.ann_optimization_api import AnnOptimizationApi
from blackfox_restapi.api.rnn_model_api import RnnModelApi
from blackfox_restapi.api.rnn_optimization_api import RnnOptimizationApi
from blackfox_restapi.api.random_forest_model_api import RandomForestModelApi
from blackfox_restapi.api.random_forest_optimization_api import RandomForestOptimizationApi
from blackfox_restapi.models.service_info import ServiceInfo

from blackfox import ApiException, NeuralNetworkType, RandomForestModelType, AnnOptimizationConfig, AnnSeriesOptimizationConfig, RnnOptimizationConfig, RandomForestOptimizationConfig, RandomForestSeriesOptimizationConfig, Range, RangeInt, InputConfig, AnnOptimizationEngineConfig, OptimizationAlgorithm
from blackfox.log_writer import LogWriter
from blackfox.validation import (validate_optimization)


BUF_SIZE = 65536  # lets read stuff in 64kb chunks!


class BlackFox:

    """BlackFox provides methods for neural network parameter optimization.

    Parameters
    ----------
    host : str
        Web API url

    """

    def __init__(self, host="http://localhost:50476/"):
        self.host = host
        configuration = Configuration()
        configuration.host = host
        self.client = ApiClient(configuration)
        #check version
        self.info_api = InfoApi(self.client)
        info = self.info_api.get()
        service_version = info.version.split('.')
        default_info = ServiceInfo()
        default_version = default_info.version.split('.')
        if service_version[0] > default_version[0]:
            raise Exception('BlackFox service('+info.version+') is newer than client('+default_info.version+'). Please update client using: pip install blackfox')
        elif service_version[0] < default_version[0]:
            raise Exception('BlackFox service('+info.version+') is older than client('+default_info.version+'). Please revert client to previous version using: pip install blackfox==<version>')
        elif service_version[1] < default_version[1]:
            raise Exception('BlackFox client('+default_info.version+') has some new features than service('+info.version+'). Please revert client to previous version using: pip install blackfox==<version>')
        elif service_version[1] > default_version[1]:
            print('BlackFox service('+info.version+') has some new features. Please update client using: pip install blackfox')
        
        self.data_set_api = DataSetApi(self.client)

        self.ann_model_api = AnnModelApi(self.client)
        self.ann_optimization_api = AnnOptimizationApi(self.client)

        self.rnn_model_api = RnnModelApi(self.client)
        self.rnn_optimization_api = RnnOptimizationApi(self.client)

        self.rf_model_api = RandomForestModelApi(self.client)
        self.rf_optimization_api = RandomForestOptimizationApi(self.client)

    #region log
    def __log_string(self, log_writer, msg):
        if log_writer is not None:
            log_writer.write_string(msg)

    def __log_status(self, log_writer, id, status):
        if log_writer is not None:
            log_writer.write_status(id, status)
    #endregion

    #region data set
    def upload_data_set(self, path):
        id = self.__sha1(path)
        try:
            self.data_set_api.exists(id)
        except ApiException as e:
            if e.status == 404:
                id = self.data_set_api.upload(file=path)
            else:
                raise e
        return id

    def download_data_set(self, id, path):
        temp_path = self.data_set_api.download(id)
        shutil.move(temp_path, path)
    #endregion

    #region utility

    def __get_ranges(self, data_set):
        ranges = []
        for row in data_set:
            for i, d in enumerate(row):
                if len(ranges) <= i or ranges[i] is None:
                    ranges.append(Range(d, d))
                else:
                    r = ranges[i]
                    r.min = min(r.min, d)
                    r.max = max(r.max, d)
        return ranges

    def __fill_inputs(self, inputs, data_set):
        if inputs is None or len(inputs) == 0:
            inputs = []
            for row in data_set:
                for i, d in enumerate(row):
                    if len(inputs) <= i or inputs[i] is None:
                        inputs.append(InputConfig(range=Range(d, d)))
                    else:
                        r = inputs[i].range
                        r.min = min(r.min, d)
                        r.max = max(r.max, d)
        else:
            for j in range(len(inputs)):
                inp = inputs[j]
                if inp.range is None:
                    inp.range = Range(float("inf"), float("-inf"))
                    for row in data_set:
                        d = row[j]
                        inp.range.min = min(inp.range.min, d)
                        inp.range.max = max(inp.range.max, d)
        return inputs

    def __sha1(self, path):
        sha1 = hashlib.sha1()
        try:
            with open(path, 'rb') as f:
                while True:
                    data = f.read(BUF_SIZE)
                    if not data:
                        break
                    sha1.update(data)

        except IOError:
            print("File " + path + " doesn't exist.")

        return sha1.hexdigest()
    #endregion

    #region ann

    def upload_ann_model(self, path):
        id = self.__sha1(path)
        try:
            self.ann_model_api.exists(id)
        except ApiException as e:
            if e.status == 404:
                id = self.ann_model_api.upload(file=path)
            else:
                raise e
        return id

    def download_ann_model(
        self, id, integrate_scaler=False,
        model_type=NeuralNetworkType.H5, path=None
    ):
        print(id, str(integrate_scaler), str(model_type))
        temp_path = self.ann_model_api.download(
            id, integrate_scaler=integrate_scaler, model_type=model_type)
        if path is None:
            return open(temp_path, 'rb')
        else:
            shutil.move(temp_path, path)
            

    def optimize_ann(
        self,
        input_set=None,
        output_set=None,
        data_set_path=None,
        config=AnnOptimizationConfig(),
        model_type=NeuralNetworkType.H5,
        integrate_scaler=False,
        model_path=None,
        delete_on_finish=True,
        status_interval=5,
        log_writer=LogWriter()
    ):
        """Starts the optimization.

        Performs the Black Fox optimization and finds the best parameters and hyperparameters of a target model neural network.

        Parameters
        ----------
        input_set : str
            Input data (x train data)
        output_set : str
            Output data (y train data or target data)
        data_set_path : str
            Optional .csv file used instead of input_set/output_set as a source for training data
        config : AnnOptimizationConfig
            Configuration for Black Fox optimization
        model_type : str
            Optimized model file format (.h5 | .onnx | .pb)
        integrate_scaler : bool
            If True, Black Fox will integrate a scaler function used for data scaling/normalization in the model
        model_path : str
            Save path for the optimized NN; will be used after the function finishes to automatically save optimized model
        delete_on_finish : bool
            Delete optimization from service after it has finished
        status_interval : int
            Time interval for repeated server calls for optimization info and logging
        log_writer : str
            Optional log writer used for logging the optimization process

        Returns
        -------
        (BytesIO, AnnOptimizedModel, dict)
            byte array from model, optimized model info, network metadata
        """
        return self.__optimize_ann(
            is_series=False,
            input_set=input_set,
            output_set=output_set,
            data_set_path=data_set_path,
            config=config,
            model_type=model_type,
            integrate_scaler=integrate_scaler,
            model_path=model_path,
            delete_on_finish=delete_on_finish,
            status_interval=status_interval,
            log_writer=log_writer
        )

    def optimize_ann_series(
        self,
        input_set=None,
        output_set=None,
        data_set_path=None,
        config=AnnSeriesOptimizationConfig(),
        model_type=NeuralNetworkType.H5,
        integrate_scaler=False,
        model_path=None,
        delete_on_finish=True,
        status_interval=5,
        log_writer=LogWriter()
    ):
        """Starts the optimization.

        Performs the Black Fox optimization for timeseries data and finds the best parameters and hyperparameters of a target model neural network.

        Parameters
        ----------
        input_set : str
            Input data (x train data)
        output_set : str
            Output data (y train data or target data)
        data_set_path : str
            Optional .csv file used instead of input_set/output_set as a source for training data
        config : AnnSeriesOptimizationConfig
            Configuration for Black Fox optimization
        model_type : str
            Optimized model file format (.h5 | .onnx | .pb)
        integrate_scaler : bool
            If True, Black Fox will integrate a scaler function used for data scaling/normalization in the model
        model_path : str
            Save path for the optimized NN; will be used after the function finishes to automatically save optimized model
        delete_on_finish : bool
            Delete optimization from service after it has finished
        status_interval : int
            Time interval for repeated server calls for optimization info and logging
        log_writer : str
            Optional log writer used for logging the optimization process

        Returns
        -------
        (BytesIO, AnnOptimizedModel, dict)
            byte array from model, optimized network info, model metadata
        """
        return self.__optimize_ann(
            is_series=True,
            input_set=input_set,
            output_set=output_set,
            data_set_path=data_set_path,
            config=config,
            model_type=model_type,
            integrate_scaler=integrate_scaler,
            model_path=model_path,
            delete_on_finish=delete_on_finish,
            status_interval=status_interval,
            log_writer=log_writer
        )

    def __optimize_ann(
        self,
        is_series=False,
        input_set=None,
        output_set=None,
        data_set_path=None,
        config=None,
        model_type=NeuralNetworkType.H5,
        integrate_scaler=False,
        model_path=None,
        delete_on_finish=True,
        status_interval=5,
        log_writer=LogWriter()
    ):
        print('Use CTRL + C to stop optimization')
        tmp_file = None
        if input_set is not None and output_set is not None:
            if type(input_set) is not list:
                input_set = input_set.tolist()
            if type(output_set) is not list:
                output_set = output_set.tolist()
            tmp_file = NamedTemporaryFile(delete=False)
            # input ranges
            config.inputs = self.__fill_inputs(config.inputs, input_set)
            # output ranges
            if config.output_ranges is None:
                config.output_ranges = self.__get_ranges(output_set)
            data_set = list(map(lambda x, y: (','.join(map(str, x)))+',' +
                                (','.join(map(str, y))), input_set, output_set))

            column_count = len(config.inputs) + len(config.output_ranges)
            column_range = range(0, column_count)
            headers = map(lambda i: 'column_'+str(i), column_range)
            data_set.insert(0, ','.join(headers))
            csv = '\n'.join(data_set)
            tmp_file.write(csv.encode("utf-8"))
            tmp_file.close()
            if data_set_path is not None:
                self.__log_string(log_writer, 'Ignoring data_set_path')
            data_set_path = str(tmp_file.name)

        if is_series:
            if len(config.inputs) != len(config.input_window_range_configs):
                raise Exception('Number of input columns is not same as input_window_range_configs')
            if len(config.output_ranges) != len(config.output_window_configs):
                raise Exception('Number of output columns is not same as output_window_configs')

        if config.hidden_layer_count_range is None:
            config.hidden_layer_count_range = RangeInt(1, 15)

        if config.dropout is None:
            config.dropout = Range(0, 0.25)

        if config.engine_config is None:
            config.engine_config = AnnOptimizationEngineConfig()
        if config.engine_config.mutation_probability is None:
            if config.engine_config.optimization_algorithm == OptimizationAlgorithm.VIDNEROVANERUDA:
                config.engine_config.mutation_probability = 0.2
            else:
                config.engine_config.mutation_probability = 0.01

        if config.neurons_per_layer is None:
            if config.inputs is None or config.output_ranges is None:
                config.neurons_per_layer = RangeInt(1, 10)
            else:
                avg_count = int(len(config.inputs) + len(config.output_ranges)) / 2
                min_neurons = int(avg_count / 3)
                max_neurons = int(avg_count * 3)
                if min_neurons <= 0:
                    min_neurons = 1
                if max_neurons < 10:
                    max_neurons = 10
                config.neurons_per_layer = RangeInt(min_neurons, max_neurons)

        if data_set_path is not None:
            if config.inputs is None:
                self.__log_string(log_writer, "config.inputs is None")
                return None, None, None
            if config.output_ranges is None:
                self.__log_string(log_writer, "config.output_ranges is None")
                return None, None, None
            if tmp_file is not None:
                self.__log_string(log_writer, "Uploading data set")
            else:
                self.__log_string(
                    log_writer, "Uploading data set " + data_set_path)
            config.dataset_id = self.upload_data_set(data_set_path)

        if tmp_file is not None:
            os.remove(tmp_file.name)

        self.__log_string(log_writer, "Starting...")
        if is_series:
            id = self.ann_optimization_api.start_series(ann_series_optimization_config=config)
        else:
            id = self.ann_optimization_api.start(ann_optimization_config=config)

        return self.continue_ann_optimization(id, model_type, integrate_scaler, model_path,  delete_on_finish, status_interval, log_writer)

    def continue_ann_optimization(self, id, model_type=NeuralNetworkType.H5, integrate_scaler=False, model_path=None, delete_on_finish=True, status_interval=5, log_writer=LogWriter()):
        """Continue optimization.

        Continue the Black Fox optimization and finds the best parameters and hyperparameters of a target model neural network.

        Parameters
        ----------
        id : str
            Optimization id
        model_type : str
            Optimized model file format (.h5 | .onnx | .pb)
        integrate_scaler : bool
            If True, Black Fox will integrate a scaler function used for data scaling/normalization in the model
        model_path : str
            Save path for the optimized NN; will be used after the function finishes to automatically save optimized model
        delete_on_finish : bool
            Delete optimization from service after it has finished
        status_interval : int
            Time interval for repeated server calls for optimization info and logging
        log_writer : str
            Optional log writer used for logging the optimization process

        Returns
        -------
        (BytesIO, AnnOptimizedModel, dict)
            byte array from model, optimized network info, model metadata
        """
        def signal_handler(sig, frame):
            self.__log_string(log_writer, "Stopping optimization : "+id)
            if hasattr(log_writer, 'log_file') is False or log_writer.log_file is not sys.stdout:
                print("Stopping optimization: "+id)
            self.stop_ann_optimization(id)

        signal.signal(signal.SIGINT, signal_handler)

        running = True
        status = None
        while running:
            try:
                status = self.ann_optimization_api.get_status(id)
                if status is not None and len(status) > 0:
                    status = status[-1]
                running = (status.state == 'Active')
                self.__log_status(log_writer, id, status)
            except Exception as e:
                self.__log_string(log_writer, "Error: " + str(e))
            time.sleep(status_interval)

        if status.state == 'Finished' or status.state == 'Stopped':
            print('Optimization state: ', status.state)
            if status.best_model is not None:
                model_id = self.ann_optimization_api.get_model_id(id, status.generation)
                self.__log_string(log_writer, "Downloading model " + model_id)
                model_stream = self.download_ann_model(
                    model_id,
                    integrate_scaler=integrate_scaler,
                    model_type=model_type
                )
                data = model_stream.read()
                if model_path is not None:
                    self.__log_string(log_writer,
                                      "Saving model " +
                                      model_id + " to " + model_path)
                    with open(model_path, 'wb') as f:
                        f.write(data)
                byte_io = BytesIO(data)
                metadata = self.ann_model_api.get_metadata(model_id)
                if delete_on_finish:
                    self.ann_optimization_api.delete(id)
                return byte_io, status.best_model, metadata
            else:
                return None, None, None

        elif status.state == 'Error':
            self.__log_string(log_writer, "Optimization error")
        else:
            self.__log_string(log_writer, "Unknown error")

        return None, None, None

    @validate_optimization
    def optimize_ann_async(
        self,
        config=AnnOptimizationConfig(),
        data_set_path=None
    ):
        """Async optimization call.

        Performs the Black Fox optimization asynchronously (non-blocking), so the user must querry the server periodically in order to get the progress info.

        Parameters
        ----------
        config : KerasOptimizationConfig
            Configuration for Black Fox optimization
        data_set_path : str
            Path to a .csv file holding the training dataset

        Returns
        -------
        str
            Optimization process id
        """
        # validate_optimize_keras(config)
        if data_set_path is not None:
            config.dataset_id = self.upload_data_set(data_set_path)
        return self.optimization_api.post(config=config)

    def get_ann_optimization_status(self, id):
        """Gets current async optimization status.

        Query of the current optimization status when it is performed asynchronously.

        Parameters
        ----------
        id : str
            Optimization process id
        Returns
        -------
        list[AnnOptimizationStatus]
            An object depicting the current optimization status
        """
        status = self.ann_optimization_api.get_status(id)

        return status

    def stop_ann_optimization(self, id):
        """Stops current async optimization.

        Sends a request for stopping the ongoing optimization, and returns the current best solution.

        Parameters
        ----------
        id : str
            Optimization process id
        model_path : str
            Save path for the optimized NN; will be used after the function finishes to automatically save optimized network

        Returns
        -------
        AnnOptimizationStatus
            An object depicting the current optimization status
        """
        self.ann_optimization_api.stop(id)
        state = 'Active'
        last_status = None
        while state == 'Active':
            status = self.get_ann_optimization_status(id)
            if status is not None or len(status) > 0:
                last_status = status[-1]
                state = last_status.state

        return last_status

    #endregion

    #region rnn

    def upload_rnn_model(self, path):
        id = self.__sha1(path)
        try:
            self.rnn_model_api.exists(id)
        except ApiException as e:
            if e.status == 404:
                id = self.rnn_model_api.upload(file=path)
            else:
                raise e
        return id

    def download_rnn_model(
        self, id, integrate_scaler=False,
        model_type=NeuralNetworkType.H5, path=None
    ):
        temp_path = self.rnn_model_api.download(
            id, integrate_scaler=integrate_scaler, model_type=model_type)
        if path is None:
            return open(temp_path, 'rb')
        else:
            shutil.move(temp_path, path)

    def optimize_rnn(
        self,
        input_set=None,
        output_set=None,
        integrate_scaler=False,
        model_type=NeuralNetworkType.H5,
        data_set_path=None,
        config=RnnOptimizationConfig(),
        model_path=None,
        status_interval=5,
        log_writer=LogWriter()
    ):
        """Starts the optimization.

        Performs the Black Fox optimization using recurrent neural networks and finds the best parameters and hyperparameters of a target model.

        Parameters
        ----------
        input_set : str
            Input data (x train data)
        output_set : str
            Output data (y train data or target data)
        integrate_scaler : bool
            If True, Black Fox will integrate a scaler function used for data scaling/normalization in the model
        model_type : str
            Optimized model file format (.h5 | .onnx | .pb)
        data_set_path : str
            Optional .csv file used instead of input_set/output_set as a source for training data
        config : RnnOptimizationConfig
            Configuration for Black Fox optimization
        model_path : str
            Save path for the optimized NN; will be used after the function finishes to automatically save optimized network
        status_interval : int
            Time interval for repeated server calls for optimization info and logging
        log_writer : str
            Optional log writer used for logging the optimization process

        Returns
        -------
        (BytesIO, KerasOptimizedNetwork, dict)
            byte array from network model, optimized network info, network metadata
        """
        print('Use CTRL + C to stop optimization')
        tmp_file = None
        if input_set is not None and output_set is not None:
            if type(input_set) is not list:
                input_set = input_set.tolist()
            if type(output_set) is not list:
                output_set = output_set.tolist()
            tmp_file = NamedTemporaryFile(delete=False)
            # input ranges
            config.inputs = self.__fill_inputs(config.inputs, input_set)
            # output ranges
            if config.output_ranges is None:
                config.output_ranges = self.__get_ranges(output_set)
            data_set = list(map(lambda x, y: (','.join(map(str, x)))+',' +
                                (','.join(map(str, y))), input_set, output_set))

            column_count = len(config.inputs) + len(config.output_ranges)
            column_range = range(0, column_count)
            headers = map(lambda i: 'column_'+str(i), column_range)
            data_set.insert(0, ','.join(headers))
            csv = '\n'.join(data_set)
            tmp_file.write(csv.encode("utf-8"))
            tmp_file.close()
            if data_set_path is not None:
                self.__log_string(log_writer, 'Ignoring data_set_path')
            data_set_path = str(tmp_file.name)

        if config.hidden_layer_count_range is None:
            config.hidden_layer_count_range = RangeInt(1, 15)

        if config.dropout is None:
            config.dropout = Range(0, 0.25)

        if config.recurrent_dropout is None:
            config.recurrent_dropout = Range(0, 0.25)

        if config.neurons_per_layer is None:
            if config.inputs is None or config.output_ranges is None:
                config.neurons_per_layer = RangeInt(1, 10)
            else:
                avg_count = int(len(config.inputs) + len(config.output_ranges)) / 2
                min_neurons = int(avg_count / 3)
                max_neurons = int(avg_count * 3)
                if min_neurons <= 0:
                    min_neurons = 1
                if max_neurons < 10:
                    max_neurons = 10
                config.neurons_per_layer = RangeInt(min_neurons, max_neurons)

        if data_set_path is not None:
            if config.inputs is None:
                self.__log_string(log_writer, "config.inputs is None")
                return None, None, None
            if config.output_ranges is None:
                self.__log_string(log_writer, "config.output_ranges is None")
                return None, None, None
            if tmp_file is not None:
                self.__log_string(log_writer, "Uploading data set")
            else:
                self.__log_string(log_writer, "Uploading data set " +
                                  data_set_path)
            config.dataset_id = self.upload_data_set(data_set_path)

        if tmp_file is not None:
            os.remove(tmp_file.name)

        self.__log_string(log_writer, "Starting...")
        id = self.rnn_optimization_api.post(config=config)
        return self.continue_rnn_optimization(id, model_path, status_interval, log_writer)

    def continue_rnn_optimization(self, id, model_path=None, status_interval=5, log_writer=LogWriter()):
        """Continue optimization.

        Countinue the Black Fox optimization using recurrent neural networks and finds the best parameters and hyperparameters of a target model.

        Parameters
        ----------
        id : str
            Optimization id
        model_path : str
            Save path for the optimized NN; will be used after the function finishes to automatically save optimized network
        status_interval : int
            Time interval for repeated server calls for optimization info and logging
        log_writer : str
            Optional log writer used for logging the optimization process

        Returns
        -------
        (BytesIO, KerasOptimizedNetwork, dict)
            byte array from network model, optimized network info, network metadata
        """
        def signal_handler(sig, frame):
            self.__log_string(log_writer, "Stopping optimization : "+id)
            if hasattr(log_writer, 'log_file') is False or log_writer.log_file is not sys.stdout:
                print("Stopping optimization: "+id)
            self.stop_rnn_optimization(id)

        signal.signal(signal.SIGINT, signal_handler)

        running = True
        status = None
        while running:
            status = self.recurrent_optimization_api.get_status(id)
            if status is not None and len(status) > 0:
                status = status[0]
            running = (status.state == 'Active')
            self.__log_status(log_writer, id, status)
            time.sleep(status_interval)

        if status.state == 'Finished' or status.state == 'Stopped':
            print('Optimization state: ', status.state)
            if status.network is not None and status.network.id is not None:
                self.__log_string(log_writer,
                                  "Downloading network " +
                                  status.network.id)
                network_stream = self.download_network(
                    status.network.id,
                    integrate_scaler=integrate_scaler,
                    model_type=model_type
                )
                data = network_stream.read()
                if model_path is not None:
                    self.__log_string(log_writer,
                                      "Saving network " +
                                      status.network.id + " to " + model_path)
                    with open(model_path, 'wb') as f:
                        f.write(data)
                byte_io = BytesIO(data)
                metadata = self.network_api.get_metadata(status.network.id)
                return byte_io, status.network, metadata
            else:
                return None, None, None

        elif status.state == 'Error':
            self.__log_string(log_writer, "Optimization error")
        else:
            self.__log_string(log_writer, "Unknown error")

        return None, None, None

    #endregion

    #region random forest

    def upload_random_forest_model(self, path):
        id = self.__sha1(path)
        try:
            self.rf_model_api.exists(id)
        except ApiException as e:
            if e.status == 404:
                id = self.rf_model_api.upload(file=path)
            else:
                raise e
        return id

    def download_random_forest_model(
        self, id, integrate_scaler=False,
        model_type=RandomForestModelType.BINARY, path=None
    ):
        temp_path = self.rf_model_api.download(
            id, integrate_scaler=integrate_scaler, model_type=model_type)
        if path is None:
            return open(temp_path, 'rb')
        else:
            shutil.move(temp_path, path)

    def optimize_random_forest_sync(
        self,
        input_set=None,
        output_set=None,
        integrate_scaler=False,
        model_type='h5',
        data_set_path=None,
        config=None,
        model_path=None,
        status_interval=5,
        log_writer=LogWriter()
    ):
        """Starts the optimization.

        Performs the Black Fox optimization using random forest and finds the best parameters and hyperparameters of a target model.

        Parameters
        ----------
        input_set : str
            Input data (x train data)
        output_set : str
            Output data (y train data or target data)
        integrate_scaler : bool
            If True, Black Fox will integrate a scaler function used for data scaling/normalization in the model
        model_type : str
            Optimized model file format (.h5 | .onnx | .pb)
        data_set_path : str
            Optional .csv file used instead of input_set/output_set as a source for training data
        config : RandomForestOptimizationConfig
            Configuration for Black Fox optimization
        model_path : str
            Save path for the optimized NN; will be used after the function finishes to automatically save optimized network
        status_interval : int
            Time interval for repeated server calls for optimization info and logging
        log_writer : str
            Optional log writer used for logging the optimization process

        Returns
        -------
        (BytesIO, KerasOptimizedNetwork, dict)
            byte array from network model, optimized network info, network metadata
        """
        print('Use CTRL + C to stop optimization')
        tmp_file = None
        if input_set is not None and output_set is not None:
            if type(input_set) is not list:
                input_set = input_set.tolist()
            if type(output_set) is not list:
                output_set = output_set.tolist()
            tmp_file = NamedTemporaryFile(delete=False)
            # input ranges
            config.inputs = self.__fill_inputs(config.inputs, input_set)
            # output ranges
            if config.output_ranges is None:
                config.output_ranges = self.__get_ranges(output_set)
            data_set = list(map(lambda x, y: (','.join(map(str, x)))+',' +
                                (','.join(map(str, y))), input_set, output_set))

            column_count = len(config.inputs) + len(config.output_ranges)
            column_range = range(0, column_count)
            headers = map(lambda i: 'column_'+str(i), column_range)
            data_set.insert(0, ','.join(headers))
            csv = '\n'.join(data_set)
            tmp_file.write(csv.encode("utf-8"))
            tmp_file.close()
            if data_set_path is not None:
                self.__log_string(log_writer, 'Ignoring data_set_path')
            data_set_path = str(tmp_file.name)

        if data_set_path is not None:
            if config.inputs is None:
                self.__log_string(log_writer, "config.inputs is None")
                return None, None, None
            if config.output_ranges is None:
                self.__log_string(log_writer, "config.output_ranges is None")
                return None, None, None
            if tmp_file is not None:
                self.__log_string(log_writer, "Uploading data set")
            else:
                self.__log_string(log_writer, "Uploading data set " +
                                  data_set_path)
            config.dataset_id = self.upload_data_set(data_set_path)

        if tmp_file is not None:
            os.remove(tmp_file.name)

        self.__log_string(log_writer, "Starting...")
        id = self.optimization_api.post_forest(config=config)

        def signal_handler(sig, frame):
            self.__log_string(log_writer, "Stopping optimization : "+id)
            if hasattr(log_writer, 'log_file') is False or log_writer.log_file is not sys.stdout:
                print("Stopping optimization : "+id)
            self.stop_random_forest_optimization(id)

        signal.signal(signal.SIGINT, signal_handler)

        running = True
        status = None
        while running:
            status = self.optimization_api.get_status(id)
            running = (status.state == 'Active')
            self.__log_status(log_writer, id, status)
            time.sleep(status_interval)

        if status.state == 'Finished' or status.state == 'Stopped':
            print('Optimization state: ', status.state)
            if status.network is not None and status.network.id is not None:
                self.__log_string(log_writer,
                                  "Downloading network " +
                                  status.network.id)
                network_stream = self.download_network(
                    status.network.id,
                    integrate_scaler=integrate_scaler,
                    model_type=model_type
                )
                data = network_stream.read()
                if model_path is not None:
                    self.__log_string(log_writer,
                                      "Saving network " +
                                      status.network.id + " to " + model_path)
                    with open(model_path, 'wb') as f:
                        f.write(data)
                byte_io = BytesIO(data)
                metadata = self.network_api.get_metadata(status.network.id)
                return byte_io, status.network, metadata
            else:
                return None, None, None

        elif status.state == 'Error':
            self.__log_string(log_writer, "Optimization error")
        else:
            self.__log_string(log_writer, "Unknown error")

        return None, None, None

    #endregion

    #region metadata
    def get_ann_metadata(self, model_path):
        """Ann model metadata retrieval

        Gets the neural network metadata from a network file.

        Parameters
        ----------
        model_path : str
            Load path for the model file from which the metadata would be read

        Returns
        -------
        dict
            ann model metadata
        """
        id = None
        if isinstance(model_path, BytesIO):
            with NamedTemporaryFile(delete=False) as out:
                out.write(model_path.read())
                file_path = str(out.name)
            id = self.upload_ann_model(file_path)
            os.remove(file_path)
        else:
            id = self.upload_ann_model(model_path)

        return self.ann_model_api.get_metadata(id)

    def get_rnn_metadata(self, model_path):
        """Rnn model metadata retrieval

        Gets the neural network metadata from a network file.

        Parameters
        ----------
        model_path : str
            Load path for the model file from which the metadata would be read

        Returns
        -------
        dict
            rnn model metadata
        """
        id = None
        if isinstance(model_path, BytesIO):
            with NamedTemporaryFile(delete=False) as out:
                out.write(model_path.read())
                file_path = str(out.name)
            id = self.upload_rnn_model(file_path)
            os.remove(file_path)
        else:
            id = self.upload_rnn_model(model_path)

        return self.rnn_model_api.get_metadata(id)

    def get_random_forest_metadata(self, model_path):
        """Random forest model metadata retrieval

        Gets the random forest metadata from a model file.

        Parameters
        ----------
        model_path : str
            Load path for the model file from which the metadata would be read

        Returns
        -------
        dict
            model metadata
        """
        id = None
        if isinstance(model_path, BytesIO):
            with NamedTemporaryFile(delete=False) as out:
                out.write(model_path.read())
                file_path = str(out.name)
            id = self.upload_random_forest_model(file_path)
            os.remove(file_path)
        else:
            id = self.upload_random_forest_model(model_path)

        return self.random_forest_model_api.get_metadata(id)

    #endregion

    #region convert
    def convert_ann_to(self, model_path, model_type, model_dst_path=None, integrate_scaler=False):
        id = None
        if isinstance(model_path, BytesIO):
            with NamedTemporaryFile(delete=False) as out:
                out.write(model_path.read())
                file_path = str(out.name)
            id = self.upload_network(file_path)
            os.remove(file_path)
        else:
            id = self.upload_network(model_path)
        stream = self.download_network(
            id,
            model_type=model_type,
            integrate_scaler=integrate_scaler,
            path=model_dst_path
        )
        if stream is not None:
            data = stream.read()
            byte_io = BytesIO(data)
            return byte_io

    def convert_ann_to_onnx(
        self, model_path,
        model_dst_path=None, integrate_scaler=False
    ):
        self.convert_to(model_path, 'onnx', model_dst_path,
                        integrate_scaler=integrate_scaler)

    def convert_ann_to_pb(
        self, model_path,
        model_dst_path=None, integrate_scaler=False
    ):
        self.convert_to(model_path, 'pb', model_dst_path,
                        integrate_scaler=integrate_scaler)
    #endregion
