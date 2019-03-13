#
#  Copyright 2019 The FATE Authors. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
import tensorflow as tf

from arch.api.utils import log_utils
from federatedml.ftl.autoencoder import Autoencoder
from federatedml.logistic_regression.hetero_dnn_logistic_regression import HeteroDNNLRGuest
from federatedml.param import LogisticParam
from federatedml.param.param import DNNLocalModelParam
from federatedml.util import ParamExtract
from federatedml.util import consts
from workflow.workflow import WorkFlow

LOGGER = log_utils.getLogger()


class DNNLRGuestWorkFlow(WorkFlow):

    def _initialize_model(self, config):
        logistic_param = LogisticParam()
        local_model_param = DNNLocalModelParam()
        self.logistic_param = ParamExtract.parse_param_from_config(logistic_param, config)
        local_model_param = ParamExtract.parse_param_from_config(local_model_param, config)
        self.local_model = self._create_local_model(local_model_param)
        self.model = HeteroDNNLRGuest(self.local_model, self.logistic_param)
        self.model.set_data_shape(local_model_param.encode_dim)

    def _create_local_model(self, local_model_param):
        autoencoder = Autoencoder("local_guest_model_01")
        autoencoder.build(input_dim=local_model_param.input_dim, hidden_dim=local_model_param.encode_dim,
                          learning_rate=local_model_param.learning_rate)
        return autoencoder

    def _initialize_role_and_mode(self):
        self.role = consts.GUEST
        self.mode = consts.HETERO

    def train(self, train_data_instance, validation_data=None):
        LOGGER.debug("@ enter guest workflow train function")
        init = tf.global_variables_initializer()
        sess = tf.Session()
        self.local_model.set_session(sess)
        sess.run(init)
        super(DNNLRGuestWorkFlow, self).train(train_data_instance, validation_data)
        sess.close()

    def predict(self, data_instance):
        LOGGER.debug("@ enter guest workflow predict function")
        init = tf.global_variables_initializer()
        sess = tf.Session()
        self.local_model.set_session(sess)
        sess.run(init)
        super(DNNLRGuestWorkFlow, self).predict(data_instance)
        sess.close()


if __name__ == "__main__":
    guest_wf = DNNLRGuestWorkFlow()
    guest_wf.run()
